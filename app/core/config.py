import yaml
from pathlib import Path
from functools import lru_cache
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class Settings:
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DEVICE_CONFIG_PATH: Path = BASE_DIR / "device.yaml"
    CREDENTIALS_PATH: Path = BASE_DIR / "credentials.yaml"

    def load_device_config(self) -> Dict[str, Any]:
        try:
            with open(self.DEVICE_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                # 確保回傳的一定是字典，避免 yaml 格式錯誤或為空時回傳 None/List
                return data if isinstance(data, dict) else {"vendors": []}
        except Exception as e:
            logger.error(f"Failed to load device config: {e}")
            return {"vendors": []}

    def load_credentials(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        載入憑證檔案。
        Returns:
            Tuple[credentials_dict, default_dict]
        """
        if not self.CREDENTIALS_PATH.exists():
            logger.warning("credentials.yaml not found.")
            return {}, {}
            
        try:
            with open(self.CREDENTIALS_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                
                # 安全性檢查 1: 檔案如果是空的或格式不對，確保 data 是字典
                if not isinstance(data, dict):
                    data = {}

                # 安全性檢查 2: 取出的值如果是 None (例如 yaml key 存在但為空)，強制轉為 {}
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

@lru_cache()
def get_settings() -> Settings:
    return Settings()