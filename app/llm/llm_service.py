import requests
from pathlib import Path
from typing import Generator
from dotenv import load_dotenv  # <-- Bunu əlavə edirik

from google import genai
from google.genai import types

from app.llm.tools import TOOL_ENDPOINT_MAP, POST_TOOLS, build_gemini_tools

FASTAPI_URL = "http://localhost:8001"
MAX_HISTORY = 20
TEMPERATURE = 0.3

BASE_DIR = Path(__file__).parent

# 1. Müştərini başlatmadan əvvəl .env faylındakı dəyişənləri sistemə (os.environ) yükləyirik
load_dotenv()

# 2. İndi genai.Client() GOOGLE_API_KEY-i avtomatik tapacaq
client = genai.Client()


def _load_system_prompt(role: str) -> str:
    path = BASE_DIR / "system_prompts" / f"{role}.txt"
    with open(path, encoding="utf-8") as f:
        return f.read()


def _call_fastapi(tool_name: str, arguments: dict) -> dict:
    print(f"[DEBUG] Tool called: {tool_name}  args: {arguments}")
    endpoint = TOOL_ENDPOINT_MAP.get(tool_name)
    if not endpoint:
        return {"error": f"No endpoint mapped for tool '{tool_name}'"}
    try:
        if tool_name in POST_TOOLS:
            response = requests.post(
                f"{FASTAPI_URL}{endpoint}",
                params=arguments,
                timeout=10,
            )
        else:
            response = requests.get(
                f"{FASTAPI_URL}{endpoint}",
                params=arguments,
                timeout=10,
            )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


def _history_to_contents(history: list[dict]) -> list[types.Content]:
    """
    Converts our internal history format into Gemini's Content objects.

    Internal history entries look like one of:
      {"role": "user", "content": "..."}
      {"role": "assistant", "content": "..."}
      {"role": "assistant", "function_call": {"name": ..., "args": {...}, "thought_signature": bytes|None}}
      {"role": "function", "name": ..., "response": {...}}

    Gemini 3 ("thinking") models attach an opaque `thought_signature` to
    each function-call Part. That signature MUST be echoed back on the
    matching Part when we replay history, or the API rejects the request
    with: "Function call is missing a thought_signature". We therefore
    store it alongside the function call and re-attach it here.
    """
    contents = []
    for turn in history:
        role = turn["role"]

        if role == "user":
            contents.append(
                types.Content(role="user", parts=[types.Part.from_text(text=turn["content"])])
            )
        elif role == "assistant":
            if turn.get("function_call"):
                fc = turn["function_call"]
                part = types.Part.from_function_call(name=fc["name"], args=fc["args"])
                if fc.get("thought_signature"):
                    part.thought_signature = fc["thought_signature"]
                contents.append(types.Content(role="model", parts=[part]))
            else:
                contents.append(
                    types.Content(role="model", parts=[types.Part.from_text(text=turn.get("content", ""))])
                )
        elif role == "function":
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_function_response(name=turn["name"], response=turn["response"])],
                )
            )
    return contents


def _first_function_call_part(response):
    """Returns the first Part in the response that contains a function
    call, preserving its thought_signature (response.function_calls only
    returns bare FunctionCall objects and drops the signature)."""
    if not response.candidates or not response.candidates[0].content:
        return None
    for part in response.candidates[0].content.parts or []:
        if part.function_call is not None:
            return part
    return None


def _build_config(system_prompt: str) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=build_gemini_tools(),
        temperature=TEMPERATURE,
        # We execute tool calls ourselves via _call_fastapi (HTTP calls to
        # our own FastAPI endpoints), so Gemini's automatic function
        # calling — which expects local Python callables — must stay off.
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )


def _run_tool_call(fc, thought_signature, history: list[dict], system_prompt: str, model: str):
    """Executes one function call, appends the result to history, and asks
    the model for a final answer given the tool result."""
    args = dict(fc.args) if fc.args else {}
    tool_result = _call_fastapi(fc.name, args)

    if "error" in tool_result:
        tool_result["_system_note"] = (
            "Tool call failed. Do NOT estimate or invent data. "
            "Tell the user the data is unavailable and ask them to try again."
        )

    history.append({
        "role": "assistant",
        "function_call": {"name": fc.name, "args": args, "thought_signature": thought_signature},
    })
    history.append({"role": "function", "name": fc.name, "response": tool_result})

    return history


def chat(
    user_message: str,
    model: str,
    role: str,
    history: list[dict],
) -> tuple[str, list[dict]]:
    system_prompt = _load_system_prompt(role)
    history.append({"role": "user", "content": user_message})

    contents = _history_to_contents(history)
    try:
        response = client.models.generate_content(
            model=model, contents=contents, config=_build_config(system_prompt)
        )

        fc_part = _first_function_call_part(response)
        if fc_part:
            fc = fc_part.function_call
            history = _run_tool_call(fc, fc_part.thought_signature, history, system_prompt, model)

            contents = _history_to_contents(history)
            final = client.models.generate_content(
                model=model, contents=contents, config=_build_config(system_prompt)
            )
            answer = final.text or ""
        else:
            print("[DEBUG] No tool called — model answered directly.")
            answer = response.text or ""
    except Exception as e:
        print(f"[LLM ERROR] Quota or API error in chat: {e}")
        answer = (
            "The AI Assistant (Gemini) has exceeded its daily free API quota limit. "
            "However, the rule-based Freight Estimator is fully functional. Please use the "
            "calculator panel on the left to estimate costs, select optimal vehicles, and book dispatches."
        )

    history.append({"role": "assistant", "content": answer})

    if len(history) > MAX_HISTORY:
        history[:] = history[-MAX_HISTORY:]

    return answer, history


def stream_chat(
    user_message: str,
    model: str,
    role: str,
    history: list[dict],
) -> Generator[str, None, None]:
    system_prompt = _load_system_prompt(role)
    history.append({"role": "user", "content": user_message})

    contents = _history_to_contents(history)

    try:
        # Probe (non-streaming) first, same pattern as before, so we can detect
        # a function call and run it before streaming the final answer.
        probe = client.models.generate_content(
            model=model, contents=contents, config=_build_config(system_prompt)
        )

        fc_part = _first_function_call_part(probe)
        if fc_part:
            yield "Calculating..."

            fc = fc_part.function_call
            history = _run_tool_call(fc, fc_part.thought_signature, history, system_prompt, model)

            contents = _history_to_contents(history)
            full = ""
            for chunk in client.models.generate_content_stream(
                model=model, contents=contents, config=_build_config(system_prompt)
            ):
                token = chunk.text or ""
                if token:
                    full += token
                    yield token

            history.append({"role": "assistant", "content": full})
        else:
            answer = probe.text or ""
            for word in answer.split(" "):
                if word:
                    yield word + " "
            history.append({"role": "assistant", "content": answer})
    except Exception as e:
        print(f"[LLM ERROR] Quota or API error in stream_chat: {e}")
        fallback_msg = (
            "The AI Assistant (Gemini) has exceeded its daily free API quota limit. "
            "However, the rule-based Freight Estimator is fully functional. Please use the "
            "calculator panel on the left to estimate costs, select optimal vehicles, and book dispatches."
        )
        for word in fallback_msg.split(" "):
            yield word + " "
        history.append({"role": "assistant", "content": fallback_msg})

    if len(history) > MAX_HISTORY:
        history[:] = history[-MAX_HISTORY:]