"""L'appariement de un à un entre le fait de séjour et le passage d'hospitalisation.

Un épisode d'hospitalisation est écrit deux fois : une ligne de passage de type hospitalisé, et un
séjour reconstitué depuis les mouvements. Aucune clé étrangère ne les relie —
`docs/decisions/0024-limites-documentees-des-faits.md` a décidé de n'en poser aucune — mais la
correspondance existe par le couple (patient, instant d'admission), et elle est de un à un.

CE QUE CE CONTRÔLE VERROUILLE : cette correspondance, dans les deux sens, et l'unicité de la clé de
part et d'autre. Perdre l'appariement signifierait qu'un épisode existe d'un côté et pas de l'autre,
ce qui serait un défaut de génération et non un choix.

CE QU'IL NE VERROUILLE PAS, ET POURQUOI : les deux durées divergent — deux tirages indépendants pour
le même épisode, consigné à `docs/decisions/0059-...md`. Asserter cette divergence — que les sommes
diffèrent d'environ tant de jours, qu'aucune paire ne coïncide — transformerait un défaut en
propriété attendue, et une correction future ferait rougir le contrôle à tort. **On ne fige pas un
défaut par une assertion : on le consigne.** La divergence est donc décrite dans l'enregistrement,
et absente d'ici.

GARDE D'APPLICABILITÉ : aucune, et c'est mesurable plutôt que supposé. La propriété est
STRUCTURELLE — elle compare deux ensembles de clés, non des volumes — et vaut sur une fenêtre de
trois mois comme sur la période entière : chaque épisode généré est écrit des deux côtés quel que
soit leur nombre. Le seul cas qu'elle ne couvrirait pas est celui d'un jeu vide, où deux ensembles
vides sont trivialement égaux ; le contrôle exige donc explicitement que les deux tables portent au
moins une ligne.
"""

from __future__ import annotations

from pathlib import Path

import psycopg
import pytest

RACINE = Path(__file__).resolve().parent.parent
APPLIQUER_DDL = RACINE / "ingestion" / "appliquer_ddl.py"

# La valeur qui identifie un passage d'hospitalisation. Elle n'est pas déduite du nom de la
# colonne :
# `generator/config/nomenclatures_organisation_activite.yml::nomenclature_type_passage` la déclare
# (`H` = Hospitalisés, provenance DOC, preuve S-06), et `generator/mouvements.py` la retient pour
# fixer le nombre de séjours.
TYPE_HOSPITALISATION = "H"


def _charger_module(chemin: Path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(chemin.stem, chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _connexion() -> psycopg.Connection:
    variables = _charger_module(APPLIQUER_DDL).charger_environnement()
    try:
        return psycopg.connect(
            host=variables["POSTGRES_HOST"],
            port=variables["POSTGRES_PORT"],
            dbname=variables["POSTGRES_DB"],
            user=variables["POSTGRES_USER"],
            password=variables.get("POSTGRES_PASSWORD", ""),
        )
    except psycopg.OperationalError as exc:
        pytest.fail(
            f"connexion impossible à la base ({exc}) : marts.fct_sejour et marts.fct_passage "
            "doivent être construites avant ce contrôle"
        )


def _mesures() -> dict[str, int]:
    conn = _connexion()
    try:
        with conn.cursor() as curseur:
            curseur.execute(
                """
                select
                  (select count(*) from marts.fct_sejour),
                  (select count(*) from marts.fct_passage where type_passage = %(type)s),
                  (select count(*) from marts.fct_sejour s
                     join marts.fct_passage p
                       on p.n_ipp = s.n_ipp
                      and p.type_passage = %(type)s
                      and p.date_heure_entree = s.date_heure_admission),
                  (select count(*) from marts.fct_sejour s
                    where not exists (select 1 from marts.fct_passage p
                                       where p.n_ipp = s.n_ipp
                                         and p.type_passage = %(type)s
                                         and p.date_heure_entree = s.date_heure_admission)),
                  (select count(*) from marts.fct_passage p
                    where p.type_passage = %(type)s
                      and not exists (select 1 from marts.fct_sejour s
                                       where s.n_ipp = p.n_ipp
                                         and s.date_heure_admission = p.date_heure_entree)),
                  (select count(*) from (select n_ipp, date_heure_admission
                                           from marts.fct_sejour
                                          group by 1, 2 having count(*) > 1) as d),
                  (select count(*) from (select n_ipp, date_heure_entree
                                           from marts.fct_passage where type_passage = %(type)s
                                          group by 1, 2 having count(*) > 1) as e)
                """,
                {"type": TYPE_HOSPITALISATION},
            )
            ligne = curseur.fetchone()
    finally:
        conn.close()
    return dict(
        zip(
            (
                "sejours",
                "passages",
                "paires",
                "sejours_sans_passage",
                "passages_sans_sejour",
                "cles_sejour_en_double",
                "cles_passage_en_double",
            ),
            ligne,
            strict=True,
        )
    )


def test_chaque_sejour_a_son_passage_et_reciproquement() -> None:
    """La correspondance, dans les deux sens, et l'unicité de la clé de part et d'autre."""
    m = _mesures()

    assert m["sejours"] > 0 and m["passages"] > 0, (
        f"population vide : {m['sejours']} séjours, {m['passages']} passages de type "
        f"« {TYPE_HOSPITALISATION} » — la propriété serait trivialement vraie"
    )

    ecarts = []
    if m["sejours_sans_passage"]:
        ecarts.append(
            f"{m['sejours_sans_passage']} séjour(s) sans passage d'hospitalisation apparié "
            f"sur (patient, instant d'admission), pour {m['sejours']} séjours"
        )
    if m["passages_sans_sejour"]:
        ecarts.append(
            f"{m['passages_sans_sejour']} passage(s) d'hospitalisation sans séjour apparié, "
            f"pour {m['passages']} passages"
        )
    if m["cles_sejour_en_double"]:
        ecarts.append(
            f"{m['cles_sejour_en_double']} clé(s) (patient, instant) portée(s) par plus d'un séjour"
        )
    if m["cles_passage_en_double"]:
        ecarts.append(f"{m['cles_passage_en_double']} clé(s) portée(s) par plus d'un passage")
    if m["paires"] != m["sejours"] or m["paires"] != m["passages"]:
        ecarts.append(
            f"{m['paires']} paires pour {m['sejours']} séjours et {m['passages']} passages"
        )

    assert not ecarts, (
        "l'appariement séjour / passage d'hospitalisation n'est plus de un à un :\n"
        + "\n".join(ecarts)
    )
