import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserLoginSchema(BaseModel):
    username: str = Field(..., max_length=250, description="Username of the User")
    password: str = Field(..., max_length=250, description="Password of the User")


class UserRegisterSchema(BaseModel):
    username: str = Field(..., max_length=250, description="Username of the User")
    password: str = Field(..., max_length=250, description="Password of the User")
    password_confirm: str = Field(
        ..., max_length=250, description="Confirm Password of the User"
    )

    @field_validator("password_confirm")
    def check_password_confirm_match(cls, password_confirm, validation):
        if password_confirm != validation.data.get("password"):
            raise ValueError("password doesn't match!")
        return password_confirm


class UserRefreshTokenSchema(BaseModel):
    refresh_token: str = Field(
        ..., max_length=250, description="Refresh token of the User"
    )


class UserReadSchema(BaseModel):
    id: int = Field(..., description="Unique id of the User")
    user_uid: int = Field(..., description="User uid of the User")
    mobile_number: str = Field(..., description="Mobile number of the User")
    first_name: str = Field(..., description="First name of the User")
    last_name: str = Field(..., description="Last name of the User")
    is_admin: bool = Field(..., description="Is admin of the User")

    model_config = ConfigDict(from_attributes=True)
