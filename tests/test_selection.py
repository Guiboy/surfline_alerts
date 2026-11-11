"""Tests de la sélection des créneaux et de la construction de l'email."""

from datetime import datetime, timezone

from worker.selection import (
    build_email,
    degrees_to_compass,
    rating_rank,
    select_good_windows,
)

NOW = datetime(2026, 2, 5, 15, 0, tzinfo=timezone.utc)  # jeudi 16h Paris

SPOTS_BY_ID = {
    "spot-1": {"name": "La Couronne", "url": "https://www.surfline.com/surf-report/la-couronne/spot-1"},
}


def _ts(day_offset: int, hour_paris: int) -> int:
    from datetime import timedelta
    from zoneinfo import ZoneInfo

    tz = ZoneInfo("Europe/Paris")
    local = (NOW + timedelta(days=day_offset)).astimezone(tz).replace(
        hour=hour_paris, minute=0, second=0, microsecond=0
    )
    return int(local.timestamp())


def _forecast(ratings_by_ts: dict[int, str]) -> dict:
    return {
        "conditions": [{"timestamp": ts, "rating": rating} for ts, rating in ratings_by_ts.items()],
        "wave": [
            {"timestamp": ts, "surf_min_m": 0.5, "surf_max_m": 1.0}
            for ts in ratings_by_ts
        ],
        "wind": [
            {"timestamp": ts, "speed_kts": 8.0, "direction": 45.0}
            for ts in ratings_by_ts
        ],
    }


def test_rating_rank_ordering():
    assert rating_rank("FLAT") < rating_rank("POOR") < rating_rank("FAIR") < rating_rank("GOOD")
    assert rating_rank("unknown") == -1


def test_degrees_to_compass():
    assert degrees_to_compass(0) == "N"
    assert degrees_to_compass(45) == "NE"
    assert degrees_to_compass(350) == "N"
    assert degrees_to_compass(None) is None


def test_selects_good_windows_next_two_days():
    forecasts = {
        "spot-1": _forecast(
            {
                _ts(1, 10): "FAIR",
                _ts(1, 11): "FAIR_TO_GOOD",
                _ts(1, 22): "GOOD",  # hors heures diurnes
                _ts(2, 14): "GOOD",
                _ts(0, 10): "EPIC",  # aujourd'hui : ignoré
                _ts(3, 10): "GOOD",  # J+3 : ignoré
            }
        )
    }
    windows = select_good_windows(forecasts, SPOTS_BY_ID, now=NOW, days_ahead=[1, 2])
    assert len(windows) == 2
    day1 = next(w for w in windows if w["date"] == "2026-02-06")
    assert [entry["hour"] for entry in day1["intervals"]] == [10, 11]
    assert day1["intervals"][0]["surf_max_m"] == 1.0
    assert day1["intervals"][0]["wind_direction"] == "NE"


def test_default_window_covers_seven_days():
    forecasts = {
        "spot-1": _forecast(
            {_ts(offset, 10): "GOOD" for offset in range(1, 8)}
        )
    }
    windows = select_good_windows(forecasts, SPOTS_BY_ID, now=NOW)
    assert len(windows) == 7
    assert windows[0]["date"] == "2026-02-06"
    assert windows[-1]["date"] == "2026-02-12"


def test_min_rating_filters_poor():
    forecasts = {"spot-1": _forecast({_ts(1, 10): "POOR", _ts(1, 11): "FAIR"})}
    windows = select_good_windows(forecasts, SPOTS_BY_ID, now=NOW, min_rating="FAIR")
    assert len(windows) == 1
    assert [entry["hour"] for entry in windows[0]["intervals"]] == [11]


def test_no_windows_when_flat():
    forecasts = {"spot-1": _forecast({_ts(1, 10): "FLAT"})}
    assert select_good_windows(forecasts, SPOTS_BY_ID, now=NOW) == []


def test_build_email_contains_spot_and_link():
    forecasts = {"spot-1": _forecast({_ts(1, 10): "GOOD"})}
    windows = select_good_windows(forecasts, SPOTS_BY_ID, now=NOW)
    subject, text_body, html_body = build_email(windows)
    assert "La Couronne" in subject or "La Couronne" in text_body
    assert "https://www.surfline.com/surf-report/la-couronne/spot-1" in html_body
    assert "vent" in text_body
    assert "10h" not in text_body and "10:00" not in text_body
    assert "🌊🌊🌊" in text_body
    assert "(Good)" not in text_body and "GOOD" not in text_body
    assert "Légende" in text_body
