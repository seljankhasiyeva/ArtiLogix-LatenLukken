import json
import requests
from pathlib import Path
from typing import Generator

from app.llm.tools import (
    TOOLS,
    TOOL_ENDPOINT_MAP,
    supports_native_tools,
    build_tool_prompt_suffix,
    parse_tool_call,
)

OLLAMA_URL  = "http://localhost:11434/api/chat"
FASTAPI_URL = "http://localhost:8001"
MAX_HISTORY = 20
TEMPERATURE = 0.3

# Tools whose FastAPI endpoint is declared with @router.post (see dispatch.py).
# Everything else (forecast, route-history, warehouse, store) is @router.get.
POST_TOOLS = {"get_dispatch_plan", "get_scenario"}

BASE_DIR = Path(__file__).parent


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


def _call_ollama(model: str, messages: list[dict], use_tools: bool) -> dict:
    payload = {
        "model"   : model,
        "messages": messages,
        "stream"  : False,
        "options" : {"temperature": TEMPERATURE},
    }
    if use_tools:
        payload["tools"] = TOOLS
    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def _handle_tool_call(
    tool_calls    : list,
    history       : list[dict],
    system_prompt : str,
    model         : str,
) -> tuple[str, list[dict]]:
    tool_call       = tool_calls[0]["function"]
    tool_name       = tool_call["name"]
    arguments       = tool_call.get("arguments", {})
    tool_result     = _call_fastapi(tool_name, arguments)

    if "error" in tool_result:
        tool_result["_system_note"] = (
            "Tool call failed. Do NOT estimate or invent data. "
            "Tell the user the data is unavailable and ask them to try again."
        )

    tool_result_str = json.dumps(tool_result, ensure_ascii=False)

    history.append({"role": "assistant", "content": "", "tool_calls": tool_calls})
    history.append({"role": "tool", "content": tool_result_str})

    messages = [{"role": "system", "content": system_prompt}] + history
    final    = _call_ollama(model, messages, use_tools=False)
    answer   = final.get("message", {}).get("content", "")

    history.append({"role": "assistant", "content": answer})
    return answer, history


def _extract_tool_calls(native: bool, assistant_msg: dict) -> list | None:
    tool_calls = assistant_msg.get("tool_calls") if native else None
    if not tool_calls and not native:
        parsed = parse_tool_call(assistant_msg.get("content", ""))
        if parsed:
            tool_calls = [{"function": {"name": parsed["tool"], "arguments": parsed["arguments"]}}]
    return tool_calls


def chat(
    user_message: str,
    model       : str,
    role        : str,
    history     : list[dict],
) -> tuple[str, list[dict]]:
    system_prompt = _load_system_prompt(role)
    native        = supports_native_tools(model)

    if not native:
        system_prompt += build_tool_prompt_suffix()

    history.append({"role": "user", "content": user_message})
    messages      = [{"role": "system", "content": system_prompt}] + history
    result        = _call_ollama(model, messages, use_tools=native)
    assistant_msg = result.get("message", {})
    tool_calls    = _extract_tool_calls(native, assistant_msg)

    if tool_calls:
        answer, history = _handle_tool_call(tool_calls, history, system_prompt, model)
    else:
        print("[DEBUG] No tool called — model answered directly.")
        answer = assistant_msg.get("content", "")
        history.append({"role": "assistant", "content": answer})

    if len(history) > MAX_HISTORY:
        history[:] = history[-MAX_HISTORY:]

    return answer, history


def stream_chat(
    user_message: str,
    model       : str,
    role        : str,
    history     : list[dict],
) -> Generator[str, None, None]:
    system_prompt = _load_system_prompt(role)
    native        = supports_native_tools(model)

    if not native:
        system_prompt += build_tool_prompt_suffix()

    history.append({"role": "user", "content": user_message})
    messages      = [{"role": "system", "content": system_prompt}] + history
    probe         = _call_ollama(model, messages, use_tools=native)
    probe_msg     = probe.get("message", {})
    tool_calls    = _extract_tool_calls(native, probe_msg)

    if tool_calls:
        yield "Calculating..."

        tool_call       = tool_calls[0]["function"]
        tool_result     = _call_fastapi(tool_call["name"], tool_call.get("arguments", {}))

        if "error" in tool_result:
            tool_result["_system_note"] = (
                "Tool call failed. Do NOT estimate or invent data. "
                "Tell the user the data is unavailable and ask them to try again."
            )

        tool_result_str = json.dumps(tool_result, ensure_ascii=False)

        history.append({"role": "assistant", "content": "", "tool_calls": tool_calls})
        history.append({"role": "tool", "content": tool_result_str})

        messages = [{"role": "system", "content": system_prompt}] + history
        payload  = {
            "model"   : model,
            "messages": messages,
            "stream"  : True,
            "options" : {"temperature": TEMPERATURE},
        }

        full = ""
        with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=(5, 120)) as resp:
            for line in resp.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                token = chunk.get("message", {}).get("content", "")
                if token:
                    full += token
                    yield token
                if chunk.get("done"):
                    break

        history.append({"role": "assistant", "content": full})

    else:
        answer = probe_msg.get("content", "")
        for word in answer.split(" "):
            if word:
                yield word + " "
        history.append({"role": "assistant", "content": answer})

    if len(history) > MAX_HISTORY:
        history[:] = history[-MAX_HISTORY:]