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

Le dépôt ne contient aucune donnée : elles se produisent en local. Tout ce qui suit la mise en
route de la composition est indispensable, faute de quoi le tableau de bord démarre mais ne peut rien afficher — le schéma
`instantane` qu'il interroge n'existe pas encore.

1. Copier `.env.example` vers `.env`, puis renseigner **toutes** ses clés. Aucune n'a de valeur par
   défaut : nom de projet Docker Compose, hôte, port, base, utilisateur et mot de passe PostgreSQL,
   identifiant d'utilisateur du système pour Airflow (`AIRFLOW_UID`, la valeur de `id -u`), ports
   publiés d'Airflow et de Streamlit, clé Fernet et clé d'API d'Airflow, identifiants de son
   administrateur. La clé Fernet est une clé de 32 octets encodée en base64 URL :
   `python -c "import base64, secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"`.
2. Installer l'environnement Python : `uv sync --frozen`.
3. Lancer `docker compose -f docker/docker-compose.yml --env-file .env up --wait`.
4. Exporter les variables de connexion dans le shell, en plus du fichier : `set -a; . ./.env; set +a`.
   Les modules d'ingestion lisent `.env` mais ceux de rapprochement attendent les variables dans
   l'environnement.
5. Produire le jeu de données : `uv run python -m generator generator/output`.
6. Appliquer les schémas : `uv run python ingestion/appliquer_ddl.py` puis
   `uv run python -m linkage.appliquer_ddl`. Ces commandes s'exécutent sur une base vide ; les
   rejouer sur une base déjà pourvue échoue.
7. Charger les données : `uv run python -m ingestion.chargeur generator/output/scenario_30`.
8. Déclarer le profil de connexion de dbt. Il ne figure pas dans le dépôt : écrire un
   `profiles.yml` sous `~/.dbt/` ou pointer `DBT_PROFILES_DIR` sur un répertoire qui en contient un,
   avec les variables `DBT_POSTGRES_HOST`, `DBT_POSTGRES_PORT`, `DBT_POSTGRES_USER`,
   `DBT_POSTGRES_PASSWORD` et `DBT_POSTGRES_DB` renseignées. Le fichier de workflow d'intégration
   continue en donne un exemple complet.
9. Construire l'entrepôt : `cd dbt && uv run dbt seed && uv run dbt run --threads 1`.
10. Rapprocher les identités puis constituer l'instantané que lit le tableau de bord :
    `uv run python -m linkage.prediction`, `uv run python -m linkage.evaluation`,
    `uv run python -m instantane.rafraichir`. Le rapprochement lit la vérité terrain du scénario
    produit par la génération ci-dessus (`VERITE_TERRAIN_PATIENTS`).
11. Ouvrir le tableau de bord sur le port déclaré par `STREAMLIT_PORT` dans `.env`.

Le graphe quotidien (`airflow/saa_daily.py`) enchaîne génération, chargement, construction, rapprochement et rafraîchissement pour une date d'extraction
donnée, une fois les schémas en place.

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
