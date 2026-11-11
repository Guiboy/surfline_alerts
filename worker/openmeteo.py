"""Client HTTP Open-Meteo (houle + vent), sans clé API."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import httpx

from worker.config import (
    FORECAST_DAYS,
    OPENMETEO_MARINE_URL,
    OPENMETEO_WEATHER_URL,
    SPOTS,
)
from worker.rating import compute_rating

SPOTS_BY_ID = {spot.spot_id: spot for spot in SPOTS}


def _to_epoch(iso: str, utc_offset_seconds: int) -> int:
    local_dt = datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)
    return int(local_dt.timestamp() - utc_offset_seconds)


def _parse_hourly(payload: dict[str, Any]) -> tuple[list[int], dict[str, list[Any]]]:
    offset = payload.get("utc_offset_seconds", 0)
    hourly = payload.get("hourly", {})
    times = [_to_epoch(t, offset) for t in hourly.get("time", [])]
    return times, hourly


def build_spot_forecast(
    marine_payload: dict[str, Any],
    weather_payload: dict[str, Any],
    facing_deg: float,
) -> dict[str, Any]:
    """Assemble houle + vent et calcule le rating horaire.

    Contrat identique à l'ancien client Surfline :
    {"conditions": [...], "wave": [...], "wind": [...]}
    """
    marine_times, marine = _parse_hourly(marine_payload)
    weather_times, weather = _parse_hourly(weather_payload)

    wind_by_ts: dict[int, tuple[Any, Any]] = {}
    for i, ts in enumerate(weather_times):
        wind_by_ts[ts] = (
            weather.get("wind_speed_10m", [None] * len(weather_times))[i],
            weather.get("wind_direction_10m", [None] * len(weather_times))[i],
        )

    hs = marine.get("wave_height", [])
    period = marine.get("wave_period", [])
    direction = marine.get("wave_direction", [])

    conditions: list[dict[str, Any]] = []
    wave: list[dict[str, Any]] = []
    wind: list[dict[str, Any]] = []
    for i, ts in enumerate(marine_times):
        height = hs[i] if i < len(hs) else None
        per = period[i] if i < len(period) else None
        speed_kts, wind_deg = wind_by_ts.get(ts, (None, None))
        rating = compute_rating(height, per, speed_kts, wind_deg, facing_deg)
        conditions.append({"timestamp": ts, "rating": rating})
        wave.append(
            {
                "timestamp": ts,
                "surf_min_m": round(height * 0.7, 2) if height is not None else None,
                "surf_max_m": round(height * 1.2, 2) if height is not None else None,
            }
        )
        wind.append(
            {
                "timestamp": ts,
                "speed_kts": speed_kts,
                "direction": wind_deg,
            }
        )
    return {"conditions": conditions, "wave": wave, "wind": wind}


async def fetch_spot_forecasts(spot_ids: list[str]) -> dict[str, dict[str, Any]]:
    """Récupère houle et vent pour chaque spot et calcule les ratings horaires."""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:

        async def fetch_one(spot_id: str) -> tuple[str, dict[str, Any]]:
            spot = SPOTS_BY_ID[spot_id]
            marine_params = {
                "latitude": spot.lat,
                "longitude": spot.lon,
                "hourly": "wave_height,wave_period,wave_direction",
                "models": "best_match",
                "forecast_days": FORECAST_DAYS,
                "timezone": "UTC",
            }
            weather_params = {
                "latitude": spot.lat,
                "longitude": spot.lon,
                "hourly": "wind_speed_10m,wind_direction_10m",
                "wind_speed_unit": "kn",
                "forecast_days": FORECAST_DAYS,
                "timezone": "UTC",
            }
            marine_r, weather_r = await asyncio.gather(
                client.get(OPENMETEO_MARINE_URL, params=marine_params),
                client.get(OPENMETEO_WEATHER_URL, params=weather_params),
            )
            marine_r.raise_for_status()
            weather_r.raise_for_status()
            return spot_id, build_spot_forecast(
                marine_r.json(), weather_r.json(), spot.facing_deg
            )

        pairs = await asyncio.gather(*(fetch_one(spot_id) for spot_id in spot_ids))
    return dict(pairs)
