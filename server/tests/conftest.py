import os
import pathlib

import pytest

from raspberrypiserver.app import create_app, load_configuration


@pytest.fixture
def app(tmp_path: pathlib.Path):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
APP_NAME = "TestServer"
REST_API_PREFIX = "/api/v1"
"""
    )
    os.environ["RPI_SERVER_CONFIG"] = str(config_path)
    app = create_app()
    yield app
    os.environ.pop("RPI_SERVER_CONFIG", None)
