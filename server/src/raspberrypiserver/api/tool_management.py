"""API endpoints for tool management (loans)."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from raspberrypiserver.services import LoanNotFoundError, ToolManagementService

toolmgmt_bp = Blueprint("tool_management", __name__)


def _get_service() -> ToolManagementService | None:
    return current_app.config.get("TOOLMGMT_SERVICE")


def _normalize_limit(value: str | None, default: int, maximum: int) -> int:
    try:
        parsed = int(value) if value is not None else default
    except (TypeError, ValueError):
        parsed = default
    return max(1, min(parsed, maximum))


def _loans_response():
    service = _get_service()
    if not service:
        return jsonify({"error": "tool_management_unavailable"}), 503
    open_limit = _normalize_limit(request.args.get("open_limit"), 100, 1000)
    history_limit = _normalize_limit(request.args.get("history_limit"), 50, 500)
    open_loans = service.list_open_loans(open_limit)
    history = service.list_recent_history(history_limit)
    return jsonify(
        {
            "open_loans": open_loans,
            "history": history,
            "open_limit": open_limit,
            "history_limit": history_limit,
        }
    )


@toolmgmt_bp.get("/api/loans")
@toolmgmt_bp.get("/api/v1/loans")
def api_loans_list():
    return _loans_response()


def _manual_return_response(loan_id: int):
    service = _get_service()
    if not service:
        return jsonify({"error": "tool_management_unavailable"}), 503
    try:
        result = service.manual_return(loan_id)
    except LoanNotFoundError:
        return jsonify({"error": "not_found"}), 404
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500
    return jsonify({"status": "ok", **result})


@toolmgmt_bp.post("/api/loans/<int:loan_id>/manual_return")
@toolmgmt_bp.post("/api/v1/loans/<int:loan_id>/manual_return")
def api_loans_manual_return(loan_id: int):
    return _manual_return_response(loan_id)


def _delete_loan_response(loan_id: int):
    service = _get_service()
    if not service:
        return jsonify({"error": "tool_management_unavailable"}), 503
    try:
        result = service.delete_open_loan(loan_id)
    except LoanNotFoundError:
        return jsonify({"error": "not_found"}), 404
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500
    return jsonify({"status": "deleted", **result})


@toolmgmt_bp.delete("/api/loans/<int:loan_id>")
@toolmgmt_bp.delete("/api/v1/loans/<int:loan_id>")
def api_delete_loan(loan_id: int):
    return _delete_loan_response(loan_id)
