"""Security utilities for authentication and authorization."""

from datetime import datetime, timedelta
from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import Settings, get_settings

security = HTTPBearer()


class UserContext:
    """User context extracted from JWT token."""

    def __init__(
        self,
        user_id: str,
        email: str,
        organization_id: str,
        tier: str,
        roles: list[str],
    ) -> None:
        self.user_id = user_id
        self.email = email
        self.organization_id = organization_id
        self.tier = tier
        self.roles = roles

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles

    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.has_role("admin") or self.has_role("owner")


async def verify_token_with_auth_service(
    token: str,
    settings: Settings,
) -> dict[str, Any]:
    """
    Verify JWT token with QuickSpin authentication service.

    Args:
        token: JWT token to verify
        settings: Application settings

    Returns:
        Token payload dictionary

    Raises:
        HTTPException: If token is invalid or verification fails
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.quickspin_auth_url}/api/v1/auth/verify",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0,
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Authentication service unavailable: {exc}",
        ) from exc


async def decode_jwt_token(
    token: str,
    settings: Settings,
) -> dict[str, Any]:
    """
    Decode and validate JWT token locally.

    Args:
        token: JWT token to decode
        settings: Application settings

    Returns:
        Token payload dictionary

    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    settings: Settings = Depends(get_settings),
) -> UserContext:
    """
    Extract current user context from JWT token.

    Args:
        credentials: HTTP bearer token credentials
        settings: Application settings

    Returns:
        UserContext instance with user information

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials

    # Try local JWT decoding first (faster)
    try:
        payload = await decode_jwt_token(token, settings)
    except HTTPException:
        # Fallback to auth service verification
        payload = await verify_token_with_auth_service(token, settings)

    # Extract user information from payload
    try:
        user_id = payload["sub"]
        email = payload.get("email", "")
        organization_id = payload.get("org_id", "")
        tier = payload.get("tier", "starter")
        roles = payload.get("roles", ["member"])

        return UserContext(
            user_id=user_id,
            email=email,
            organization_id=organization_id,
            tier=tier,
            roles=roles,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        ) from exc


def create_access_token(
    data: dict[str, Any],
    settings: Settings,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a new JWT access token.

    Args:
        data: Payload data to encode
        settings: Application settings
        expires_delta: Token expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt
