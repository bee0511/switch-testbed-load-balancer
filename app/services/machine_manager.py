"""機器管理模組 - 負責機器分配和管理"""

import logging
from typing import Dict, List, Optional

from app.models.machine import Machine
from app.services.validator import Validator
from app.utils import iter_device_entries

logger = logging.getLogger("machine_manager")


class MachineManager:
    """Manages the allocation and status of machines."""

    def __init__(self) -> None:
        self._machines = self._load_machines_from_config()
        self._validator = Validator(self._machines)
        self._process_machine_status()

    def _load_machines_from_config(self) -> Dict[str, Machine]:
        """Load machines from the device configuration.

        Returns:
            Dict[str, Machine]: A dictionary of machines indexed by their serial numbers.
        """
        machines: Dict[str, Machine] = {}

        has_entries = False
        for vendor, model, version, version_entry in iter_device_entries():
            has_entries = True
            for dev in version_entry.get("devices", []):
                try:
                    mgmt_ip = str(dev["mgmt_ip"])
                    port = int(dev["port"])
                    serial = str(dev["serial_number"])
                    hostname = str(dev["hostname"])
                    default_gateway = str(dev["default_gateway"])
                    netmask = str(dev["netmask"])
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
                machine = Machine(
                    vendor=vendor,
                    model=model,
                    version=version,
                    mgmt_ip=mgmt_ip,
                    port=port,
                    serial=serial,
                    hostname=hostname,
                    default_gateway=default_gateway,
                    netmask=netmask,
                )
                machines[serial] = machine
        if not has_entries:
            logger.warning("No valid machines found in config.")

        return machines

    def _process_machine_status(self) -> None:
        """Process the status of each machine."""
        for machine in self._machines.values():
            self._check_specific_machine_status(machine)

    def _check_specific_machine_status(self, machine: Machine) -> bool:
        """Check the status of a specific machine.

        Args:
            machine (Machine): The machine to check.

        Returns:
            bool: True if the machine is reachable and has a valid serial, False otherwise.
        """
        if not self._check_reachability(machine):
            machine.status = "unreachable"
            return False
        elif not self._check_serial(machine):
            machine.status = "unavailable"
            return False
        else:
            machine.status = "available"
        return True

    def _matches(self, machine: Machine, vendor: str, model: str, version: str) -> bool:
        """Check whether the machine matches the given criteria.

        Args:
            machine (Machine): the machine to check.
            vendor (str): the vendor to match.
            model (str): the model to match.
            version (str): the version to match.

        Returns:
            bool: True if the machine matches the criteria, False otherwise.
        """
        return (
            machine.vendor == vendor
            and machine.model == model
            and machine.version == version
        )

    def _check_reachability(self, machine: Machine) -> bool:
        """Check whether the machine is reachable.

        Args:
            machine (Machine): The machine to check.

        Returns:
            bool: True if the machine is reachable, False otherwise.
        """
        return self._validator.validate_machine_reachability(machine)

    def _check_serial(self, machine: Machine) -> bool:
        """Check whether the machine's serial number is valid.
        Args:
            machine (Machine): The machine to check.

        Returns:
            bool: True if the machine's serial number is valid, False otherwise.
        """
        return self._validator.check_serial(machine)

    def list_machines(
        self,
        vendor: str | None = None,
        model: str | None = None,
        version: str | None = None,
        status: str | None = None,
    ) -> List[Machine]:
        """
        List machines filtered by the given criteria.
        Args:
            vendor (str | None): Vendor identifier from device.yaml.
            model (str | None): Model identifier.
            version (str | None): Version string.
            status (str | None): Machine status filter (available/unavailable/unreachable).
        Returns:
            List[Machine]: List of machines matching the criteria.
        """

        results: List[Machine] = []
        for machine in self._machines.values():
            if not self._matches(
                machine,
                vendor if vendor is not None else machine.vendor,
                model if model is not None else machine.model,
                version if version is not None else machine.version,
            ):
                continue
            if status is not None and machine.status != status:
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
            if machine.status == "available"
            and self._matches(machine, vendor, model, version)
        ]

        if not available_candidates:
            logger.info(
                "No available machines for %s/%s/%s", vendor, model, version
            )
            return None

        selected = None
        for candidate in available_candidates:
            if self._check_specific_machine_status(candidate):
                selected = candidate
                break
        if selected:
            selected.status = "unavailable"
            logger.info(
                "Reserved machine %s for %s/%s/%s",
                selected.serial,
                vendor,
                model,
                version,
            )
        else:
            logger.warning(
                "No reachable and valid machines for %s/%s/%s",
                vendor,
                model,
                version,
            )

        return selected

    def release_machine(self, serial: str) -> bool:
        """Release the machine with the corresponding serial number

        Args:
            serial (str): The serial number for the machine

        Returns:
            bool: True if the machine is successfully released, False otherwise.
        """
        machine = self._machines.get(serial)
        if not machine:
            logger.warning(
                "Attempted to release unknown machine serial=%s", serial)
            return False

        if machine.status == "available":
            logger.warning("Machine %s already available", serial)
            return True
        
        if not self._check_reachability(machine):
            logger.error(
                "Cannot release machine %s (%s): unreachable.",
                machine.serial,
                machine.mgmt_ip,
            )
            return False

        try:
            if self._validator.reset_machine(machine):
                logger.info("Reset machine %s successfully.", machine.serial)
        except Exception as e:
            logger.error(
                "Failed to reset machine %s (%s): %s",
                machine.serial,
                machine.mgmt_ip,
                e,
            )
            return False

        machine.status = "available"
        logger.info("Released machine %s", serial)
        return True

    def get_machine_by_serial(self, serial: str) -> Optional[Machine]:
        """Retrieve a machine by its serial number.

        Args:
            serial (str): The serial number of the machine.

        Returns:
            Optional[Machine]: The machine if found, None otherwise.
        """
        return self._machines.get(serial)
