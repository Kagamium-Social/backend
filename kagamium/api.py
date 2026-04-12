from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordRequestForm

from kagamium.auth import create_access_token, hash_password, verify_access_token, verify_password
from kagamium.config import Settings
from kagamium.database import Database
from kagamium.schemas import AuthResponse, LoginRequest, RegisterRequest, TokenResponse


def _route_with_prefix(api_prefix: str, path: str) -> str:
    return f"{api_prefix}{path}" if api_prefix else path


def create_api_router(settings: Settings, database: Database) -> APIRouter:
    router = APIRouter()
    api_prefix = settings.api_prefix
    bearer_scheme = HTTPBearer(auto_error=False)

    def authenticate_user(login: str, password: str) -> int | None:
        user_record = database.get_user_credentials(login)
        if user_record is None:
            return None

        user_id, stored_password_hash = user_record
        if not verify_password(password, stored_password_hash):
            return None

        return user_id

    def issue_access_token(user_id: int) -> str:
        return create_access_token(
            user_id=user_id,
            secret_key=settings.jwt_secret,
            expires_in_minutes=settings.jwt_expiration_minutes,
        )

    async def resolve_authenticated_user_id(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    ) -> int | None:
        if credentials is None:
            return None

        payload = verify_access_token(credentials.credentials, settings.jwt_secret)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload.user_id

    @router.get(_route_with_prefix(api_prefix, "/"))
    async def root() -> dict[str, str]:
        return {
            "motd": settings.instance_motd,
            "mascotName": settings.instance_mascot_name,
            "mascotImage": settings.instance_mascot_image,
        }

    @router.post(_route_with_prefix(api_prefix, "/token"), response_model=TokenResponse)
    async def create_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    ) -> TokenResponse:
        user_id = authenticate_user(form_data.username, form_data.password)
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect login or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenResponse(
            access_token=issue_access_token(user_id),
            token_type="bearer",
        )

    @router.post(_route_with_prefix(api_prefix, "/login"), response_model=AuthResponse)
    async def login_process(
        data: LoginRequest,
    ) -> AuthResponse:
        user_id = authenticate_user(data.login, data.password.get_secret_value())
        if user_id is None:
            return AuthResponse(status="failed")

        return AuthResponse(
            status="success",
            access_token=issue_access_token(user_id),
            token_type="bearer",
        )

    @router.post(_route_with_prefix(api_prefix, "/register"), response_model=AuthResponse)
    async def register_process(
        data: RegisterRequest,
    ) -> AuthResponse:
        if database.login_exists(data.login):
            return AuthResponse(status="failed")

        user_id = database.create_user(
            login=data.login,
            password_hash=hash_password(data.password.get_secret_value()),
            username=data.username,
            firstname=data.firstname,
            lastname=data.lastname,
            nickname=data.nickname,
        )
        return AuthResponse(
            status="success",
            access_token=issue_access_token(user_id),
            token_type="bearer",
        )

    @router.get(_route_with_prefix(api_prefix, "/profile"))
    async def give_profile_info(
        authenticated_user_id: Annotated[int | None, Depends(resolve_authenticated_user_id)],
        user_id: Annotated[int | None, Query(alias="id")] = None,
    ) -> dict[str, int | str | None]:
        if user_id is None:
            user_id = authenticated_user_id
            if user_id is None:
                return {
                    "status": "failed",
                    "details": "User ID is not specified",
                }

        profile = database.get_profile(user_id)
        if profile is None:
            return {"status": "failed", "details": "User does not exist"}

        return profile.as_response()

    @router.get(_route_with_prefix(api_prefix, "/profile/follow"))
    async def follow_profile(
        authenticated_user_id: Annotated[int | None, Depends(resolve_authenticated_user_id)],
        *,
        user_id: Annotated[int, Query(alias="id")],
    ) -> dict[str, str]:
        if authenticated_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not database.user_exists(user_id):
            return {"status": "failed", "details": "User does not exist"}

        details = database.follow_user(authenticated_user_id, user_id)
        if details is None:
            return {"status": "success"}

        return {"status": "success", "details": details}

    return router
