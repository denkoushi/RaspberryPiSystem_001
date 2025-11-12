from __future__ import annotations

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from flask import (
    Flask,
    abort,
    current_app,
    jsonify,
    render_template,
    request,
    send_from_directory,
    url_for,
)

BASE_DIR = Path(__file__).resolve().parent.parent


def _resolve_documents_dir() -> Path:
    override = os.getenv("VIEWER_LOCAL_DOCS_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (BASE_DIR / "documents").resolve()


DOCUMENTS_DIR = _resolve_documents_dir()
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)


app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

API_BASE = os.getenv("VIEWER_API_BASE", "http://raspi-server.local:8501")
API_TOKEN = os.getenv("VIEWER_API_TOKEN")
SOCKET_BASE = os.getenv("VIEWER_SOCKET_BASE", API_BASE)
SOCKET_PATH = os.getenv("VIEWER_SOCKET_PATH", "/socket.io")
SOCKET_AUTO_OPEN = os.getenv("VIEWER_SOCKET_AUTO_OPEN", "1").lower() not in {"0", "false", "no"}
SOCKET_CLIENT_SRC = os.getenv(
    "VIEWER_SOCKET_CLIENT_SRC",
    "https://cdn.socket.io/4.7.5/socket.io.min.js",
)
LOG_PATH_RAW = os.getenv("VIEWER_LOG_PATH", "").strip()
LOG_PATH = Path(LOG_PATH_RAW).expanduser().resolve() if LOG_PATH_RAW else None


def _parse_csv_env(name: str) -> list[str]:
    raw_value = os.getenv(name, "")
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


ACCEPT_DEVICE_IDS = _parse_csv_env("VIEWER_ACCEPT_DEVICE_IDS")
ACCEPT_LOCATION_CODES = _parse_csv_env("VIEWER_ACCEPT_LOCATION_CODES")


def _resolve_socket_events() -> list[str]:
    """
    Resolve the list of Socket.IOイベント名.

    優先順位:
    1. `VIEWER_SOCKET_EVENTS`（カンマ区切り）
    2. `VIEWER_SOCKET_EVENT`（単一指定）
    3. 互換性維持のための既定リスト
    """

    events = _parse_csv_env("VIEWER_SOCKET_EVENTS")
    single_event = os.getenv("VIEWER_SOCKET_EVENT", "").strip()
    if single_event:
        events.append(single_event)

    if not events:
        events = ["scan.ingested", "part_location_updated", "scan_update"]

    seen = set()
    deduped: list[str] = []
    for event in events:
        normalized = event.strip()
        if not normalized or normalized in seen:
            continue
        deduped.append(normalized)
        seen.add(normalized)
    return deduped


SOCKET_EVENTS = _resolve_socket_events()


def _build_socket_script_url() -> str | None:
    override = SOCKET_CLIENT_SRC.strip() if SOCKET_CLIENT_SRC else ""
    if override:
        return override
    if not SOCKET_BASE:
        return None
    base = SOCKET_BASE.rstrip("/")
    path = SOCKET_PATH.strip() or "/socket.io"
    if not path.startswith("/"):
        path = f"/{path}"
    script_path = f"{path.rstrip('/')}/socket.io.js"
    return f"{base}{script_path}"


def find_document_filename(part_number: str) -> Optional[str]:
    """Return the PDF filename for the given part number if it exists."""
    normalized = part_number.strip()
    if not normalized:
        return None

    lower = normalized.lower()
    for pdf_path in DOCUMENTS_DIR.glob("*.pdf"):
        if pdf_path.stem.lower() == lower:
            return pdf_path.name

    candidate = DOCUMENTS_DIR / f"{normalized}.pdf"
    if candidate.exists():
        return candidate.name
    return None


def _configure_logger() -> logging.Logger:
    logger = logging.getLogger("document_viewer")
    logger.setLevel(logging.INFO)
    for handler in list(logger.handlers):
        if getattr(handler, "_document_viewer_handler", False):
            logger.removeHandler(handler)
            try:
                handler.close()
            except Exception:  # pylint: disable=broad-except
                pass

    if LOG_PATH is None:
        return logger

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return logger

    handler = RotatingFileHandler(LOG_PATH, maxBytes=3 * 1024 * 1024, backupCount=3)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    handler._document_viewer_handler = True  # type: ignore[attr-defined]
    logger.addHandler(handler)
    return logger


LOGGER = _configure_logger()


def _log_info(message: str, *args) -> None:
    LOGGER.info(message, *args)
    current_app.logger.info(message, *args)


def _log_warning(message: str, *args) -> None:
    LOGGER.warning(message, *args)
    current_app.logger.warning(message, *args)


@app.after_request
def disable_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/")
def index():
    return render_template(
        "index.html",
        api_base=API_BASE,
        api_token=API_TOKEN,
        socket_script=_build_socket_script_url(),
        docviewer_config={
            "apiBase": API_BASE,
            "apiToken": API_TOKEN,
            "socketBase": SOCKET_BASE,
            "socketPath": SOCKET_PATH,
            "socketAutoOpen": SOCKET_AUTO_OPEN,
            "socketEvents": SOCKET_EVENTS,
            "acceptDeviceIds": ACCEPT_DEVICE_IDS,
            "acceptLocationCodes": ACCEPT_LOCATION_CODES,
        },
    )


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/documents/<path:filename>")
def serve_document(filename: str):
    safe_path = DOCUMENTS_DIR / filename
    if not safe_path.exists() or not safe_path.is_file():
        _log_warning("Invalid document access attempt: %s", filename)
        abort(404)
    _log_info("Document served: %s", filename)
    return send_from_directory(DOCUMENTS_DIR, filename, mimetype="application/pdf")


@app.route("/api/documents/<path:part_number>")
def api_get_document(part_number: str):
    filename = find_document_filename(part_number)
    if not filename:
        _log_info("Document not found: %s", part_number)
        return jsonify({"found": False, "message": "document not found"}), 404

    document_url = url_for("serve_document", filename=filename)
    # Append a timestamp to avoid aggressive kiosk caching
    cache_bust = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    document_url_with_cache = f"{document_url}?v={cache_bust}"
    _log_info("Document lookup success: %s -> %s", part_number, filename)
    return jsonify({
        "found": True,
        "partNumber": part_number,
        "filename": filename,
        "url": document_url_with_cache,
    })


@app.route("/api/socket-events", methods=["POST"])
def api_log_socket_event():
    if not request.is_json:
        return jsonify({"logged": False, "error": "invalid payload"}), 400
    data = request.get_json(silent=True) or {}
    event_name = str(data.get("event") or "unknown").strip() or "unknown"
    payload = data.get("payload")
    _log_info("Socket.IO event: %s payload=%s", event_name, payload)
    return jsonify({"logged": True}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
