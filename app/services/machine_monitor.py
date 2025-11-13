import logging
import threading
import time
from typing import Dict, Callable

from app.models.machine import Machine

logger = logging.getLogger("machine_monitor")


class MachineMonitor:
    """Monitors unreachable machines and automatically recovers them when they become available."""

    def __init__(
        self,
        machines: Dict[str, Machine],
        check_reachability_func: Callable[[Machine], bool],
        check_interval: int = 10,
    ) -> None:
        """Initialize the machine monitor.

        Args:
            machines (Dict[str, Machine]): Dictionary of machines to monitor.
            check_reachability_func (Callable): Function to check if a machine is reachable.
            check_serial_func (Callable): Function to validate machine serial number.
            check_interval (int): Interval in seconds between each check (default: 10).
        """
        self._machines = machines
        self._check_reachability = check_reachability_func
        self._check_interval = check_interval
        self._monitoring = False
        self._monitor_thread: threading.Thread | None = None
        self._monitor_lock = threading.Lock()

    def start(self) -> None:
        """Start background monitoring thread for unreachable machines."""
        with self._monitor_lock:
            if self._monitoring:
                logger.warning("Monitoring is already running.")
                return

            self._monitoring = True
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="MachineMonitor",
            )
            self._monitor_thread.start()
            logger.info(
                "Started background monitoring for unreachable machines (interval: %ds)",
                self._check_interval,
            )

    def stop(self) -> None:
        """Stop the background monitoring thread."""
        with self._monitor_lock:
            if not self._monitoring:
                logger.warning("Monitoring is not running.")
                return

            self._monitoring = False
            if self._monitor_thread:
                self._monitor_thread.join(timeout=5)
                self._monitor_thread = None
            logger.info(
                "Stopped background monitoring for unreachable machines")

    def _monitor_loop(self) -> None:
        """Background thread function that monitors unreachable machines."""
        logger.info("Machine monitoring thread started")

        while self._monitoring:
            try:
                # 找出所有 unreachable 的機器
                unreachable_machines = [
                    machine
                    for machine in self._machines.values()
                    if machine.status == "unreachable"
                ]

                if unreachable_machines:
                    logger.debug(
                        "Checking %d unreachable machine(s)", len(
                            unreachable_machines)
                    )

                for machine in unreachable_machines:
                    if not self._monitoring:
                        break

                    self._check_and_recover_machine(machine)

                # 等待下一次檢查
                for _ in range(self._check_interval):
                    if not self._monitoring:
                        break
                    time.sleep(1)

            except Exception as e:
                logger.error("Error in monitoring thread: %s",
                             e, exc_info=True)
                time.sleep(self._check_interval)

        logger.info("Machine monitoring thread stopped")

    def _check_and_recover_machine(self, machine: Machine) -> None:
        """Check and attempt to recover an unreachable machine.

        Args:
            machine (Machine): The machine to check and recover.
        """
        # 嘗試檢查機器狀態
        if self._check_reachability(machine):
            machine.status = "available"
            logger.info(
                "Machine %s (%s) recovered and set to available",
                machine.serial,
                machine.mgmt_ip,
            )
        else:
            logger.debug(
                "Machine %s (%s) is still unreachable",
                machine.serial,
                machine.mgmt_ip,
            )
