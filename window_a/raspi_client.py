"""Minimal HTTP client for talking to RaspberryPiServer."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

import requests


class RaspiServerError(Exception):
    """Base error."""


class RaspiServerAuthError(RaspiServerError):
    """Authentication error."""


class RaspiServerClientError(RaspiServerError):
    """Request/response error."""


class RaspiServerConfigError(RaspiServerError):
    """Configuration missing."""


@dataclass
class RaspiServerClient:
    base_url: str
    api_token: Optional[str] = None
    timeout: float = 5.0

    @classmethod
    def from_env(cls) -> "RaspiServerClient":
        base = os.getenv("RASPI_SERVER_BASE", "").strip()
        token = os.getenv("RASPI_SERVER_API_TOKEN")
        timeout = float(os.getenv("RASPI_SERVER_TIMEOUT", "5.0"))
        return cls(base_url=base, api_token=token, timeout=timeout)

    def is_configured(self) -> bool:
        return bool(self.base_url)

    def _build_url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url.rstrip('/')}{path}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
        allow_statuses: Optional[Iterable[int]] = None,
    ) -> requests.Response:
        if not self.is_configured():
            raise RaspiServerConfigError("RASPI_SERVER_BASE is not configured")

        url = self._build_url(path)
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=self.timeout,
                headers=headers,
            )
        except requests.RequestException as exc:
            raise RaspiServerClientError(str(exc)) from exc

        allowed = set(allow_statuses or {200})
        if response.status_code == 401:
            raise RaspiServerAuthError(response.text or "Unauthorized")
        if response.status_code not in allowed:
            raise RaspiServerClientError(
                f"{method} {path} returned {response.status_code}: {response.text}"
            )
        return response

    def get_json(self, path: str, params: Optional[dict] = None, allow_statuses: Optional[Sequence[int]] = None):
        response = self._request("GET", path, params=params, allow_statuses=allow_statuses)
        try:
            return response.json()
        except ValueError as exc:
            raise RaspiServerClientError("Invalid JSON response") from exc

    def post_json(self, path: str, payload: Optional[dict] = None, allow_statuses: Optional[Sequence[int]] = None):
        response = self._request("POST", path, json=payload, allow_statuses=allow_statuses)
        try:
            return response.json()
        except ValueError:
            return {"status": response.text}
