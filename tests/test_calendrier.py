"""Contrôles bloquants sur le calendrier marocain (generator/config/calendrier.yml)."""

import importlib.util
from datetime import date, timedelta
from pathlib import Path

from generator import calendrier, config

RACINE = Path(__file__).resolve().parent.parent

ANNEES = (2024, 2025, 2026)
GRANDEURS_MOBILES = ("ramadan_debut", "ramadan_fin", "aid_al_fitr", "aid_al_adha")


def charger_module(chemin: Path):
    spec = importlib.util.spec_from_file_location(chemin.stem, chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def entrees_par_nom() -> dict[str, dict]:
    return {e["nom"]: e for e in config.charger_entrees()}


def dates_mobiles(entrees: dict[str, dict]) -> dict[int, dict[str, date]]:
    return {
        annee: {
            grandeur: date.fromisoformat(entrees[f"{grandeur}_{annee}"]["valeur"])
            for grandeur in GRANDEURS_MOBILES
        }
        for annee in ANNEES
    }


def feries_fixes_annee(entrees: dict[str, dict], annee: int) -> list[date]:
    premiere_annee_wahda = entrees["aid_al_wahda_premiere_annee"]["valeur"]
    resultat = []
    for nom, entree in entrees.items():
        if not nom.startswith("ferie_fixe_"):
            continue
        if nom == "ferie_fixe_aid_al_wahda" and annee < premiere_annee_wahda:
            continue
        mois, jour = (int(partie) for partie in entree["valeur"].split("-"))
        resultat.append(date(annee, mois, jour))
    return resultat


def feries_mobiles_annee(
    entrees: dict[str, dict], mobiles: dict[int, dict[str, date]], annee: int
) -> list[date]:
    duree = entrees["duree_aid_jours"]["valeur"]
    resultat = []
    for grandeur in ("aid_al_fitr", "aid_al_adha"):
        debut = mobiles[annee][grandeur]
        for decalage in range(duree):
            resultat.append(debut + timedelta(days=decalage))
    return resultat


def test_ajout_calendrier_augmente_le_chargement_generique(tmp_path: Path) -> None:
    dossier_sans_calendrier = tmp_path / "config"
    dossier_sans_calendrier.mkdir()
    for nom_fichier in ("periode.yml", "volumetrie.yml"):
        source = config.DOSSIER_CONFIG / nom_fichier
        (dossier_sans_calendrier / nom_fichier).write_text(
            source.read_text(encoding="utf-8"), encoding="utf-8"
        )

    avant = len(config.charger_entrees(dossier_sans_calendrier))
    apres = len(config.charger_entrees())
    print(f"entrées avant calendrier.yml : {avant} — après : {apres}")
    assert apres > avant


def test_dates_mobiles_valides_et_couverture() -> None:
    entrees = entrees_par_nom()
    for annee in ANNEES:
        for grandeur in GRANDEURS_MOBILES:
            nom = f"{grandeur}_{annee}"
            assert nom in entrees, f"paramètre manquant : {nom}"
            date.fromisoformat(entrees[nom]["valeur"])


def test_invariants_calendrier_lunaire() -> None:
    entrees = entrees_par_nom()
    mobiles = dates_mobiles(entrees)

    durees = {a: (mobiles[a]["ramadan_fin"] - mobiles[a]["ramadan_debut"]).days + 1 for a in ANNEES}
    for annee, duree in durees.items():
        assert duree in (29, 30), f"{annee} : durée de Ramadan hors plage : {duree}"

    ecarts_fitr = {a: (mobiles[a]["aid_al_fitr"] - mobiles[a]["ramadan_fin"]).days for a in ANNEES}
    for annee, ecart in ecarts_fitr.items():
        assert ecart == 1, f"{annee} : Aïd al-Fitr ne suit pas immédiatement la fin du Ramadan"

    ecarts_adha = {a: (mobiles[a]["aid_al_adha"] - mobiles[a]["aid_al_fitr"]).days for a in ANNEES}
    assert len(set(ecarts_adha.values())) == 1, f"écarts Fitr->Adha non égaux : {ecarts_adha}"

    couples = list(zip(ANNEES, ANNEES[1:], strict=False))
    decalages = {
        (a1, a2): (mobiles[a2]["ramadan_debut"] - mobiles[a1]["ramadan_debut"]).days
        for a1, a2 in couples
    }
    assert len(set(decalages.values())) == 1, f"décalages annuels non égaux : {decalages}"


def test_duree_aid_dans_jours_feries() -> None:
    entrees = entrees_par_nom()
    duree = entrees["duree_aid_jours"]["valeur"]
    mobiles = dates_mobiles(entrees)

    for annee in ANNEES:
        feries = calendrier.jours_feries(annee)
        for grandeur in ("aid_al_fitr", "aid_al_adha"):
            debut = mobiles[annee][grandeur]
            for decalage in range(duree):
                jour = debut + timedelta(days=decalage)
                assert jour in feries, f"{annee} {grandeur} jour {decalage} absent des fériés"


def test_application_differee_ferie_31_octobre() -> None:
    entrees = entrees_par_nom()
    premiere_annee = entrees["aid_al_wahda_premiere_annee"]["valeur"]

    for annee in ANNEES:
        feries = calendrier.jours_feries(annee)
        present = date(annee, 10, 31) in feries
        if annee < premiere_annee:
            assert not present, f"{annee} : le 31 octobre ne devrait pas être férié"
        else:
            assert present, f"{annee} : le 31 octobre devrait être férié"


def test_collisions_feries_fixes_et_mobiles() -> None:
    entrees = entrees_par_nom()
    mobiles = dates_mobiles(entrees)

    for annee in ANNEES:
        fixes = feries_fixes_annee(entrees, annee)
        mobiles_annee = feries_mobiles_annee(entrees, mobiles, annee)
        collisions = len(set(fixes) & set(mobiles_annee))
        print(f"{annee} : collisions={collisions}")

        cardinal_mesure = len(calendrier.jours_feries(annee))
        cardinal_attendu = len(fixes) + len(mobiles_annee) - collisions
        assert cardinal_mesure == cardinal_attendu


def test_predicat_ramadan_sur_periode() -> None:
    entrees = entrees_par_nom()
    debut_periode = date.fromisoformat(entrees["date_debut"]["valeur"])
    fin_periode = date.fromisoformat(entrees["date_fin"]["valeur"])
    mobiles = dates_mobiles(entrees)

    jours_ramadan_mesures = 0
    jour = debut_periode
    while jour <= fin_periode:
        if calendrier.est_ramadan(jour):
            jours_ramadan_mesures += 1
        jour += timedelta(days=1)

    total_independant = 0
    for annee in ANNEES:
        debut_intersect = max(mobiles[annee]["ramadan_debut"], debut_periode)
        fin_intersect = min(mobiles[annee]["ramadan_fin"], fin_periode)
        if debut_intersect <= fin_intersect:
            total_independant += (fin_intersect - debut_intersect).days + 1

    assert jours_ramadan_mesures == total_independant


def test_seed_calendrier_synchronise_avec_la_source(tmp_path: Path) -> None:
    generer_seed_calendrier = charger_module(
        RACINE / "docs" / "calendrier" / "generer_seed_calendrier.py"
    )

    generer_seed_calendrier.generer(tmp_path)

    committe = RACINE / "dbt" / "seeds" / "calendrier_marocain.csv"
    genere = tmp_path / "dbt" / "seeds" / "calendrier_marocain.csv"

    assert genere.exists(), f"{genere} : non régénéré"
    assert committe.read_bytes() == genere.read_bytes(), (
        f"{committe} : divergent de la régénération depuis generator/config/calendrier.yml"
    )


def test_rang_jour_ramadan() -> None:
    entrees = entrees_par_nom()
    mobiles = dates_mobiles(entrees)

    for annee in ANNEES:
        debut = mobiles[annee]["ramadan_debut"]
        fin = mobiles[annee]["ramadan_fin"]
        duree = (fin - debut).days + 1

        assert calendrier.rang_ramadan(debut) == 1
        assert calendrier.rang_ramadan(fin) == duree
        assert calendrier.rang_ramadan(debut - timedelta(days=1)) is None
        assert calendrier.rang_ramadan(fin + timedelta(days=1)) is None
