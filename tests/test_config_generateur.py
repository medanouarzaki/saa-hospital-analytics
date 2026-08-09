"""Contrôles bloquants sur la configuration du générateur (generator/config/)."""

from datetime import date
from pathlib import Path

import yaml

from generator import config

RACINE = Path(__file__).resolve().parent.parent
SOURCES = RACINE / "docs" / "sources" / "sources.yml"
RELATIONS = RACINE / "docs" / "relations_injectees.yml"

PROVENANCES_AUTORISEES = {"OBS", "DOC", "HYP"}


def charger_sources() -> dict[str, dict]:
    with SOURCES.open(encoding="utf-8") as f:
        donnees = yaml.safe_load(f)
    return {s["id"]: s for s in donnees}


def charger_relations() -> list[dict]:
    with RELATIONS.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def par_nom() -> dict[str, dict]:
    return {e["nom"]: e for e in config.charger_entrees()}


def test_chargement_et_schema() -> None:
    entrees = config.charger_entrees()
    sources = charger_sources()

    noms = [e["nom"] for e in entrees]
    doublons = {n for n in noms if noms.count(n) > 1}
    assert not doublons, f"noms de paramètre en double : {doublons}"

    for e in entrees:
        for cle in config.CLES_OBLIGATOIRES:
            assert cle in e, f"{e.get('nom', '?')} : clé manquante '{cle}'"
        assert e["provenance"] in PROVENANCES_AUTORISEES, (
            f"{e['nom']} : provenance '{e['provenance']}' hors ensemble autorisé"
        )
        if e["provenance"] == "DOC":
            assert e["preuve"] in sources, (
                f"{e['nom']} : preuve DOC '{e['preuve']}' absente du registre des sources"
            )


def test_valeur_fausse_mais_legitime(tmp_path: Path) -> None:
    dossier = tmp_path / "config"
    dossier.mkdir()

    (dossier / "valide.yml").write_text(
        yaml.safe_dump(
            {
                "parametres": [
                    {
                        "nom": "grandeur_nulle",
                        "valeur": 0,
                        "unite": "unités",
                        "provenance": "DOC",
                        "preuve": "S-30",
                        "note": "Zéro imprimé dans la source, une mesure légitime.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    entrees = config.charger_entrees(dossier)
    assert entrees[0]["valeur"] == 0

    (dossier / "invalide.yml").write_text(
        yaml.safe_dump(
            {
                "parametres": [
                    {
                        "nom": "grandeur_sans_valeur",
                        "unite": "unités",
                        "provenance": "HYP",
                        "preuve": "sans_preuve_externe",
                        "note": "Clé valeur absente, doit échouer.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    config.vider_cache()
    try:
        config.charger_entrees(dossier)
        raise AssertionError("une entrée sans clé 'valeur' aurait dû être rejetée")
    except ValueError:
        pass


def test_periode() -> None:
    entrees = par_nom()
    debut = date.fromisoformat(entrees["date_debut"]["valeur"])
    fin = date.fromisoformat(entrees["date_fin"]["valeur"])
    jours_calcules = (fin - debut).days + 1
    assert jours_calcules == entrees["nombre_jours_periode"]["valeur"]


def test_indicateurs_sejour_se_reconstituent() -> None:
    entrees = par_nom()
    capacite = entrees["capacite_litiere_fonctionnelle"]["valeur"]
    journees = entrees["journees_hospitalisation"]["valeur"]
    admissions = entrees["admissions_annuelles"]["valeur"]
    jours_an = entrees["jours_annee_reference"]["valeur"]

    tom = journees / (capacite * jours_an) * 100
    dms = journees / admissions
    trot = admissions / capacite
    irot = (capacite * jours_an - journees) / admissions

    tolerance = 0.05
    assert abs(tom - entrees["tom_publie"]["valeur"]) < tolerance
    assert abs(dms - entrees["dms_publie"]["valeur"]) < tolerance
    assert abs(trot - entrees["trot_publie"]["valeur"]) < tolerance
    assert abs(irot - entrees["irot_publie"]["valeur"]) < tolerance


def test_consultations() -> None:
    entrees = par_nom()
    consultations = entrees["consultations_specialisees_externes"]["valeur"]
    medecins = entrees["medecins_consultations_specialisees"]["valeur"]
    calcule = consultations / medecins
    publie = entrees["consultations_par_medecin_publie"]["valeur"]
    assert abs(calcule - publie) < 0.5


def test_laboratoire() -> None:
    entrees = par_nom()
    categories = [
        "examens_bacteriologie",
        "examens_parasitologie",
        "examens_immuno_serologie",
        "examens_hematologie_transfusion",
        "examens_hygiene_alimentaire",
        "examens_chimie_biologie",
    ]
    somme = sum(entrees[c]["valeur"] for c in categories)
    assert somme == entrees["examens_laboratoire_total"]["valeur"]

    total = entrees["examens_laboratoire_total"]["valeur"]
    prelevements = entrees["prelevements_laboratoire"]["valeur"]
    ratio_calcule = total / prelevements
    assert abs(ratio_calcule - entrees["ratio_examens_par_prelevement"]["valeur"]) < 0.01


def test_scenarios_urgences() -> None:
    entrees = par_nom()
    scenarios = entrees["scenarios_passages_urgences"]["valeur"]
    retenu = entrees["passages_urgences_par_jour"]["valeur"]
    assert retenu in scenarios
    assert scenarios == sorted(scenarios)
    assert len(scenarios) == len(set(scenarios)), "la liste doit être strictement croissante"


def test_nom_parametre_impose() -> None:
    relations = charger_relations()
    relation_r19 = next(r for r in relations if r["id"] == "R-19")
    nom_impose = relation_r19["parametre"]

    entrees = par_nom()
    assert nom_impose in entrees, (
        f"le paramètre '{nom_impose}', imposé par la relation R-19, est absent de la configuration"
    )
