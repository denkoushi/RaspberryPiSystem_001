from pathlib import Path

import pytest

from raspberrypiserver import app as app_module


def test_create_app_configures_file_logging(tmp_path, monkeypatch):
    log_file = tmp_path / "logs" / "app.log"
    config_file = tmp_path / "config.toml"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(
        "\n".join(
            [
                'APP_NAME = "LogTest"',
                "",
                "[logging]",
                'level = "DEBUG"',
                f'path = "{log_file}"',
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("RPI_SERVER_CONFIG", str(config_file))
    flask_app = app_module.create_app()

    flask_app.logger.debug("file logging configured")

    assert log_file.exists(), "log file should be created by configure_logging"
    contents = Path(log_file).read_text(encoding="utf-8")
    assert "file logging configured" in contents

    monkeypatch.delenv("RPI_SERVER_CONFIG", raising=False)
