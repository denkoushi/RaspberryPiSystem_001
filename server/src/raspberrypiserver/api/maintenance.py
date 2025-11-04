"""Maintenance/admin endpoints for RaspberryPiServer."""

from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, current_app, jsonify, request

from raspberrypiserver.services.backlog import BacklogDrainService

maintenance_bp = Blueprint("maintenance", __name__, url_prefix="/api/v1/admin")


@maintenance_bp.route("/drain-backlog", methods=["POST"])
def trigger_backlog_drain():
    """
    Trigger backlog drain job once.

    Accepts optional JSON ペイロード ({"limit": 100}) またはクエリ文字列 (?limit=100) で
    一度のドレイン件数を上書きできる。
    """
    service: BacklogDrainService | None = current_app.config.get("BACKLOG_DRAIN_SERVICE")

    if not service or not service.is_configured():
        return (
            jsonify(
                {
                    "status": "skipped",
                    "reason": "backlog-drain-disabled",
                }
            ),
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    payload = request.get_json(silent=True) or {}
    limit = payload.get("limit")
    if limit is None:
        limit = request.args.get("limit", type=int)

    drained = service.drain_once(limit=limit)
    return (
        jsonify(
            {
                "status": "ok",
                "drained": drained,
                "limit": limit or service.limit,
            }
        ),
        HTTPStatus.OK,
    )


@maintenance_bp.route("/backlog-status", methods=["GET"])
def backlog_status():
    """Return backlog statistics (pending count, limits, auto-drain settings)."""
    service: BacklogDrainService | None = current_app.config.get("BACKLOG_DRAIN_SERVICE")
    auto_limit = int(current_app.config.get("AUTO_DRAIN_ON_INGEST", 0) or 0)

    if not service or not service.is_configured():
        return (
            jsonify(
                {
                    "status": "disabled",
                    "pending": 0,
                    "auto_drain_on_ingest": auto_limit,
                }
            ),
            HTTPStatus.OK,
        )

    pending = service.count_backlog()
    return (
        jsonify(
            {
                "status": "ok",
                "pending": pending,
                "drain_limit": service.limit,
                "auto_drain_on_ingest": auto_limit,
            }
        ),
        HTTPStatus.OK,
    )
