"""Ce que chaque page LIT, confronté à ce que le registre DÉCLARE pour elle.

L'INVARIANT QUE CE FICHIER ÉCRIT ET VÉRIFIE.

Le registre des indicateurs nomme ses objets dans la couche modélisée — `marts`, `intermediate`,
`linkage` — parce que c'est là qu'est la provenance analytique : un objet y est produit par un
modèle, documenté, et testé. Les pages, elles, lisent le schéma d'instantané, parce qu'une
reconstruction de la couche modélisée fait disparaître ses vues le temps qu'elle dure et qu'un
lecteur y rencontrerait une erreur d'objet inexistant. **Les deux ont raison, et la divergence de
schéma n'est pas un défaut : c'est un invariant que rien n'écrivait.**

L'invariant est celui-ci : *pour chaque page, l'ensemble des tables que ses requêtes nomment, privé
de son schéma, égale l'ensemble des tables que ses entrées de registre déclarent, privé du sien ; et
chaque table nommée existe dans l'instantané.* Le nom de table est le pont ; le schéma dit de quel
côté du pont on se tient. Deux tables de service font exception et sont déclarées telles quelles :
`instantane_etat` et `instantane_parametres` n'existent que dans l'instantané, dont elles décrivent
l'état, et n'ont aucun homologue modélisé à nommer.

CE CONTRÔLE OBSERVE, IL N'ANALYSE PAS DU CODE SOURCE. Une extraction syntaxique des requêtes s'est
déjà trompée dans ce dépôt : elle attribuait une table à une requête qui ne la nomme pas, et elle ne
résout pas une requête construite par interpolation, dont le texte n'existe qu'à l'exécution. Les
requêtes recueillies ici sont celles que la page ÉMET, à travers le point de lecture qu'elle emploie
elle-même.

PAR PAGE, ET NON PAR INDICATEUR — et c'est une forme plus faible, déclarée comme telle.
`dashboard.lecture.interroger` ne reçoit que du SQL ; l'identifiant de l'indicateur n'accompagne la
requête à aucun niveau commun aux neuf pages — cinq portent un auxiliaire `q(identifiant)`, quatre
appellent le point de lecture directement. Ce contrôle ne peut donc pas dire quelle entrée lit
quelle table, seulement ce que la page entière lit. Il verra une table lue que rien ne déclare, et
une table déclarée que rien ne lit ; il ne verra pas une table déclarée par la mauvaise entrée d'une
même page.

CE QU'IL NE REFAIT PAS. Que chaque objet cité existe au catalogue est déjà vérifié par
`tests/test_registre_indicateurs.py`; qu'il existe dans l'instantané et que la copie ait le même
contenu que son origine, par `tests/test_instantane.py`. Ce fichier ne porte que la correspondance.

Aucun travail au niveau du module : ni connexion, ni lecture de variable d'environnement à l'import.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
PAGES = RACINE / "dashboard" / "pages"
REGISTRE = RACINE / "dashboard" / "indicateurs.yml"

# --- extraction des noms de tables d'une requête ------------------------------------------------
#
# C'est un motif textuel, et il se trompe : ses témoins vivent dans ce fichier, dans les deux sens.
# Quatre formes qu'il doit voir, dix qu'il ne doit pas.

_COMMENTAIRE_LIGNE = re.compile(r"--[^\n]*")
_COMMENTAIRE_BLOC = re.compile(r"/\*.*?\*/", re.DOTALL)
# `is distinct from x` : ce `from` compare deux valeurs et n'introduit aucune table. Mesuré : sans
# cette exclusion, la page de facturation « lit » une colonne nommée montant_lignes.
_DISTINCT_FROM = re.compile(r"\bis\s+(?:not\s+)?distinct\s+from\b", re.IGNORECASE)
# `extract(hour from t)`, `substring(s from 2)`, `trim(both ' ' from s)`, `overlay(... from ...)` :
# dans ces quatre fonctions, `from` sépare des arguments. Mesuré : sans cette exclusion, la page
# d'activité « lit » trois colonnes d'horodatage.
_FONCTIONS_A_FROM = re.compile(r"\b(?:extract|substring|trim|overlay)\s*\([^()]*\)", re.IGNORECASE)
_EXPRESSION_COMMUNE = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)\s+as\s*\(", re.IGNORECASE)
_TABLE = re.compile(r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_.]*)", re.IGNORECASE)


def tables_nommees(sql: str) -> set[str]:
    """Les noms de tables qu'une requête nomme, sans schéma, expressions communes exclues."""
    depouille = _COMMENTAIRE_BLOC.sub(" ", sql)
    depouille = _COMMENTAIRE_LIGNE.sub(" ", depouille)
    depouille = _DISTINCT_FROM.sub(" est_distinct_de ", depouille)
    while True:
        reduit = _FONCTIONS_A_FROM.sub(" ", depouille)
        if reduit == depouille:
            break
        depouille = reduit
    communes = {m.group(1).lower() for m in _EXPRESSION_COMMUNE.finditer(depouille)}
    return {
        nom
        for nom in (m.group(1).split(".")[-1].lower() for m in _TABLE.finditer(depouille))
        if nom not in communes
    }


TEMOINS_POSITIFS = (
    ("from simple", "select * from fct_sejour", {"fct_sejour"}),
    ("join", "select * from fct_sejour join fct_passage on 1=1", {"fct_sejour", "fct_passage"}),
    ("table qualifiée par son schéma", "select * from marts.fct_sejour", {"fct_sejour"}),
    (
        "plusieurs union",
        "select 1 from fct_rendez_vous union all select 1 from fct_passage "
        "union all select 1 from fct_sejour",
        {"fct_rendez_vous", "fct_passage", "fct_sejour"},
    ),
)

TEMOINS_NEGATIFS = (
    (
        "nom dont un autre est le préfixe",
        "select * from fct_passage_urgence",
        {"fct_passage_urgence"},
    ),
    (
        "mention en commentaire de ligne",
        "select * from fct_sejour -- et non fct_passage",
        {"fct_sejour"},
    ),
    (
        "mention en commentaire de bloc",
        "/* fct_passage */ select * from fct_sejour",
        {"fct_sejour"},
    ),
    ("alias portant un nom de table", "select * from fct_sejour as fct_passage", {"fct_sejour"}),
    ("expression de table commune", "with bornes as (select 1) select * from bornes", set()),
    (
        "deux expressions de table communes",
        "with a as (select 1), b as (select 2 from a) select * from b join fct_sejour on 1=1",
        {"fct_sejour"},
    ),
    (
        "extract(unité from horodatage)",
        "select extract(hour from date_heure_entree) from fct_passage",
        {"fct_passage"},
    ),
    (
        "is distinct from",
        "select count(*) filter (where montant_total is distinct from montant_lignes) "
        "from fct_facturation",
        {"fct_facturation"},
    ),
    (
        "is not distinct from",
        "select 1 from fct_facturation where a is not distinct from b",
        {"fct_facturation"},
    ),
    (
        "substring(chaîne from rang)",
        "select substring(nom from 2) from dim_patient",
        {"dim_patient"},
    ),
)


@pytest.mark.parametrize(("libelle", "sql", "attendu"), TEMOINS_POSITIFS + TEMOINS_NEGATIFS)
def test_le_motif_d_extraction_repond_a_chacun_de_ses_temoins(
    libelle: str, sql: str, attendu: set[str]
) -> None:
    """Un motif textuel se trompe : celui-ci est éprouvé dans les deux sens avant d'être cru."""
    obtenu = tables_nommees(sql)
    assert obtenu == attendu, (
        f"témoin « {libelle} » : {sorted(obtenu)} au lieu de {sorted(attendu)}"
    )


# --- la correspondance ---------------------------------------------------------------------------


def _lecture():
    """Importé à l'appel, jamais à l'import : le module ouvre des connexions."""
    from dashboard import lecture

    return lecture


def _instantane_pret(lecture) -> dict:
    """Précondition établie ici, non héritée : si l'état ne peut être lu, on rafraîchit."""
    try:
        etat = lecture.etat()
    except Exception:
        etat = None
    if etat is None or etat.get("rafraichi_le") is None:
        from instantane import rafraichir

        reussite, message = rafraichir.rafraichir()
        if not reussite:
            pytest.fail(f"l'instantané ne peut être constitué : {message}")
        etat = lecture.etat()
    return etat


def _pages() -> list[str]:
    return sorted(fichier.stem for fichier in PAGES.glob("*.py"))


def _declarees_par_page() -> dict[str, set[str]]:
    """Les tables déclarées, privées de leur schéma, groupées par page."""
    registre = yaml.safe_load(REGISTRE.read_text(encoding="utf-8"))
    par_page: dict[str, set[str]] = {}
    for entree in registre["indicateurs"]:
        cible = par_page.setdefault(entree["page"], set())
        for objet in entree["objets_lus"]:
            cible.add(objet.split(".")[-1].lower())
    return par_page


# Le rendu se fait dans un PROCESSUS FILS, un par page, et ce n'est pas une précaution de style.
# Mesuré : trois rendus successifs dans un même processus se terminent sans trace ni code d'erreur
# à l'intérieur de l'image du service, là où un rendu par processus rend la main normalement.
# `tests/test_tableau_de_bord.py` porte la même observation sur la machine de développement. Un
# contrôle qui rendrait les neuf pages dans son propre processus mourrait donc en silence sur
# l'exécuteur, et un contrôle mort ne rougit pas.
_ENFANT = """
import json, sys
sys.path.insert(0, {racine!r})
from streamlit.testing.v1 import AppTest
from dashboard import lecture

requetes = []
with lecture.requetes_observees() as journal:
    application = AppTest.from_file({chemin!r}, default_timeout=300).run()
    exceptions = [str(e.value)[:300] for e in application.exception]
    requetes.extend(journal)
    for rang in range(len(application.selectbox)):
        for option in application.selectbox[rang].options:
            journal.clear()
            application = application.selectbox[rang].select(option).run()
            exceptions.extend(str(e.value)[:300] for e in application.exception)
            requetes.extend(journal)

print("<<<" + json.dumps({{"requetes": requetes, "exceptions": exceptions}}) + ">>>")
"""


def _lues_par_page(nom: str) -> set[str]:
    """Les tables que la page nomme dans les requêtes qu'elle ÉMET réellement.

    Chaque option de chaque sélecteur est exercée : une page dont l'objet lu dépend d'un choix de
    l'utilisateur ne lit qu'une table par rendu, et ne déclarer que celle-là serait faux.
    """
    source = _ENFANT.format(racine=str(RACINE), chemin=str(PAGES / f"{nom}.py"))
    acheve = subprocess.run(  # noqa: S603
        [sys.executable, "-c", source],
        cwd=str(RACINE),
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert acheve.returncode == 0, (
        f"le rendu de la page « {nom} » s'est terminé avec le code {acheve.returncode} : "
        f"{acheve.stderr[-500:]}"
    )
    debut = acheve.stdout.find("<<<")
    fin = acheve.stdout.rfind(">>>")
    assert debut >= 0 and fin > debut, (
        f"le rendu de la page « {nom} » n'a rien rapporté : {acheve.stdout[-500:]}"
    )
    rapport = json.loads(acheve.stdout[debut + 3 : fin])
    assert not rapport["exceptions"], f"la page « {nom} » a levé : {rapport['exceptions'][0]}"

    lues: set[str] = set()
    for requete in rapport["requetes"]:
        lues |= tables_nommees(requete)
    return lues


def test_chaque_page_lit_exactement_les_tables_que_le_registre_declare_pour_elle() -> None:
    """L'invariant, dans les deux sens : rien de lu qui ne soit déclaré, rien de déclaré
    qui ne soit lu."""
    lecture = _lecture()
    _instantane_pret(lecture)

    declarees = _declarees_par_page()
    ecarts = []
    for page in _pages():
        attendues = declarees.get(page)
        assert attendues, f"la page « {page} » ne porte aucune entrée au registre"
        lues = _lues_par_page(page)

        non_declarees = sorted(lues - attendues)
        non_lues = sorted(attendues - lues)
        if non_declarees:
            ecarts.append(f"{page} : lit {non_declarees} que le registre ne déclare pas")
        if non_lues:
            ecarts.append(f"{page} : déclare {non_lues} qu'elle ne lit pas")

    assert not ecarts, "le registre et l'usage divergent :\n" + "\n".join(ecarts)


def test_chaque_table_lue_existe_dans_l_instantane() -> None:
    """Le pont tient par le nom : la table lue sans schéma doit exister dans l'instantané."""
    lecture = _lecture()
    _instantane_pret(lecture)

    presentes = set(
        lecture.interroger(
            "select table_name from information_schema.tables where table_schema = 'instantane'"
        )["table_name"]
    )
    assert presentes, "le schéma d'instantané ne porte aucune table"

    absentes = []
    for page in _pages():
        for table in sorted(_lues_par_page(page)):
            if table not in presentes:
                absentes.append(f"{page} : lit « {table} », absente de l'instantané")

    assert not absentes, "\n".join(absentes)
