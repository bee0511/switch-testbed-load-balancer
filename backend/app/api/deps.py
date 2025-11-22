from app.services.machine_manager import MachineManager

_manager_instance = None

def get_machine_manager() -> MachineManager:
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = MachineManager()
    return _manager_instance