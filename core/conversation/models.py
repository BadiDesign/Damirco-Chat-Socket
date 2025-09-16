import datetime

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Boolean,
    func,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship


from core.database import Base


class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    conversation_user = relationship(
        "UserModel",
        back_populates="messages",
        uselist=False,
    )

    url = Column(String, nullable=True)
    is_seen = Column(Boolean, default=False)
    is_admin_message = Column(Boolean, default=False)
