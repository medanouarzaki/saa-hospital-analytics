# saa-hospital-analytics

## Objet

Chaîne de données et tableau de bord d'aide à la décision pour un service d'accueil et d'admission hospitalier : génération, chargement, entrepôt dimensionnel, rapprochement probabiliste d'identités, orchestration, restitution.

## Avertissement sur les données

Le jeu de données est entièrement synthétique. Aucune donnée réelle de patient n'entre dans ce dépôt. Les identifiants, numéros de pièce d'identité et numéros de téléphone sont générés dans des espaces disjoints des séries réellement émises.

## Prérequis

- Docker
- Docker Compose
- `uv`
- Python 3.12

## Démarrage

1. Copier `.env.example` vers `.env`, puis renseigner les valeurs locales (ports, mot de passe PostgreSQL, clés Airflow).
2. Lancer `docker compose -f docker/docker-compose.yml --env-file .env up --wait`.
3. Ouvrir le tableau de bord sur le port déclaré par `STREAMLIT_PORT` dans `.env`.

## Structure du dépôt

| Répertoire | Rôle |
| --- | --- |
| `generator/` | Génération du jeu de données synthétique et de sa configuration |
| `ingestion/` | Chargement des données générées vers l'entrepôt |
| `dbt/` | Modélisation dimensionnelle de l'entrepôt |
| `linkage/` | Rapprochement probabiliste d'identités |
| `airflow/` | Orchestration des traitements |
| `dashboard/` | Tableau de bord de restitution |
| `exports/` | Exports produits par la chaîne |
| `docker/` | Socle de conteneurisation |
| `tests/` | Tests automatisés |
| `report/` | Rapport et figures associées |
| `slides/` | Support de présentation |
| `docs/` | Documentation d'observation, de champs, de sources et de décisions |
