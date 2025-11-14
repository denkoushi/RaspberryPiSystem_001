"""Production plan and standard time API blueprint."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

production_bp = Blueprint("production", __name__, url_prefix="/api/v1")

DEFAULT_LIMIT = 200


def _normalize_limit(value: str | None, default: int = DEFAULT_LIMIT) -> int:
    try:
        parsed = int(value) if value is not None else default
    except (TypeError, ValueError):
        parsed = default
    return max(1, min(parsed, 1000))


@production_bp.get("/production-plan")
def get_production_plan():
    limit = _normalize_limit(request.args.get("limit"))
    provider = current_app.config.get("PRODUCTION_PLAN_PROVIDER")
    entries = provider.list_entries(limit=limit) if provider else []
    return jsonify({"entries": list(entries)})


@production_bp.get("/standard-times")
def get_standard_times():
    limit = _normalize_limit(request.args.get("limit"))
    provider = current_app.config.get("STANDARD_TIME_PROVIDER")
    entries = provider.list_entries(limit=limit) if provider else []
    return jsonify({"entries": list(entries)})
