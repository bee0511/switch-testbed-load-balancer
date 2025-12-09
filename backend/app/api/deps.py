import logging
import os

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.machine_manager import MachineManager

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)

_manager_instance = None

async def get_machine_manager() -> MachineManager:
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = MachineManager()
    return _manager_instance


async def verify_bearer_token(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> str:
    """
    簡易的 Bearer Token 驗證。
    透過環境變數 API_BEARER_TOKEN 設定預期的 token。
    """
    expected_token = os.getenv("API_BEARER_TOKEN")
    if not expected_token:
        logger.error("API_BEARER_TOKEN is not set; rejecting request.")

    if (
        not expected_token
        or credentials is None
        or credentials.credentials != expected_token
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials
