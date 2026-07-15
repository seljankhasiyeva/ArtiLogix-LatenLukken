"""
Tool definitions for Google Gemini function calling.

Gemini has native function calling support, so unlike the old Ollama
version, we don't need a JSON-mode fallback, a native-model allowlist,
or manual text parsing of tool calls. The model always returns
structured function_calls on the response object.
"""

from google.genai import types

REGIONS = [
    "Absheron", "Ganja", "Khachmaz", "Lankaran",
    "Nakhchivan", "Qazakh", "Sheki", "Yevlakh",
    "Kalbajar", "Khankendi",
]

HUBS = ["Absheron", "Ganja", "Yevlakh", "Lankaran", "Khachmaz"]

# Tool specs, kept close to the original OpenAI/Ollama-style schema —
# Gemini's FunctionDeclaration.parameters accepts the same JSON-Schema shape.
TOOL_SPECS = [
    {
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
                    "description": "Region name.",
                    "enum": REGIONS,
                },
                "date_from": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format.",
                },
                "weeks": {
                    "type": "integer",
                    "description": "Number of weeks to forecast. Default 1.",
                },
            },
            "required": ["region", "date_from"],
        },
    },
    {
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
                    "enum": REGIONS,
                },
                "date": {
                    "type": "string",
                    "description": "Dispatch date in YYYY-MM-DD format.",
                },
                "cold_chain": {
                    "type": "boolean",
                    "description": "Refrigerated transport needed? Default false.",
                },
            },
            "required": ["region", "date"],
        },
    },
    {
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
                    "enum": REGIONS,
                },
                "date_from": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format.",
                },
                "delta_pct": {
                    "type": "number",
                    "description": (
                        "Demand change as percentage. "
                        "Positive = increase, negative = decrease. "
                        "Example: 20 means +20%, -15 means -15%."
                    ),
                },
            },
            "required": ["region", "date_from", "delta_pct"],
        },
    },
    {
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
                    "enum": HUBS,
                },
                "destination": {
                    "type": "string",
                    "description": "Destination hub.",
                    "enum": HUBS,
                },
                "weeks_back": {
                    "type": "integer",
                    "description": "Weeks of history to include. Default 12.",
                },
            },
            "required": ["origin", "destination"],
        },
    },
    {
        "name": "get_warehouse_assignment",
        "description": (
            "Predicts which warehouse will fulfill an order for a given "
            "region, item count, and delivery type. Call this when the "
            "user asks which warehouse handles an order."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "region": {
                    "type": "string",
                    "description": "Region name.",
                    "enum": REGIONS,
                },
                "item_count": {
                    "type": "integer",
                    "description": "Number of items in the order.",
                },
                "delivery_type": {
                    "type": "string",
                    "description": "Delivery type, e.g. 'standard' or 'express'.",
                },
                "order_hour": {
                    "type": "integer",
                    "description": "Hour of day the order was placed (0-23). Default 12.",
                },
            },
            "required": ["region", "item_count", "delivery_type"],
        },
    },
    {
        "name": "get_store_assignment",
        "description": (
            "Predicts which store will fulfill/receive an order for a "
            "given region, item count, and delivery type. Call this when "
            "the user asks which store handles an order."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "region": {
                    "type": "string",
                    "description": "Region name.",
                    "enum": REGIONS,
                },
                "item_count": {
                    "type": "integer",
                    "description": "Number of items in the order.",
                },
                "delivery_type": {
                    "type": "string",
                    "description": "Delivery type, e.g. 'standard' or 'express'.",
                },
            },
            "required": ["region", "item_count", "delivery_type"],
        },
    },
]

# Which FastAPI endpoint each tool maps to. Provider-agnostic — unchanged
# from the Ollama version.
TOOL_ENDPOINT_MAP = {
    "get_weekly_forecast": "/predict/forecast",
    "get_dispatch_plan": "/predict/dispatch",
    "get_scenario": "/predict/scenario",
    "get_route_history": "/predict/route-history",
    "get_warehouse_assignment": "/predict/warehouse",
    "get_store_assignment": "/predict/store",
}

# Tools whose FastAPI endpoint is declared with @router.post (see dispatch.py).
# Everything else (forecast, route-history) is @router.get.
POST_TOOLS = {"get_dispatch_plan", "get_scenario"}


def build_gemini_tools() -> list[types.Tool]:
    """Converts TOOL_SPECS into the Gemini SDK's Tool/FunctionDeclaration objects."""
    declarations = [
        types.FunctionDeclaration(
            name=spec["name"],
            description=spec["description"],
            parameters=spec["parameters"],
        )
        for spec in TOOL_SPECS
    ]
    return [types.Tool(function_declarations=declarations)]


def get_tool_spec(name: str) -> dict:
    for spec in TOOL_SPECS:
        if spec["name"] == name:
            return spec
    raise ValueError(f"Unknown tool: {name}")