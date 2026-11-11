"""Sélection des créneaux de bonnes conditions et construction de l'email."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from worker.config import (
    RATING_LABELS_FR,
    RATING_ORDER,
    TIMEZONE,
)

_COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

_DAYS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
_MONTHS_FR = [
    "", "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def rating_rank(rating: str) -> int:
    return RATING_ORDER.get(rating.upper(), -1)


def degrees_to_compass(degrees: float | None) -> str | None:
    if degrees is None:
        return None
    index = round((degrees % 360) / 22.5) % 16
    return _COMPASS[index]


def _date_label(date_iso: str) -> str:
    date = datetime.fromisoformat(date_iso).date()
    return f"{_DAYS_FR[date.weekday()]} {date.day} {_MONTHS_FR[date.month]}"


def select_good_windows(
    forecasts: dict[str, dict],
    spots_by_id: dict[str, dict],
    now: datetime,
    min_rating: str = "FAIR",
    days_ahead: list[int] | None = None,
    day_start_hour: int = 6,
    day_end_hour: int = 21,
) -> list[dict]:
    """Retourne les créneaux dont le rating est >= min_rating.

    `forecasts` : {spot_id: {"conditions": [...], "wave": [...], "wind": [...]}}
    `spots_by_id` : {spot_id: {"name": ..., "url": ...}}
    Les créneaux sont groupés par spot et par journée, bornés aux heures
    diurnes [day_start_hour, day_end_hour) du fuseau TIMEZONE.
    """
    days_ahead = days_ahead if days_ahead is not None else [1, 2]
    tz = ZoneInfo(TIMEZONE)
    now_local = now.astimezone(tz)
    target_dates = {
        (now_local + timedelta(days=offset)).date() for offset in days_ahead
    }
    min_rank = rating_rank(min_rating)

    windows: list[dict] = []
    for spot_id, forecast in forecasts.items():
        spot = spots_by_id.get(spot_id)
        if spot is None:
            continue
        wave_by_ts = {entry["timestamp"]: entry for entry in forecast.get("wave", [])}
        wind_by_ts = {entry["timestamp"]: entry for entry in forecast.get("wind", [])}

        intervals_by_date: dict[object, list[dict]] = {}
        for condition in forecast.get("conditions", []):
            rating = condition.get("rating", "")
            if rating_rank(rating) < min_rank:
                continue
            ts = condition.get("timestamp")
            if ts is None:
                continue
            local_dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(tz)
            if local_dt.date() not in target_dates:
                continue
            if not (day_start_hour <= local_dt.hour < day_end_hour):
                continue
            wave = wave_by_ts.get(ts, {})
            wind = wind_by_ts.get(ts, {})
            entry = {
                "timestamp": ts,
                "hour": local_dt.hour,
                "rating": rating,
                "surf_min_m": wave.get("surf_min_m"),
                "surf_max_m": wave.get("surf_max_m"),
                "wind_speed_kts": wind.get("speed_kts"),
                "wind_direction": degrees_to_compass(wind.get("direction")),
            }
            intervals_by_date.setdefault(local_dt.date(), []).append(entry)

        for date, intervals in intervals_by_date.items():
            intervals.sort(key=lambda entry: entry["timestamp"])
            windows.append(
                {
                    "spot_id": spot_id,
                    "spot_name": spot["name"],
                    "spot_url": spot["url"],
                    "date": date.isoformat(),
                    "intervals": intervals,
                }
            )

    windows.sort(key=lambda window: (window["date"], window["spot_name"]))
    return windows


def _format_window_line(window: dict) -> str:
    intervals = window["intervals"]
    hours = ", ".join(f"{entry['hour']:02d}h" for entry in intervals)
    best = max(intervals, key=lambda entry: rating_rank(entry["rating"]))
    surf_max = max(
        (entry["surf_max_m"] for entry in intervals if entry["surf_max_m"] is not None),
        default=None,
    )
    wind_speeds = [
        entry["wind_speed_kts"]
        for entry in intervals
        if entry["wind_speed_kts"] is not None
    ]
    wind = f"{min(wind_speeds):.0f}-{max(wind_speeds):.0f} kts" if wind_speeds else "n/d"
    directions = sorted(
        {
            entry["wind_direction"]
            for entry in intervals
            if entry.get("wind_direction")
        }
    )
    wind_dir = f" {('/'.join(directions))}" if directions else ""
    surf = f"{surf_max:.1f} m max" if surf_max is not None else "n/d"
    rating_fr = RATING_LABELS_FR.get(best["rating"], best["rating"])
    return (
        f"{hours} — {rating_fr} ({best['rating'].replace('_', ' ').title()}) — "
        f"houle {surf} — vent {wind}{wind_dir}"
    )


def build_email(
    windows: list[dict],
) -> tuple[str, str, str]:
    """Construit (sujet, corps texte, corps HTML) de l'email d'alerte."""
    by_date: dict[str, list[dict]] = {}
    for window in windows:
        by_date.setdefault(window["date"], []).append(window)

    text_lines: list[str] = []
    html_sections: list[str] = []
    for date_iso in sorted(by_date):
        text_lines.append(f"=== {_date_label(date_iso)} ===")
        rows: list[str] = []
        for window in sorted(by_date[date_iso], key=lambda w: w["spot_name"]):
            line = _format_window_line(window)
            text_lines.append(f"{window['spot_name']} — {line}")
            rows.append(
                f"<li><a href=\"{window['spot_url']}\">{window['spot_name']}</a> — {line}</li>"
            )
        html_sections.append(
            f"<h3>{_date_label(date_iso).capitalize()}</h3><ul>{''.join(rows)}</ul>"
        )

    text_body = (
        "Bonnes conditions de surf prévues :\n\n" + "\n".join(text_lines)
        + "\n\nPrévisions : Open-Meteo (houle + vent) — notes calculées localement."
        + "\nSpots sur Surfline : https://www.surfline.com"
    )
    html_body = (
        "<h2>🏄 Bonnes conditions de surf à venir</h2>"
        + "".join(html_sections)
        + "<p style=\"color:#888\">Prévisions Open-Meteo — notes calculées automatiquement."
        " Spots : <a href=\"https://www.surfline.com\">Surfline</a>.</p>"
    )
    subject = f"🏄 Surf : {len(windows)} spot(s) bien notés à J+1/J+2"
    return subject, text_body, html_body
