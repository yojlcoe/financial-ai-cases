import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config import get_settings


security = HTTPBasic()


def require_basic_auth(
    credentials: HTTPBasicCredentials = Depends(security),
) -> None:
    settings = get_settings()
    valid_username = secrets.compare_digest(
        credentials.username,
        settings.basic_auth_username,
    )
    valid_password = secrets.compare_digest(
        credentials.password,
        settings.basic_auth_password,
    )
    if not (valid_username and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication",
            headers={"WWW-Authenticate": "Basic"},
        )
