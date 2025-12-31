import pytest
import yaml

from app.core.config import Settings, get_settings


def test_settings_requires_config_dir(monkeypatch):
    monkeypatch.delenv("CONFIG_DIR", raising=False)
    with pytest.raises(RuntimeError):
        Settings()


def test_ensure_file_raises_when_missing(tmp_path):
    missing = tmp_path / "missing.yaml"
    with pytest.raises(FileNotFoundError):
        Settings._ensure_file(missing, "device config")


def test_ensure_file_raises_when_not_file(tmp_path):
    directory = tmp_path / "config-dir"
    directory.mkdir()
    with pytest.raises(FileExistsError):
        Settings._ensure_file(directory, "device config")


def test_load_device_config_requires_mapping(monkeypatch, tmp_path):
    device_path = tmp_path / "device.yaml"
    device_path.write_text("- not-a-mapping\n", encoding="utf-8")
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path))

    settings = Settings()
    with pytest.raises(ValueError):
        settings.load_device_config()


def test_load_device_config_success(monkeypatch, tmp_path):
    device_path = tmp_path / "device.yaml"
    device_path.write_text("cisco:\n  n9k: {}\n", encoding="utf-8")
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path))

    settings = Settings()
    data = settings.load_device_config()

    assert data["cisco"]["n9k"] == {}


def test_load_credentials_requires_mapping(monkeypatch, tmp_path):
    credentials_path = tmp_path / "credentials.yaml"
    credentials_path.write_text("- bad\n", encoding="utf-8")
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path))

    settings = Settings()
    with pytest.raises(ValueError):
        settings.load_credentials()


def test_load_credentials_requires_credentials_key(monkeypatch, tmp_path):
    credentials_path = tmp_path / "credentials.yaml"
    credentials_path.write_text(yaml.safe_dump({"default": {"username": "u"}}), encoding="utf-8")
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path))

    settings = Settings()
    with pytest.raises(ValueError):
        settings.load_credentials()


def test_load_credentials_requires_default_mapping(monkeypatch, tmp_path):
    credentials_path = tmp_path / "credentials.yaml"
    credentials_path.write_text(
        yaml.safe_dump({"credentials": {}, "default": ["bad"]}),
        encoding="utf-8",
    )
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path))

    settings = Settings()
    with pytest.raises(ValueError):
        settings.load_credentials()


def test_load_credentials_success(monkeypatch, tmp_path):
    credentials_path = tmp_path / "credentials.yaml"
    credentials_path.write_text(
        yaml.safe_dump(
            {
                "credentials": {"S1": {"username": "user", "password": "pass"}},
                "default": {"username": "default", "password": "default"},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path))

    settings = Settings()
    creds, defaults = settings.load_credentials()

    assert creds["S1"]["username"] == "user"
    assert defaults["password"] == "default"


def test_get_settings_returns_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path))

    settings = get_settings()

    assert isinstance(settings, Settings)
