import os
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.auth import verify_token, verify_token_query
from app.llm.llm_service import chat, stream_chat

router = APIRouter()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

_sessions: dict[str, list[dict]] = {}


def _scoped_key(email: str, session_id: str) -> str:
    """Namespaces session_id by user email so two different logged-in
    users can never read/overwrite each other's chat history just by
    picking the same session_id (e.g. both using 'default' or 't1')."""
    return f"{email}:{session_id}"


def _get_history(key: str) -> list[dict]:
    if key not in _sessions:
        _sessions[key] = []
    return _sessions[key]


class ChatRequest(BaseModel):
    message   : str
    session_id: str = "default"


@router.post("/message")
def send_message(
    req         : ChatRequest,
    current_user: dict = Depends(verify_token),
):
    # Role now comes from the caller's JWT (set at /auth/token login),
    # not hardcoded — marketplace users get the marketplace prompt,
    # logistics users get the logistics prompt.
    role = current_user["role"]
    key  = _scoped_key(current_user["email"], req.session_id)
    history = _get_history(key)

    answer, updated = chat(
        user_message = req.message,
        model        = GEMINI_MODEL,
        role         = role,
        history      = history,
    )
    _sessions[key] = updated

    return {
        "response"  : answer,
        "session_id": req.session_id,
        "role"      : role,
    }


@router.get("/stream")
def stream_message(
    message   : str,
    token     : str,
    session_id: str = "default",
):
    # EventSource (used by the frontend for SSE) cannot send an
    # Authorization header, so the token is passed as a query param here
    # instead and verified the same way as the header-based flow.
    current_user = verify_token_query(token)
    role = current_user["role"]
    key  = _scoped_key(current_user["email"], session_id)
    history = _get_history(key)

    def event_stream():
        for token_chunk in stream_chat(
            user_message = message,
            model        = GEMINI_MODEL,
            role         = role,
            history      = history,
        ):
            # Frontend does JSON.parse(event.data) expecting {"content": "..."},
            # so every chunk must be JSON, not a raw text token.
            payload = json.dumps({"content": token_chunk})
            yield f"data: {payload}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type = "text/event-stream",
        headers    = {
            "Cache-Control"              : "no-cache",
            "X-Accel-Buffering"          : "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.delete("/session/{session_id}")
def clear_session(
    session_id  : str,
    current_user: dict = Depends(verify_token),
):
    key = _scoped_key(current_user["email"], session_id)
    _sessions.pop(key, None)
    return {"status": "cleared", "session_id": session_id}