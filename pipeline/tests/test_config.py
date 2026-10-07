from pathlib import Path

import pytest
import yaml

from metabo.config import load_config
from metabo.errors import ConfigError


def test_repository_config_is_valid():
    config = load_config()
    umbrales = config.cobertura.umbrales
    assert umbrales.completa > umbrales.casi_completa > umbrales.parcial


def _write(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def _base() -> dict:
    return yaml.safe_load(Path(__file__).parents[1].joinpath("config.yaml").read_text())


def test_unordered_thresholds_are_rejected(tmp_path):
    data = _base()
    data["cobertura"]["umbrales"] = {"completa": 100, "casi_completa": 20, "parcial": 30}
    with pytest.raises(ConfigError, match="completa > casi_completa > parcial"):
        load_config(_write(tmp_path, data))


def test_unknown_keys_are_rejected(tmp_path):
    data = _base()
    data["descargas"]["clave_inventada"] = 1
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_invalid_contact_email_is_rejected(tmp_path):
    data = _base()
    data["descargas"]["contacto"] = "no-es-un-correo"
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_missing_file_is_a_config_error(tmp_path):
    with pytest.raises(ConfigError, match="No existe"):
        load_config(tmp_path / "no-existe.yaml")


def test_repository_config_never_stores_the_contact_email():
    raw = yaml.safe_load(Path(__file__).parents[1].joinpath("config.yaml").read_text())
    assert raw["descargas"]["contacto"] is None


def test_contact_is_read_from_environment(monkeypatch):
    monkeypatch.setenv("METABO_CONTACTO", "  contacto@ejemplo.invalid  ")
    assert load_config().descargas.contacto == "contacto@ejemplo.invalid"


def test_without_environment_contact_is_missing(monkeypatch):
    monkeypatch.delenv("METABO_CONTACTO", raising=False)
    assert load_config().descargas.contacto is None


def test_invalid_environment_contact_is_rejected_without_echoing_it(monkeypatch):
    monkeypatch.setenv("METABO_CONTACTO", "valor-secreto-invalido")
    with pytest.raises(ConfigError, match="METABO_CONTACTO") as error:
        load_config()
    assert "valor-secreto-invalido" not in str(error.value)
