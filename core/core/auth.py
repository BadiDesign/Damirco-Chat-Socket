from fastapi import Depends, HTTPException, WebSocket, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import DecodeError, InvalidSignatureError

from users.models import UserModel
from core.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import jwt
from core.config import settings


def verify_token(token: str):
    if token == "fake-session-123":
        print("token is valid")
        return {
            "id": 1,
            "mobile_number": "09123456789",
            "user_uid": 1234567890,
            "is_admin": True,
        }
    return None


async def get_authenticated_user(websocket: WebSocket):
    token = websocket.cookies.get("session_key")

    user = verify_token(token.replace("Bearer ", "")) if token else None
    if not user:
        await websocket.close(code=1008)
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


async def get_uid_session_by_socket(websocket: WebSocket):
    token = websocket.cookies.get("session_uid")
    if not token:
        await websocket.close(code=1008)
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token


async def get_uid_session_by_http_session(session: Session):
    token = session.get("session_uid")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token
