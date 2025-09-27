import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterator, Tuple

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
