"""Blueprint placeholder for /api/v1/scans endpoint."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Any, Dict

from flask import Blueprint, current_app, jsonify, request

logger = logging.getLogger(__name__)

scans_bp = Blueprint("scans", __name__, url_prefix="/api/v1")


@scans_bp.route("/scans", methods=["POST"])
def ingest_scan():
    """Placeholder endpoint for ingesting scan data."""
    payload: Dict[str, Any] = request.get_json(silent=True) or {}

    # TODO: integrate with actual persistence / Socket.IO broadcast
    logger.info("Received scan payload: %s", payload)

    response = {
        "status": "accepted",
        "received": payload,
        "app": current_app.config.get("APP_NAME"),
    }
    return jsonify(response), HTTPStatus.ACCEPTED
