from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, SecretStr


PasswordField = Annotated[
    SecretStr,
    Field(
        min_length=1,
        json_schema_extra={"format": "password"},
    ),
]


class LoginRequest(BaseModel):
    login: str
    password: PasswordField


class RegisterRequest(BaseModel):
    login: str
    password: PasswordField
    username: str
    firstname: str
    lastname: str | None = None
    nickname: str | None = None


class AuthResponse(BaseModel):
    status: Literal["success", "failed"]
    access_token: str | None = None
    token_type: Literal["bearer"] | None = None
    details: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
