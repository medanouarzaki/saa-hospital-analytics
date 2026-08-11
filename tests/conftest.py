"""Génération partagée d'une exécution complète, une fois par session de test.

Une exécution complète de l'orchestrateur (`generator.execution.executer`), pour la graine
et le scénario par défaut, coûte plusieurs dizaines de secondes ; produite indépendamment
par chaque fichier de test qui en a besoin, elle domine le temps de la suite (mesuré avant
d'écrire ce fichier, voir le rapport). La fixture `generation_partagee` ci-dessous la
produit une fois par session pytest (portée "session", le mécanisme prévu par le lanceur
pour cela) et la partage entre tous les fichiers qui la demandent ; les tests qui exigent
une autre graine continuent d'en produire une eux-mêmes, indépendamment.

La sortie vit sous le répertoire temporaire de la session pytest (`tmp_path_factory`,
lui-même de portée "session"), jamais sous `generator/output/` : deux sessions
concurrentes reçoivent chacune un répertoire numéroté distinct, et une session interrompue
ne laisse rien dans le dépôt suivi.
"""

import pytest

from generator import config, execution

GRAINE_PARTAGEE = 1


def _entrees_config() -> dict[str, dict]:
    return {e["nom"]: e for e in config.charger_entrees()}


@pytest.fixture(scope="session")
def generation_partagee(tmp_path_factory) -> dict:
    entrees = _entrees_config()
    racine = tmp_path_factory.mktemp("generation_partagee")
    execution_obj, contexte = execution.executer(racine, GRAINE_PARTAGEE, entrees=entrees)
    return {
        # contexte.entrees, pas la variable locale entrees ci-dessus : depuis que
        # generator/execution.py copie entrees en interne pour ne jamais muter l'objet
        # reçu en argument (mesuré avant d'écrire, voir le rapport -- deux appels avec le
        # même entrees produisaient des empreintes différentes autrement), la variable
        # locale ne porte plus les valeurs dérivées (orientation_urgences["HO"]) que les
        # tests attendent.
        "entrees": contexte.entrees,
        "episodes": contexte.episodes,
        "population": contexte.population,
        "lignes": contexte.lignes,
        "execution": execution_obj,
        "racine": racine,
    }
