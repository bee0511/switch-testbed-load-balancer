import yaml
import os
from pathlib import Path
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class Settings:
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    CONFIG_DIR: Path = Path(os.getenv("CONFIG_DIR", str(BASE_DIR / "config")))
    
    @property
    def DEVICE_CONFIG_PATH(self) -> Path:
        return self.CONFIG_DIR / "device.yaml"

    @property
    def CREDENTIALS_PATH(self) -> Path:
        return self.CONFIG_DIR / "credentials.yaml"

    def load_device_config(self) -> Dict[str, Any]:
        """
        載入 device.yaml。
        每次呼叫都會重新讀取檔案，以支援動態更新。
        """
        try:
            logger.debug(f"Loading device config from {self.DEVICE_CONFIG_PATH}")
            with open(self.DEVICE_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                # 確保回傳的一定是字典
                return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.error(f"Failed to load device config: {e}")
            return {}

    def load_credentials(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        載入 credentials.yaml。
        Returns:
            Tuple[credentials_dict, default_dict]
        """
        if not self.CREDENTIALS_PATH.exists():
            logger.warning("credentials.yaml not found.")
            return {}, {}
            
        try:
            logger.debug(f"Loading credentials from {self.CREDENTIALS_PATH}")
            with open(self.CREDENTIALS_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                
                if not isinstance(data, dict):
                    data = {}

                creds = data.get("credentials")
                if not isinstance(creds, dict):
                    creds = {}

                defaults = data.get("default")
                if not isinstance(defaults, dict):
                    defaults = {}

                return creds, defaults

        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return {}, {}

def get_settings() -> Settings:
    return Settings()