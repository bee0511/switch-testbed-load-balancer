import pytest

from app.services import machine_manager
from app.services.machine_manager import MachineManager, MachineStatus, ReleaseResult


class FakeDeviceConnector:
    """Stub connector to avoid real network calls in unit tests."""

    def __init__(self):
        self.is_reachable_map = {}
        self.serial_map = {}
        self.reset_results = {}

    async def is_reachable(self, ip: str) -> bool:
        return self.is_reachable_map.get(ip, True)

    async def get_serial_via_ssh(self, machine):
        return self.serial_map.get(machine.serial, machine.serial)

    async def reset_device(self, machine) -> bool:
        return self.reset_results.get(machine.serial, True)


@pytest.fixture
def config_data():
    return {
        "cisco": {
            "n9k": {
                "9.3": [
                    {"serial": "S1", "mgmt_ip": "10.0.0.1", "hostname": "leaf1"},
                ],
            }
        },
        "hp": {
            "5945": {
                "1.0": [
                    {"serial": "H1", "mgmt_ip": "10.0.0.2", "hostname": "core1"},
                ],
            }
        },
    }


@pytest.fixture
def manager(monkeypatch, config_data):
    class DummySettings:
        def load_device_config(self):
            return config_data

        def load_credentials(self):
            return {}, {}

    monkeypatch.setattr(machine_manager, "get_settings", lambda: DummySettings())
    monkeypatch.setattr(machine_manager, "DeviceConnector", FakeDeviceConnector)
    return MachineManager()


def test_loads_devices_from_config(manager):
    serials = {m.serial for m in manager._machines.values()}
    assert serials == {"S1", "H1"}
    assert manager.get_machine("S1").vendor == "cisco"


def test_get_machines_filters_by_vendor_and_status(manager):
    manager._machines["S1"].status = MachineStatus.UNAVAILABLE
    filtered = manager.get_machines(vendor="cisco", status=MachineStatus.UNAVAILABLE)
    assert [m.serial for m in filtered] == ["S1"]


@pytest.mark.asyncio
async def test_refresh_machine_status_marks_unreachable(manager):
    machine = manager.get_machine("S1")
    manager.connector.is_reachable_map[machine.mgmt_ip] = False
    await manager.refresh_machine_status(machine)
    assert machine.status == MachineStatus.UNREACHABLE


@pytest.mark.asyncio
async def test_refresh_machine_status_marks_unavailable_on_serial_mismatch(manager):
    machine = manager.get_machine("S1")
    manager.connector.serial_map[machine.serial] = "WRONG"
    await manager.refresh_machine_status(machine)
    assert machine.status == MachineStatus.UNAVAILABLE


@pytest.mark.asyncio
async def test_reserve_machine_success_sets_unavailable(manager):
    reserved = await manager.reserve_machine("cisco", "n9k", "9.3")
    assert reserved.serial == "S1"
    assert reserved.status == MachineStatus.UNAVAILABLE


@pytest.mark.asyncio
async def test_reserve_machine_returns_none_when_all_unreachable(manager):
    machine = manager.get_machine("S1")
    manager.connector.is_reachable_map[machine.mgmt_ip] = False
    reserved = await manager.reserve_machine("cisco", "n9k", "9.3")
    assert reserved is None
    assert machine.status == MachineStatus.UNREACHABLE


@pytest.mark.asyncio
async def test_release_machine_success_sets_rebooting(manager):
    machine = manager.get_machine("S1")
    machine.status = MachineStatus.UNAVAILABLE
    manager.connector.reset_results[machine.serial] = True
    result = await manager.release_machine(machine.serial)
    assert result == ReleaseResult.SUCCESS
    assert machine.status == MachineStatus.REBOOTING


@pytest.mark.asyncio
async def test_release_machine_failed_keeps_unavailable(manager):
    machine = manager.get_machine("S1")
    machine.status = MachineStatus.UNAVAILABLE
    manager.connector.reset_results[machine.serial] = False
    result = await manager.release_machine(machine.serial)
    assert result == ReleaseResult.FAILED
    assert machine.status == MachineStatus.UNAVAILABLE


@pytest.mark.asyncio
async def test_release_machine_not_unavailable_returns_failed(manager):
    machine = manager.get_machine("S1")
    machine.status = MachineStatus.AVAILABLE
    result = await manager.release_machine(machine.serial)
    assert result == ReleaseResult.FAILED
    assert machine.status == MachineStatus.AVAILABLE


@pytest.mark.asyncio
async def test_release_machine_not_found(manager):
    result = await manager.release_machine("UNKNOWN")
    assert result == ReleaseResult.NOT_FOUND


@pytest.mark.asyncio
async def test_reload_machines_preserves_status_and_updates_list(manager, config_data):
    manager._machines["S1"].status = MachineStatus.UNAVAILABLE
    config_data["cisco"]["n9k"]["9.3"].append(
        {"serial": "S2", "mgmt_ip": "10.0.0.3", "hostname": "leaf2"}
    )
    count = await manager.reload_machines()
    assert count == 3
    assert manager.get_machine("S1").status == MachineStatus.UNAVAILABLE
    assert manager.get_machine("S2").hostname == "leaf2"
