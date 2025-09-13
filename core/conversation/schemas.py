import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MessageBaseSchema(BaseModel):
    text: str = Field(..., max_length=20, description="message text")


class MessageReadSchema(MessageBaseSchema):
    id: int = Field(..., description="Unique id of the Message")
    conversation_user_id: int = Field(
        ..., description="Conversation user id of the Message"
    )
    is_admin_message: bool = Field(..., description="Is admin message")
    is_seen: bool = Field(..., description="Is seen message")
    created_at: datetime.datetime = Field(..., description="Create time of the Message")
