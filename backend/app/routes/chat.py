from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from ..utils.auth import get_current_user
from ..database import db

router = APIRouter(prefix="/chat", tags=["chat"])

class MessageSendRequest(BaseModel):
    receiver: str
    message: str

@router.post("/send")
async def send_message(request: MessageSendRequest, current_user: dict = Depends(get_current_user)):
    sender = current_user["username"]
    receiver = request.receiver
    message_text = request.message.strip()

    if not message_text:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Check if receiver exists
    receiver_user = await db.users.find_one({"username": receiver})
    if not receiver_user:
        raise HTTPException(status_code=404, detail="Receiver not found")

    # Optional: Check if sender and receiver are friends (you can skip or add)

    message_doc = {
        "sender": sender,
        "receiver": receiver,
        "message": message_text,
        "timestamp": datetime.utcnow()
    }

    await db.messages.insert_one(message_doc)

    return {"msg": "Message sent"}

@router.get("/history/{username}")
async def get_chat_history(username: str, current_user: dict = Depends(get_current_user)):
    user = current_user["username"]

    # Fetch messages where (sender=user AND receiver=username) OR (sender=username AND receiver=user)
    cursor = db.messages.find({
        "$or": [
            {"sender": user, "receiver": username},
            {"sender": username, "receiver": user}
        ]
    }).sort("timestamp", 1)  # ascending order

    messages = []
    async for msg in cursor:
        messages.append({
            "sender": msg["sender"],
            "receiver": msg["receiver"],
            "message": msg["message"],
            "timestamp": msg["timestamp"].isoformat()
        })

    return {"messages": messages}
