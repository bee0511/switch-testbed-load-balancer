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
            rebooting = manager.get_machines(status=MachineStatus.REBOOTING)
            for machine in rebooting:
                # 如果 Ping 通 -> 代表還在關機過程中，或者剛重啟完還沒死透 -> 保持 REBOOTING 不變，不做任何事
                # 如果 Ping 不通 -> 代表終於關機成功了 -> 轉為 UNREACHABLE (等待下次啟動被上面的邏輯1捕獲)
                if not await manager.connector.is_reachable(machine.mgmt_ip):
                    logger.info(f"Machine {machine.serial} finally went down (Reboot confirmed).")
                    machine.status = MachineStatus.UNREACHABLE
                else:
                    logger.debug(f"Machine {machine.serial} is still rebooting (Pingable)...")
            await asyncio.sleep(INTERVAL)
        except asyncio.CancelledError:
            logger.info("Monitor stopped.")
            break
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            await asyncio.sleep(INTERVAL)
            