"""
Minimal RaspberryPiServer application skeleton.

This module sets up a Flask app with a placeholder health endpoint.
The goal is to provide a starting point for migrating the existing Pi5
server code into a more modular structure.
"""

from __future__ import annotations

from flask import Flask, jsonify


def create_app() -> Flask:
    """Create and configure the Flask application instance."""
    app = Flask(__name__)

    @app.route("/healthz", methods=["GET"])
    def healthz():
        """Return application health information."""
        return jsonify({"status": "ok"}), 200

    return app


def run() -> None:
    """Run the development server (for local testing only)."""
    app = create_app()
    app.run(host="0.0.0.0", port=8501, debug=True)


if __name__ == "__main__":
    run()
