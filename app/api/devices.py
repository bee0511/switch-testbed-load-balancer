from fastapi import APIRouter

from app.utils import load_device

router = APIRouter()


@router.get("/options")
def get_device_options() -> dict:
    """Return the structured device configuration for filter selections."""
    config = load_device()
    return config
