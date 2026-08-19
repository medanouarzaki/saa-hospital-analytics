"""Les quatre indicateurs de séjour TELS QUE LA PAGE LES AFFICHE, éprouvés par deux références.

Ce contrôle existe parce qu'aucun autre ne lisait ce que la page lit. Ceux qui portaient sur ces
grandeurs interrogeaient la couche modélisée, quand la page interroge l'instantané ; celui qui
portait sur la page retranscrivait sa formule et se comparait à elle, ce qui ne peut départager une
formule juste d'une formule fausse. Un taux de rotation faux d'un facteur voisin de 2,5 a traversé
les deux sans être vu.

Les deux références portées ici ne se recouvrent pas, et aucune n'est une retranscription :

1. RÉFÉRENCE EXTERNE AU CODE — les quatre sorties de la page sont confrontées aux quatre valeurs
   publiées par la source statistique, lues dans `generator/config/volumetrie.yml`, à la tolérance
   relative que porte `tests/test_indicateurs_sejour.py`. Ni les valeurs ni la tolérance ne sont
   écrites ici : elles sont lues là où elles vivent. Aucune écriture du dépôt ne peut rendre cette
   assertion vraie, son second membre lui étant extérieur.

2. ACCORD ENTRE DEUX IMPLÉMENTATIONS — les quatre sorties de la page, calculées EN SQL SUR
   L'INSTANTANÉ, sont confrontées à celles que `test_indicateurs_sejour.indicateurs_recalcules`
   calcule EN PYTHON DEPUIS LES LIGNES BRUTES de la couche modélisée. La formule n'est pas
   recopiée : la fonction est importée et appelée. Deux langages, deux schémas, une seule
   convention — leur coïncidence est une propriété, non une tautologie.

La page est APPELÉE, non recopiée : son module est chargé sans être rendu, ses paramètres sont ceux
qu'elle lit, et ses requêtes passent par son propre point de lecture, celui qui restreint le chemin
de recherche au schéma d'instantané. Un contrôle qui ouvrirait sa propre connexion ne prouverait
rien de ce que la page voit.

GARDE D'APPLICABILITÉ. Les quatre grandeurs sont annualisées et n'ont de sens que sur une génération
couvrant la période entière : c'est la décision consignée à
`docs/decisions/0026-garde-applicabilite-indicateurs-sejour.md`, et la condition retenue y est une
égalité mesurée — la date d'admission maximale contre la date de fin de période configurée — jamais
une marge. Ce contrôle reprend cette condition et la pose DES DEUX CÔTÉS, la couche modélisée et
l'instantané devant l'un et l'autre couvrir la période entière pour être comparables. Sur une
fenêtre partielle, les deux implémentations divergent pour une raison qui ne dit rien de leur
justesse : l'une annualise un volume de trois mois par la durée de la période complète, l'autre
prolonge jusqu'à la borne de fin les séjours qu'une fenêtre courte laisse tous ouverts. S'abstenir
avec un motif explicite vaut mieux qu'élargir une tolérance jusqu'à ne plus rien détecter.

Aucun travail au niveau du module : ni connexion, ni lecture de variable d'environnement à
l'import. Le fichier se collecte sur un clone frais sans base.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
PAGES = RACINE / "dashboard" / "pages"
VOLUMETRIE = RACINE / "generator" / "config" / "volumetrie.yml"

INDICATEUR = "sejours_indicateurs_reglementaires"
PAGE = "sejours"

# Ce qui relie une colonne de sortie de la page à la grandeur publiée qui lui répond, et au nom que
# la convention de l'entrepôt lui donne. La correspondance est la seule chose écrite ici ; les
# valeurs qu'elle relie sont toutes lues. Le facteur porte l'unité : le taux d'occupation est une
# proportion côté page — la page le multiplie par cent pour l'afficher — et un pourcentage côté
# source publiée comme côté entrepôt.
CORRESPONDANCE = (
    ("taux_occupation", "tom_publie", "TOM", 100.0),
    ("duree_moyenne_jours", "dms_publie", "DMS", 1.0),
    ("rotation", "trot_publie", "TROT", 1.0),
    ("intervalle_rotation_jours", "irot_publie", "IROT", 1.0),
)

# Tolérance de l'accord entre les deux implémentations. Elle n'a rien à voir avec la tolérance de
# conformité aux valeurs publiées, qui est lue ailleurs : deux calculs de la même convention doivent
# coïncider à l'arithmétique près, pas à trois pour cent près. Sa valeur tient compte de ce que
# l'une des deux passe par une décimale exacte côté serveur et l'autre par un flottant.
TOLERANCE_ENTRE_IMPLEMENTATIONS = 1e-9


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


def _module_de_page(nom: str) -> dict:
    """Le module d'une page, chargé sans être rendu — même idiome que les contrôles voisins."""
    source = (PAGES / f"{nom}.py").read_text(encoding="utf-8")
    source = source.replace("\nrendre()\n", "\n")
    espace: dict = {}
    exec(compile(source, f"{nom}.py", "exec"), espace)
    return espace


def _sorties_de_la_page(lecture) -> dict[str, float]:
    """Ce que la page obtient, par SES paramètres et SON point de lecture."""
    page = _module_de_page(PAGE)
    substitutions = {
        "capacite": int(page["_parametre"](page["PARAMETRE_CAPACITE"])["valeur"]),
        "jours_annee": int(page["_parametre"](page["PARAMETRE_JOURS_ANNEE"])["valeur"]),
        "jours_periode": int(page["_parametre"](page["PARAMETRE_JOURS_PERIODE"])["valeur"]),
    }
    ligne = lecture.interroger(page["REQUETES"][INDICATEUR] % substitutions).iloc[0]
    return {colonne: float(ligne[colonne]) * facteur for colonne, _, _, facteur in CORRESPONDANCE}


def _fenetre_complete_ou_abstention(lecture) -> None:
    """S'abstient si l'une des deux couches ne couvre pas la période entière.

    La condition est celle de `tests/test_indicateurs_sejour.py` : la date d'admission maximale
    doit égaler la date de fin de période configurée. Elle est vérifiée sur les DEUX couches, la
    fonction du contrôle de l'entrepôt étant appelée pour la sienne.
    """
    from generator import config
    from tests import test_indicateurs_sejour as entrepot

    date_fin = date.fromisoformat(config.valeur("date_fin"))

    conn = entrepot._connexion()
    try:
        max_marts = entrepot._max_jour_admission(conn)
    finally:
        conn.close()

    max_instantane = lecture.interroger("select max(jour_admission) as fin from fct_sejour")["fin"][
        0
    ]

    for couche, mesuree in (
        ("marts.fct_sejour", max_marts),
        ("instantane.fct_sejour", max_instantane),
    ):
        if mesuree != date_fin:
            pytest.skip(
                f"fenêtre chargée partielle : date d'admission maximale de {couche} ({mesuree}) "
                f"!= date de fin de période configurée ({date_fin}) -- les quatre indicateurs, "
                "annualisés sur la période complète, ne sont comparables ni aux valeurs publiées "
                "ni entre eux sur une génération qui ne couvre pas cette période dans son entier"
            )


def _valeurs_publiees() -> dict[str, float]:
    """Les quatre valeurs relevées, lues dans le fichier de configuration qui les porte."""
    contenu = yaml.safe_load(VOLUMETRIE.read_text(encoding="utf-8"))
    return {entree["nom"]: entree["valeur"] for entree in contenu["parametres"]}


def test_les_quatre_indicateurs_affiches_tiennent_aux_valeurs_publiees() -> None:
    """Première référence : extérieure au code, donc impossible à rendre vraie par construction."""
    from tests.test_indicateurs_sejour import TOLERANCE_RELATIVE

    lecture = _lecture()
    _instantane_pret(lecture)
    _fenetre_complete_ou_abstention(lecture)

    obtenues = _sorties_de_la_page(lecture)
    publiees = _valeurs_publiees()

    echecs = []
    for colonne, nom_publie, _, _facteur in CORRESPONDANCE:
        assert nom_publie in publiees, f"{nom_publie} absent de {VOLUMETRIE.name}"
        mesure = obtenues[colonne]
        cible = float(publiees[nom_publie])
        ecart_relatif = abs(mesure - cible) / cible
        if ecart_relatif > TOLERANCE_RELATIVE:
            echecs.append(
                f"{colonne} : affiché {mesure:.4f}, publié {cible}, écart relatif "
                f"{ecart_relatif:.4%}, tolérance {TOLERANCE_RELATIVE:.0%}"
            )

    assert not echecs, "indicateurs affichés hors tolérance des valeurs publiées :\n" + "\n".join(
        echecs
    )


def test_les_quatre_indicateurs_affiches_egalent_l_implementation_de_l_entrepot() -> None:
    """Seconde référence : deux implémentations écrites séparément, dans deux langages.

    La formule n'est pas recopiée — la fonction de l'entrepôt est importée et appelée. Une
    divergence de convention entre l'écran et l'entrepôt fait rougir ceci, et rien d'autre.
    """
    from generator import config
    from tests import test_indicateurs_sejour as entrepot

    lecture = _lecture()
    _instantane_pret(lecture)
    _fenetre_complete_ou_abstention(lecture)

    conn = entrepot._connexion()
    try:
        date_fin = date.fromisoformat(config.valeur("date_fin"))
        date_debut = date.fromisoformat(config.valeur("date_debut"))
        lignes = entrepot._sejours(conn)
    finally:
        conn.close()

    attendues = entrepot.indicateurs_recalcules(lignes, date_fin, (date_fin - date_debut).days + 1)
    obtenues = _sorties_de_la_page(lecture)

    echecs = []
    for colonne, _, nom_entrepot, _facteur in CORRESPONDANCE:
        mesure = obtenues[colonne]
        cible = attendues[nom_entrepot]
        if abs(mesure - cible) > TOLERANCE_ENTRE_IMPLEMENTATIONS:
            echecs.append(
                f"{colonne} ({nom_entrepot}) : la page rend {mesure!r}, la convention de "
                f"l'entrepôt {cible!r}, écart {abs(mesure - cible)!r} au-delà de "
                f"{TOLERANCE_ENTRE_IMPLEMENTATIONS}"
            )

    assert not echecs, "l'écran et l'entrepôt divergent de convention :\n" + "\n".join(echecs)
