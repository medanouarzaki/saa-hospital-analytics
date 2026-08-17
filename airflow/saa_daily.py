"""Graphe quotidien de la chaîne de données du projet.

Une exécution correspond à une DATE D'EXTRACTION, pas à une date d'événement métier : le
système source d'où proviennent les fichiers expose, à une date d'extraction donnée, un
instantané de son contenu (rendez-vous passés et futurs compris), pas seulement l'activité du
jour même. « Un jour », pour ce graphe, est donc le jour où un fichier a été extrait, et c'est
cette date qui est passée aux commandes de chargement.

La génération du scénario et l'application des schémas (source, quarantaine, rapprochement)
sont des préalables à ce graphe, pas des tâches qu'il exécute : elles ne sont pas rejouables
sans réinitialisation et n'ont donc pas leur place dans une chaîne planifiée à répétition. Ce
graphe suppose que les schémas existent déjà et que les fichiers de la date d'extraction
traitée ont déjà été déposés ; sa première tâche vérifie cette seconde condition et échoue si
elle n'est pas remplie.

Les contrôles d'entrée (validité des lignes, unicité) s'exécutent À L'INTÉRIEUR du chargement,
pas dans une étape séparée : il n'existe aucune invocation de ces contrôles indépendante du
chargeur. La tâche qui suit le chargement n'exécute donc pas les contrôles une seconde fois :
elle observe et rapporte le résultat déjà produit (le contenu de la quarantaine pour la date
traitée, ventilé par table), ET compare le taux de rejet cumulé de la journée, sur les onze
tables, au seuil du chargeur (`ingestion/controles.yml`) — elle bloque le graphe si ce taux est
dépassé, avant toute construction de la couche dbt ou du rapprochement. Ses entrées
(`source`/`quarantaine` de la seule date traitée) ne dépendent d'aucune couche aval, ce qui rend
cette position possible ; docs/decisions/0040-controle-qualite-taux-rejet-cumule.md consigne
pourquoi elle est nécessaire à cette position plutôt qu'après les agrégats.

Toutes les tâches sont des commandes shell : ce fichier n'importe rien d'autre que
l'orchestrateur et la bibliothèque standard, pour rester analysable sans que les dépendances du
projet soient installées là où il est lu. Les commandes qu'il déclenche s'exécutent dans
l'environnement hérité du processus qui a démarré l'orchestrateur — paramètres de connexion
compris — mais dans un répertoire de travail que ce fichier fixe lui-même pour chaque tâche
(`cwd`), dérivé de son propre emplacement (`SAA_REPO_ROOT`, si définie, prévaut toujours) :
sans un répertoire de travail explicite, l'opérateur shell exécute silencieusement dans un
répertoire temporaire propre à l'appel, jamais le dépôt (docs/decisions/
0012-mode-execution-orchestrateur.md, amendé). Aucun identifiant, aucun mot de passe et aucune
variable de connexion ne sont écrits ici.

Les deux tâches finales constituent l'instantané que lit le tableau de bord, puis en tirent les
livrables. Le rafraîchissement précède l'export : l'export lit l'instantané, et le lire avant qu'il
ne soit constitué livrerait l'état de la veille. Toutes deux restent en aval du contrôle de qualité,
qui bloque la chaîne sur dégradation — un livrable produit malgré un contrôle bloqué serait pire
qu'un livrable absent.
"""

import os
from pathlib import Path

import pendulum
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

# Dérivée de l'emplacement de ce fichier, à l'analyse du graphe : plus une précondition, son
# absence ne change plus le comportement. `SAA_REPO_ROOT`, si définie, prévaut toujours.
RACINE_DEPOT = os.environ.get("SAA_REPO_ROOT", str(Path(__file__).resolve().parent.parent))
RACINE_DBT = str(Path(RACINE_DEPOT) / "dbt")
RACINE_SCENARIO = '"${SAA_SCENARIO_ROOT:-generator/output/scenario_30}"'
DATE_EXTRACTION = "{{ logical_date | ds }}"

TABLES_SOURCE = (
    "creances",
    "encaissements",
    "factures",
    "lignes_facture",
    "mouvements",
    "passages",
    "passages_urgences",
    "patients",
    "prises_en_charge",
    "relances",
    "rendez_vous",
)

SELECTEUR_INTERMEDIAIRE = "path:models/intermediate"
SELECTEUR_DIMENSIONS = "path:models/marts/dim_*.sql"
SELECTEUR_FAITS = "path:models/marts/fct_*.sql"
SELECTEUR_AGREGATS = "path:models/marts/agg_*.sql"

with DAG(
    dag_id="saa_daily",
    description="Chargement, transformation et rapprochement d'une date d'extraction",
    schedule="@daily",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=True,
    max_active_runs=1,
    tags=["saa"],
) as dag:
    # Le chargeur tolère qu'une table n'ait aucun fichier pour une date donnée
    # (ingestion/chargeur.py : « une date sans fichier pour une table est ignorée sans
    # erreur ») : certaines tables (ex. relances) n'ont pas de partition pour la
    # majorité des dates. La disponibilité de l'extraction ne peut donc pas exiger la
    # présence des onze tables, seulement qu'AU MOINS UNE en porte une pour cette date.
    verifier_disponibilite_extraction = BashOperator(
        task_id="verifier_disponibilite_extraction",
        cwd=RACINE_DEPOT,
        bash_command=(
            f"set -euo pipefail\n"
            f"racine={RACINE_SCENARIO}\n"
            f'date_extraction="{DATE_EXTRACTION}"\n'
            "trouvees=0\n"
            + "\n".join(
                f'if [ -d "$racine/source.{table}/$date_extraction" ]; then\n'
                f"    trouvees=$((trouvees + 1))\n"
                f"fi"
                for table in TABLES_SOURCE
            )
            + "\n"
            'if [ "$trouvees" -eq 0 ]; then\n'
            '    echo "aucune partition pour $date_extraction sur les onze tables" >&2\n'
            "    exit 1\n"
            "fi\n"
            'echo "extraction disponible pour $date_extraction : $trouvees table(s) sur 11"\n'
        ),
    )

    charger_journee = BashOperator(
        task_id="charger_journee",
        cwd=RACINE_DEPOT,
        bash_command=(
            f"set -euo pipefail\n"
            f"racine={RACINE_SCENARIO}\n"
            f'uv run python -m ingestion.chargeur "$racine" '
            f'--date-debut "{DATE_EXTRACTION}" --date-fin "{DATE_EXTRACTION}"\n'
        ),
    )

    # Prend la place de l'ancienne tâche d'observation de la quarantaine (affichage seul,
    # ne bloquait jamais) : ce contrôle en reprend le rôle de compte-rendu (ventilation par
    # table) et y ajoute un blocage réel — comparaison du taux de rejet cumulé de la journée
    # au seuil du chargeur. Placée ici, avant la couche dbt et le rapprochement, plutôt
    # qu'après les agrégats (docs/decisions/0040-controle-qualite-taux-rejet-cumule.md) :
    # ses entrées ne dépendent d'aucune couche aval, et un défaut d'extraction doit arrêter
    # la chaîne avant que l'entrepôt ne soit reconstruit sur des données déjà défectueuses.
    controle_qualite = BashOperator(
        task_id="controle_qualite",
        cwd=RACINE_DEPOT,
        bash_command=f'uv run python -m ingestion.controle_qualite "{DATE_EXTRACTION}"\n',
    )

    # --threads 1 sur `dbt run` : à la concurrence par défaut du profil (4 fils), le
    # remplacement d'une vue (création temporaire, renommage, suppression de l'ancienne)
    # entre en interblocage sur le catalogue système (docs/decisions/
    # 0027-materialisation-dbt-un-seul-fil.md) — mesuré : reproduit deux fois de suite sur
    # ce graphe avant que ce paramètre ne soit ajouté. `dbt test`, lecture seule, garde son
    # parallélisme.
    dbt_intermediaire = BashOperator(
        task_id="dbt_intermediaire",
        cwd=RACINE_DBT,
        bash_command=f'uv run dbt run --threads 1 --select "{SELECTEUR_INTERMEDIAIRE}"\n',
    )

    dbt_dimensions = BashOperator(
        task_id="dbt_dimensions",
        cwd=RACINE_DBT,
        bash_command=f'uv run dbt run --threads 1 --select "{SELECTEUR_DIMENSIONS}"\n',
    )

    dbt_faits = BashOperator(
        task_id="dbt_faits",
        cwd=RACINE_DBT,
        bash_command=f'uv run dbt run --threads 1 --select "{SELECTEUR_FAITS}"\n',
    )

    # dbt sélectionne aussi, par défaut, les tests d'un modèle NON sélectionné dès lors
    # qu'ils référencent un des modèles sélectionnés (mesuré : les tests "relationships"
    # déclarés sur les fichiers .yml des agrégats, qui référencent les dimensions,
    # étaient inclus alors même que les agrégats ne sont pas encore construits à ce
    # stade du graphe). Exclusion explicite des déclarations de test des agrégats.
    dbt_tests = BashOperator(
        task_id="dbt_tests",
        cwd=RACINE_DBT,
        bash_command=(
            f'uv run dbt test --select "{SELECTEUR_INTERMEDIAIRE}" '
            f'"{SELECTEUR_DIMENSIONS}" "{SELECTEUR_FAITS}" '
            f'--exclude "path:models/marts/agg_*.yml"\n'
        ),
    )

    rapprochement_prediction = BashOperator(
        task_id="rapprochement_prediction",
        cwd=RACINE_DEPOT,
        bash_command="uv run python -m linkage.prediction\n",
    )

    rapprochement_regroupement_evaluation = BashOperator(
        task_id="rapprochement_regroupement_evaluation",
        cwd=RACINE_DEPOT,
        bash_command="uv run python -m linkage.evaluation\n",
    )

    dbt_agregats = BashOperator(
        task_id="dbt_agregats",
        cwd=RACINE_DBT,
        bash_command=f'uv run dbt run --threads 1 --select "{SELECTEUR_AGREGATS}"\n',
    )

    # Le rafraichissement precede l'export : l'export lit l'instantane, et le lire avant qu'il
    # ne soit constitue livrerait l'etat de la veille. Les deux tachent restent terminales et en
    # aval du controle de qualite, qui bloque la chaine sur degradation ; seul leur ordre relatif
    # a change.
    #
    # Un verrou consultatif interdit deux rafraichissements simultanes : la seconde invocation
    # renonce avec un code de sortie qui lui est propre. Le recouvrement d'executions est en outre
    # interdit au niveau du graphe par max_active_runs.
    rafraichir_instantane = BashOperator(
        task_id="rafraichir_instantane",
        cwd=RACINE_DEPOT,
        bash_command="uv run python -m instantane.rafraichir\n",
    )

    exporter = BashOperator(
        task_id="exporter",
        cwd=RACINE_DEPOT,
        bash_command="uv run python -m livraison.exporter\n",
    )

    (
        verifier_disponibilite_extraction
        >> charger_journee
        >> controle_qualite
        >> dbt_intermediaire
        >> dbt_dimensions
        >> dbt_faits
        >> dbt_tests
        >> rapprochement_prediction
        >> rapprochement_regroupement_evaluation
        >> dbt_agregats
        >> rafraichir_instantane
        >> exporter
    )
