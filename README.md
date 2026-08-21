# saa-hospital-analytics

Une chaîne de données complète — génération, chargement, entrepôt dimensionnel, rapprochement
d'identités, orchestration, tableau de bord — pour le service d'accueil et d'admission d'un hôpital.

[![ci](https://github.com/medanouarzaki/saa-hospital-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/medanouarzaki/saa-hospital-analytics/actions/workflows/ci.yml)
[![licence MIT](https://img.shields.io/badge/licence-MIT-blue)](LICENSE)

> **Aucune donnée de ce dépôt n'est réelle.**
> Ni patient, ni dossier, ni activité d'établissement. Le jeu de données est produit par un
> programme écrit pour ce projet ; les identifiants, pièces d'identité et numéros de téléphone sont
> tirés dans des espaces structurellement disjoints des séries réellement émises.

---

## Le problème

Un service d'accueil et d'admission enregistre des rendez-vous, des passages aux urgences, des
séjours et des factures dans un progiciel hospitalier.

Les données existent. Les grandeurs qui permettraient d'arbitrer — délai d'obtention d'un
rendez-vous, taux d'absence par activité, ancienneté des créances, part des dossiers en double —
n'en sortent pas.

Ce dépôt construit la chaîne qui les produirait, et la fait tourner de bout en bout. Pas sur les
données du service : elles ne sortent pas de l'établissement, et un stagiaire n'a accès qu'à un
seul des cinq profils applicatifs.

---

## Ce que contient le dépôt

- **Un générateur** de 912 jours d'activité, calibré sur des statistiques publiques marocaines.
- **Une chaîne d'ingestion** qui met en quarantaine plutôt qu'elle n'écarte.
- **Un entrepôt dimensionnel** de 11 modèles intermédiaires, 6 dimensions, 6 faits et 7 agrégats.
- **Un rapprochement probabiliste d'identités**, évalué contre une vérité terrain connue.
- **Un tableau de bord** de 40 indicateurs sur 9 pages, chacun défini dans un registre.
- **Un rapport et une présentation**, composés à chaque exécution et publiés en artefacts.

---

## La chaîne, d'un bout à l'autre

```text
  generator/          fichiers de paramètres  ->  912 jours d'activité
       |
       v
  ingestion/          zone d'atterrissage  ->  couche source  +  quarantaine
       |                                    (11 tables, tout en texte)
       v
  dbt/                couche intermédiaire  ->  schéma en étoile
       |              typage, normalisation     6 dimensions, 6 faits, 7 agrégats
       |
       +--> linkage/  rapprochement d'identités  ->  grappes + évaluation
       |
       v
  instantane/         26 objets figés, échangés en une transaction
       |
       v
  dashboard/          9 pages, 40 indicateurs        livraison/  ->  exports/
```

---

## Mise en route

Il faut **Docker**, **Docker Compose**, **`uv`** et **Python 3.12**.

Le dépôt ne contient aucune donnée : elles se produisent en local. Toutes les étapes sont
nécessaires — sans elles, le tableau de bord démarre sans rien pouvoir afficher.

### 1. Renseigner l'environnement

Copier `.env.example` vers `.env` et renseigner **toutes** ses clés : aucune n'a de valeur par
défaut. Pour la clé Fernet d'Airflow :

```bash
python -c "import base64, secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
```

### 2. Installer l'environnement Python

```bash
uv sync --frozen
```

### 3. Démarrer les services

```bash
docker compose -f docker/docker-compose.yml --env-file .env up --wait
```

### 4. Exporter les variables dans le shell

Les modules d'ingestion lisent `.env` ; ceux de rapprochement attendent les variables dans
l'environnement.

```bash
set -a; . ./.env; set +a
```

### 5. Produire le jeu de données

```bash
uv run python -m generator generator/output
```

### 6. Appliquer les schémas

> Ces deux commandes sont **rejouables**, mais elles **détruisent les données déjà chargées** des
> tables qu'elles recréent. Les rejouer impose de recharger.

```bash
uv run python ingestion/appliquer_ddl.py
uv run python -m linkage.appliquer_ddl
```

### 7. Charger les données

```bash
uv run python -m ingestion.chargeur generator/output/scenario_30
```

### 8. Déclarer le profil de connexion dbt

Il ne figure pas au dépôt. Écrire un `profiles.yml` sous `~/.dbt/`, ou pointer `DBT_PROFILES_DIR`
sur un répertoire qui en contient un, avec `DBT_POSTGRES_HOST`, `DBT_POSTGRES_PORT`,
`DBT_POSTGRES_USER`, `DBT_POSTGRES_PASSWORD` et `DBT_POSTGRES_DB`. Le fichier d'intégration
continue en donne un exemple complet.

### 9. Construire l'entrepôt

> **Revenir à la racine après** : les commandes suivantes échouent depuis `dbt/` sur
> `No module named 'linkage'`.

```bash
cd dbt && uv run dbt seed && uv run dbt run --threads 1 && uv run dbt test && cd ..
```

### 10. Rapprocher les identités et figer l'instantané

```bash
uv run python -m linkage.prediction
uv run python -m linkage.evaluation
uv run python -m instantane.rafraichir
```

### 11. Ouvrir le tableau de bord

Il est servi par la composition Docker, sur le port déclaré par `STREAMLIT_PORT` dans `.env`.

### 12. Facultatif — produire le livrable

Seul moyen de peupler `exports/`, qui reste vide sans cela.

```bash
uv run python -m livraison.exporter
```

Le graphe quotidien `airflow/saa_daily.py` enchaîne génération, chargement, construction,
rapprochement et rafraîchissement pour une date d'extraction donnée, une fois les schémas en place.

---

## Carte du dépôt

| Répertoire | Contenu |
| --- | --- |
| `generator/` | Génération du jeu de données et de sa configuration |
| `ingestion/` | Chargement vers l'entrepôt, contrôles d'entrée et quarantaine |
| `dbt/` | Modélisation dimensionnelle |
| `linkage/` | Rapprochement probabiliste d'identités et son évaluation |
| `instantane/` | Schéma figé que lit le tableau de bord |
| `airflow/` | Orchestration des traitements |
| `dashboard/` | Tableau de bord de restitution et registre de ses indicateurs |
| `livraison/` | Production du classeur et des fichiers de restitution |
| `exports/` | Fichiers produits par la restitution ; vide tant qu'elle n'a pas tourné |
| `echantillon/` | Extrait de chaque table, chaque ligne portant sa mention de simulation |
| `extraction/` | Engendrement de cet extrait |
| `docker/` | Socle de conteneurisation |
| `tests/` | 75 fichiers de contrôle, 545 propriétés |
| `report/` | Sources du rapport, bibliographie, dictionnaire de données |
| `slides/` | Support de présentation |
| `docs/` | Registres de champs et de sources, relevé d'observation, et 79 enregistrements de décision |

---

## L'échantillon versé au dépôt

`echantillon/` contient 23 fichiers à séparateur virgule, un par table, prélevés systématiquement —
une ligne sur *N*, dans l'ordre d'une clé stable — et reproductibles.

Ils montrent la **forme** des données. Ils ne mesurent rien : un extrait d'une ligne sur *N* ne
porte aucun total, aucune moyenne et aucune proportion exploitables.

---

## Contrôles

L'intégration continue exécute 6 travaux : style et garde-fou de collecte, la matrice des
contrôles, la provenance des colonnes, l'entrepôt dbt, la chaîne complète jusqu'au tableau de bord,
et la composition du rapport et de la présentation.

Les contrôles n'affirment aucune volumétrie écrite d'avance : chaque attendu est une égalité entre
deux mesures calculées séparément.

**La compilation qui fait foi est celle de l'intégration continue.** Aucun PDF n'est versé au
dépôt ; une distribution locale ne sert qu'à relire.

---

## Ce que ce dépôt ne prouve pas

**Aucun chiffre ne mesure l'activité d'un établissement réel.** Une relation qu'on lit à la sortie
peut avoir été mise dans les paramètres du générateur ; le registre des relations injectées liste
celles qui le sont.

**Un seul profil applicatif sur cinq a été observé au poste.** Sur 175 champs du modèle, 81 sont
observés, 72 documentés par une source écrite, 22 posés faute de source.

**Ce que la chaîne démontre est qu'elle sait calculer ces grandeurs**, non ce qu'elles vaudraient
ailleurs.

---

## Décisions de conception

Elles ne sont pas dans ce fichier. Chacune a son enregistrement sous `docs/decisions/`, avec ce qui
a été mesuré avant de trancher, ce qui a été écarté, et ce qui aurait invalidé la décision.
