"""機器管理模組 - 負責機器分配和管理"""

import logging
from typing import Dict, List, Optional

from app.models.machine import Machine
from app.utils import iter_device_entries

logger = logging.getLogger("machine_manager")


class MachineManager:
    """集中管理 device.yaml 中所有測試機的可用狀態。"""

    def __init__(self) -> None:
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
                except (KeyError, TypeError, ValueError) as error:
                    logger.error(
                        "Bad device entry under %s/%s/%s: %s (%s)",
                        vendor,
                        model,
                        version,
                        dev,
                        error,
                    )
                    continue

                if serial in machines:
                    logger.warning(
                        "Duplicate serial '%s' found; overriding previous entry.", serial
                    )

                machines[serial] = Machine(
                    vendor=vendor,
                    model=model,
                    version=version,
                    ip=ip,
                    port=port,
                    serial=serial,
                    available=True,
                )

        if not has_entries:
            logger.warning("No valid machines found in config.")

        return machines

    def _matches(self, machine: Machine, vendor: str, model: str, version: str) -> bool:
        return (
            machine.vendor == vendor
            and machine.model == model
            and machine.version == version
        )

    def list_machines(
        self,
        vendor: str | None = None,
        model: str | None = None,
        version: str | None = None,
        status: str | None = None,
    ) -> List[Machine]:
        """Return machines filtered by optional criteria."""

        expected_availability: bool | None = None
        if status is not None:
            normalized = status.lower()
            if normalized not in {"available", "unavailable"}:
                raise ValueError(f"Unsupported status filter: {status}")
            expected_availability = normalized == "available"

        results: List[Machine] = []
        for machine in self._machines.values():
            if not self._matches(
                machine,
                vendor if vendor is not None else machine.vendor,
                model if model is not None else machine.model,
                version if version is not None else machine.version,
            ):
                continue
            if expected_availability is not None and machine.available != expected_availability:
                continue
            results.append(machine)

        return results

    def reserve_machines(
        self, vendor: str, model: str, version: str
    ) -> Machine | None:
        """Reserve available machines that match the given spec.

        Args:
            vendor: Vendor identifier from device.yaml.
            model: Model identifier.
            version: Version string.
        Returns:
            Machine | None: reserved machine. The machine is flagged unavailable immediately.
        """

        available_candidates = [
            machine
            for machine in self._machines.values()
            if machine.available and self._matches(machine, vendor, model, version)
        ]

        if not available_candidates:
            logger.info(
                "No available machines for %s/%s/%s", vendor, model, version
            )
            return None

        selected = available_candidates[0]
        selected.available = False
        logger.info(
            "Reserved machine %s for %s/%s/%s",
            selected.serial,
                vendor,
                model,
                version,
            )

        return selected

    def release_machine(self, serial: str) -> bool:
        machine = self._machines.get(serial)
        if not machine:
            logger.warning("Attempted to release unknown machine serial=%s", serial)
            return False

        if machine.available:
            logger.info("Machine %s already available", serial)
            return True

        machine.available = True
        logger.info("Released machine %s", serial)
        return True

    def get_machine_by_serial(self, serial: str) -> Optional[Machine]:
        return self._machines.get(serial)