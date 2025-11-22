import logging
from typing import Dict, List, Optional, Any
import asyncio

from app.core.config import get_settings
from app.models.machine import Machine, MachineStatus, ReleaseResult
from app.services.device_connector import DeviceConnector

logger = logging.getLogger(__name__)


class MachineManager:
    def __init__(self):
        self.connector = DeviceConnector()
        self._machines: Dict[str, Machine] = {}
        self._lock = asyncio.Lock()  # 用於並發安全

        self.load_machines()
        
    def _parse_config_to_machines(self, config: Dict[str, Any]) -> Dict[str, Machine]:
        """
        將巢狀字典結構解析為扁平的 Machine 物件列表。
        結構: vendor -> model -> version -> [devices]
        """
        parsed_machines = {}
        
        # 第一層: Vendor (例如 "cisco", "hp")
        for vendor, models in config.items():
            if not isinstance(models, dict):
                # 略過非字典的設定項
                continue
                
            # 第二層: Model (例如 "n9k", "c8k")
            for model, versions in models.items():
                if not isinstance(versions, dict):
                    continue
                    
                # 第三層: Version (例如 "9.3(13)")
                for version, devices in versions.items():
                    if not isinstance(devices, list):
                        continue
                        
                    # 第四層: Device List
                    for dev in devices:
                        try:
                            serial = str(dev["serial"])
                            
                            # Smart Reload 核心: 嘗試繼承記憶體中舊機器的狀態
                            # 如果機器已存在，保留其 Status (例如 unavailable)
                            # 如果是新機器，預設為 AVAILABLE
                            old_machine = self._machines.get(serial)
                            current_status = old_machine.status if old_machine else MachineStatus.AVAILABLE

                            m = Machine(
                                vendor=vendor,
                                model=model,
                                version=str(version),
                                serial=serial,
                                mgmt_ip=str(dev["mgmt_ip"]),
                                port=dev.get("port", 22),
                                hostname=dev.get("hostname", ""),
                                default_gateway=dev.get("default_gateway"),
                                netmask=dev.get("netmask"),
                                status=current_status
                            )
                            parsed_machines[serial] = m
                        except KeyError as e:
                            logger.error(f"Missing field {e} for device in {vendor}/{model}")
                        except Exception as e:
                            logger.error(f"Error parsing device config: {e}")
                            
        return parsed_machines
    
    def load_machines(self):
        """初始載入 (同步執行)"""
        config = get_settings().load_device_config()
        self._machines = self._parse_config_to_machines(config)
        logger.info(f"Loaded {len(self._machines)} machines from config.")
    
    async def reload_machines(self) -> int:
        """
        動態重載設定檔 (Smart Reload)。
        保留現有機器的狀態 (Available/Unavailable)，僅更新屬性或新增/移除機器。
        """
        async with self._lock:
            # 1. 重新讀取設定檔 (config.py 會讀取最新檔案)
            config = get_settings().load_device_config()
            
            # 2. 解析新設定 (會自動在 _parse_config_to_machines 中繼承舊狀態)
            new_machine_map = self._parse_config_to_machines(config)

            # 3. 計算差異 (僅供 Log 參考)
            added = set(new_machine_map.keys()) - set(self._machines.keys())
            removed = set(self._machines.keys()) - set(new_machine_map.keys())
            
            # 4. 原子替換 (Atomic Replace)
            self._machines = new_machine_map
            
            if added: logger.info(f"Machines added: {added}")
            if removed: logger.info(f"Machines removed: {removed}")
            logger.info(f"Reload complete. Total machines: {len(self._machines)}")
            
            return len(self._machines)

    async def initialize_status(self):
        """啟動時並行檢查所有機器狀態"""
        logger.info("Initializing machine statuses...")
        tasks = [self.refresh_machine_status(m)
                 for m in self._machines.values()]
        await asyncio.gather(*tasks)

    async def refresh_machine_status(self, machine: Machine):
        """更新單台機器狀態 (Ping + Serial Check)"""
        if not await self.connector.is_reachable(machine.mgmt_ip):
            machine.status = MachineStatus.UNREACHABLE
            return

        # Check the serial via SSH
        serial = await self.connector.get_serial_via_ssh(machine)
        if serial == machine.serial:
            machine.status = MachineStatus.AVAILABLE
            logger.info(f"Machine {machine.serial} is AVAILABLE.")
        else:
            machine.status = MachineStatus.UNAVAILABLE
            logger.warning(f"Machine {machine.serial} marked as UNAVAILABLE due to serial mismatch. (Expected: {machine.serial}, Got: {serial})")

    def get_machines(self, vendor: Optional[str] = None, model: Optional[str] = None, version: Optional[str] = None, status: Optional[str] = None) -> List[Machine]:
        """過濾機器列表"""
        return [
            m for m in self._machines.values()
            if (not vendor or m.vendor == vendor)
            and (not model or m.model == model)
            and (not version or m.version == version)
            and (not status or m.status == status)
        ]

    def get_machine(self, serial: str) -> Optional[Machine]:
        return self._machines.get(serial)

    async def reserve_machine(self, vendor: str, model: str, version: str) -> Optional[Machine]:
        async with self._lock:  # 防止 race condition
            candidates = self.get_machines(
                vendor, model, version, status=MachineStatus.AVAILABLE)

            for machine in candidates:
                # 再次確認目前是否真的可連線 (Double check)
                if await self.connector.is_reachable(machine.mgmt_ip):
                    machine.status = MachineStatus.UNAVAILABLE
                    logger.info(f"Reserved machine: {machine.serial}")
                    return machine
                else:
                    machine.status = MachineStatus.UNREACHABLE

            return None

    async def release_machine(self, serial: str) -> ReleaseResult:
        """
        釋放機器並執行重置。
        回傳 ReleaseResult Enum 以便 API 層判斷 HTTP 狀態碼。
        """
        machine = self.get_machine(serial)
        if not machine:
            return ReleaseResult.NOT_FOUND
        
        if machine.status == MachineStatus.AVAILABLE:
            logger.info(f"Machine {serial} is already available.")
            return ReleaseResult.ALREADY_AVAILABLE
        
        if machine.status == MachineStatus.UNREACHABLE:
            logger.warning(f"Machine {serial} is unreachable, cannot release via SSH.")
            return ReleaseResult.UNREACHABLE

        # 非同步執行重置
        success = await self.connector.reset_device(machine)
        
        if success:
            machine.status = MachineStatus.UNREACHABLE
            logger.info(f"Machine {serial} reset initiated.")
            return ReleaseResult.SUCCESS
        else:
            logger.error(f"Failed to release/reset {serial}")
            return ReleaseResult.FAILED
