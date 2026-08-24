"""Minimal Home Assistant Core API client for an app container."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class HomeAssistantClient:
    def __init__(self, base_url: str = "http://supervisor/core/api") -> None:
        token = os.environ.get("SUPERVISOR_TOKEN")
        if not token:
            raise RuntimeError("SUPERVISOR_TOKEN is not available")
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        return self._request_url(method, f"{self.base_url}/{path.lstrip('/')}", payload)

    def supervisor_request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> Any:
        return self._request_url(method, f"http://supervisor/{path.lstrip('/')}", payload)

    def _request_url(
        self, method: str, url: str, payload: dict[str, Any] | None = None
    ) -> Any:
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(
            url,
            data=data,
            headers=self.headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Home Assistant API returned HTTP {error.code}: {detail}") from error

    def get_report_links(self, configured_base_url: str = "") -> tuple[str, str | None]:
        addon = self.supervisor_request("GET", "addons/self/info").get("data", {})
        slug = addon.get("slug")
        if not slug:
            raise RuntimeError("Supervisor did not return the app slug")
        path = f"/app/{slug}"
        core_config = self.request("GET", "config")
        base_url = configured_base_url or core_config.get("external_url") or core_config.get("internal_url")
        absolute = f"{str(base_url).rstrip('/')}{path}" if base_url else None
        return path, absolute

    def call_service(
        self, domain: str, service: str, data: dict[str, Any], *, return_response: bool = False
    ) -> Any:
        suffix = "?return_response" if return_response else ""
        return self.request("POST", f"services/{domain}/{service}{suffix}", data)

    def get_statistics(
        self,
        statistic_ids: list[str],
        start_time: str,
        end_time: str,
        period: str = "hour",
    ) -> dict[str, Any]:
        response = self.call_service(
            "recorder",
            "get_statistics",
            {
                "statistic_ids": statistic_ids,
                "start_time": start_time,
                "end_time": end_time,
                "period": period,
                "types": ["min", "max", "mean"],
            },
            return_response=True,
        )
        return response.get("service_response", {}).get("statistics", {})

    def get_forecast(self, weather_entity: str, forecast_type: str = "daily") -> dict[str, Any]:
        return self.call_service(
            "weather",
            "get_forecasts",
            {"entity_id": weather_entity, "type": forecast_type},
            return_response=True,
        ).get("service_response", {})
