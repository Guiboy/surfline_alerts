"""Client HTTP pour l'API Surfline (kbyg)."""

from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx

from worker.config import (
    FT_TO_M,
    SURFLINE_BASE_URL,
    SURFLINE_FORECAST_DAYS,
)

_TOKEN_CACHE: dict[str, Any] = {"token": None}
_TOKEN_LOCK = asyncio.Lock()

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


async def _get_access_token(client: httpx.AsyncClient) -> str | None:
    if _TOKEN_CACHE["token"]:
        return _TOKEN_CACHE["token"]
    env_token = os.environ.get("SURFLINE_ACCESS_TOKEN")
    if env_token:
        _TOKEN_CACHE["token"] = env_token
        return env_token
    async with _TOKEN_LOCK:
        if _TOKEN_CACHE["token"]:
            return _TOKEN_CACHE["token"]
        try:
            response = await client.post(
                f"{SURFLINE_BASE_URL}/access/anonymous-token",
                json={},
            )
            response.raise_for_status()
            token = response.json().get("access_token")
            if token:
                _TOKEN_CACHE["token"] = token
            return token
        except httpx.HTTPError:
            return None


async def _get_json(
    client: httpx.AsyncClient,
    path: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    url = f"{SURFLINE_BASE_URL}{path}"
    response = await client.get(url, params=params)
    if response.status_code in (401, 403):
        token = await _get_access_token(client)
        if token:
            response = await client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
            )
    response.raise_for_status()
    return response.json()


async def _fetch_spot(
    client: httpx.AsyncClient,
    spot_id: str,
) -> dict[str, Any]:
    params = {
        "spotId": spot_id,
        "days": SURFLINE_FORECAST_DAYS,
        "intervalHours": 1,
        "units": "e",
    }
    conditions = await _get_json(
        client, "/kbyg/spots/forecasts/conditions", params
    )
    wave = await _get_json(client, "/kbyg/spots/forecasts/wave", params)
    wind = await _get_json(client, "/kbyg/spots/forecasts/wind", params)
    return {
        "conditions": conditions.get("data", {}).get("conditions", []),
        "wave": wave.get("data", {}).get("wave", []),
        "wind": wind.get("data", {}).get("wind", []),
    }


async def fetch_spot_forecasts(spot_ids: list[str]) -> dict[str, dict[str, Any]]:
    """Récupère conditions, houle et vent pour chaque spot.

    Retourne un dict {spot_id: {"conditions": [...], "wave": [...], "wind": [...]}}
    avec les hauteurs converties en mètres.
    """
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(
        timeout=30.0, headers=headers, follow_redirects=True
    ) as client:
        results: dict[str, dict[str, Any]] = {}
        for spot_id in spot_ids:
            raw = await _fetch_spot(client, spot_id)
            results[spot_id] = {
                "conditions": raw["conditions"],
                "wave": [
                    {
                        "timestamp": entry["timestamp"],
                        "surf_min_m": round(
                            entry.get("surf", {}).get("min", 0) * FT_TO_M, 2
                        ),
                        "surf_max_m": round(
                            entry.get("surf", {}).get("max", 0) * FT_TO_M, 2
                        ),
                    }
                    for entry in raw["wave"]
                ],
                "wind": [
                    {
                        "timestamp": entry["timestamp"],
                        "speed_kts": entry.get("speed"),
                        "direction": entry.get("direction"),
                    }
                    for entry in raw["wind"]
                ],
            }
    return results
