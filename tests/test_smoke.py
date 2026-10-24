"""Smoke tests: package imports, entry point runs, configuration is validated."""

import importlib

import pytest

import ecodrop
from ecodrop.__main__ import main
from ecodrop.core.config import ConfigError, Settings

LAYERS = ["api", "core", "domain", "repositories", "services"]


def test_package_has_version():
    assert ecodrop.__version__


@pytest.mark.parametrize("layer", LAYERS)
def test_layers_import(layer):
    importlib.import_module(f"ecodrop.{layer}")


def test_main_runs_with_defaults(monkeypatch):
    monkeypatch.delenv("ECODROP_ENV", raising=False)
    monkeypatch.delenv("ECODROP_LOG_LEVEL", raising=False)
    assert main([]) == 0


def test_main_accepts_cli_overrides():
    assert main(["--env", "test", "--log-level", "debug"]) == 0


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
