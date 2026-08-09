"""Contrôles bloquants sur le moteur temporel (generator/temporel.py)."""

from datetime import date, timedelta

from generator import alea, calendrier, config, temporel


def entrees_par_nom() -> dict[str, dict]:
    return {e["nom"]: e for e in config.charger_entrees()}


def periode_generation(entrees: dict[str, dict]) -> tuple[date, date]:
    return (
        date.fromisoformat(entrees["date_debut"]["valeur"]),
        date.fromisoformat(entrees["date_fin"]["valeur"]),
    )


def iterer_jours(debut: date, fin: date) -> list[date]:
    jours = []
    jour = debut
    while jour <= fin:
        jours.append(jour)
        jour += timedelta(days=1)
    return jours


def test_normalisation_profils_horaires_base() -> None:
    entrees = entrees_par_nom()
    profil = entrees["profil_horaire"]["valeur"]
    programme = profil["programme"]
    urgences = profil["urgences"]

    assert len(programme) == 24
    assert len(urgences) == 24
    assert abs(sum(programme) - 1.0) < 1e-9
    assert abs(sum(urgences) - 1.0) < 1e-9

    heures_positives_programme = {h for h, v in enumerate(programme) if v > 0}
    heures_nulles_programme = set(range(24)) - heures_positives_programme
    assert heures_nulles_programme, "le profil programme devrait comporter des heures nulles"
    assert set(profil["fenetre_pic_programme"]) <= heures_positives_programme
    assert set(profil["fenetre_apres_creux_programme"]) <= heures_positives_programme

    assert all(v > 0 for v in urgences), "le profil urgences doit être strictement positif"


def test_forme_profil_programme() -> None:
    entrees = entrees_par_nom()
    profil = entrees["profil_horaire"]["valeur"]
    programme = profil["programme"]

    masse_pic = sum(programme[h] for h in profil["fenetre_pic_programme"])
    masse_apres_creux = sum(programme[h] for h in profil["fenetre_apres_creux_programme"])
    assert masse_pic > masse_apres_creux


def test_multiplicativite_ferie_et_aout() -> None:
    entrees = entrees_par_nom()
    debut, fin = periode_generation(entrees)
    jour = next(j for j in iterer_jours(debut, fin) if calendrier.est_ferie(j) and j.month == 8)
    assert not calendrier.est_ramadan(jour)

    poids_mesure = temporel.poids_jour(jour, "programme", entrees)

    facteur_semaine = entrees["profil_hebdomadaire"]["valeur"]["programme"][jour.weekday()]
    facteur_ferie = entrees["effet_calendaire"]["valeur"]["coefficient_ferie_programme"]
    facteur_aout = entrees["effet_calendaire"]["valeur"]["coefficient_aout_programme"]

    assert poids_mesure == facteur_semaine * facteur_ferie * facteur_aout


def test_conservation_totale_repartition() -> None:
    entrees = entrees_par_nom()
    debut, fin = periode_generation(entrees)
    jours = iterer_jours(debut, fin)

    for total in (0, 3, 100, 10_000, 1_000_000):
        repartition = temporel.repartir_total(total, jours, "programme")
        assert sum(repartition.values()) == total
        assert all(v >= 0 for v in repartition.values())


def test_jours_fermes_egale_dimanches_ou_feries() -> None:
    entrees = entrees_par_nom()
    debut, fin = periode_generation(entrees)
    jours = iterer_jours(debut, fin)

    fermes_mesures = sum(1 for j in jours if temporel.poids_jour(j, "programme", entrees) == 0)
    fermes_independants = sum(1 for j in jours if j.weekday() == 6 or calendrier.est_ferie(j))

    assert fermes_mesures == fermes_independants


def test_urgences_ne_ferment_jamais() -> None:
    entrees = entrees_par_nom()
    debut, fin = periode_generation(entrees)
    jours = iterer_jours(debut, fin)

    for jour in jours:
        assert temporel.poids_jour(jour, "urgences", entrees) > 0

    repartition = temporel.repartir_total(len(jours) * 10, jours, "urgences")
    assert all(v >= 1 for v in repartition.values())


def test_amplitude_effet_ramadan() -> None:
    entrees = entrees_par_nom()
    debut, fin = periode_generation(entrees)
    jours = iterer_jours(debut, fin)

    candidats_ramadan = [
        j
        for j in jours
        if calendrier.est_ramadan(j) and not calendrier.est_ferie(j) and j.month != 8
    ]
    candidats_hors = [
        j
        for j in jours
        if not calendrier.est_ramadan(j) and not calendrier.est_ferie(j) and j.month != 8
    ]
    jour_ramadan, jour_hors = next(
        (jr, jh)
        for jr in candidats_ramadan
        for jh in candidats_hors
        if jh.weekday() == jr.weekday()
    )

    poids_ramadan = temporel.poids_jour(jour_ramadan, "programme", entrees)
    poids_hors = temporel.poids_jour(jour_hors, "programme", entrees)
    coefficient = entrees["effet_ramadan"]["valeur"]["coefficient_programme"]

    assert abs(poids_ramadan / poids_hors - coefficient) < 1e-9


def test_decalage_horaire_ramadan() -> None:
    entrees = entrees_par_nom()
    debut, fin = periode_generation(entrees)
    jour_ramadan = next(j for j in iterer_jours(debut, fin) if calendrier.est_ramadan(j))

    base = entrees["profil_horaire"]["valeur"]["programme"]
    decalage = entrees["effet_ramadan"]["valeur"]["decalage_heures_programme"]

    profil_module = temporel.profil_horaire_applicable(jour_ramadan, "programme", entrees)
    profil_attendu = [base[(heure - decalage) % 24] for heure in range(24)]

    assert profil_module == profil_attendu


def test_report_post_rupture_urgences() -> None:
    entrees = entrees_par_nom()
    debut, fin = periode_generation(entrees)
    jour_ramadan = next(j for j in iterer_jours(debut, fin) if calendrier.est_ramadan(j))

    base = entrees["profil_horaire"]["valeur"]["urgences"]
    ramadan = entrees["effet_ramadan"]["valeur"]
    heure_rupture = ramadan["heure_rupture_jeune"]
    duree = ramadan["duree_report_heures"]
    heures_fenetre = [(heure_rupture + decalage) % 24 for decalage in range(duree)]

    profil_ramadan = temporel.profil_horaire_applicable(jour_ramadan, "urgences", entrees)
    part_ramadan = sum(profil_ramadan[h] for h in heures_fenetre)
    part_hors_ramadan = sum(base[h] for h in heures_fenetre)

    assert part_ramadan > part_hors_ramadan
    assert abs(sum(profil_ramadan) - 1.0) < 1e-9


def test_determinisme_tirage() -> None:
    jour = date(2025, 6, 2)

    generateur_a = alea.construire_generateur(123)
    generateur_b = alea.construire_generateur(123)
    suite_a = [temporel.tirer_horodatage(jour, "programme", generateur_a) for _ in range(20)]
    suite_b = [temporel.tirer_horodatage(jour, "programme", generateur_b) for _ in range(20)]
    assert suite_a == suite_b

    generateur_c = alea.construire_generateur(456)
    suite_c = [temporel.tirer_horodatage(jour, "programme", generateur_c) for _ in range(20)]
    assert suite_a != suite_c
