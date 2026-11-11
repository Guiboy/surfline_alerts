# Alertes Surf Martigues → Hyères

Agent Mistral Workflow qui surveille les prévisions [Surfline](https://www.surfline.com)
entre Martigues et Hyères et envoie un email lorsque de bonnes conditions sont
prévues à J+1 ou J+2.

## Fonctionnement

- Workflow `surfline-alerts` : récupère les prévisions (conditions, houle, vent)
  de l'API Surfline pour les spots configurés, filtre les créneaux diurnes
  (6h–21h, Europe/Paris) des jours J+1 et J+2 dont le rating Surfline est
  supérieur ou égal au minimum configuré (`FAIR` par défaut), puis envoie un
  email récapitulatif via le connecteur Gmail.
- Aucun email n'est envoyé si aucune condition ne dépasse le seuil.
- Exécution planifiée deux fois par jour (8h et 18h, Europe/Paris).

## Spots surveillés

La Couronne (Carro), Le Rouet, La Corniche, Le Prado, Cassis, La Ciotat,
Cap Saint-Louis, Fabregas, Six Fours, La Coudoulière, Bandol.

Pour ajouter un spot, ajoutez une entrée dans `worker/config.py`
(`Spot(nom, id_surfline, slug)`).

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
