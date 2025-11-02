"""
Minimal RaspberryPiServer application skeleton.

This module sets up a Flask app with a placeholder health endpoint.
The goal is to provide a starting point for migrating the existing Pi5
server code into a more modular structure.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from flask import Flask, jsonify

DEFAULT_CONFIG: Dict[str, Any] = {
    "APP_NAME": "RaspberryPiServer",
    "REST_API_PREFIX": "/api/v1",
    "SOCKETIO_NAMESPACE": "/socket.io",
}


def create_app() -> Flask:
    """Create and configure the Flask application instance."""
    app = Flask(__name__)
    load_configuration(app)

    @app.route("/healthz", methods=["GET"])
    def healthz():
        """Return application health information."""
        return (
            jsonify(
                {
                    "status": "ok",
                    "app": app.config.get("APP_NAME"),
                    "api_prefix": app.config.get("REST_API_PREFIX"),
                }
            ),
            200,
        )

    return app


def load_configuration(app: Flask, config_path: Optional[str] = None) -> None:
    """
    Load configuration into the Flask app.

    Preference order:
    1. Explicit `config_path` (pointing to TOML file)
    2. `RPI_SERVER_CONFIG` environment variable
    3. `server/config/default.toml` (if present)
    4. In-memory defaults (`DEFAULT_CONFIG`)
    """
    app.config.from_mapping(DEFAULT_CONFIG)

    explicit_path = config_path or app.config.get("RPI_SERVER_CONFIG")

    if explicit_path:
        config_file = Path(explicit_path).expanduser()
    else:
        config_file = Path(__file__).resolve().parents[2] / "config" / "default.toml"

    if config_file.exists():
        try:
            import tomllib

            with config_file.open("rb") as fh:
                data = tomllib.load(fh)
            app.config.update(data)
        except Exception as exc:  # pylint: disable=broad-except
            app.logger.warning("Failed to load config %s: %s", config_file, exc)  # noqa: PLE1205


def run() -> None:
    """Run the development server (for local testing only)."""
    app = create_app()
    app.run(host="0.0.0.0", port=8501, debug=True)


if __name__ == "__main__":
    run()
