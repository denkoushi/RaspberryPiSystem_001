"""Logistics jobs API blueprint."""

from __future__ import annotations

from typing import Iterable

from flask import Blueprint, current_app, jsonify, request

logistics_bp = Blueprint("logistics", __name__, url_prefix="/api")

DEFAULT_LIMIT = 100


def _get_limit() -> int:
    try:
        limit = int(request.args.get("limit", DEFAULT_LIMIT))
    except (TypeError, ValueError):
        return DEFAULT_LIMIT
    return max(1, min(limit, 500))


def _list_jobs_response():
    provider = current_app.config.get("LOGISTICS_PROVIDER")
    limit = _get_limit()
    items: Iterable[dict] = []
    if provider is not None:
        items = provider.list_jobs(limit=limit)
    elif current_app.config.get("LOGISTICS_JOBS"):
        items = current_app.config.get("LOGISTICS_JOBS")[:limit]
    return jsonify({"items": list(items)})


@logistics_bp.get("/logistics/jobs")
def list_logistics_jobs():
    """Return logistics jobs from the configured provider."""
    return _list_jobs_response()


@logistics_bp.get("/v1/logistics/jobs")
def list_logistics_jobs_v1():
    """Alias for /api/logistics/jobs (legacy Pi4 compatibility)."""
    return _list_jobs_response()
