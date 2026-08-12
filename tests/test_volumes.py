"""Contrôles bloquants sur la conversion des volumes (generator/volumes.py)."""

from collections import defaultdict

from generator import calendrier, config, temporel, volumes

VOLUME_PROGRAMME = "admissions_annuelles"
VOLUME_PROGRAMME_LARGE = "examens_laboratoire_total"
VOLUME_TAUX = "passages_urgences_par_jour"

ANNEES_PLEINES = (2024, 2025)
ANNEE_PARTIELLE = 2026


def entrees_config() -> dict[str, dict]:
    return {e["nom"]: e for e in config.charger_entrees()}


def test_conservation_exacte_annee_pleine() -> None:
    entrees = entrees_config()
    volume_mesure = entrees[VOLUME_PROGRAMME]["valeur"]
    comptes = volumes.comptes_journaliers(VOLUME_PROGRAMME, entrees=entrees)

    for annee in ANNEES_PLEINES:
        somme = sum(v for d, v in comptes.items() if d.year == annee)
        assert somme == volume_mesure, f"{annee} : somme {somme} != volume mesuré {volume_mesure}"


def test_proratisation_annee_partielle() -> None:
    entrees = entrees_config()
    volume_mesure = entrees[VOLUME_PROGRAMME]["valeur"]
    flux = entrees["correspondance_volume_flux"]["valeur"][VOLUME_PROGRAMME]
    comptes = volumes.comptes_journaliers(VOLUME_PROGRAMME, entrees=entrees)

    rapport = volumes.rapport_annee_partielle(ANNEE_PARTIELLE, flux, entrees)
    cible_independante = round(volume_mesure * rapport)

    somme = sum(v for d, v in comptes.items() if d.year == ANNEE_PARTIELLE)
    assert somme == cible_independante


def test_total_periode_egale_somme_cibles_annuelles() -> None:
    entrees = entrees_config()
    volume_mesure = entrees[VOLUME_PROGRAMME]["valeur"]
    flux = entrees["correspondance_volume_flux"]["valeur"][VOLUME_PROGRAMME]
    comptes = volumes.comptes_journaliers(VOLUME_PROGRAMME, entrees=entrees)

    rapport_2026 = volumes.rapport_annee_partielle(2026, flux, entrees)
    cibles_independantes = {
        2024: round(volume_mesure),
        2025: round(volume_mesure),
        2026: round(volume_mesure * rapport_2026),
    }

    somme_totale = sum(comptes.values())
    somme_cibles = sum(cibles_independantes.values())
    assert somme_totale == somme_cibles

    for annee, cible in cibles_independantes.items():
        somme_annee = sum(v for d, v in comptes.items() if d.year == annee)
        assert somme_annee == cible, f"{annee} : {somme_annee} != cible indépendante {cible}"


def test_positivite_et_jours_fermes() -> None:
    entrees = entrees_config()
    comptes = volumes.comptes_journaliers(VOLUME_PROGRAMME, entrees=entrees)

    assert all(v >= 0 for v in comptes.values())

    for jour, compte in comptes.items():
        if temporel.poids_jour(jour, "programme", entrees) == 0:
            assert compte == 0, f"{jour} : poids nul mais compte {compte}"

    jours_compte_nul = {d for d, v in comptes.items() if v == 0}
    jours_fermes_independants = {d for d in comptes if d.weekday() == 6 or calendrier.est_ferie(d)}
    assert jours_compte_nul == jours_fermes_independants


def test_determinisme() -> None:
    entrees = entrees_config()
    comptes_a = volumes.comptes_journaliers(VOLUME_PROGRAMME, entrees=entrees)
    comptes_b = volumes.comptes_journaliers(VOLUME_PROGRAMME, entrees=entrees)
    assert comptes_a == comptes_b


def test_modulation_ramadan_traverse() -> None:
    entrees = entrees_config()
    coefficient = entrees["effet_ramadan"]["valeur"]["coefficient_programme"]
    comptes = volumes.comptes_journaliers(VOLUME_PROGRAMME_LARGE, entrees=entrees)

    par_jour_semaine_ramadan = defaultdict(list)
    par_jour_semaine_hors = defaultdict(list)
    for jour, compte in comptes.items():
        if calendrier.est_ferie(jour) or jour.month == 8 or jour.weekday() == 6:
            continue
        if calendrier.est_ramadan(jour):
            par_jour_semaine_ramadan[jour.weekday()].append(compte)
        else:
            par_jour_semaine_hors[jour.weekday()].append(compte)

    # Tolérance mesurée : écart maximal observé 0,0017 sur cette même grandeur (rapport de
    # rapport.md). Seuil fixé à 0,005, au-dessus de l'écart mesuré, pas au jugé.
    tolerance = 0.005
    for jour_semaine in range(6):
        valeurs_ramadan = par_jour_semaine_ramadan[jour_semaine]
        valeurs_hors = par_jour_semaine_hors[jour_semaine]
        moyenne_ramadan = sum(valeurs_ramadan) / len(valeurs_ramadan)
        moyenne_hors = sum(valeurs_hors) / len(valeurs_hors)
        ratio = moyenne_ramadan / moyenne_hors
        assert abs(ratio - coefficient) < tolerance, (
            f"jour_semaine={jour_semaine} : ratio {ratio} écarté de {coefficient} au-delà de "
            f"la tolérance"
        )


def test_taux_journalier() -> None:
    entrees = entrees_config()
    taux_configure = entrees[VOLUME_TAUX]["valeur"]
    comptes = volumes.comptes_journaliers(VOLUME_TAUX, entrees=entrees)

    moyenne = sum(comptes.values()) / len(comptes)
    assert abs(moyenne - taux_configure) < 0.5


def test_taux_est_un_argument() -> None:
    entrees = entrees_config()
    comptes_bas = volumes.comptes_journaliers(
        VOLUME_TAUX, taux_urgences_par_jour=14, entrees=entrees
    )
    comptes_haut = volumes.comptes_journaliers(
        VOLUME_TAUX, taux_urgences_par_jour=54, entrees=entrees
    )

    total_bas = sum(comptes_bas.values())
    total_haut = sum(comptes_haut.values())
    ratio_mesure = total_haut / total_bas
    ratio_attendu = 54 / 14
    assert abs(ratio_mesure - ratio_attendu) < 0.01
