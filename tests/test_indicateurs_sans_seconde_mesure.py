"""Les trois indicateurs qu'aucun contrôle ne touchait, chacun sous la référence qu'il admet.

Trois indicateurs du tableau de bord n'étaient couverts par aucun contrôle lisant leurs objets :
`qualite_provenance_champs`, `facturation_taux_recouvrement`, `facturation_aboutissement_relances`.
Ils lisent deux agrégats — `agg_provenance_champs` et `agg_recouvrement` — que rien d'autre
n'interroge.

LES DEUX RÉFÉRENCES NE SONT PAS DE MÊME FORCE, ET LE FICHIER NE PRÉTEND PAS LE CONTRAIRE.

Pour la provenance des champs, une référence EXTERNE existe : le registre des champs,
`docs/champs/registre_champs.yml`, porte l'étiquette de provenance de chaque colonne de la couche
source. L'agrégat, lui, est construit depuis les commentaires du catalogue PostgreSQL. Deux
artefacts produits par deux chemins indépendants portent donc la même grandeur, et leur coïncidence
est une propriété réelle : changer une étiquette dans le fichier fait diverger les deux.

Pour les deux indicateurs de recouvrement, AUCUNE référence externe n'existe. `agg_recouvrement` est
le seul artefact du dépôt qui porte ces montants ; les recalculer depuis les créances
retranscrirait le modèle qui les produit, et une retranscription ne peut pas falsifier ce qu'elle
retranscrit — le dépôt vient d'en retirer une pour cette raison. Ce qui reste affirmable sans
retranscrire est une propriété de COHÉRENCE INTERNE, plus faible qu'une égalité et déclarée telle :
un montant recouvré ne dépasse pas le montant dû, des relances abouties ne dépassent pas les
relances émises, et un taux tombe entre zéro et un. Inverser un rapport ou sommer la mauvaise
colonne la fait rougir ; une erreur d'échelle qui préserverait les bornes lui échapperait.

Les valeurs éprouvées sont celles que LA PAGE obtient : ses requêtes sont exécutées par son propre
point de lecture, celui qui restreint le chemin de recherche au schéma d'instantané.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
PAGES = RACINE / "dashboard" / "pages"
REGISTRE_CHAMPS = RACINE / "docs" / "champs" / "registre_champs.yml"


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


def _requete_de_page(page: str, identifiant: str) -> str:
    """La requête d'un indicateur, prise dans la page qui la porte, sans la rendre."""
    source = (PAGES / f"{page}.py").read_text(encoding="utf-8").replace("\nrendre()\n", "\n")
    espace: dict = {}
    exec(compile(source, f"{page}.py", "exec"), espace)
    requetes = espace["REQUETES"]
    assert identifiant in requetes, f"{identifiant} absent des requêtes de la page {page}"
    requete = requetes[identifiant]
    return requete.format(filtre="") if "{filtre}" in requete else requete


def test_la_provenance_affichee_egale_celle_du_registre_des_champs() -> None:
    """Référence externe : deux artefacts indépendants portent la même grandeur."""
    lecture = _lecture()
    _instantane_pret(lecture)

    affichee = lecture.interroger(
        _requete_de_page("provenance_et_parametres", "qualite_provenance_champs")
    )
    par_etiquette = {ligne.provenance: int(ligne.nb_colonnes) for ligne in affichee.itertuples()}

    registre = yaml.safe_load(REGISTRE_CHAMPS.read_text(encoding="utf-8"))
    attendu: dict[str, int] = {}
    for champ in registre:
        attendu[champ["provenance"]] = attendu.get(champ["provenance"], 0) + 1

    assert par_etiquette == attendu, (
        f"provenance affichée {par_etiquette} contre {attendu} au registre des champs, que "
        f"{REGISTRE_CHAMPS.name} porte ligne à ligne"
    )

    total_affiche = sum(par_etiquette.values())
    somme_des_parts = sum(float(ligne.part_pourcent) for ligne in affichee.itertuples())
    assert abs(somme_des_parts - 100.0) <= 0.2, (
        f"les parts affichées somment à {somme_des_parts} pour {total_affiche} colonnes"
    )


def test_les_deux_indicateurs_de_recouvrement_restent_dans_leurs_bornes() -> None:
    """Cohérence interne : plus faible qu'une égalité, et falsifiable par une inversion."""
    lecture = _lecture()
    _instantane_pret(lecture)

    recouvrement = lecture.interroger(
        _requete_de_page("facturation", "facturation_taux_recouvrement")
    ).iloc[0]
    relances = lecture.interroger(
        _requete_de_page("facturation", "facturation_aboutissement_relances")
    ).iloc[0]

    if recouvrement["creances_nees"] is None or relances["relances_emises"] is None:
        pytest.skip(
            "aucune créance ni relance dans la fenêtre chargée : les bornes portent sur une "
            "population vide et ne diraient rien"
        )

    dues = float(recouvrement["creances_nees"])
    recouvrees = float(recouvrement["creances_recouvrees"])
    emises = float(relances["relances_emises"])
    abouties = float(relances["relances_abouties"])

    ecarts = []
    if dues <= 0:
        ecarts.append(f"créances nées {dues} : un montant dû nul ou négatif ne se recouvre pas")
    if recouvrees < 0 or recouvrees > dues:
        ecarts.append(f"recouvré {recouvrees} hors de [0, {dues}] dû")
    if emises <= 0:
        ecarts.append(f"relances émises {emises} : aucune relance à faire aboutir")
    if abouties < 0 or abouties > emises:
        ecarts.append(f"relances abouties {abouties} hors de [0, {emises}] émises")
    for nom, taux in (
        ("taux de recouvrement", recouvrement["taux"]),
        ("taux d'aboutissement", relances["taux"]),
    ):
        if taux is None:
            ecarts.append(f"{nom} : indéfini alors que son dénominateur ne l'est pas")
        elif not 0.0 <= float(taux) <= 1.0:
            ecarts.append(f"{nom} : {float(taux)} hors de [0, 1]")

    assert not ecarts, "les indicateurs de recouvrement sortent de leurs bornes :\n" + "\n".join(
        ecarts
    )
