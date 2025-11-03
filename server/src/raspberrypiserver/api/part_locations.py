"""Part locations API."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from raspberrypiserver.repositories import PartLocationRepository

part_locations_bp = Blueprint("part_locations", __name__, url_prefix="/api/v1")


@part_locations_bp.route("/part-locations", methods=["GET"])
def list_part_locations():
    limit = request.args.get("limit", default=200, type=int)
    limit = max(1, min(limit, 500))

    repo: PartLocationRepository = current_app.config["PART_LOCATION_REPOSITORY"]
    entries = []
    for item in repo.list(limit):
        entries.append(
            {
                "order_code": item.get("order_code"),
                "location_code": item.get("location_code"),
                "device_id": item.get("device_id"),
                "updated_at": str(item.get("updated_at")) if item.get("updated_at") else None,
            }
        )

    return jsonify({"entries": entries})
