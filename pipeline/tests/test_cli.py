from metabo.cli import STAGES, main
from metabo.paths import PIPELINE_DIR


def test_validate_command(capsys):
    assert main(["validate"]) == 0
    assert "OK" in capsys.readouterr().out


def test_build_command_lists_every_stage(capsys):
    assert main(["build"]) == 0
    out = capsys.readouterr().out
    for name, _ in STAGES:
        assert name in out
    assert "no se descargará nada" in out


def test_fuentes_command_marks_link_only_sources(capsys):
    assert main(["fuentes"]) == 0
    kegg = next(line for line in capsys.readouterr().out.splitlines() if line.startswith("kegg"))
    assert "no descargable" in kegg


def test_errors_are_reported_without_traceback(capsys, monkeypatch, tmp_path):
    # Raíz sin sources.yaml: el comando debe fallar con un mensaje, no con una traza.
    monkeypatch.setenv("METABO_ROOT", str(tmp_path))
    (tmp_path / "schema").symlink_to(PIPELINE_DIR.parent / "schema")
    assert main(["fuentes"]) == 1
    assert "Error:" in capsys.readouterr().err
