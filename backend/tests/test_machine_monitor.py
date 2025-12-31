import asyncio

import pytest

from app.models.machine import Machine, MachineStatus
from app.services import machine_monitor


class FakeConnector:
    def __init__(self, reachability):
        self.reachability = reachability

    async def is_reachable(self, ip: str) -> bool:
        return self.reachability.get(ip, False)


class FakeManager:
    def __init__(self, machines, reachability):
        self._machines = machines
        self.connector = FakeConnector(reachability)

    def get_machines(self, status=None):
        if status is None:
            return list(self._machines)
        return [machine for machine in self._machines if machine.status == status]


@pytest.mark.asyncio
async def test_monitor_machines_updates_statuses(monkeypatch):
    machines = [
        Machine(
            vendor="cisco",
            model="n9k",
            version="1.0",
            mgmt_ip="10.0.0.1",
            serial="U1",
            hostname="u1",
            status=MachineStatus.UNREACHABLE,
        ),
        Machine(
            vendor="cisco",
            model="n9k",
            version="1.0",
            mgmt_ip="10.0.0.5",
            serial="U2",
            hostname="u2",
            status=MachineStatus.UNREACHABLE,
        ),
        Machine(
            vendor="cisco",
            model="n9k",
            version="1.0",
            mgmt_ip="10.0.0.2",
            serial="A1",
            hostname="a1",
            status=MachineStatus.AVAILABLE,
        ),
        Machine(
            vendor="cisco",
            model="n9k",
            version="1.0",
            mgmt_ip="10.0.0.3",
            serial="R1",
            hostname="r1",
            status=MachineStatus.REBOOTING,
        ),
        Machine(
            vendor="cisco",
            model="n9k",
            version="1.0",
            mgmt_ip="10.0.0.4",
            serial="R2",
            hostname="r2",
            status=MachineStatus.REBOOTING,
        ),
    ]
    reachability = {
        "10.0.0.1": True,
        "10.0.0.2": False,
        "10.0.0.3": False,
        "10.0.0.4": True,
        "10.0.0.5": False,
    }
    manager = FakeManager(machines, reachability)

    async def fake_sleep(interval):
        raise asyncio.CancelledError

    monkeypatch.setattr(machine_monitor.asyncio, "sleep", fake_sleep)

    await machine_monitor.monitor_machines(manager)

    assert machines[0].status == MachineStatus.AVAILABLE
    assert machines[1].status == MachineStatus.UNREACHABLE
    assert machines[2].status == MachineStatus.UNREACHABLE
    assert machines[3].status == MachineStatus.UNREACHABLE
    assert machines[4].status == MachineStatus.REBOOTING


@pytest.mark.asyncio
async def test_monitor_machines_handles_exception(monkeypatch):
    class ExplodingManager:
        def __init__(self):
            self.connector = FakeConnector({})

        def get_machines(self, status=None):
            raise RuntimeError("boom")

    manager = ExplodingManager()

    async def fake_sleep(interval):
        raise asyncio.CancelledError

    monkeypatch.setattr(machine_monitor.asyncio, "sleep", fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await machine_monitor.monitor_machines(manager)
