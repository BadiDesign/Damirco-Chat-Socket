from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.orm import relationship

from core.database import Base


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    is_admin = Column(Boolean, default=False)
    mobile_number = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    last_message_at = Column(DateTime, nullable=True)
    new_message_count = Column(Integer, default=0)

    messages = relationship("MessageModel", back_populates="conversation_user")
