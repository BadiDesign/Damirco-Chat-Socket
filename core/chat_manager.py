from typing import List
import datetime
import json
from sqlalchemy.orm import Session
from conversation.models import MessageModel
from users.models import UserModel
from fastapi import WebSocket
from core.ws_manager import manager


class ChatManager:
    @staticmethod
    def seen_message_dict(message_id: int):
        return {
            "type": "seen_message",
            "data": {
                "message_id": message_id,
            },
        }

    @staticmethod
    async def send_seen_notification(
        user_object: UserModel, message_id: int, db: Session, websocket: WebSocket
    ):
        message = db.query(MessageModel).filter(MessageModel.id == message_id).first()
        if user_object.is_admin:
            print(
                "###SEND_SEEN_NOTIFICATION### user_object.is_admin",
                user_object.is_admin,
            )
            await manager.send_personal_message(
                json.dumps(ChatManager.seen_message_dict(message_id)),
                message.conversation_user_id,
            )
        else:
            for admin_user in ChatManager.get_admins(db):
                print("###SEND_SEEN_NOTIFICATION### admin_user", admin_user)
                await manager.send_personal_message(
                    json.dumps(ChatManager.seen_message_dict(message_id)),
                    admin_user.id,
                )

    @staticmethod
    def seen_message(user_object: UserModel, message_id: int, db: Session):
        if user_object.is_admin:
            db.query(MessageModel).filter(
                MessageModel.id == message_id,
                MessageModel.is_seen == False,
                MessageModel.is_admin_message == False,
            ).update({"is_seen": True})
        else:
            db.query(MessageModel).filter(
                MessageModel.id == message_id,
                MessageModel.is_seen == False,
                MessageModel.is_admin_message == True,
                MessageModel.conversation_user_id == user_object.id,
            ).update({"is_seen": True})

        db.commit()

    @staticmethod
    def seen_messages_of(chat_id: int, is_admin_viewing: bool, db: Session):
        db.query(MessageModel).filter(
            MessageModel.conversation_user_id == chat_id,
            MessageModel.is_seen == False,
            MessageModel.is_admin_message != is_admin_viewing,
        ).update({"is_seen": True})
        db.commit()

    @staticmethod
    def get_messages_of_chat(chat_id: int, db: Session) -> dict:
        messages = ChatManager.get_messages_objects(chat_id, db)
        return {
            "type": "messages",
            "data": [
                {
                    "id": message.id,
                    "text": message.text,
                    "is_admin_message": message.is_admin_message,
                    "is_seen": message.is_seen,
                    "created_at": message.created_at.isoformat(),
                }
                for message in messages
            ],
        }

    @staticmethod
    def get_messages_objects(chat_id: int, db: Session) -> List[MessageModel]:
        return (
            db.query(MessageModel)
            .filter(MessageModel.conversation_user_id == chat_id)
            .order_by(MessageModel.created_at.asc())
            .all()
        )

    @staticmethod
    def get_admins(db: Session) -> List[UserModel]:
        return db.query(UserModel).filter(UserModel.is_admin == True).all()

    @staticmethod
    def get_messages_of_chat(chat_id: int, db: Session) -> dict:
        messages = ChatManager.get_messages_objects(chat_id, db)
        return {
            "type": "messages",
            "data": [
                {
                    "id": message.id,
                    "text": message.text,
                    "is_admin_message": message.is_admin_message,
                    "is_seen": message.is_seen,
                    "created_at": message.created_at.isoformat(),
                }
                for message in messages
            ],
        }

    @staticmethod
    def get_members_objects(db: Session) -> List[UserModel]:
        return (
            db.query(UserModel)
            .filter(UserModel.is_admin == False)
            .order_by(UserModel.last_message_at.desc())
            .all()
        )

    @staticmethod
    def get_chats(db: Session) -> dict:
        users = ChatManager.get_members_objects(db)
        return {
            "type": "chats",
            "data": [
                {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "mobile_number": user.mobile_number,
                    "last_message_at": user.last_message_at.isoformat(),
                    "last_message_text": user.last_message_text,
                    "new_message_count": user.new_message_count,
                }
                for user in users
            ],
        }

    @staticmethod
    def new_message_notification(message: MessageModel, db: Session) -> dict:
        return {
            "type": "new_message",
            "data": {
                "id": message.id,
                "text": message.text,
                "is_admin_message": message.is_admin_message,
                "is_seen": message.is_seen,
                "created_at": message.created_at.isoformat(),
                "conversation_user_id": message.conversation_user_id,
            },
        }

    @staticmethod
    async def send_message(
        payload: dict, user_object: UserModel, db: Session, websocket: WebSocket
    ):
        conversation_user_id = (
            payload.get("chat_id") if user_object.is_admin else user_object.id
        )
        if conversation_user_id is None:
            await websocket.send_text(json.dumps({"error": "chat_id not found"}))
            return
        conversation_user = (
            db.query(UserModel).filter(UserModel.id == conversation_user_id).first()
        )
        if not conversation_user:
            await websocket.send_text(
                json.dumps({"error": "conversation_user not found"})
            )
            return
        message = MessageModel(
            conversation_user_id=conversation_user_id,
            text=payload.get("text"),
            is_admin_message=user_object.is_admin,
        )
        db.add(message)
        conversation_user.last_message_at = datetime.datetime.now()
        conversation_user.last_message_text = payload.get("text")
        if user_object.is_admin:
            if conversation_user.new_message_count < 0:
                conversation_user.new_message_count = 1
            else:
                conversation_user.new_message_count += 1
        else:
            if conversation_user.new_message_count >= 0:
                conversation_user.new_message_count = -1
            else:
                conversation_user.new_message_count -= 1
        db.commit()

        if user_object.is_admin:
            await manager.send_personal_message(
                json.dumps(ChatManager.new_message_notification(message, db)),
                conversation_user_id,
            )
        else:
            for admin_user in ChatManager.get_admins(db):
                await manager.send_personal_message(
                    json.dumps(ChatManager.new_message_notification(message, db)),
                    admin_user.id,
                )

        await manager.send_personal_message(
            json.dumps(
                {
                    "type": "message_sent",
                    "data": {
                        "message_id": message.id,
                        "text": message.text,
                    },
                }
            ),
            user_object.id,
        )
