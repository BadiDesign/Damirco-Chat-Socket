import json
import datetime
import uuid
from typing import Annotated, List
from fastapi import (
    Cookie,
    FastAPI,
    Response,
    WebSocket,
    WebSocketDisconnect,
    Header,
    Depends,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
from sqlalchemy.orm import Session

from conversation.routes import router as conversation_routes
from conversation.models import MessageModel
from conversation.schemas import MessageReadSchema
from chat_manager import ChatManager
from core.database import get_db
from users.models import UserModel
from users.schemas import UserReadSchema
from core.ws_manager import manager
from core.auth import get_authenticated_user, get_uid_session_by_socket
from core.config import settings


app = FastAPI(
    title="Damirco ChatApp",
    description="Damirco ChatApp",
    version="0.0.1",
    contact={
        "name": "Mohammad Shekari Badi",
        "url": "https://badiDesign.ir/",
        "email": "m.shekari79b5@gmail.com",
    },
    license_info={
        "name": "Apache 2.0",
        "identifier": "MIT",
    },
)
origins = [
    "http://damirco.com",
    "https://damirco.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def get():
    return HTMLResponse()


async def validate_token(token: str, db: Session = Depends(get_db)) -> UserModel:
    token = "Bearer " + token
    headers = {
        "Authorization": token,
        "MicroToken": settings.MICROSERVICE_TOKEN,
    }
    url = settings.MICROSERVICE_URL + "/api/v1/microservice/validate_token/"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
        )
    try:
        result = response.json()
        if result.get("code") == "token_not_valid":
            raise Exception("invalid_token")
        if not result.get("id"):
            raise Exception("user_not_found")
    except json.JSONDecodeError:
        raise Exception("json_decode_error")
    user = db.query(UserModel).filter(UserModel.id == result.get("id")).first()
    if not user:
        user = UserModel(
            id=result.get("id"),
            mobile_number=result.get("mobile_number"),
            first_name=result.get("first_name"),
            last_name=result.get("last_name"),
            is_admin=result.get("is_admin"),
        )
        db.add(user)
    else:
        user.mobile_number = result.get("mobile_number")
        user.is_admin = result.get("is_admin")
        user.first_name = result.get("first_name")
        user.last_name = result.get("last_name")
    db.commit()
    db.refresh(user)
    return user


@app.websocket("/websocket")
async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db),
):
    await websocket.accept()

    try:
        # اولین پیام باید auth باشه
        first_message = await websocket.receive_text()
        try:
            auth_data = json.loads(first_message)
        except json.JSONDecodeError:
            await websocket.close(code=4001, reason="json decode error")
            return

        if auth_data.get("type") != "auth" or not auth_data.get("token"):
            await websocket.close(code=4002, reason="auth data error")
            return

        try:
            # اعتبارسنجی توکن اینجا
            user_object = await validate_token(auth_data["token"], db)
        except Exception as e:
            await websocket.close(code=4003, reason=str(e))
            return

        # فقط اگر auth اوکی بود کانکت می‌کنیم6
        await manager.connect(user_object.id, websocket)

        await manager.send_personal_message(
            json.dumps(
                {
                    "type": "system",
                    "data": {"message": "connected " + user_object.first_name},
                }
            ),
            user_object.id,
        )
        if user_object.is_admin:
            await manager.send_personal_message(
                json.dumps(ChatManager.get_chats(db)),
                user_object.id,
            )
        else:
            messages = ChatManager.get_messages_of_chat(user_object.id, db)
            await manager.send_personal_message(
                json.dumps(messages),
                user_object.id,
            )
            ChatManager.seen_messages_of(user_object.id, False, db)
        try:
            while True:
                data = await websocket.receive_text()
                payload = json.loads(data)
                if payload.get("type") == "get_messages":
                    if not user_object.is_admin:
                        await websocket.send_text(
                            json.dumps({"error": "you are not admin"})
                        )
                    user_id = payload.get("data").get("user_id")
                    chat_messages = ChatManager.get_messages_of_chat(user_id, db)
                    await manager.send_personal_message(
                        json.dumps(chat_messages),
                        user_object.id,
                    )
                    ChatManager.seen_messages_of(user_id, True, db)
                elif payload.get("type") == "send_message":
                    await ChatManager.send_message(
                        payload,
                        user_object,
                        db,
                        websocket,
                    )
                elif payload.get("type") == "seen_message":
                    ChatManager.seen_message(
                        user_object, payload.get("data").get("message_id"), db
                    )
                    await ChatManager.send_seen_notification(
                        user_object,
                        payload.get("data").get("message_id"),
                        db,
                        websocket,
                    )
                elif payload.get("type") == "get_chats" and user_object.is_admin:
                    await manager.send_personal_message(
                        json.dumps(ChatManager.get_chats(db)),
                        user_object.id,
                    )
        except WebSocketDisconnect:
            manager.disconnect(user_object.id, websocket)
            # await manager.broadcast(f"Client #{user_object.id} left the chat")

    except WebSocketDisconnect:
        await websocket.close(code=4004, reason="WebSocketDisconnect")
        pass


# @app.websocket("/websocket_old")
# async def websocket_endpoint_old(
#     websocket: WebSocket,
#     session_uid: str = Depends(get_uid_session_by_socket),
#     db: Session = Depends(get_db),
# ):
#     await manager.connect(session_uid, websocket)
#     await manager.send_personal_message(
#         json.dumps({"message": "connected"}), session_uid
#     )

#     for message in (
#         db.query(MessageModel)
#         .join(MessageModel.conversation_user)
#         .filter(UserModel.user_uid == session_uid)
#     ):
#         await manager.send_personal_message(
#             json.dumps(
#                 {
#                     "text": message.text,
#                     "is_admin_message": message.is_admin_message,
#                     "is_seen": message.is_seen,
#                 },
#             ),
#             session_uid,
#         )
#     try:
#         while True:
#             data = await websocket.receive_text()
#             user = db.query(UserModel).filter(UserModel.user_uid == session_uid).first()
#             payload = json.loads(data)
#             if user.is_admin:
#                 chat_id = payload.get("chat_id")
#             else:
#                 chat_id = user.user_uid
#             await manager.send_personal_message(json.dumps(payload), chat_id)
#             db.add(
#                 MessageModel(
#                     conversation_user_id=user.id,
#                     text=payload.get("text"),
#                     is_admin_message=user.is_admin,
#                 )
#             )
#             db.commit()
#     except WebSocketDisconnect:
#         manager.disconnect(session_uid, websocket)
#         await manager.broadcast(f"Client #{session_uid} left the chat")


# @app.post("/authenticate")
# def authenticate(
#     response: Response,
#     session_uid: Annotated[str | None, Cookie()] = None,
#     db: Session = Depends(get_db),
# ):
#     if session_uid:
#         user = db.query(UserModel).filter(UserModel.user_uid == session_uid).first()
#         if user:
#             return {"message": "already logged in", "user_uid": user.user_uid}
#     new_session_uid = str(uuid.uuid4())
#     response.set_cookie(
#         key="session_uid",
#         value=str(new_session_uid),
#         max_age=60 * 60 * 24 * 30,  # 30 روز
#         expires=datetime.datetime.now(datetime.timezone.utc)
#         + datetime.timedelta(days=30),  # روش دیگه
#         httponly=False,  # امنیت بیشتر
#         samesite="lax",  # یا "Strict"/"None"
#     )
#     db.add(UserModel(user_uid=new_session_uid, is_admin=False))
#     db.commit()
#     user = db.query(UserModel).filter(UserModel.user_uid == new_session_uid).first()
#     return {"message": "logged in " + new_session_uid, "user_uid": user.user_uid}


# @app.get("/messages", response_model=List[MessageReadSchema])
# def show_all_messages(
#     db: Session = Depends(get_db),
# ):
#     return db.query(MessageModel).all()
