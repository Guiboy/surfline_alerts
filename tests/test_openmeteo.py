"""Tests de l'assemblage des prévisions Open-Meteo (sans réseau)."""

from worker.openmeteo import _as_location_list, build_spot_forecast

MARINE = {
    "utc_offset_seconds": 0,
    "hourly": {
        "time": ["2026-02-05T10:00", "2026-02-05T11:00", "2026-02-05T12:00"],
        "wave_height": [0.2, 0.9, 1.4],
        "wave_period": [6.0, 7.0, 9.0],
        "wave_direction": [180.0, 185.0, 190.0],
    },
}

WEATHER = {
    "utc_offset_seconds": 0,
    "hourly": {
        "time": ["2026-02-05T10:00", "2026-02-05T11:00", "2026-02-05T12:00"],
        "wind_speed_10m": [12.0, 14.0, 9.0],
        "wind_direction_10m": [20.0, 25.0, 30.0],
    },
}


def test_build_spot_forecast_contract():
    forecast = build_spot_forecast(MARINE, WEATHER, facing_deg=200)
    assert set(forecast) == {"conditions", "wave", "wind"}
    assert len(forecast["conditions"]) == 3
    assert forecast["conditions"][0]["rating"] == "FLAT"
    assert forecast["conditions"][2]["rating"] in ("FAIR", "FAIR_TO_GOOD", "GOOD")


def test_timestamps_are_epoch_seconds():
    forecast = build_spot_forecast(MARINE, WEATHER, facing_deg=200)
    ts = forecast["conditions"][0]["timestamp"]
    assert ts == 1770285600


def test_wave_heights_scaled_to_surf_range():
    forecast = build_spot_forecast(MARINE, WEATHER, facing_deg=200)
    wave = forecast["wave"][2]
    assert wave["surf_min_m"] == round(1.4 * 0.7, 2)
    assert wave["surf_max_m"] == round(1.4 * 1.2, 2)


def test_location_list_accepts_batched_and_single_payloads():
    assert _as_location_list([MARINE, MARINE]) == [MARINE, MARINE]
    assert _as_location_list(MARINE) == [MARINE]


def test_wind_entries_match_weather():
    forecast = build_spot_forecast(MARINE, WEATHER, facing_deg=200)
    wind = forecast["wind"][1]
    assert wind["speed_kts"] == 14.0
    assert wind["direction"] == 25.0
