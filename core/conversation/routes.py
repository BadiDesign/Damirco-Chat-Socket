from typing import List
import json

from fastapi import APIRouter, Depends, HTTPException, Path, Query, WebSocket
from fastapi.websockets import WebSocketDisconnect
from fastapi.responses import JSONResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.database import get_db
from conversation.schemas import *
from conversation.models import MessageModel
from users.models import UserModel
from core.ws_manager import manager
from core.auth import get_authenticated_user

router = APIRouter(tags=["conversations"])


@router.get("/", response_model=List[MessageReadSchema])
async def retrieve_conversation_detail(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_authenticated_user),
):
    messages = (
        db.query(MessageModel)
        .filter(
            or_(
                MessageModel.sender_id == user_id,
                MessageModel.receiver_id == user_id,
            )
        )
        .all()
    )
    return messages


@router.websocket("/ws/{user_id}")
async def chat_ws(websocket: WebSocket, user_id: int):
    print("connected", user_id)
    await manager.connect(user_id, websocket)
    await websocket.send_text(json.dumps({"message": "connected"}))

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            # فقط broadcast ساده به همه
            await manager.broadcast(
                json.dumps({"user_id": user_id, "message": payload.get("message")})
            )

    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
        print("disconnected", user_id)


@router.websocket("/wss/{user_id}")
async def chat_wss(websocket: WebSocket, user_id: int):
    print("connected", user_id)
    await manager.connect(user_id, websocket)
    await websocket.send_text(json.dumps({"message": "connected"}))
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            await websocket.send_text(json.dumps({"message": "received"}))
            await manager.broadcast(json.dumps(payload))

            # payload باید شامل chat_id و متن پیام باشه
            chat_id = payload.get("chat_id")
            text = payload.get("text")

            if not chat_id or not text:
                await websocket.send_text(
                    json.dumps({"error": "chat_id and text required"})
                )
                continue

            # ذخیره پیام در دیتابیس
            # message = MessageModel(
            #     conversation_id=chat_id, sender_id=user_id, text=text
            # )
            # db.add(message)
            # db.commit()
            # db.refresh(message)

            # ارسال پیام به تمام کانکشن‌های اون کاربر
            # await manager.send_personal_message(
            #     json.dumps(
            #         {
            #             "chat_id": chat_id,
            #             "sender_id": user_id,
            #             "text": text,
            #             "timestamp": str(message.created_at),
            #         }
            #     ),
            #     user_id,
            # )

    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
