import yaml
import os
from pathlib import Path
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class Settings:
    def __init__(self):
        self.BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
        config_dir = os.getenv("CONFIG_DIR")
        if not config_dir:
            raise RuntimeError("CONFIG_DIR is required but not set.")

        self.CONFIG_DIR: Path = Path(config_dir)
        self.DEVICE_CONFIG_PATH: Path = Path(
            os.getenv("DEVICE_CONFIG_PATH", str(self.CONFIG_DIR / "device.yaml"))
        )
        self.CREDENTIALS_PATH: Path = Path(
            os.getenv("CREDENTIALS_PATH", str(self.CONFIG_DIR / "credentials.yaml"))
        )

    @staticmethod
    def _ensure_file(path: Path, kind: str) -> None:
        if not path.exists():
            raise FileNotFoundError(f"{kind} not found at {path}")
        if not path.is_file():
            raise FileExistsError(f"{kind} at {path} is not a file")

    def load_device_config(self) -> Dict[str, Any]:
        """
        載入 device.yaml。
        每次呼叫都會重新讀取檔案，以支援動態更新。
        """
        self._ensure_file(self.DEVICE_CONFIG_PATH, "device config")
        logger.debug(f"Loading device config from {self.DEVICE_CONFIG_PATH}")
        with open(self.DEVICE_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError("device.yaml must be a mapping")

        return data

    def load_credentials(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        載入 credentials.yaml。
        Returns:
            Tuple[credentials_dict, default_dict]
        """
        self._ensure_file(self.CREDENTIALS_PATH, "credentials config")
        logger.debug(f"Loading credentials from {self.CREDENTIALS_PATH}")
        with open(self.CREDENTIALS_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError("credentials.yaml must be a mapping")

        creds = data.get("credentials")
        if not isinstance(creds, dict):
            raise ValueError("credentials.yaml missing 'credentials' mapping")

        defaults = data.get("default")
        if defaults is not None and not isinstance(defaults, dict):
            raise ValueError("credentials.yaml 'default' must be a mapping when provided")

        return creds, defaults or {}

def get_settings() -> Settings:
    return Settings()
