from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict
from ..utils.auth import get_current_user
from ..database import db
from jose import jwt, JWTError
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

router = APIRouter(prefix="/ws", tags=["websocket"])

# Manage active connections: username -> WebSocket
active_connections: Dict[str, WebSocket] = {}

async def get_username_from_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.websocket("/chat/{chat_with}")
async def websocket_endpoint(websocket: WebSocket, chat_with: str):
    # Token comes from query parameter for WebSocket (e.g. ws://.../chat/jane?token=xyz)
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)  # policy violation
        return

    try:
        username = await get_username_from_token(token)
    except HTTPException:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    active_connections[username] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            message_text = data.strip()
            if not message_text:
                continue

            # Save message in DB
            message_doc = {
                "sender": username,
                "receiver": chat_with,
                "message": message_text,
                "timestamp": datetime.utcnow()
            }
            await db.messages.insert_one(message_doc)

            # Send message to receiver if connected
            receiver_ws = active_connections.get(chat_with)
            if receiver_ws:
                await receiver_ws.send_json({
                    "sender": username,
                    "message": message_text,
                    "timestamp": message_doc["timestamp"].isoformat()
                })

            # Optionally, echo back to sender for confirmation
            await websocket.send_json({
                "sender": username,
                "message": message_text,
                "timestamp": message_doc["timestamp"].isoformat()
            })

    except WebSocketDisconnect:
        active_connections.pop(username, None)
