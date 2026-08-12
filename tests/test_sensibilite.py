"""Contrôles bloquants sur le tableau de l'analyse de sensibilité aux trois scénarios de
passages aux urgences (14, 30, 54 passages/jour, `generator/config/volumetrie.yml`).

Le tableau lui-même (`_construire_tableau`) n'est pas un mécanisme de génération : il lit les
manifestes des trois exécutions déjà produites par ce module et les recompose, sans jamais
recopier de valeur constante. Trois exécutions complètes par session pytest (portée module),
partagées entre les tests de ce fichier.
"""

from collections import Counter
from datetime import date, datetime
from datetime import time as dtime

import pytest
import yaml

from generator import config, execution

GRAINE = 1
SCENARIOS = [14, 30, 54]

TOLERANCE_REGLE_10 = 0.03
TOLERANCE_GRANDEURS_ALEATOIRES = 0.05


def _admission(lignes_sejour: list[dict]) -> dict:
    return next(ligne for ligne in lignes_sejour if ligne["date_heure_admission"] is not None)


def _sortie(lignes_sejour: list[dict]):
    for ligne in lignes_sejour:
        if ligne["date_heure_sortie"] is not None:
            return ligne["date_heure_sortie"]
    return None


def _grandeurs_relevees(contexte, entrees: dict) -> dict:
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])
    lignes = contexte.lignes

    lignes_h = [p for p in lignes["source.passages"] if p["type_passage"] == "H"]
    lignes_c = [p for p in lignes["source.passages"] if p["type_passage"] == "C"]
    mesure_sejours = Counter(p["date_heure_entree"].year for p in lignes_h)
    mesure_consultations = Counter(p["date_heure_entree"].year for p in lignes_c)

    groupes: dict[str, list[dict]] = {}
    for ligne in lignes["source.mouvements"]:
        groupes.setdefault(ligne["n_sejour"], []).append(ligne)

    mesure_journees: Counter = Counter()
    for ls in groupes.values():
        adm = _admission(ls)["date_heure_admission"]
        s = _sortie(ls)
        fin = s if s is not None else datetime.combine(date_fin, dtime(23, 59, 59))
        dj = (fin - adm).total_seconds() / 86400
        if adm.year == fin.year:
            mesure_journees[adm.year] += dj
        else:
            fin_annee = date(adm.year, 12, 31)
            jaa = (fin_annee - adm.date()).days + 1
            mesure_journees[adm.year] += min(jaa, dj)
            reste = dj - jaa
            if reste > 0:
                mesure_journees[fin.year] += reste

    lignes_b = [ligne for ligne in lignes["source.lignes_facture"] if ligne["lettre_cle"] == "B"]
    groupes_vus = set()
    mesure_prelevements: Counter = Counter()
    for ligne in lignes_b:
        cle = (ligne["n_facture"], ligne["date_acte"])
        if cle not in groupes_vus:
            groupes_vus.add(cle)
            mesure_prelevements[ligne["date_acte"].year] += 1
    mesure_examens = Counter(ligne["date_acte"].year for ligne in lignes_b)

    return {
        "sejours": dict(mesure_sejours),
        "consultations": dict(mesure_consultations),
        "journees": {a: round(v, 1) for a, v in mesure_journees.items()},
        "prelevements": dict(mesure_prelevements),
        "examens": dict(mesure_examens),
    }


@pytest.fixture(scope="module")
def resultats(tmp_path_factory) -> dict[int, dict]:
    entrees = {e["nom"]: e for e in config.charger_entrees()}
    sortie: dict[int, dict] = {}
    for taux in SCENARIOS:
        racine = tmp_path_factory.mktemp(f"sensibilite_{taux}")
        execu, contexte = execution.executer(
            racine, GRAINE, taux_urgences_par_jour=taux, entrees=entrees
        )
        manifeste_chemin = execu.racine / "manifeste.yml"
        sortie[taux] = {
            "execution": execu,
            "contexte": contexte,
            "manifeste_chemin": manifeste_chemin,
            "HO_derive": contexte.entrees["orientation_urgences"]["valeur"]["HO"],
            "grandeurs": _grandeurs_relevees(contexte, contexte.entrees),
        }
    return sortie


def _construire_tableau(resultats: dict[int, dict]) -> list[dict]:
    # ne recopie aucun decompte : chaque ligne du tableau relit le manifeste ecrit sur
    # disque par l'execution correspondante -- c'est ce qui rend la propriete "produit par
    # les executions, jamais recopie" verifiable par mutation (voir le test dedie).
    lignes = []
    for taux, r in sorted(resultats.items()):
        with r["manifeste_chemin"].open(encoding="utf-8") as f:
            manifeste = yaml.safe_load(f)
        decompte_par_table = manifeste["decompte_lignes"]
        lignes.append(
            {
                "taux": taux,
                "decompte_par_table": decompte_par_table,
                "total": sum(decompte_par_table.values()),
                "HO_derive": r["HO_derive"],
                "grandeurs_relevees": r["grandeurs"],
            }
        )
    return lignes


def test_volumes_urgences_dans_le_meme_rapport_que_les_taux(resultats: dict[int, dict]) -> None:
    tableau = _construire_tableau(resultats)
    for ligne in tableau:
        n_urgences = ligne["decompte_par_table"]["source.passages_urgences"]
        taux = ligne["taux"]
        # ecart a l'arrondi pres : le nombre de passages urgences est pilote par
        # volumes.comptes_journaliers, jamais arrondi a l'unite sur le taux journalier lui
        # meme mais sur l'effectif quotidien -- une tolerance de 1 % couvre cet arrondi.
        rapport_attendu = taux / SCENARIOS[1]
        rapport_mesure = n_urgences / tableau[1]["decompte_par_table"]["source.passages_urgences"]
        assert abs(rapport_mesure - rapport_attendu) / rapport_attendu < 0.01, (
            taux,
            n_urgences,
            rapport_attendu,
            rapport_mesure,
        )


def test_grandeurs_relevees_stables(resultats: dict[int, dict]) -> None:
    tableau = _construire_tableau(resultats)

    for grandeur in ("sejours", "consultations"):
        valeurs_par_annee: dict[int, set] = {}
        for ligne in tableau:
            for annee, valeur in ligne["grandeurs_relevees"][grandeur].items():
                valeurs_par_annee.setdefault(annee, set()).add(valeur)
        for annee, valeurs in valeurs_par_annee.items():
            assert len(valeurs) == 1, (grandeur, annee, valeurs)

    for grandeur in ("journees", "prelevements", "examens"):
        valeurs_par_annee: dict[int, list] = {}
        for ligne in tableau:
            for annee, valeur in ligne["grandeurs_relevees"][grandeur].items():
                valeurs_par_annee.setdefault(annee, []).append(valeur)
        for annee, valeurs in valeurs_par_annee.items():
            mn, mx = min(valeurs), max(valeurs)
            spread = (mx - mn) / ((mx + mn) / 2)
            assert spread < TOLERANCE_GRANDEURS_ALEATOIRES, (grandeur, annee, valeurs, spread)


def test_ho_derive_decroit_et_reste_plausible(resultats: dict[int, dict]) -> None:
    tableau = _construire_tableau(resultats)
    tableau_trie = sorted(tableau, key=lambda ligne: ligne["taux"])

    for precedent, suivant in zip(tableau_trie, tableau_trie[1:], strict=False):
        assert suivant["HO_derive"] < precedent["HO_derive"], (precedent, suivant)

    # les bornes de plausibilite (3 % / 15,3 %) sont documentees dans la note du parametre
    # part_sejours_provenant_urgences (generator/config/urgences.yml) ; reprises ici comme
    # constantes de test car elles ne sont pas elles-memes portees par un parametre nomme.
    for ligne in tableau:
        assert 0.03 <= ligne["HO_derive"] <= 0.153, ligne


def test_regle_10_aux_trois_scenarios(resultats: dict[int, dict]) -> None:
    for taux, r in resultats.items():
        entrees = r["contexte"].entrees
        lignes = r["contexte"].lignes
        lignes_urg = lignes["source.passages_urgences"]
        lignes_mvt = lignes["source.mouvements"]

        date_debut = date.fromisoformat(entrees["date_debut"]["valeur"])
        date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])
        n_jours_periode = (date_fin - date_debut).days + 1

        taux_hospitalisation_urgences = entrees["orientation_urgences"]["valeur"]["HO"]
        sejours_annuels = entrees["admissions_annuelles"]["valeur"]

        passages_annuels_urgences = len(lignes_urg) * 365 / n_jours_periode

        admissions = [ligne for ligne in lignes_mvt if ligne["date_heure_admission"] is not None]
        n_urgence = sum(1 for a in admissions if a["mode_admission"] == "U")
        part_sejours_provenant_urgences = n_urgence / len(admissions)

        membre_gauche = passages_annuels_urgences * taux_hospitalisation_urgences
        membre_droit = sejours_annuels * part_sejours_provenant_urgences

        assert membre_gauche == pytest.approx(membre_droit, rel=TOLERANCE_REGLE_10), (
            taux,
            membre_gauche,
            membre_droit,
        )


def test_tableau_provient_des_manifestes_pas_de_constantes(resultats: dict[int, dict]) -> None:
    tableau_avant = _construire_tableau(resultats)
    taux_cible = SCENARIOS[0]
    chemin = resultats[taux_cible]["manifeste_chemin"]
    sauvegarde = chemin.with_suffix(".yml.bak")
    chemin.rename(sauvegarde)
    try:
        with sauvegarde.open(encoding="utf-8") as f:
            manifeste = yaml.safe_load(f)
        # controle positif : la cle mutee existe bien avant mutation
        assert "source.patients" in manifeste["decompte_lignes"]
        manifeste["decompte_lignes"]["source.patients"] += 999999
        with chemin.open("w", encoding="utf-8") as f:
            yaml.safe_dump(manifeste, f, allow_unicode=True, sort_keys=True)

        tableau_apres = _construire_tableau(resultats)
        ligne_avant = next(x for x in tableau_avant if x["taux"] == taux_cible)
        ligne_apres = next(x for x in tableau_apres if x["taux"] == taux_cible)
        assert ligne_apres["decompte_par_table"]["source.patients"] == (
            ligne_avant["decompte_par_table"]["source.patients"] + 999999
        )
        assert ligne_apres["total"] == ligne_avant["total"] + 999999
    finally:
        chemin.unlink(missing_ok=True)
        sauvegarde.rename(chemin)
