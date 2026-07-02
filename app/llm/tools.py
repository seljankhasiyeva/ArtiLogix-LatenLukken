"""
G-01 — Tool Definitions (Ollama version)

Ollama tool calling works differently from Anthropic:

  Option A — Native tool calling (llama3.1, mistral-nemo, qwen2.5):
    Pass TOOLS directly to the Ollama /api/chat endpoint under "tools".
    Ollama returns tool_calls in the assistant message.

  Option B — JSON mode fallback (llama3, mistral, older models):
    No native tool support. We embed the tool schema in the system prompt
    and ask the model to respond with a JSON object. We parse that ourselves.

This file supports both. llm_service.py checks the model name and picks
the right path automatically.

Native tool support:  llama3.1, llama3.2, mistral-nemo, qwen2.5
JSON fallback:        llama3, mistral, phi3, gemma2
"""

import json

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weekly_forecast",
            "description": (
                "Returns the predicted weekly order volume and estimated load "
                "(desi) for a given region starting from a specific date. "
                "Call this when the user asks about expected demand, order "
                "counts, or load forecasts."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": (
                            "Region name. One of: Absheron, Ganja, Khachmaz, "
                            "Lankaran, Nakhchivan, Qazakh, Sheki, Yevlakh, "
                            "Kalbajar, Khankendi."
                        ),
                        "enum": [
                            "Absheron", "Ganja", "Khachmaz", "Lankaran",
                            "Nakhchivan", "Qazakh", "Sheki", "Yevlakh",
                            "Kalbajar", "Khankendi"
                        ]
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format."
                    },
                    "weeks": {
                        "type": "integer",
                        "description": "Number of weeks to forecast. Default 1.",
                        "default": 1
                    }
                },
                "required": ["region", "date_from"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_dispatch_plan",
            "description": (
                "Returns the recommended vehicle type, consolidation decision, "
                "and estimated cost for a region on a given date. "
                "Call this when the user asks which vehicle to send, "
                "how much it will cost, or how to plan dispatch."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "Region name.",
                        "enum": [
                            "Absheron", "Ganja", "Khachmaz", "Lankaran",
                            "Nakhchivan", "Qazakh", "Sheki", "Yevlakh",
                            "Kalbajar", "Khankendi"
                        ]
                    },
                    "date": {
                        "type": "string",
                        "description": "Dispatch date in YYYY-MM-DD format."
                    },
                    "cold_chain": {
                        "type": "boolean",
                        "description": "Refrigerated transport needed? Default false.",
                        "default": False
                    }
                },
                "required": ["region", "date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_scenario",
            "description": (
                "Runs a what-if scenario: what happens to load, vehicle, and "
                "cost if demand changes by a given percentage. "
                "Call this for 'what if orders increase by X%' questions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "Region name.",
                        "enum": [
                            "Absheron", "Ganja", "Khachmaz", "Lankaran",
                            "Nakhchivan", "Qazakh", "Sheki", "Yevlakh",
                            "Kalbajar", "Khankendi"
                        ]
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format."
                    },
                    "delta_pct": {
                        "type": "number",
                        "description": (
                            "Demand change as percentage. "
                            "Positive = increase, negative = decrease. "
                            "Example: 20 means +20%, -15 means -15%."
                        )
                    }
                },
                "required": ["region", "date_from", "delta_pct"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_route_history",
            "description": (
                "Returns historical shipment data for an origin-destination "
                "route: delay rate, typical load, cost range, shipment count. "
                "Call this for questions about past route performance or delays."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Origin hub.",
                        "enum": ["Absheron", "Ganja", "Yevlakh", "Lankaran", "Khachmaz"]
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination hub.",
                        "enum": ["Absheron", "Ganja", "Yevlakh", "Lankaran", "Khachmaz"]
                    },
                    "weeks_back": {
                        "type": "integer",
                        "description": "Weeks of history to include. Default 12.",
                        "default": 12
                    }
                },
                "required": ["origin", "destination"]
            }
        }
    }
]

TOOL_ENDPOINT_MAP = {
    "get_weekly_forecast": "/predict/forecast",
    "get_dispatch_plan"  : "/predict/dispatch",
    "get_scenario"       : "/predict/scenario",
    "get_route_history"  : "/predict/route-history",
}

NATIVE_TOOL_MODELS = {
    "llama3.1", "llama3.1:8b", "llama3.1:70b",
    "llama3.2", "llama3.2:3b",
    "mistral-nemo", "mistral-nemo:12b",
    "qwen2.5", "qwen2.5:7b", "qwen2.5:14b",
}

def supports_native_tools(model_name: str) -> bool:
    base = model_name.split(":")[0]
    return model_name in NATIVE_TOOL_MODELS or base in {
        m.split(":")[0] for m in NATIVE_TOOL_MODELS
    }


def build_tool_prompt_suffix() -> str:
    """
    Builds a plain-text description of all 4 tools.
    Appended to the system prompt so the model knows what tools exist
    and responds with a JSON object when it needs to call one.
    """
    parts = []
    for t in TOOLS:
        fn    = t["function"]
        req   = fn["parameters"].get("required", [])
        props = fn["parameters"]["properties"]
        params = "\n".join(
            f'    {k} ({"required" if k in req else "optional"})'
            f'{"[one of: " + ", ".join(str(x) for x in v["enum"]) + "]" if "enum" in v else ""}'
            f': {v.get("description","")}'
            for k, v in props.items()
        )
        parts.append(f'TOOL: {fn["name"]}\n{fn["description"]}\nParameters:\n{params}')

    tools_block = "\n\n".join(parts)

    return f"""

## Available Tools

When you need data to answer the user, respond with ONLY this JSON — no other text:

{{
  "tool": "<tool_name>",
  "arguments": {{
    "<param>": "<value>"
  }}
}}

If you do NOT need a tool (greeting, clarification), respond normally as text.
If a required argument is missing, ask the user for it — do not guess.

{tools_block}

RULE: Never invent numbers. Always call the right tool first, then answer.
"""

def parse_tool_call(response_text: str) -> dict | None:
    """
    Tries to extract {"tool": ..., "arguments": {...}} from model output.
    Returns the dict if valid, None if the model responded with plain text.

    Handles 3 cases:
      1. Pure JSON response (native tool models, clean fallback)
      2. JSON wrapped in ```...``` fences (some models add markdown)
      3. JSON embedded inside prose (e.g. "Sure! {\"tool\": ...}")
    """
    import re

    text = response_text.strip()

    if text.startswith("```"):
        text = "\n".join(
            line for line in text.split("\n")
            if not line.startswith("```")
        ).strip()

    valid_names = {t["function"]["name"] for t in TOOLS}

    candidates = [text] + re.findall(r'\{.*?\}', text, re.DOTALL)
    for candidate in candidates:
        try:
            data = json.loads(candidate)
            if (
                isinstance(data, dict)
                and "tool" in data
                and "arguments" in data
                and data["tool"] in valid_names
            ):
                return data
        except (json.JSONDecodeError, KeyError):
            continue

    return None  


def get_tool(name: str) -> dict:
    for t in TOOLS:
        if t["function"]["name"] == name:
            return t
    raise ValueError(f"Unknown tool: {name}")