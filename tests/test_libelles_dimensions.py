"""Contrôle du registre des libellés de dimension, et de ce que les pages en rendent.

POURQUOI CE FICHIER EXISTE.

Le cadrage interdit d'inventer un libellé là où le système observé n'en fournit pas. Cette
interdiction porte sur les VALEURS DE CODE venues du système ; elle n'interdit pas d'afficher un
libellé qu'une source documentée établit. La frontière entre les deux est exactement ce que ce
fichier garde : un libellé affiché sans source est l'invention que la règle proscrit, et un code
laissé nu alors qu'une source le documente est l'appauvrissement que la règle ne demande pas.

CE QUE CE FICHIER VÉRIFIE, une fonction par propriété :

  1. tout libellé rendu par une page a une entrée au registre, et toute entrée documentée cite une
     source qui existe au registre des sources ;
  2. aucun code présent dans les données n'est absent du registre, et aucune entrée du registre ne
     porte un code absent des données — dans les deux sens, comme le garde-fou de collecte ;
  3. un code classé non documenté n'affiche aucun libellé.

CE QU'IL OBSERVE. **Ce que la page rend**, en interceptant les fonctions d'affichage et en lisant
les tableaux effectivement passés, et non ce que le registre déclare. Deux contrôles de ce dépôt ont
déjà comparé un registre à lui-même ; la première propriété part donc des chaînes rendues à l'écran
et remonte vers le registre, jamais l'inverse.

CE QU'IL NE VÉRIFIE PAS : que le libellé soit le bon. Qu'une source dise que le code 20 désigne la
médecine générale ne peut se vérifier qu'en lisant la source ; c'est la relecture humaine qui
l'attrape, et c'est pourquoi le registre exige un renvoi précis plutôt qu'un identifiant seul.

Aucun travail au niveau du module : ni connexion, ni lecture de variable d'environnement, ni
chargement de fichier à l'import. Le fichier se collecte sur un clone frais sans base ni variable
exportée.

Aucun littéral de volumétrie : les décomptes comparés sont calculés chacun de son côté, l'un depuis
la base, l'autre depuis le registre.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
DASHBOARD = RACINE / "dashboard"
LIBELLES = DASHBOARD / "libelles_dimensions.yml"
SOURCES = RACINE / "docs" / "sources" / "sources.yml"

# La dimension du registre des libellés, et la requête qui rend les codes réellement présents dans
# les données pour cette dimension. La requête est écrite ici, indépendamment des pages : comparer
# le registre aux requêtes des pages ferait dépendre les deux ensembles d'une même source.
CODES_EN_BASE = {
    "activite": "select distinct code_activite as code from fct_rendez_vous",
    "orientation_sortie": "select distinct orientation_sortie as code from fct_passage_urgence",
    "niveau_tri": "select distinct niveau_tri as code from fct_passage_urgence",
    "service": "select distinct code_service as code from dim_service",
    "type_episode": "select distinct type_episode as code from fct_facturation",
}

# Les pages qui affichent au moins un code de dimension, et la dimension qu'elles rendent.
PAGES_A_RENDRE = {
    "rendez_vous": "activite",
    "urgences": "orientation_sortie",
    "sejours": "service",
}


def _registre() -> dict:
    return yaml.safe_load(LIBELLES.read_text(encoding="utf-8"))


def _entrees() -> list[dict]:
    return _registre()["libelles"]


def _identifiants_de_sources() -> set[str]:
    contenu = yaml.safe_load(SOURCES.read_text(encoding="utf-8"))
    entrees = contenu if isinstance(contenu, list) else contenu.get("sources", [])
    return {entree["id"] for entree in entrees}


def _lecture():
    """Le module de lecture du tableau de bord, importé à l'appel et jamais à l'import."""
    import sys  # noqa: PLC0415

    if str(RACINE) not in sys.path:
        sys.path.insert(0, str(RACINE))
    from dashboard import lecture  # noqa: PLC0415

    return lecture


def _chaines_rendues(page: str) -> list[str]:
    """Toutes les chaînes que la page passe à un graphique ou à un tableau.

    C'est la mesure de ce que l'ÉCRAN porte : les fonctions d'affichage sont interceptées et les
    tableaux qu'elles reçoivent sont lus. Un libellé qui n'atteindrait pas l'écran n'apparaîtrait
    pas ici, et un libellé ajouté hors du registre y apparaîtrait.
    """
    import sys  # noqa: PLC0415

    if str(RACINE) not in sys.path:
        sys.path.insert(0, str(RACINE))
    import streamlit as st  # noqa: PLC0415
    from streamlit.testing.v1 import AppTest  # noqa: PLC0415

    recues: list = []
    origines = {}
    for nom in ("line_chart", "bar_chart", "area_chart", "scatter_chart", "dataframe"):
        origines[nom] = getattr(st, nom)

        def espion(data=None, *args, _origine=origines[nom], **kwargs):
            recues.append(data)
            return _origine(data, *args, **kwargs)

        setattr(st, nom, espion)
    try:
        application = AppTest.from_file(
            str(DASHBOARD / "pages" / f"{page}.py"), default_timeout=300
        ).run()
        assert not list(application.exception), (
            f"la page « {page} » a levé : {list(application.exception)[0].value[:300]}"
        )
    finally:
        for nom, origine in origines.items():
            setattr(st, nom, origine)

    chaines: list[str] = []
    for tableau in recues:
        colonnes = getattr(tableau, "columns", None)
        if colonnes is None:
            continue
        for colonne in colonnes:
            for valeur in tableau[colonne]:
                if isinstance(valeur, str):
                    chaines.append(valeur)
    return chaines


def test_tout_libelle_rendu_a_une_entree_et_une_source_qui_existe() -> None:
    """Part de l'écran et remonte vers le registre, jamais l'inverse."""
    from dashboard import rendu  # noqa: PLC0415

    connus = {
        f"{entree['code']}{rendu.SEPARATEUR_LIBELLE}{entree['libelle']}"
        for entree in _entrees()
        if entree.get("categorie") == "documente"
    }
    assert connus, "le registre ne porte aucun libellé documenté"

    # Structure d'abord : sans elle, une entrée mal formée ferait rougir ce contrôle par une
    # exception de clé absente plutôt que par un message qui nomme la faute — mesuré en mutant le
    # registre pour y poser un libellé sans source.
    malformees = []
    for entree in _entrees():
        cle = f"{entree.get('dimension')}/{entree.get('code')}"
        if entree.get("categorie") == "documente":
            manquants = [c for c in ("libelle", "source", "renvoi") if not entree.get(c)]
            if manquants:
                malformees.append(f"{cle} : documenté sans {', '.join(manquants)}")
        else:
            en_trop = [c for c in ("libelle", "source") if entree.get(c)]
            if en_trop:
                malformees.append(f"{cle} : non documenté mais porte {', '.join(en_trop)}")
            if not entree.get("motif"):
                malformees.append(f"{cle} : non documenté sans motif")
    assert not malformees, "entrées mal formées au registre : " + " | ".join(malformees)

    identifiants = _identifiants_de_sources()
    orphelines = [
        f"{entree['dimension']}/{entree['code']} cite « {entree['source']} »"
        for entree in _entrees()
        if entree.get("categorie") == "documente" and entree["source"] not in identifiants
    ]
    assert not orphelines, (
        "entrées citant une source absente du registre des sources : " + " | ".join(orphelines)
    )

    inventes = []
    for page, _dimension in PAGES_A_RENDRE.items():
        for chaine in _chaines_rendues(page):
            if rendu.SEPARATEUR_LIBELLE in chaine and chaine not in connus:
                inventes.append(f"{page} : « {chaine} »")

    assert not inventes, (
        "chaînes rendues à l'écran sous la forme code-libellé sans entrée documentée au "
        "registre : " + " | ".join(sorted(set(inventes)))
    )


def test_le_registre_et_les_donnees_se_couvrent_dans_les_deux_sens() -> None:
    """Aucun code des données absent du registre, aucune entrée sans code dans les données."""
    lecture = _lecture()
    par_dimension: dict[str, set[str]] = {}
    for entree in _entrees():
        par_dimension.setdefault(entree["dimension"], set()).add(str(entree["code"]))

    assert set(par_dimension) == set(CODES_EN_BASE), (
        f"dimensions du registre {sorted(par_dimension)} et dimensions interrogées "
        f"{sorted(CODES_EN_BASE)} ne coïncident pas"
    )

    fautifs = []
    for dimension, requete in CODES_EN_BASE.items():
        try:
            en_base = {str(valeur) for valeur in lecture.interroger(requete)["code"]}
        except Exception as exc:  # noqa: BLE001
            pytest.fail(
                f"interrogation impossible pour la dimension « {dimension} » ({exc}) : "
                "le schéma d'instantané doit être rafraîchi avant ce contrôle"
            )
        assert en_base, f"aucun code rendu pour la dimension « {dimension} »"
        manquants = sorted(en_base - par_dimension[dimension])
        fantomes = sorted(par_dimension[dimension] - en_base)
        if manquants:
            fautifs.append(
                f"{dimension} : codes en base absents du registre — {', '.join(manquants)}"
            )
        if fantomes:
            fautifs.append(
                f"{dimension} : codes au registre absents des données — {', '.join(fantomes)}"
            )

    assert not fautifs, "registre et données ne se couvrent pas : " + " | ".join(fautifs)


def test_un_code_non_documente_n_affiche_aucun_libelle() -> None:
    """La propriété qui empêche l'invention, observée sur ce que la page rend."""
    from dashboard import rendu  # noqa: PLC0415

    nus = {
        (entree["dimension"], str(entree["code"]))
        for entree in _entrees()
        if entree.get("categorie") != "documente"
    }
    assert nus, "le registre ne porte aucun code non documenté : la propriété serait vide"

    porteurs = [
        f"{dimension}/{code} rendu « {rendu.libelle_dimension(dimension, code)} »"
        for dimension, code in sorted(nus)
        if rendu.SEPARATEUR_LIBELLE in rendu.libelle_dimension(dimension, code)
    ]
    assert not porteurs, (
        "codes classés non documentés auxquels le mécanisme d'affichage attribue un libellé : "
        + " | ".join(porteurs)
    )

    codes_nus = {code for _dimension, code in nus}
    fautifs = []
    for page, _dimension in PAGES_A_RENDRE.items():
        for chaine in _chaines_rendues(page):
            if rendu.SEPARATEUR_LIBELLE not in chaine:
                continue
            code = chaine.split(rendu.SEPARATEUR_LIBELLE, 1)[0]
            if code in codes_nus and not any(
                entree.get("categorie") == "documente" and str(entree["code"]) == code
                for entree in _entrees()
            ):
                fautifs.append(f"{page} : « {chaine} »")

    assert not fautifs, "un code classé non documenté est rendu avec un libellé : " + " | ".join(
        sorted(set(fautifs))
    )
