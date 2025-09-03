"""Shared authentication utilities for PlutosAI."""

from __future__ import annotations

import jwt
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class UserRole(Enum):
    ADMIN = "admin"
    COMPLIANCE_OFFICER = "compliance_officer"
    INVESTMENT_ADVISOR = "investment_advisor"
    CLIENT_SERVICE = "client_service"
    VIEWER = "viewer"


class Permission(Enum):
    # Client management
    READ_CLIENT = "read:client"
    CREATE_CLIENT = "create:client"
    UPDATE_CLIENT = "update:client"
    DELETE_CLIENT = "delete:client"

    # Investment management
    READ_PORTFOLIO = "read:portfolio"
    CREATE_PORTFOLIO = "create:portfolio"
    UPDATE_PORTFOLIO = "update:portfolio"
    TRADE_PORTFOLIO = "trade:portfolio"

    # Compliance
    READ_COMPLIANCE = "read:compliance"
    REVIEW_COMPLIANCE = "review:compliance"
    CREATE_ALERT = "create:alert"

    # Reporting
    READ_REPORTS = "read:reports"
    CREATE_REPORTS = "create:reports"

    # System
    ADMIN_SYSTEM = "admin:system"


@dataclass
class User:
    """User information extracted from JWT token."""
    user_id: str
    email: str
    roles: list[UserRole]
    permissions: list[Permission]
    exp: datetime
    iat: datetime

    @property
    def is_admin(self) -> bool:
        return UserRole.ADMIN in self.roles

    @property
    def is_compliance_officer(self) -> bool:
        return UserRole.COMPLIANCE_OFFICER in self.roles

    def has_permission(self, permission: Permission) -> bool:
        return permission in self.permissions or self.is_admin


class JWTManager:
    """JWT token management utilities."""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(
        self,
        user_id: str,
        email: str,
        roles: list[UserRole],
        permissions: list[Permission],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        if expires_delta is None:
            expires_delta = timedelta(hours=1)

        expire = datetime.utcnow() + expires_delta
        to_encode = {
            "sub": user_id,
            "email": email,
            "roles": [role.value for role in roles],
            "permissions": [perm.value for perm in permissions],
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> User:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Convert string values back to enums
            roles = [UserRole(role) for role in payload.get("roles", [])]
            permissions = [Permission(perm) for perm in payload.get("permissions", [])]

            return User(
                user_id=payload["sub"],
                email=payload["email"],
                roles=roles,
                permissions=permissions,
                exp=datetime.fromtimestamp(payload["exp"]),
                iat=datetime.fromtimestamp(payload["iat"])
            )
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")


def get_role_permissions(roles: list[UserRole]) -> list[Permission]:
    """Get permissions based on user roles."""
    permissions = []

    for role in roles:
        if role == UserRole.ADMIN:
            # Admin gets all permissions
            return list(Permission)
        elif role == UserRole.COMPLIANCE_OFFICER:
            permissions.extend([
                Permission.READ_CLIENT,
                Permission.UPDATE_CLIENT,
                Permission.READ_COMPLIANCE,
                Permission.REVIEW_COMPLIANCE,
                Permission.CREATE_ALERT,
                Permission.READ_REPORTS,
            ])
        elif role == UserRole.INVESTMENT_ADVISOR:
            permissions.extend([
                Permission.READ_CLIENT,
                Permission.UPDATE_CLIENT,
                Permission.READ_PORTFOLIO,
                Permission.CREATE_PORTFOLIO,
                Permission.UPDATE_PORTFOLIO,
                Permission.TRADE_PORTFOLIO,
                Permission.READ_REPORTS,
            ])
        elif role == UserRole.CLIENT_SERVICE:
            permissions.extend([
                Permission.READ_CLIENT,
                Permission.CREATE_CLIENT,
                Permission.UPDATE_CLIENT,
                Permission.READ_PORTFOLIO,
                Permission.READ_REPORTS,
            ])
        elif role == UserRole.VIEWER:
            permissions.extend([
                Permission.READ_CLIENT,
                Permission.READ_PORTFOLIO,
                Permission.READ_REPORTS,
            ])

    return permissions


# Default JWT manager instance (will be configured per service)
jwt_manager = None


def init_jwt_manager(secret_key: str) -> None:
    """Initialize global JWT manager."""
    global jwt_manager
    jwt_manager = JWTManager(secret_key)
