# Alertes Surf Martigues → Hyères

Agent Mistral Workflow qui surveille les prévisions de surf entre Martigues et
Hyères et envoie un email lorsque de bonnes conditions sont prévues à J+1 ou J+2.

## Source de données : Open-Meteo Marine

Les prévisions viennent de l'API gratuite [Open-Meteo Marine](https://open-meteo.com/en/docs/marine-api)
(houle : hauteur, période, direction) et de l'API [Open-Meteo Forecast](https://open-meteo.com/en/docs)
(vent à 10 m en nœuds), sans clé API. Surfline reste utilisé uniquement pour les
liens vers les pages des spots.

## Notation des conditions

Le rating horaire est calculé localement dans `worker/rating.py` sur l'échelle
Surfline (FLAT → EPIC) :

```
score = wave_score(hauteur_houle) × period_factor(période) × wind_factor(vent, orientation_du_spot)
```

- **Hauteur de houle** : courbe par points (0,30 m = seuil FLAT ; 1,05 m = FAIR ;
  1,75 m = GOOD ; 2,40 m = VERY_GOOD ; décroissance au-delà de 2,70 m = close-out).
  Conversion affichée : `surf_min = Hs × 0,7`, `surf_max = Hs × 1,2`.
- **Période** : < 5,5 s → ×0,75 (windswell méditerranéen court), ≥ 9,5 s → ×1,10.
- **Vent** : offshore = direction venant de `facing_deg + 180` ; offshore léger
  ×1,12, onshore ×0,62 à ×0,85 ; pénalités supplémentaires au-delà de 22 kts et 30 kts.

### Validation croisée

L'algorithme a été validé indépendamment de Surfline :

1. **Tests unitaires physiques** (`tests/test_rating.py`) : onshore = POOR,
   offshore propre ≥ FAIR, gros onshore ruiné, gros propre = VERY_GOOD+, Mistral
   (NW) offshore pour Le Prado, etc.
2. **Accord inter-modèles Open-Meteo** sur 11 spots × 72 h (792 évaluations) :
   `best_match` vs `meteofrance_wave` vs `ecmwf_wam025` — 49 % de ratings
   identiques, 92 % à ±1 cran, écart de houle médian 22 cm. `best_match` et
   `meteofrance_wave` sont identiques en Méditerranée ; `ecmwf_wam025` est
   systématiquement un peu plus optimiste (+0,5 cran en moyenne), sans cas
   pessimiste. `ecmwf_ifs025` est exclu (grille trop grossière : `null` près
   des côtes).

## Spots surveillés

La Couronne (Carro), Le Rouet, La Corniche, Le Prado, Cassis, La Ciotat,
Cap Saint-Louis, Fabregas, Six Fours, La Coudoulière, Bandol.

Pour ajouter un spot, ajoutez une entrée dans `worker/config.py` avec
`Spot(nom, id_surfline, slug, lat, lon, facing_deg)` — `facing_deg` est
l'orientation de la plage (degrés, direction vers laquelle regarde le spot) et
servira au calcul du vent offshore/onshore.

## Lancer les tests

```bash
uv sync
uv run pytest
```

## Exécution manuelle (dry-run, sans email)

```bash
curl -X POST https://api.mistral.ai/v1/workflows/surfline-alerts/execute \
  -H "Authorization: Bearer $MISTRAL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"dry_run": true}}'
```

## Déploiement

Déploiement géré Mistral Cloud (`deploy/docker/Dockerfile.worker`), planification
8h/18h Europe/Paris créée via l'API Workflows.
