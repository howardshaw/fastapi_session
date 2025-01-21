from pydantic import BaseModel, EmailStr, StringConstraints, Field
from typing_extensions import Annotated


class Token(BaseModel):
    access_token: str = Field(description="The access token")
    token_type: str = Field(description="The type of the token")


class LoginRequest(BaseModel):
    email: EmailStr = Field(default="user@example.com", description="User's email address")
    password: Annotated[
        str,
        StringConstraints(
            min_length=8
        ),
    ] = Field(default="defaultpassword", description="User's password")
