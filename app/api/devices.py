from fastapi import APIRouter

from app.utils import load_device

router = APIRouter()


@router.get("/options")
def get_device_options() -> dict:
    """回傳 device.yaml 內部的階層式裝置資料。"""
    return load_device()
