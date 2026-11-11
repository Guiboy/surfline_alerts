"""Configuration statique de l'agent d'alertes surf."""

from dataclasses import dataclass

DEFAULT_RECIPIENT = "guillaume.ramirez@yahoo.fr"
TIMEZONE = "Europe/Paris"

SURFLINE_BASE_URL = "https://services.surfline.com"
SURFLINE_FORECAST_DAYS = 3


@dataclass(frozen=True)
class Spot:
    name: str
    spot_id: str
    slug: str

    @property
    def url(self) -> str:
        return f"https://www.surfline.com/surf-report/{self.slug}/{self.spot_id}"


SPOTS: list[Spot] = [
    Spot("La Couronne (Carro)", "584204214e65fad6a7709c1a", "la-couronne"),
    Spot("Le Rouet (Carry-le-Rouet)", "584204214e65fad6a7709c1f", "le-rouet"),
    Spot("La Corniche (Marseille)", "584204214e65fad6a7709c1d", "la-corniche"),
    Spot("Le Prado (Marseille)", "584204214e65fad6a7709c20", "le-prado"),
    Spot("Cassis", "584204214e65fad6a7709c2d", "cassis"),
    Spot("La Ciotat", "584204214e65fad6a7709c21", "la-ciotat"),
    Spot("Cap Saint-Louis (La Ciotat)", "584204214e65fad6a7709c24", "cap-saint-louis"),
    Spot("Fabregas (Sanary)", "584204214e65fad6a7709c25", "fabregas"),
    Spot("Six Fours", "584204214e65fad6a7709c23", "six-floors"),
    Spot("La Coudoulière (Six-Fours)", "6418dea7a34c332c6917cae0", "la-coudouli-re"),
    Spot("Bandol", "584204214e65fad6a7709c26", "Bandol"),
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

FT_TO_M = 0.3048
