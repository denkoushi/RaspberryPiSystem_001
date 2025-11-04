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
    raw_payload = request.get_json(silent=True)
    try:
        payload = _normalize_payload(raw_payload)
    except ValueError as exc:
        logger.info("Rejected scan payload: %s (%s)", raw_payload, exc)
        return (
            jsonify(
                {
                    "status": "error",
                    "reason": str(exc),
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )

    # TODO: integrate with actual persistence / Socket.IO broadcast
    logger.info("Received scan payload: %s", payload)
    repo: ScanRepository = current_app.config["SCAN_REPOSITORY"]
    repo.save(payload)

    broadcaster: BroadcastService | None = current_app.config.get("BROADCAST_SERVICE")
    if broadcaster:
        broadcaster.emit("scan.ingested", payload)

    drained = None
    auto_limit = int(current_app.config.get("AUTO_DRAIN_ON_INGEST", 0) or 0)
    backlog_service = current_app.config.get("BACKLOG_DRAIN_SERVICE")
    if auto_limit > 0 and backlog_service and backlog_service.is_configured():
        drained = backlog_service.drain_once(limit=auto_limit)

    response = {
        "status": "accepted",
        "received": payload,
        "app": current_app.config.get("APP_NAME"),
    }
    if drained is not None:
        response["backlog_drained"] = drained
    return jsonify(response), HTTPStatus.ACCEPTED


def _normalize_payload(raw_payload: Any) -> Dict[str, Any]:
    if not isinstance(raw_payload, dict):
        raise ValueError("invalid-json")

    order_code = raw_payload.get("order_code")
    if not isinstance(order_code, str) or not order_code.strip():
        raise ValueError("missing-order_code")

    location_code = raw_payload.get("location_code")
    if not isinstance(location_code, str) or not location_code.strip():
        raise ValueError("missing-location_code")

    device_id = raw_payload.get("device_id")
    if device_id is not None:
        if not isinstance(device_id, str) or not device_id.strip():
            raise ValueError("invalid-device_id")

    normalized: Dict[str, Any] = {
        "order_code": order_code.strip(),
        "location_code": location_code.strip(),
    }
    if device_id is not None:
        normalized["device_id"] = device_id.strip()

    metadata = raw_payload.get("metadata")
    if isinstance(metadata, dict):
        normalized["metadata"] = metadata

    return normalized
