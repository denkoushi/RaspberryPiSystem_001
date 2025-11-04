"""
Minimal RaspberryPiServer application skeleton.

This module sets up a Flask app with a placeholder health endpoint.
The goal is to provide a starting point for migrating the existing Pi5
server code into a more modular structure.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from flask import Flask, jsonify, current_app
from flask_socketio import SocketIO

from raspberrypiserver.repositories import (
    DatabasePartLocationRepository,
    DatabaseScanRepository,
    InMemoryPartLocationRepository,
    InMemoryScanRepository,
    PartLocationRepository,
    ScanRepository,
)
from raspberrypiserver.services import (
    BroadcastService,
    SocketIOBroadcastService,
    BacklogDrainService,
)

DEFAULT_CONFIG: Dict[str, Any] = {
    "APP_NAME": "RaspberryPiServer",
    "REST_API_PREFIX": "/api/v1",
    "SOCKETIO_NAMESPACE": "/",
    "SCAN_REPOSITORY_CAPACITY": 250,
    "SCAN_REPOSITORY_BACKEND": "memory",
    "SCAN_REPOSITORY_BUFFER": 500,
    "SOCKET_BROADCAST_EVENT": "scan.ingested",
    "AUTO_DRAIN_ON_INGEST": 0,
    "database": {"dsn": ""},
}

socketio = SocketIO(async_mode="gevent", cors_allowed_origins="*")


def create_app() -> Flask:
    """Create and configure the Flask application instance."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = app.config.get('SECRET_KEY', 'dev-secret')
    socketio.init_app(app, cors_allowed_origins="*")
    load_configuration(app)
    initialize_services(app)
    register_blueprints(app)

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


def register_blueprints(app: Flask) -> None:
    """Register Flask blueprints for REST APIs."""
    from raspberrypiserver.api import scans_bp, part_locations_bp, maintenance_bp

    app.register_blueprint(scans_bp)
    app.register_blueprint(part_locations_bp)
    app.register_blueprint(maintenance_bp)


@socketio.on("connect")
def handle_socket_connect(auth):
    current_app.logger.info("Socket.IO client connected auth=%s", auth)


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

    explicit_path = config_path or os.environ.get("RPI_SERVER_CONFIG") or app.config.get("RPI_SERVER_CONFIG")

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


def initialize_services(app: Flask) -> None:
    """Initialize service instances and attach to the app context."""
    capacity = int(app.config.get("SCAN_REPOSITORY_CAPACITY", 250))
    backend = str(app.config.get("SCAN_REPOSITORY_BACKEND", "memory")).lower()
    app.config["SOCKETIO_INSTANCE"] = socketio

    if backend == "db":
        database_cfg = app.config.get("database") or {}
        dsn = database_cfg.get("dsn", "")
        buffer_size = int(app.config.get("SCAN_REPOSITORY_BUFFER", 500))
        repo = DatabaseScanRepository(dsn=dsn, buffer_size=buffer_size)
    else:
        repo = InMemoryScanRepository(capacity=capacity)

    app.config["SCAN_REPOSITORY"] = repo

    if not app.config.get("BROADCAST_SERVICE"):
        namespace = app.config.get("SOCKETIO_NAMESPACE", "/")
        event_name = app.config.get("SOCKET_BROADCAST_EVENT", "scan.ingested")
        app.config["BROADCAST_SERVICE"] = SocketIOBroadcastService(
            socketio=app.config.get("SOCKETIO_INSTANCE"),
            namespace=namespace,
            default_event=event_name,
        )

    if backend == "db":
        backlog_service = BacklogDrainService(
            dsn=database_cfg.get("dsn", ""),
            limit=int(app.config.get("BACKLOG_DRAIN_LIMIT", 200)),
            backlog_table=app.config.get("BACKLOG_TABLE", "scan_ingest_backlog"),
            target_table=app.config.get("TARGET_TABLE", "part_locations"),
        )
        app.config["BACKLOG_DRAIN_SERVICE"] = backlog_service
        part_repo: PartLocationRepository = DatabasePartLocationRepository(database_cfg.get("dsn", ""))
    else:
        app.config["BACKLOG_DRAIN_SERVICE"] = None
        part_repo = InMemoryPartLocationRepository(repo)

    app.config["PART_LOCATION_REPOSITORY"] = part_repo


def run() -> None:
    """Run the development server (for local testing only)."""
    app = create_app()
    socketio.run(app, host="0.0.0.0", port=8501, debug=True, use_reloader=False)


if __name__ == "__main__":
    run()
