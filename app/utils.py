import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterator, Tuple, Optional

import yaml

from app.models.device_config import DeviceConfig, VersionEntry

logger = logging.getLogger("app.utils")


@lru_cache()
def load_device() -> DeviceConfig:
    """從 device.yaml 載入配置並快取結果以避免重複 IO"""
    config_path = Path(__file__).parent.parent / "device.yaml"
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
    except Exception as e:
        logger.exception("Error loading device.yaml: %s", e)
        data = {}

    vendors = data.get("vendors", []) if isinstance(data, dict) else []
    return {"vendors": vendors}


def iter_device_entries(config: DeviceConfig | None = None) -> Iterator[Tuple[str, str, str, VersionEntry]]:
    """遍歷裝置設定檔，回傳 vendor/model/version 與版本節點資料"""

    cfg = config or load_device()

    for vendor_entry in cfg.get("vendors", []):
        vendor = vendor_entry.get("vendor")
        if not vendor:
            continue

        for model_entry in vendor_entry.get("models", []):
            model = model_entry.get("model")
            if not model:
                continue

            for version_entry in model_entry.get("versions", []):
                version = version_entry.get("version")
                if not version:
                    continue

                yield vendor, model, str(version), version_entry


def build_supported_versions_map(config: DeviceConfig | None = None) -> Dict[str, Dict[str, list[str]]]:
    """建立 vendor -> model -> versions 的快取結構"""

    supported: Dict[str, Dict[str, list[str]]] = {}
    for vendor, model, version, _ in iter_device_entries(config):
        supported.setdefault(vendor, {}).setdefault(model, [])
        if version not in supported[vendor][model]:
            supported[vendor][model].append(version)

    return supported


@lru_cache()
def load_credentials() -> Dict[str, Dict[str, str]]:
    """從 credentials.yaml 載入登入憑證

    Returns:
        Dict[serial_number, Dict[username, password]]
        例如: {"97SQ3QZXPHF": {"username": "admin", "password": "xxx"}}
    """
    credentials_path = Path(__file__).parent.parent / "credentials.yaml"

    if not credentials_path.exists():
        logger.warning(
            "credentials.yaml not found. Please copy credentials.yaml.example "
            "to credentials.yaml and fill in your passwords."
        )
        return {}

    try:
        with open(credentials_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
    except Exception as e:
        logger.exception("Error loading credentials.yaml: %s", e)
        return {}

    return data.get("credentials", {})


def get_device_credentials(serial: str) -> Optional[tuple[str, str]]:
    """取得指定設備的登入憑證

    Args:
        serial: 設備序號

    Returns:
        (username, password) tuple
    """
    credentials = load_credentials()

    # 先查找特定設備的憑證
    if serial in credentials:
        cred = credentials[serial]
        username = cred.get("username", "admin")
        password = cred.get("password", "")
        return username, password

    # 使用預設憑證
    credentials_path = Path(__file__).parent.parent / "credentials.yaml"
    if credentials_path.exists():
        try:
            with open(credentials_path, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file) or {}
            default_cred = data.get("default", {})
            username = default_cred.get("username", "admin")
            password = default_cred.get("password", "")
            return username, password
        except Exception:
            pass

    logger.warning(
        "No credentials found for device %s or in the default credentials. Please add to credentials.yaml",
        serial
    )

    return None
