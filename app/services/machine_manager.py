"""
機器管理模組 - 負責機器分配和管理
"""

from typing import Dict, List, Optional
from app.utils import iter_device_entries
from app.models.machine import Machine

class MachineManager:
    """機器管理器 - 負責機器分配、釋放和狀態管理"""
    
    def __init__(self):
        """
        初始化機器管理器
        """
        self._machines: Dict[str, Machine] = self._load_machines_from_config()
        
    def _load_machines_from_config(self) -> Dict[str, Machine]:
        machines: Dict[str, Machine] = {}

        has_entries = False
        for vendor, model, version, version_entry in iter_device_entries():
            has_entries = True
            for dev in version_entry.get("devices", []):
                try:
                    ip = str(dev["ip"])
                    port = int(dev["port"])
                    serial = str(dev["serial_number"])
                except (KeyError, TypeError, ValueError) as e:
                    print(
                        f"[MachineManager] Bad device entry under {vendor}/{model}/{version}: {dev} ({e})"
                    )
                    continue

                # 若 serial 重複，後者覆蓋並提示
                if serial in machines:
                    print(
                        f"[MachineManager] Duplicate serial '{serial}' found; overriding previous entry."
                    )

                machines[serial] = Machine(
                    vendor=vendor,
                    model=model,
                    version=version,
                    ip=ip,
                    port=port,
                    serial=serial,
                )

        if not has_entries:
            print("[MachineManager] No valid machines found in config.")

        return machines
    
    def _check_model_supported(self, machine: Machine, vendor: str, model: str, version: str) -> bool:
        """
        檢查機器是否支援指定的型號(可用來擴展更多條件)
        """
        if machine.vendor != vendor:
            return False
        if machine.model != model:
            return False
        if machine.version != version:
            return False
        return True

    def _get_available_machines(self, vendor: str, model: str, version: str) -> List[Machine]:
        """取得空閒的機器列表"""
        available = []
        for machine in self._machines.values():
            if machine.ticket_id is None and self._check_model_supported(machine, vendor, model, version):
                available.append(machine)
        return available

    def allocate_machine(self, ticket_id: str, vendor: str, model: str, version: str) -> Optional[Machine]:
        """
        為票據分配機器
        
        Args:
            ticket_id: 票據ID
            vendor: 供應商
            model: 型號
            
        Returns:
            Optional[Machine]: 分配的機器，如果無可用機器則返回 None
        """
        available_machines = self._get_available_machines(vendor, model, version)
        if not available_machines:
            print(f"[MachineManager] No available machines for ticket: {ticket_id}")
            return None
        
        selected_machine = available_machines[0]
        
        if not selected_machine:
            print(f"[MachineManager] Failed to select machine for ticket: {ticket_id}")
            return None
        
        # 分配機器
        self._machines[selected_machine.serial].ticket_id = ticket_id
        print(f"[MachineManager] Allocated machine: {selected_machine.serial} to ticket: {ticket_id}")
        return selected_machine

    def release_machine(self, machine: Machine) -> bool:
        """
        釋放機器
        
        Args:
            machine: 機器物件
            
        Returns:
            bool: 是否成功釋放
        """
        if machine.serial not in self._machines:
            print(f"[MachineManager] Machine {machine.serial} not found")
            return False

        ticket_id = self._machines[machine.serial].ticket_id
        self._machines[machine.serial].ticket_id = None
        print(f"[MachineManager] Released machine: {machine.serial} (was processing ticket: {ticket_id})")
        return True

    def validate_ticket_machine(self, ticket_id: str, machine_serial: str) -> bool:
        """
        驗證票據確實分配給指定機器
        
        Args:
            ticket_id: 票據ID
            machine_serial: 機器ID
            
        Returns:
            bool: 是否匹配
        """
        machine = self.get_machine_by_serial(machine_serial)
        machine_ticket = machine.ticket_id if machine else None

        return machine_ticket == ticket_id

    def get_machine_status(self) -> Dict[str, Optional[str]]:
        """
        取得所有機器的狀態
        
        Returns:
            Dict[str, Optional[str]]: 機器狀態 (None = 空閒, 票據ID = 忙碌)
        """
        return {serial: machine.ticket_id for serial, machine in self._machines.items()}

    def get_machine_by_serial(self, serial: str) -> Optional[Machine]:
        """
        根據序號取得機器
        
        Args:
            serial: 機器序號
            
        Returns:
            Optional[Machine]: 機器物件或 None
        """
        return self._machines.get(serial)
    
    def get_running_count(self) -> int:
        """
        取得正在執行中的票據數量
        
        Returns:
            int: 執行中的票據數量
        """
        count = 0
        for machine in self._machines.values():
            if machine.ticket_id is not None:
                count += 1
        return count