from dataclasses import dataclass
from typing import Literal

from fastapi import Depends, Header, HTTPException, status

from app.settings import settings


Role = Literal["admin", "reviewer", "analyst"]


@dataclass(frozen=True)
class Principal:
    api_key: str
    role: Role


def _role_for_key(api_key: str) -> Role | None:
    if api_key == settings.api_key_admin:
        return "admin"
    if api_key == settings.api_key_reviewer:
        return "reviewer"
    if api_key == settings.api_key_analyst:
        return "analyst"
    return None


def require_principal(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> Principal:
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-API-Key")
    role = _role_for_key(x_api_key)
    if not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return Principal(api_key=x_api_key, role=role)


def require_role(*allowed: Role):
    def _dep(principal: Principal = Depends(require_principal)) -> Principal:
        if principal.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return principal

    return _dep

