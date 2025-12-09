import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_machine_manager
from app.main import app
from app.models.machine import Machine, MachineStatus, ReleaseResult

pytestmark = pytest.mark.asyncio


class FakeMachineManager:
    def __init__(self):
        self.machines = {
            "S1": Machine(
                vendor="cisco",
                model="n9k",
                version="9.3",
                mgmt_ip="10.0.0.1",
                serial="S1",
                hostname="leaf-1",
                status=MachineStatus.AVAILABLE,
            ),
            "S2": Machine(
                vendor="cisco",
                model="n9k",
                version="9.3",
                mgmt_ip="10.0.0.2",
                serial="S2",
                hostname="leaf-2",
                status=MachineStatus.UNAVAILABLE,
            ),
            "S3": Machine(
                vendor="hp",
                model="5945",
                version="1.0",
                mgmt_ip="10.0.0.3",
                serial="S3",
                hostname="core-1",
                status=MachineStatus.UNREACHABLE,
            ),
        }
        self.release_outcomes = {}
        self.reload_should_raise = False

    async def initialize_status(self):
        return None

    def get_machines(
        self,
        vendor=None,
        model=None,
        version=None,
        status=None,
    ):
        return [
            m
            for m in self.machines.values()
            if (vendor is None or m.vendor == vendor)
            and (model is None or m.model == model)
            and (version is None or m.version == version)
            and (status is None or m.status == status)
        ]

    def get_machine(self, serial):
        return self.machines.get(serial)

    async def reserve_machine(self, vendor, model, version):
        for machine in self.get_machines(
            vendor=vendor, model=model, version=version, status=MachineStatus.AVAILABLE
        ):
            machine.status = MachineStatus.UNAVAILABLE
            return machine
        return None

    async def release_machine(self, serial):
        machine = self.machines.get(serial)
        if machine is None:
            return ReleaseResult.NOT_FOUND

        outcome = self.release_outcomes.get(serial, ReleaseResult.SUCCESS)
        if outcome == ReleaseResult.SUCCESS:
            machine.status = MachineStatus.REBOOTING
        return outcome

    async def reload_machines(self):
        if self.reload_should_raise:
            raise RuntimeError("reload failed")
        return len(self.machines)


@pytest.fixture
def fake_manager():
    return FakeMachineManager()


@pytest.fixture
def api_token():
    return "test-token"


@pytest.fixture(autouse=True)
def set_api_token(monkeypatch, api_token):
    monkeypatch.setenv("API_BEARER_TOKEN", api_token)


@pytest.fixture
def auth_headers(api_token):
    return {"Authorization": f"Bearer {api_token}"}


@pytest_asyncio.fixture
async def client(fake_manager, auth_headers):
    original_overrides = app.dependency_overrides.copy()
    async def override_get_manager():
        return fake_manager

    app.dependency_overrides[get_machine_manager] = override_get_manager

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver", headers=auth_headers
    ) as test_client:
        yield test_client

    app.dependency_overrides = original_overrides


async def test_auth_rejects_invalid_token(client):
    response = await client.get("/machines", headers={"Authorization": "Bearer wrong-token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing token"


async def test_health_endpoint(client):
    response = await client.get("/health", headers={})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_list_machines_returns_all(client):
    response = await client.get("/machines")
    assert response.status_code == 200
    serials = {machine["serial"] for machine in response.json()["machines"]}
    assert serials == {"S1", "S2", "S3"}


async def test_list_machines_filters_by_status(client):
    response = await client.get("/machines", params={"status": MachineStatus.UNAVAILABLE.value})
    assert response.status_code == 200
    machines = response.json()["machines"]
    assert [m["serial"] for m in machines] == ["S2"]


async def test_reserve_machine_success(client, fake_manager):
    response = await client.post("/reserve/cisco/n9k/9.3")
    assert response.status_code == 200
    payload = response.json()
    assert payload["serial"] == "S1"
    assert payload["status"] == MachineStatus.UNAVAILABLE.value
    assert fake_manager.machines["S1"].status == MachineStatus.UNAVAILABLE


async def test_reserve_machine_returns_404_when_unavailable(client, fake_manager):
    fake_manager.machines["S1"].status = MachineStatus.UNREACHABLE
    response = await client.post("/reserve/cisco/n9k/9.3")
    assert response.status_code == 404
    assert response.json()["detail"] == "No available machines found"


async def test_release_machine_success(client, fake_manager):
    fake_manager.machines["S2"].status = MachineStatus.UNAVAILABLE
    response = await client.post("/release/S2")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == ReleaseResult.SUCCESS.value
    assert payload["machine"]["serial"] == "S2"
    assert payload["machine"]["status"] == MachineStatus.REBOOTING.value


async def test_release_machine_not_found(client):
    response = await client.post("/release/UNKNOWN")
    assert response.status_code == 404
    assert response.json()["detail"] == "Machine UNKNOWN not found"


async def test_release_machine_failed(client, fake_manager):
    fake_manager.release_outcomes["S2"] = ReleaseResult.FAILED
    fake_manager.machines["S2"].status = MachineStatus.UNAVAILABLE
    response = await client.post("/release/S2")
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to execute reset command on the device."


async def test_reload_configuration_success(client):
    response = await client.post("/admin/reload")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


async def test_reload_configuration_failure(client, fake_manager):
    fake_manager.reload_should_raise = True
    response = await client.post("/admin/reload")
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to reload configuration"
