import asyncio
import subprocess

import pytest

from app.models.machine import Machine
from app.services import device_connector


def make_connector(monkeypatch, credentials, default_cred):
    class DummySettings:
        def load_credentials(self):
            return credentials, default_cred

    monkeypatch.setattr(device_connector, "get_settings", lambda: DummySettings())
    monkeypatch.setattr(device_connector.shutil, "which", lambda _: None)
    return device_connector.DeviceConnector()


def make_machine(vendor="cisco", model="n9k", serial="S1"):
    return Machine(
        vendor=vendor,
        model=model,
        version="1.0",
        mgmt_ip="10.0.0.1",
        serial=serial,
        hostname="lab",
    )


def test_get_auth_uses_default_credentials(monkeypatch):
    connector = make_connector(
        monkeypatch,
        credentials={},
        default_cred={"username": "user", "password": "pass"},
    )

    assert connector._get_auth("S1") == ("user", "pass")


def test_get_auth_raises_when_missing_credentials(monkeypatch):
    connector = make_connector(monkeypatch, credentials={}, default_cred={})

    with pytest.raises(RuntimeError):
        connector._get_auth("S1")


def test_get_auth_raises_when_incomplete_credentials(monkeypatch):
    connector = make_connector(
        monkeypatch,
        credentials={"S1": {"username": "user"}},
        default_cred={},
    )

    with pytest.raises(RuntimeError):
        connector._get_auth("S1")


@pytest.mark.asyncio
@pytest.mark.parametrize("returncode, expected", [(0, True), (1, False)])
async def test_is_reachable_returncode(monkeypatch, returncode, expected):
    connector = make_connector(
        monkeypatch,
        credentials={"S1": {"username": "user", "password": "pass"}},
        default_cred={},
    )

    class DummyProc:
        def __init__(self, rc):
            self.returncode = rc

        async def wait(self):
            return None

    async def fake_exec(*args, **kwargs):
        return DummyProc(returncode)

    monkeypatch.setattr(device_connector.asyncio, "create_subprocess_exec", fake_exec)

    assert await connector.is_reachable("10.0.0.1") is expected


@pytest.mark.asyncio
async def test_is_reachable_handles_exception(monkeypatch):
    connector = make_connector(
        monkeypatch,
        credentials={"S1": {"username": "user", "password": "pass"}},
        default_cred={},
    )

    async def fake_exec(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(device_connector.asyncio, "create_subprocess_exec", fake_exec)

    assert await connector.is_reachable("10.0.0.1") is False


@pytest.mark.asyncio
async def test_get_serial_via_ssh_missing_password(monkeypatch):
    connector = make_connector(
        monkeypatch,
        credentials={"S1": {"username": "user", "password": "pass"}},
        default_cred={},
    )
    machine = make_machine()

    monkeypatch.setattr(connector, "_get_auth", lambda serial: ("user", ""))

    assert await connector.get_serial_via_ssh(machine) is None


@pytest.mark.asyncio
async def test_get_serial_via_ssh_returns_none_when_no_command(monkeypatch):
    connector = make_connector(
        monkeypatch,
        credentials={"S1": {"username": "user", "password": "pass"}},
        default_cred={},
    )
    machine = make_machine()

    monkeypatch.setattr(connector, "_get_inventory_command", lambda vendor, model: [])

    assert await connector.get_serial_via_ssh(machine) is None


@pytest.mark.asyncio
async def test_get_serial_via_ssh_returns_none_when_no_output(monkeypatch):
    connector = make_connector(
        monkeypatch,
        credentials={"S1": {"username": "user", "password": "pass"}},
        default_cred={},
    )
    machine = make_machine()

    async def fake_to_thread(func, *args, **kwargs):
        return ""

    monkeypatch.setattr(connector, "_get_inventory_command", lambda vendor, model: ["cmd"])
    monkeypatch.setattr(device_connector.asyncio, "to_thread", fake_to_thread)

    assert await connector.get_serial_via_ssh(machine) is None


@pytest.mark.asyncio
async def test_get_serial_via_ssh_parses_output(monkeypatch):
    connector = make_connector(
        monkeypatch,
        credentials={"S1": {"username": "user", "password": "pass"}},
        default_cred={},
    )
    machine = make_machine()

    async def fake_to_thread(func, *args, **kwargs):
        return 'NAME: "Chassis"\nSN: ABC123\n'

    monkeypatch.setattr(connector, "_get_inventory_command", lambda vendor, model: ["cmd"])
    monkeypatch.setattr(device_connector.asyncio, "to_thread", fake_to_thread)

    assert await connector.get_serial_via_ssh(machine) == "ABC123"


def test_get_inventory_command_mapping(monkeypatch):
    connector = make_connector(
        monkeypatch,
        credentials={"S1": {"username": "user", "password": "pass"}},
        default_cred={},
    )

    assert connector._get_inventory_command("cisco", "n9k")
    assert connector._get_inventory_command("unknown", "model") == []


def test_parse_serial_variants(monkeypatch):
    connector = make_connector(
        monkeypatch,
        credentials={"S1": {"username": "user", "password": "pass"}},
        default_cred={},
    )

    assert connector._parse_serial(
        "cisco",
        "n9k",
        'NAME: "Chassis" something SN: ABC123',
    ) == "ABC123"
    assert connector._parse_serial(
        "cisco",
        "c8k",
        'NAME: "Chassis" something SN: DEF456',
    ) == "DEF456"
    assert connector._parse_serial(
        "cisco",
        "xrv",
        'NAME: "Rack 0" SN: XYZ789',
    ) == "XYZ789"
    assert connector._parse_serial(
        "hp",
        "5945",
        "DEVICE_SERIAL_NUMBER : H123",
    ) == "H123"
    assert connector._parse_serial("acme", "unknown", "data") == ""


@pytest.mark.asyncio
async def test_reset_device_returns_false_on_restore_failure(monkeypatch):
    connector = make_connector(
        monkeypatch,
        credentials={"S1": {"username": "user", "password": "pass"}},
        default_cred={},
    )
    machine = make_machine()
    effects = [RuntimeError("restore failed")]

    async def fake_to_thread(func, *args, **kwargs):
        effect = effects.pop(0)
        if isinstance(effect, BaseException):
            raise effect
        return effect

    monkeypatch.setattr(device_connector.asyncio, "to_thread", fake_to_thread)

    assert await connector.reset_device(machine) is False


@pytest.mark.asyncio
async def test_reset_device_returns_true_on_timeout(monkeypatch):
    connector = make_connector(
        monkeypatch,
        credentials={"S1": {"username": "user", "password": "pass"}},
        default_cred={},
    )
    machine = make_machine()
    effects = ["restore output", subprocess.TimeoutExpired(cmd="ssh", timeout=8)]

    async def fake_to_thread(func, *args, **kwargs):
        effect = effects.pop(0)
        if isinstance(effect, BaseException):
            raise effect
        return effect

    monkeypatch.setattr(device_connector.asyncio, "to_thread", fake_to_thread)

    assert await connector.reset_device(machine) is True


@pytest.mark.asyncio
async def test_reset_device_returns_false_on_reload_failure(monkeypatch):
    connector = make_connector(
        monkeypatch,
        credentials={"S1": {"username": "user", "password": "pass"}},
        default_cred={},
    )
    machine = make_machine()
    effects = ["restore output", RuntimeError("reload failed")]

    async def fake_to_thread(func, *args, **kwargs):
        effect = effects.pop(0)
        if isinstance(effect, BaseException):
            raise effect
        return effect

    monkeypatch.setattr(device_connector.asyncio, "to_thread", fake_to_thread)

    assert await connector.reset_device(machine) is False


@pytest.mark.asyncio
async def test_reset_device_returns_true_on_success(monkeypatch):
    connector = make_connector(
        monkeypatch,
        credentials={"S1": {"username": "user", "password": "pass"}},
        default_cred={},
    )
    machine = make_machine()
    effects = ["restore output", "reload output"]

    async def fake_to_thread(func, *args, **kwargs):
        effect = effects.pop(0)
        if isinstance(effect, BaseException):
            raise effect
        return effect

    monkeypatch.setattr(device_connector.asyncio, "to_thread", fake_to_thread)

    assert await connector.reset_device(machine) is True


@pytest.mark.asyncio
async def test_reset_device_returns_false_for_unsupported_model(monkeypatch):
    connector = make_connector(
        monkeypatch,
        credentials={"S2": {"username": "user", "password": "pass"}},
        default_cred={},
    )
    machine = make_machine(vendor="hp", model="5945", serial="S2")

    assert await connector.reset_device(machine) is False


def test_ssh_exec_xrv_uses_single_command(monkeypatch):
    connector = make_connector(
        monkeypatch,
        credentials={"S1": {"username": "user", "password": "pass"}},
        default_cred={},
    )
    machine = make_machine(vendor="cisco", model="xrv")
    captured = {}

    class DummyResult:
        def __init__(self, returncode, stdout, stderr):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return DummyResult(0, "ok", "")

    monkeypatch.setattr(device_connector.subprocess, "run", fake_run)

    output = connector._ssh_exec(machine, "user", "pass", ["show inventory"])

    assert output == "ok"
    assert "-tt" not in captured["cmd"]
    assert "show inventory" in captured["cmd"]


def test_ssh_exec_other_vendor_adds_tty_and_warns(monkeypatch):
    connector = make_connector(
        monkeypatch,
        credentials={"S1": {"username": "user", "password": "pass"}},
        default_cred={},
    )
    machine = make_machine(vendor="cisco", model="n9k")
    captured = {}

    class DummyResult:
        def __init__(self, returncode, stdout, stderr):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["input"] = kwargs.get("input")
        return DummyResult(1, "output", "stderr")

    monkeypatch.setattr(device_connector.subprocess, "run", fake_run)

    output = connector._ssh_exec(machine, "user", "pass", ["cmd1", "cmd2"])

    assert output == "output"
    assert "-tt" in captured["cmd"]
    assert "cmd1" in captured["input"]
