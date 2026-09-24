"""
Minimal proof-of-life for role enforcement. Not a real admin API — that
comes with the admin-facing features in a later phase (user management,
system config, etc. per the master prompt's ADMIN role scope).
"""

from fastapi import APIRouter, Depends

from app.api.deps import require_role
from app.models import User

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/ping")
def ping(current_user: User = Depends(require_role("admin"))):
    return {"status": "ok", "as": current_user.username}
