"""Contrôles bloquants sur les nomenclatures (generator/nomenclatures.py)."""

from pathlib import Path

import yaml

from generator import config, nomenclatures

RACINE = Path(__file__).resolve().parent.parent
RELEVE = RACINE / "docs" / "observation" / "releve_champs.yml"
REGISTRE = RACINE / "docs" / "champs" / "registre_champs.yml"

# Table de correspondance établie par la mesure : identifiant de relevé -> colonne du registre.
CORRESPONDANCE_RELEVE = {
    "REL-PAT.D09": ("source.patients", "type_piece_identite"),
    "REL-PAT.D11": ("source.patients", "etat_civil"),
    "REL-PAT.A01": ("source.patients", "compagnie_assurance"),
    "REL-PAT.H07": ("source.patients", "nationalite"),
    "REL-PAT.N05": ("source.patients", "pays_naissance"),
    "REL-RDV.R03": ("source.rendez_vous", "origine"),
    "REL-RDV.R11": ("source.rendez_vous", "etat"),
}

# Colonnes dont la note du registre énumère des valeurs admises (mesure 1.2).
COLONNES_ENUMEREES_AU_REGISTRE = [
    "source.passages.type_passage",
    "source.mouvements.mode_admission",
    "source.mouvements.mode_sortie",
    "source.prises_en_charge.etat",
    "source.factures.type_facture",
    "source.factures.etat",
    "source.passages_urgences.mode_arrivee",
    "source.passages_urgences.orientation_sortie",
    "source.creances.type_debiteur",
    "source.creances.motif_non_recouvrement",
]

TERMES_INTERDITS = ["chirurg", "bactério", "bacterio", "parasito", "hygiène aliment"]


def entrees_config() -> dict[str, dict]:
    return {e["nom"]: e for e in config.charger_entrees()}


def champs_releve() -> dict[str, dict]:
    with RELEVE.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    champs = {}
    for ecran in data["ecrans"]:
        for champ in ecran["champs"]:
            champs[champ["id"]] = champ
    return champs


def colonnes_code_registre() -> list[dict]:
    with REGISTRE.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return [e for e in data if e["type_metier"] == "code"]


def test_bonne_formation() -> None:
    entrees = entrees_config()
    for nom in nomenclatures.noms_nomenclatures(entrees):
        couples = entrees[nom]["valeur"]
        assert couples, f"{nom} : nomenclature vide"

        codes = [c["code"] for c in couples]
        assert len(codes) == len(set(codes)), f"{nom} : codes en double"

        for couple in couples:
            assert isinstance(couple["code"], str), f"{nom} : code non textuel {couple['code']!r}"
            assert couple["code"] != "", f"{nom} : code vide"
            assert couple["libelle"] != "", f"{nom} : libellé vide pour le code {couple['code']!r}"


def test_partition_exhaustive_trois_categories() -> None:
    entrees = entrees_config()
    identifiants = {(c["table"], c["colonne"]) for c in entrees["colonnes_identifiants"]["valeur"]}
    differees = {(c["table"], c["colonne"]) for c in entrees["colonnes_differees"]["valeur"]}
    correspondance = {
        (c["table"], c["colonne"])
        for c in entrees["correspondance_colonnes_nomenclatures"]["valeur"]
    }

    assert identifiants.isdisjoint(differees)
    assert identifiants.isdisjoint(correspondance)
    assert differees.isdisjoint(correspondance)

    colonnes_registre = {(e["table"], e["colonne"]) for e in colonnes_code_registre()}
    union = identifiants | differees | correspondance

    assert union == colonnes_registre
    assert len(identifiants) + len(differees) + len(correspondance) == len(colonnes_code_registre())


def test_dette_se_vide() -> None:
    entrees = entrees_config()
    differees = {(c["table"], c["colonne"]) for c in entrees["colonnes_differees"]["valeur"]}
    correspondance = {
        (c["table"], c["colonne"])
        for c in entrees["correspondance_colonnes_nomenclatures"]["valeur"]
    }
    assert differees.isdisjoint(correspondance)


def test_aucune_nomenclature_orpheline() -> None:
    entrees = entrees_config()
    noms_definis = set(nomenclatures.noms_nomenclatures(entrees))
    noms_cites = {
        c["nomenclature"] for c in entrees["correspondance_colonnes_nomenclatures"]["valeur"]
    }
    assert noms_definis == noms_cites, (
        f"orphelines : {noms_definis - noms_cites} ; citées sans définition : "
        f"{noms_cites - noms_definis}"
    )


def test_ancrage_observation() -> None:
    entrees = entrees_config()
    champs = champs_releve()

    for identifiant, (table, colonne) in CORRESPONDANCE_RELEVE.items():
        valeurs = champs[identifiant]["valeurs_observees"]
        nom_nomenclature = nomenclatures.nomenclature_colonne(table, colonne, entrees)
        couples = entrees[nom_nomenclature]["valeur"]

        if len(valeurs) == 2:
            code, libelle_observe = valeurs
            assert any(c["code"] == code and c["libelle"] == libelle_observe for c in couples), (
                f"{identifiant} : couple {valeurs} absent de {nom_nomenclature}"
            )
        else:
            (libelle_observe,) = valeurs
            assert any(c["libelle"] == libelle_observe for c in couples), (
                f"{identifiant} : libellé {libelle_observe!r} absent de {nom_nomenclature}"
            )


def test_ancrage_registre() -> None:
    entrees = entrees_config()
    with REGISTRE.open(encoding="utf-8") as f:
        registre_donnees = yaml.safe_load(f)
    par_colonne = {(e["table"], e["colonne"]): e for e in registre_donnees}

    for chemin in COLONNES_ENUMEREES_AU_REGISTRE:
        table, colonne = chemin.rsplit(".", 1)
        preuve_registre = par_colonne[(table, colonne)]["preuve"]
        nom_nomenclature = nomenclatures.nomenclature_colonne(table, colonne, entrees)
        preuve_nomenclature = entrees[nom_nomenclature]["preuve"]
        assert preuve_nomenclature == preuve_registre, (
            f"{chemin} : preuve {preuve_nomenclature!r} != registre {preuve_registre!r}"
        )


def test_interdits_mesures() -> None:
    entrees = entrees_config()

    fabrique = [
        *entrees["nomenclature_activite"]["valeur"],
        {"code": "X", "libelle": "Chirurgie test"},
    ]
    entrees_positives = dict(entrees)
    entrees_positives["nomenclature_activite"] = {
        **entrees["nomenclature_activite"],
        "valeur": fabrique,
    }
    trouve = any(
        any(any(t in couple["libelle"].lower() for t in TERMES_INTERDITS) for couple in e["valeur"])
        for nom, e in entrees_positives.items()
        if nom.startswith("nomenclature_")
    )
    assert trouve, "le contrôle positif fabriqué n'a pas été détecté"

    for nom in nomenclatures.noms_nomenclatures(entrees):
        for couple in entrees[nom]["valeur"]:
            libelle_bas = couple["libelle"].lower()
            for terme in TERMES_INTERDITS:
                assert terme not in libelle_bas, (
                    f"{nom} : libellé interdit {couple['libelle']!r} contient {terme!r}"
                )


def test_erreurs_nommees() -> None:
    try:
        nomenclatures.codes_nomenclature("nomenclature_inexistante")
        raise AssertionError("une nomenclature inconnue aurait dû lever une erreur")
    except KeyError as erreur:
        assert "nomenclature_inexistante" in str(erreur)

    try:
        nomenclatures.libelle("nomenclature_sexe", "ZZ")
        raise AssertionError("un code absent aurait dû lever une erreur")
    except KeyError as erreur:
        assert "ZZ" in str(erreur)

    try:
        nomenclatures.nomenclature_colonne("source.lignes_facture", "code_acte")
        raise AssertionError("une colonne différée aurait dû lever une erreur")
    except KeyError as erreur:
        assert "code_acte" in str(erreur)
