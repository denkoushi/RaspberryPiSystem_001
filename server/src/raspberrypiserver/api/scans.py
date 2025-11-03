"""Blueprint placeholder for /api/v1/scans endpoint."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Any, Dict

from flask import Blueprint, current_app, jsonify, request

from raspberrypiserver.repositories import ScanRepository
from raspberrypiserver.services import BroadcastService

logger = logging.getLogger(__name__)

scans_bp = Blueprint("scans", __name__, url_prefix="/api/v1")


@scans_bp.route("/scans", methods=["POST"])
def ingest_scan():
    """Placeholder endpoint for ingesting scan data."""
    payload: Dict[str, Any] = request.get_json(silent=True) or {}

    # TODO: integrate with actual persistence / Socket.IO broadcast
    logger.info("Received scan payload: %s", payload)
    repo: ScanRepository = current_app.config["SCAN_REPOSITORY"]
    repo.save(payload)

    broadcaster: BroadcastService | None = current_app.config.get("BROADCAST_SERVICE")
    if broadcaster:
        broadcaster.emit("scan.ingested", payload)

    response = {
        "status": "accepted",
        "received": payload,
        "app": current_app.config.get("APP_NAME"),
    }
    return jsonify(response), HTTPStatus.ACCEPTED
