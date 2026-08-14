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
chargeur. La tâche de vérification qui suit le chargement n'exécute donc pas les contrôles une
seconde fois, elle en observe et rapporte le résultat déjà produit (le contenu de la
quarantaine pour la date traitée).

Toutes les tâches sont des commandes shell : ce fichier n'importe rien d'autre que
l'orchestrateur et la bibliothèque standard, pour rester analysable sans que les dépendances du
projet soient installées là où il est lu. Les commandes qu'il déclenche s'exécutent dans
l'environnement hérité du processus qui a démarré l'orchestrateur — paramètres de connexion et
racine du dépôt compris. Aucun identifiant, aucun mot de passe et aucune variable de connexion
ne sont écrits ici.

La tâche de contrôle de qualité existe dans ce graphe mais ne bloque encore rien : son contenu
sera écrit plus tard. Les deux tâches finales (export et rafraîchissement de l'instantané du
tableau de bord) sont des aboutissements vides, en attente d'un travail ultérieur.
"""

import pendulum
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

CD_DEPOT = 'cd "${SAA_REPO_ROOT:-.}"'
CD_DBT = 'cd "${SAA_REPO_ROOT:-.}/dbt"'
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
        bash_command=(
            f"set -euo pipefail\n"
            f"{CD_DEPOT}\n"
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
        bash_command=(
            f"set -euo pipefail\n"
            f"{CD_DEPOT}\n"
            f"racine={RACINE_SCENARIO}\n"
            f'uv run python -m ingestion.chargeur "$racine" '
            f'--date-debut "{DATE_EXTRACTION}" --date-fin "{DATE_EXTRACTION}"\n'
        ),
    )

    verifier_controles_et_quarantaine = BashOperator(
        task_id="verifier_controles_et_quarantaine",
        bash_command=(
            f"set -euo pipefail\n"
            f"{CD_DEPOT}\n"
            f'export DATE_EXTRACTION="{DATE_EXTRACTION}"\n'
            "uv run python3 - <<'PYEOF'\n"
            "import os\n"
            "import psycopg2\n"
            "\n"
            'jour = os.environ["DATE_EXTRACTION"]\n'
            "conn = psycopg2.connect(\n"
            '    host=os.environ["POSTGRES_HOST"],\n'
            '    port=os.environ.get("POSTGRES_PORT", "5432"),\n'
            '    dbname=os.environ["POSTGRES_DB"],\n'
            '    user=os.environ["POSTGRES_USER"],\n'
            '    password=os.environ.get("POSTGRES_PASSWORD", ""),\n'
            ")\n"
            "cur = conn.cursor()\n"
            f"tables = {TABLES_SOURCE!r}\n"
            "total = 0\n"
            "for table in tables:\n"
            "    cur.execute(\n"
            f'        f"select count(*) from quarantaine.{{table}} where rejet_partition = %s",\n'
            "        (jour,),\n"
            "    )\n"
            "    n = cur.fetchone()[0]\n"
            "    total += n\n"
            '    print(f"quarantaine.{table} : {n} ligne(s) pour {jour}")\n'
            'print(f"total quarantaine pour {jour} : {total}")\n'
            "PYEOF\n"
        ),
    )

    dbt_intermediaire = BashOperator(
        task_id="dbt_intermediaire",
        bash_command=f'{CD_DBT}\nuv run dbt run --select "{SELECTEUR_INTERMEDIAIRE}"\n',
    )

    dbt_dimensions = BashOperator(
        task_id="dbt_dimensions",
        bash_command=f'{CD_DBT}\nuv run dbt run --select "{SELECTEUR_DIMENSIONS}"\n',
    )

    dbt_faits = BashOperator(
        task_id="dbt_faits",
        bash_command=f'{CD_DBT}\nuv run dbt run --select "{SELECTEUR_FAITS}"\n',
    )

    # dbt sélectionne aussi, par défaut, les tests d'un modèle NON sélectionné dès lors
    # qu'ils référencent un des modèles sélectionnés (mesuré : les tests "relationships"
    # déclarés sur les fichiers .yml des agrégats, qui référencent les dimensions,
    # étaient inclus alors même que les agrégats ne sont pas encore construits à ce
    # stade du graphe). Exclusion explicite des déclarations de test des agrégats.
    dbt_tests = BashOperator(
        task_id="dbt_tests",
        bash_command=(
            f"{CD_DBT}\n"
            f'uv run dbt test --select "{SELECTEUR_INTERMEDIAIRE}" '
            f'"{SELECTEUR_DIMENSIONS}" "{SELECTEUR_FAITS}" '
            f'--exclude "path:models/marts/agg_*.yml"\n'
        ),
    )

    rapprochement_prediction = BashOperator(
        task_id="rapprochement_prediction",
        bash_command=f"{CD_DEPOT}\nuv run python -m linkage.prediction\n",
    )

    rapprochement_regroupement_evaluation = BashOperator(
        task_id="rapprochement_regroupement_evaluation",
        bash_command=f"{CD_DEPOT}\nuv run python -m linkage.evaluation\n",
    )

    dbt_agregats = BashOperator(
        task_id="dbt_agregats",
        bash_command=f'{CD_DBT}\nuv run dbt run --select "{SELECTEUR_AGREGATS}"\n',
    )

    controle_qualite = BashOperator(
        task_id="controle_qualite",
        bash_command=('echo "controle de qualite : aucun seuil bloquant defini pour le moment"\n'),
    )

    exporter = BashOperator(
        task_id="exporter",
        bash_command='echo "export : aboutissement vide, contenu a ecrire plus tard"\n',
    )

    rafraichir_instantane = BashOperator(
        task_id="rafraichir_instantane",
        bash_command=(
            "echo \"rafraichissement de l'instantane : "
            'aboutissement vide, contenu a ecrire plus tard"\n'
        ),
    )

    (
        verifier_disponibilite_extraction
        >> charger_journee
        >> verifier_controles_et_quarantaine
        >> dbt_intermediaire
        >> dbt_dimensions
        >> dbt_faits
        >> dbt_tests
        >> rapprochement_prediction
        >> rapprochement_regroupement_evaluation
        >> dbt_agregats
        >> controle_qualite
        >> exporter
        >> rafraichir_instantane
    )
