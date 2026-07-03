from fastapi import APIRouter

router = APIRouter()


@router.post("/message")
def send_message(message: str, role: str = "marketplace"):
    return {"status": "stub", "message": message, "role": role}


@router.get("/stream")
def stream_chat(message: str, role: str = "marketplace"):
    return {"status": "stub", "message": message, "role": role}