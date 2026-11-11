"""Algorithme de notation des conditions de surf (Méditerranée)."""

from __future__ import annotations

from worker.config import RATING_ORDER

RATING_SCALE: list[str] = [
    "FLAT",
    "VERY_POOR",
    "POOR",
    "POOR_TO_FAIR",
    "FAIR",
    "FAIR_TO_GOOD",
    "GOOD",
    "VERY_GOOD",
    "GOOD_TO_EPIC",
    "EPIC",
]

FLAT_THRESHOLD_M = 0.35

_WAVE_SCORE_POINTS: list[tuple[float, float]] = [
    (0.45, 0.5),
    (0.65, 1.0),
    (0.85, 2.0),
    (1.10, 3.0),
    (1.40, 4.0),
    (1.75, 5.0),
    (2.15, 6.0),
    (2.55, 7.0),
    (2.90, 8.0),
    (3.20, 7.0),
    (3.60, 6.0),
]


def angle_diff(a: float, b: float) -> float:
    """Écart angulaire minimal entre deux directions (0..180)."""
    diff = abs((a - b) % 360)
    return 360 - diff if diff > 180 else diff


def _interpolate(points: list[tuple[float, float]], x: float) -> float:
    if x <= points[0][0]:
        return points[0][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return points[-1][1]


def wave_score(wave_height_m: float) -> float:
    """Score de houle 0..8 (au-delà de ~2,5 m la Méditerranée ferme)."""
    return _interpolate(_WAVE_SCORE_POINTS, wave_height_m)


def period_factor(period_s: float | None) -> float:
    """Pénalise la houle de vent courte, bonus au-delà de 9,5 s."""
    if period_s is None:
        return 1.0
    if period_s < 5.5:
        return 0.60
    if period_s < 7.5:
        return 0.75
    if period_s < 9.5:
        return 0.90
    return 1.0


def wind_factor(
    wind_kts: float | None,
    wind_from_deg: float | None,
    facing_deg: float,
) -> float:
    """Facteur vent selon l'angle par rapport à l'offshore du spot.

    Offshore = vent venant de la terre (opposé de la direction que le spot
    fait face). Un vent fort dégrade la surface sauf s'il est offshore.
    """
    if wind_kts is None or wind_from_deg is None:
        return 1.0
    offshore_deg = (facing_deg + 180) % 360
    off = angle_diff(wind_from_deg, offshore_deg)
    if off <= 45:
        base = 1.00
    elif off <= 80:
        base = 0.90
    elif off <= 115:
        base = 0.75
    elif off <= 150:
        base = 0.60
    else:
        base = 0.50
    if wind_kts > 30:
        return base * (0.75 if off <= 45 else 0.65)
    if wind_kts > 22:
        return base * (0.85 if off <= 45 else 0.75)
    return base


def compute_rating(
    wave_height_m: float | None,
    period_s: float | None,
    wind_kts: float | None,
    wind_from_deg: float | None,
    facing_deg: float,
) -> str:
    """Note de 0 (FLAT) à 9 (EPIC) pour une heure donnée."""
    if wave_height_m is None or wave_height_m < FLAT_THRESHOLD_M:
        return "FLAT"
    score = (
        wave_score(wave_height_m)
        * period_factor(period_s)
        * wind_factor(wind_kts, wind_from_deg, facing_deg)
    )
    index = min(max(int(round(score)), 1), 9)
    return RATING_SCALE[index]


def rating_rank(rating: str) -> int:
    return RATING_ORDER.get(rating.upper(), -1)
