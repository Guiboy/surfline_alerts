"""Tests de l'algorithme de notation des conditions."""

from worker.rating import compute_rating, wave_score, wind_factor, angle_diff


def test_flat_below_threshold():
    assert compute_rating(0.2, 6.0, 10.0, 0.0, 200) == "FLAT"
    assert compute_rating(None, None, None, None, 200) == "FLAT"


def test_small_onshore_is_poor():
    rating = compute_rating(0.6, 5.0, 18.0, 200, 200)
    assert rating in ("VERY_POOR", "POOR")


def test_clean_offshore_waist_high_is_conservative():
    rating = compute_rating(1.0, 8.0, 10.0, 20, 200)
    assert rating in ("POOR_TO_FAIR", "FAIR", "FAIR_TO_GOOD")


def test_strong_onshore_ruins_big_swell():
    rating = compute_rating(1.5, 7.0, 32.0, 200, 200)
    assert rating in ("POOR", "POOR_TO_FAIR")


def test_big_clean_swell_rates_high():
    rating = compute_rating(2.0, 10.0, 8.0, 20, 200)
    assert rating in ("VERY_GOOD", "GOOD_TO_EPIC")


def test_offshore_wind_beats_onshore_at_same_swell():
    offshore = compute_rating(0.9, 7.0, 12.0, 20, 200)
    onshore = compute_rating(0.9, 7.0, 12.0, 200, 200)
    from worker.config import RATING_ORDER

    assert RATING_ORDER[offshore] > RATING_ORDER[onshore]


def test_mistral_is_offshore_for_prado():
    from worker.config import RATING_ORDER

    mistral = compute_rating(0.8, 7.0, 25.0, 330, 200)
    same_size_onshore = compute_rating(0.8, 7.0, 25.0, 200, 200)
    assert RATING_ORDER[mistral] > RATING_ORDER[same_size_onshore]


def test_period_improves_rating():
    from worker.config import RATING_ORDER

    short = compute_rating(1.0, 4.5, 8.0, 20, 200)
    long = compute_rating(1.0, 10.0, 8.0, 20, 200)
    assert RATING_ORDER[long] >= RATING_ORDER[short]


def test_wave_score_shape():
    assert wave_score(0.3) < wave_score(1.0) < wave_score(2.0)
    assert wave_score(3.5) < wave_score(2.4)


def test_wind_factor_bounds():
    assert wind_factor(10.0, 20, 200) > wind_factor(10.0, 200, 200)
    assert wind_factor(None, None, 200) == 1.0


def test_angle_diff():
    assert angle_diff(10, 350) == 20
    assert angle_diff(0, 180) == 180
    assert angle_diff(200, 200) == 0
