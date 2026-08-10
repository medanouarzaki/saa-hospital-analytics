"""Contrôles propres à la table des passages aux urgences (generator/urgences.py).

Ne porte que ce que tests/test_invariants_tables.py ne couvre pas déjà génériquement : la
bijection avec les passages de type urgence, la répartition des niveaux de tri, le délai et
le taux de respect de la cible par niveau, le modulateur d'origine, la cohérence
inter-tables avec les admissions de mode urgence, l'ordre des horodatages, l'effet du
Ramadan et l'absence de toute orientation chirurgicale. Consomme la génération partagée de
tests/conftest.py.
"""

import re
import statistics
from collections import Counter

import pytest

from generator import calendrier, nomenclatures

TABLE = "source.passages_urgences"


@pytest.fixture(scope="module")
def generation(generation_partagee: dict) -> dict:
    return generation_partagee


def test_bijection_avec_passages_urgence(generation: dict) -> None:
    lignes_urg = generation["lignes"][TABLE]
    lignes_passages = generation["lignes"]["source.passages"]
    lignes_u = [ligne for ligne in lignes_passages if ligne["type_passage"] == "U"]

    assert len(lignes_urg) == len(lignes_u)

    n_passages_urg = {ligne["n_passage"] for ligne in lignes_urg}
    n_passages_u = {ligne["n_passage"] for ligne in lignes_u}
    assert n_passages_urg == n_passages_u


def test_repartition_niveaux_tri(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_urg = generation["lignes"][TABLE]

    cible = entrees["repartition_niveaux_tri"]["valeur"]
    total = len(lignes_urg)
    mesure = Counter(ligne["niveau_tri"] for ligne in lignes_urg)

    # tolerance mesuree sur 3 graines independantes : ecart maximal observe 0,0028
    TOLERANCE = 0.01
    for niveau, part_attendue in cible.items():
        part_mesuree = mesure[niveau] / total
        assert abs(part_mesuree - part_attendue) < TOLERANCE, (niveau, part_attendue, part_mesuree)


def test_delai_median_par_niveau_et_ordre(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_urg = generation["lignes"][TABLE]

    cible = entrees["delai_pec_par_niveau"]["valeur"]

    # tolerance mesuree sur 3 graines independantes : ecart maximal observe 82,7 minutes
    # (niveau 5, la cible la plus elevee, 240 minutes) - relatif a la cible ci-dessous
    TOLERANCE_RELATIVE = 0.4
    medianes: dict[str, float] = {}
    for niveau, cible_minutes in cible.items():
        delais = [
            (ligne["date_heure_pec_medicale"] - ligne["date_heure_arrivee"]).total_seconds() / 60
            for ligne in lignes_urg
            if ligne["niveau_tri"] == niveau
        ]
        assert len(delais) > 0
        mediane = statistics.median(delais)
        medianes[niveau] = mediane
        assert abs(mediane - cible_minutes) / cible_minutes < TOLERANCE_RELATIVE, (
            niveau,
            cible_minutes,
            mediane,
        )

    niveaux_ordonnes = sorted(medianes, key=int)
    for precedent, suivant in zip(niveaux_ordonnes, niveaux_ordonnes[1:], strict=False):
        assert medianes[precedent] < medianes[suivant], (precedent, suivant, medianes)


def test_taux_respect_cible(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_urg = generation["lignes"][TABLE]

    cible_delai = entrees["delai_pec_par_niveau"]["valeur"]
    taux_attendu = entrees["taux_respect_cible"]["valeur"]

    # tolerance mesuree sur 3 graines independantes : ecart maximal observe 0,023 (par
    # niveau), 0,0065 (global)
    TOLERANCE = 0.05

    def respecte(ligne: dict) -> bool:
        ecart = ligne["date_heure_pec_medicale"] - ligne["date_heure_arrivee"]
        delai = ecart.total_seconds() / 60
        return delai <= cible_delai[ligne["niveau_tri"]]

    n_respect_global = sum(1 for ligne in lignes_urg if respecte(ligne))
    taux_global = n_respect_global / len(lignes_urg)
    assert abs(taux_global - taux_attendu) < TOLERANCE, (taux_global, taux_attendu)

    for niveau in cible_delai:
        lignes_niveau = [ligne for ligne in lignes_urg if ligne["niveau_tri"] == niveau]
        n_respect = sum(1 for ligne in lignes_niveau if respecte(ligne))
        taux = n_respect / len(lignes_niveau)
        assert abs(taux - taux_attendu) < TOLERANCE, (niveau, taux, taux_attendu)


def test_modulateur_origine_ordre_et_total(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_urg = generation["lignes"][TABLE]

    cible = entrees["repartition_niveaux_tri"]["valeur"]
    total = len(lignes_urg)

    smur = [ligne for ligne in lignes_urg if ligne["mode_arrivee"] == "SMUR"]
    non_smur = [ligne for ligne in lignes_urg if ligne["mode_arrivee"] != "SMUR"]
    assert smur and non_smur

    mesure_smur = Counter(ligne["niveau_tri"] for ligne in smur)
    mesure_non_smur = Counter(ligne["niveau_tri"] for ligne in non_smur)

    # assertion d'ordre : les niveaux les plus graves (1, 2) sont surrepresentes parmi les
    # arrivees SMUR par rapport aux arrivees non-SMUR.
    for niveau in ("1", "2"):
        part_smur = mesure_smur[niveau] / len(smur)
        part_non_smur = mesure_non_smur[niveau] / len(non_smur)
        assert part_smur > part_non_smur, (niveau, part_smur, part_non_smur)

    # le modulateur redistribue, il ne deplace pas le total : la repartition globale reste
    # celle du parametre.
    TOLERANCE = 0.01
    mesure_globale = Counter(ligne["niveau_tri"] for ligne in lignes_urg)
    for niveau, part_attendue in cible.items():
        part_mesuree = mesure_globale[niveau] / total
        assert abs(part_mesuree - part_attendue) < TOLERANCE, (niveau, part_attendue, part_mesuree)


def test_coherence_orientation_hospitalisation_admissions_urgence(generation: dict) -> None:
    lignes_urg = generation["lignes"][TABLE]
    lignes_mvt = generation["lignes"]["source.mouvements"]

    n_ho = sum(1 for ligne in lignes_urg if ligne["orientation_sortie"] == "HO")
    admissions = [ligne for ligne in lignes_mvt if ligne["date_heure_admission"] is not None]
    n_u = sum(1 for ligne in admissions if ligne["mode_admission"] == "U")

    assert n_ho > 0 and n_u > 0

    # premiere regle de cohérence inter-tables du bloc : egalite entre deux calculs
    # independants (nombre de passages aux urgences orientes vers l'hospitalisation,
    # nombre d'admissions de mode urgence aux mouvements), pas une comparaison a une
    # valeur litterale. Tolerance mesuree sur 3 graines independantes : ecart relatif
    # maximal observe 3,48 %.
    TOLERANCE_RELATIVE = 0.1
    assert abs(n_u - n_ho) / n_ho < TOLERANCE_RELATIVE, (n_u, n_ho)


def test_ordre_des_horodatages(generation: dict) -> None:
    lignes_urg = generation["lignes"][TABLE]

    assert lignes_urg, "aucune ligne à contrôler"
    for ligne in lignes_urg:
        assert ligne["date_heure_arrivee"] < ligne["date_heure_pec_medicale"], ligne
        assert ligne["date_heure_pec_medicale"] < ligne["date_heure_sortie"], ligne


def test_duree_presence_par_orientation(generation: dict) -> None:
    # seuil mesuré : sur une exécution de mesure, la plus petite durée minimale par
    # orientation était de 11,37 minutes (sortie contre avis) ; 5 minutes reste en deçà de
    # toute mesure mais exclut la reprise de l'ancien artefact (sortie une seconde après la
    # prise en charge, mesuré à 22 % des lignes avant correction).
    SEUIL_MINUTES = 5

    lignes_urg = generation["lignes"][TABLE]
    by_orientation: dict[str, list[float]] = {}
    for ligne in lignes_urg:
        duree = (ligne["date_heure_sortie"] - ligne["date_heure_arrivee"]).total_seconds() / 60
        by_orientation.setdefault(ligne["orientation_sortie"], []).append(duree)

    assert by_orientation
    for orientation, valeurs in by_orientation.items():
        assert min(valeurs) > SEUIL_MINUTES, (orientation, min(valeurs))

    mediane_tr = statistics.median(by_orientation["TR"])
    mediane_rd = statistics.median(by_orientation["RD"])
    assert mediane_tr > mediane_rd, (mediane_tr, mediane_rd)


def test_effet_ramadan_sur_les_arrivees(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_urg = generation["lignes"][TABLE]

    heure_rupture = entrees["effet_ramadan"]["valeur"]["heure_rupture_jeune"]
    duree_report = entrees["effet_ramadan"]["valeur"]["duree_report_heures"]
    fenetre = {(heure_rupture + decalage) % 24 for decalage in range(duree_report)}

    def en_ramadan(ligne: dict) -> bool:
        return calendrier.est_ramadan(ligne["date_heure_arrivee"].date())

    ramadan = [ligne for ligne in lignes_urg if en_ramadan(ligne)]
    hors_ramadan = [ligne for ligne in lignes_urg if not en_ramadan(ligne)]
    assert ramadan and hors_ramadan

    part_ramadan = sum(1 for ligne in ramadan if ligne["date_heure_arrivee"].hour in fenetre) / len(
        ramadan
    )
    part_hors_ramadan = sum(
        1 for ligne in hors_ramadan if ligne["date_heure_arrivee"].hour in fenetre
    ) / len(hors_ramadan)

    assert part_ramadan > part_hors_ramadan, (part_ramadan, part_hors_ramadan)


def test_aucune_orientation_chirurgicale(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_urg = generation["lignes"][TABLE]

    motif = re.compile(r"chirurg", re.IGNORECASE)
    assert motif.search("Chirurgie générale"), "le motif ne detecte pas son propre cas positif"

    valeurs = {ligne["service_orientation"] for ligne in lignes_urg if ligne["service_orientation"]}
    assert valeurs, "aucune orientation de service observee a controler"
    for code in valeurs:
        libelle = nomenclatures.libelle("nomenclature_service", code, entrees)
        assert not motif.search(libelle), (code, libelle)
