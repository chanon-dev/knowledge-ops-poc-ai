import base64
import json
from datetime import timedelta
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, verify_password
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.user import UserResponse
from app.services.user_service import UserService

router = APIRouter()


def _decode_jwt_payload(token: str) -> dict:
    """Decode JWT payload without verification (already verified by Keycloak)."""
    parts = token.split(".")
    if len(parts) != 3:
        return {}
    payload = parts[1]
    # Add padding
    payload += "=" * (4 - len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


async def _keycloak_login(email: str, password: str) -> dict:
    """Authenticate via Keycloak and return decoded token claims."""
    token_url = f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            token_url,
            data={
                "grant_type": "password",
                "client_id": "the-expert-app",
                "username": email,
                "password": password,
            },
        )
        if token_resp.status_code != 200:
            raise UnauthorizedError("Invalid email or password")

        token_data = token_resp.json()

    # Decode user info directly from JWT claims
    claims = _decode_jwt_payload(token_data["access_token"])
    return {
        "email": claims.get("email", email),
        "preferred_username": claims.get("preferred_username", email),
        "given_name": claims.get("given_name", ""),
        "family_name": claims.get("family_name", ""),
        "tenant_id": claims.get("tenant_id", "00000000-0000-0000-0000-000000000001"),
        "role": claims.get("role", "member"),
    }


async def _get_or_create_user(db: AsyncSession, userinfo: dict) -> User:
    """Find user in DB or auto-create from Keycloak data."""
    email = userinfo.get("email", "")

    stmt = select(User).where(User.email == email, User.deleted_at.is_(None))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        return user

    # Auto-create tenant if needed
    tenant_id_str = userinfo.get("tenant_id", "00000000-0000-0000-0000-000000000001")
    tenant_uuid = UUID(tenant_id_str)
    tenant_stmt = select(Tenant).where(Tenant.id == tenant_uuid)
    tenant_result = await db.execute(tenant_stmt)
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        tenant = Tenant(
            id=tenant_uuid,
            name="Demo Corp",
            slug="demo-corp",
            plan_tier="enterprise",
            status="active",
            settings={},
        )
        db.add(tenant)
        await db.flush()

    # Auto-create user from Keycloak info
    role = userinfo.get("role", "member")
    full_name = f"{userinfo.get('given_name', '')} {userinfo.get('family_name', '')}".strip() or email

    user = User(
        email=email,
        full_name=full_name,
        role=role,
        tenant_id=tenant_uuid,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        userinfo = await _keycloak_login(body.email, body.password)
        user = await _get_or_create_user(db, userinfo)
    except UnauthorizedError:
        raise
    except Exception:
        # Fallback to DB-based login if Keycloak is down
        service = UserService(db)
        user = await service.get_user_by_email(body.email)
        if not user:
            raise UnauthorizedError("Invalid email or password")
        password_hash = user.preferences.get("_password_hash") if user.preferences else None
        if password_hash and not verify_password(body.password, password_hash):
            raise UnauthorizedError("Invalid email or password")

    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "email": user.email,
            "role": user.role,
        },
        expires_delta=expires,
    )

    return LoginResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": str(user.id),
            "email": user.email,
            "name": user.full_name,
            "role": user.role,
            "tenant_id": str(user.tenant_id),
            "tenant_name": "Demo Corp",
            "departments": [],
        },
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user
