import asyncio
import logging
from app.services.machine_manager import MachineManager
from app.models.machine import MachineStatus

logger = logging.getLogger(__name__)

async def monitor_machines(manager: MachineManager):
    """背景任務：定期檢查機器是否可以連線"""
    INTERVAL = 10
    logger.info("Background monitor started.")
    while True:
        try:
            unreachable = manager.get_machines(status=MachineStatus.UNREACHABLE)
            for machine in unreachable:
                # 如果 Ping 通了，改回 Available
                if await manager.connector.is_reachable(machine.mgmt_ip):
                    logger.info(f"Machine {machine.serial} recovered.")
                    machine.status = MachineStatus.AVAILABLE
                else:
                    logger.debug(f"Machine {machine.serial} still unreachable.")
            
            available = manager.get_machines(status=MachineStatus.AVAILABLE)
            for machine in available:
                # 如果不可達，改成 Unreachable
                if not await manager.connector.is_reachable(machine.mgmt_ip):
                    logger.info(f"Machine {machine.serial} became unreachable.")
                    machine.status = MachineStatus.UNREACHABLE
            await asyncio.sleep(INTERVAL)
        except asyncio.CancelledError:
            logger.info("Monitor stopped.")
            break
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            await asyncio.sleep(INTERVAL)
            