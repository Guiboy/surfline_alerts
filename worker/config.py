"""Configuration statique de l'agent d'alertes surf."""

from dataclasses import dataclass

DEFAULT_RECIPIENT = "guillaume.ramirez@yahoo.fr"
TIMEZONE = "Europe/Paris"

OPENMETEO_MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
OPENMETEO_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
FORECAST_DAYS = 3

# Modèles de vagues validés en Méditerranée (ecmwf_ifs025 exclu : null près des côtes)
WAVE_MODELS = ("best_match", "meteofrance_wave", "ecmwf_wam025")


@dataclass(frozen=True)
class Spot:
    name: str
    spot_id: str
    slug: str
    lat: float
    lon: float
    facing_deg: float

    @property
    def url(self) -> str:
        return f"https://www.surfline.com/surf-report/{self.slug}/{self.spot_id}"


SPOTS: list[Spot] = [
    Spot("La Couronne (Carro)", "584204214e65fad6a7709c1a", "la-couronne", 43.335, 5.054, 200),
    Spot("Le Rouet (Carry-le-Rouet)", "584204214e65fad6a7709c1f", "le-rouet", 43.338, 5.163, 185),
    Spot("La Corniche (Marseille)", "584204214e65fad6a7709c1d", "la-corniche", 43.274, 5.362, 185),
    Spot("Le Prado (Marseille)", "584204214e65fad6a7709c20", "le-prado", 43.267, 5.395, 200),
    Spot("Cassis", "584204214e65fad6a7709c2d", "cassis", 43.209, 5.630, 160),
    Spot("La Ciotat", "584204214e65fad6a7709c21", "la-ciotat", 43.177, 5.608, 165),
    Spot("Cap Saint-Louis (La Ciotat)", "584204214e65fad6a7709c24", "cap-saint-louis", 43.163, 5.641, 140),
    Spot("Fabregas (Sanary)", "584204214e65fad6a7709c25", "fabregas", 43.118, 5.790, 215),
    Spot("Six Fours", "584204214e65fad6a7709c23", "six-floors", 43.093, 5.826, 215),
    Spot("La Coudoulière (Six-Fours)", "6418dea7a34c332c6917cae0", "la-coudouli-re", 43.082, 5.835, 235),
    Spot("Bandol", "584204214e65fad6a7709c26", "Bandol", 43.098, 5.758, 170),
]

RATING_ORDER: dict[str, int] = {
    "FLAT": 0,
    "VERY_POOR": 1,
    "POOR": 2,
    "POOR_TO_FAIR": 3,
    "FAIR": 4,
    "FAIR_TO_GOOD": 5,
    "GOOD": 6,
    "VERY_GOOD": 7,
    "GOOD_TO_EPIC": 8,
    "EPIC": 9,
}

RATING_LABELS_FR: dict[str, str] = {
    "FLAT": "Plat",
    "VERY_POOR": "Très mauvais",
    "POOR": "Mauvais",
    "POOR_TO_FAIR": "Mauvais à moyen",
    "FAIR": "Moyen",
    "FAIR_TO_GOOD": "Moyen à bon",
    "GOOD": "Bon",
    "VERY_GOOD": "Très bon",
    "GOOD_TO_EPIC": "Bon à excellent",
    "EPIC": "Épique",
}
