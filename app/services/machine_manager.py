import logging
from typing import Dict, List, Optional
import asyncio

from app.core.config import get_settings
from app.models.machine import Machine, MachineStatus, ReleaseResult
from app.services.device_connector import DeviceConnector

logger = logging.getLogger(__name__)


class MachineManager:
    def __init__(self):
        self.connector = DeviceConnector()
        self._machines: Dict[str, Machine] = {}
        self._load_machines()
        self._lock = asyncio.Lock()  # 用於並發安全

    def _load_machines(self):
        config = get_settings().load_device_config()
        for vendor_entry in config.get("vendors", []):
            vendor = vendor_entry["vendor"]
            for model_entry in vendor_entry.get("models", []):
                model = model_entry["model"]
                for ver_entry in model_entry.get("versions", []):
                    version = ver_entry["version"]
                    for dev in ver_entry.get("devices", []):
                        m = Machine(
                            vendor=vendor, model=model, version=version,
                            mgmt_ip=str(dev["mgmt_ip"]),
                            port=dev.get("port", 22),
                            serial=str(dev["serial_number"]),
                            hostname=dev.get("hostname", ""),
                            default_gateway=dev.get("default_gateway"),
                            netmask=dev.get("netmask")
                        )
                        self._machines[m.serial] = m
        logger.info(f"Loaded {len(self._machines)} machines.")

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
