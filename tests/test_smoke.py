"""Smoke tests: package imports, entry point runs, configuration is validated."""

import importlib

import pytest

import ecodrop
from ecodrop.__main__ import main
from ecodrop.core.config import ConfigError, Settings

LAYERS = ["api", "core", "domain", "repositories", "schemas", "services"]


@pytest.fixture(autouse=True)
def server_calls(monkeypatch):
    """Record uvicorn.run calls instead of starting a real server."""
    calls = []
    monkeypatch.setattr(
        "ecodrop.__main__.uvicorn.run", lambda *args, **kwargs: calls.append(kwargs)
    )
    return calls


def test_package_has_version():
    assert ecodrop.__version__


@pytest.mark.parametrize("layer", LAYERS)
def test_layers_import(layer):
    importlib.import_module(f"ecodrop.{layer}")


def test_main_runs_with_defaults(monkeypatch, server_calls):
    for name in ("ECODROP_ENV", "ECODROP_LOG_LEVEL", "ECODROP_HOST", "ECODROP_PORT"):
        monkeypatch.delenv(name, raising=False)
    assert main([]) == 0
    assert server_calls == [{"host": "127.0.0.1", "port": 8000, "log_level": "info"}]


def test_main_accepts_cli_overrides(server_calls):
    args = ["--env", "test", "--log-level", "debug", "--host", "0.0.0.0", "--port", "9000"]
    assert main(args) == 0
    assert server_calls == [{"host": "0.0.0.0", "port": 9000, "log_level": "debug"}]


def test_main_rejects_invalid_port(monkeypatch, capsys, server_calls):
    monkeypatch.setenv("ECODROP_PORT", "http")
    assert main([]) == 2
    assert "Configuration error" in capsys.readouterr().err
    assert server_calls == []


def test_main_rejects_invalid_env_variable(monkeypatch, capsys):
    monkeypatch.setenv("ECODROP_ENV", "staging")
    assert main([]) == 2
    assert "Configuration error" in capsys.readouterr().err


def test_main_rejects_invalid_cli_argument():
    with pytest.raises(SystemExit) as exc_info:
        main(["--env", "staging"])
    assert exc_info.value.code == 2


def test_settings_from_env_normalizes_values():
    settings = Settings.from_env({"ECODROP_ENV": " Production ", "ECODROP_LOG_LEVEL": "warning"})
    assert settings == Settings(env="production", log_level="WARNING")


def test_settings_rejects_invalid_log_level():
    with pytest.raises(ConfigError):
        Settings(log_level="VERBOSE")


def test_settings_rejects_out_of_range_port():
    with pytest.raises(ConfigError):
        Settings(port=70000)
