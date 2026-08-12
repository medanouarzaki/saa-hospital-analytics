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

# Mesure 1.4 du lot : catégories de laboratoire non nulles sur la période, et le préfixe de
# code d'acte retenu pour chacune (§3). Les trois catégories mesurées à zéro (bactériologie,
# parasitologie, hygiène alimentaire) ne portent aucun préfixe : aucun acte ne doit leur
# correspondre.
PREFIXES_LABORATOIRE_NON_NUL = {"LAB-IS-": 6, "LAB-HT-": 6, "LAB-CB-": 6}
FRAGMENTS_LABORATOIRE_NUL = ["BACT", "PARA", "HYG"]


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

    entrees = entrees_config()
    entrees_avec_colonne_differee = dict(entrees)
    entrees_avec_colonne_differee["colonnes_differees"] = {
        **entrees["colonnes_differees"],
        "valeur": [*entrees["colonnes_differees"]["valeur"], {"table": "source.x", "colonne": "y"}],
    }
    try:
        nomenclatures.nomenclature_colonne("source.x", "y", entrees_avec_colonne_differee)
        raise AssertionError("une colonne différée aurait dû lever une erreur")
    except KeyError as erreur:
        assert "y" in str(erreur)

    try:
        nomenclatures.nomenclature_colonne("source.inconnue", "z", entrees)
        raise AssertionError("une colonne sans nomenclature aurait dû lever une erreur")
    except KeyError as erreur:
        assert "z" in str(erreur)


def test_lettre_cle_existante() -> None:
    entrees = entrees_config()
    lettres_valides = {c["code"] for c in entrees["nomenclature_lettres_cles"]["valeur"]}
    actes = entrees["nomenclature_actes"]["valeur"]
    assert actes
    lettres_utilisees = {acte["lettre_cle"] for acte in actes}

    for acte in actes:
        assert acte["lettre_cle"] in lettres_valides, acte

    orphelines = lettres_valides - lettres_utilisees
    assert lettres_utilisees == lettres_valides, f"orphelines : {orphelines}"


def test_rattachement_acte() -> None:
    entrees = entrees_config()
    codes_activite = set(nomenclatures.codes_nomenclature("nomenclature_activite", entrees))
    codes_service = set(nomenclatures.codes_nomenclature("nomenclature_service", entrees))
    actes = entrees["nomenclature_actes"]["valeur"]
    assert actes

    for acte in actes:
        assert acte["type_rattachement"] in ("activite", "service"), acte
        if acte["type_rattachement"] == "activite":
            assert acte["rattachement"] in codes_activite, acte
        else:
            assert acte["rattachement"] in codes_service, acte


def test_coefficients_et_valeurs_strictement_positifs() -> None:
    entrees = entrees_config()
    for lettre in entrees["nomenclature_lettres_cles"]["valeur"]:
        assert lettre["valeur_unitaire"] > 0, lettre
    for acte in entrees["nomenclature_actes"]["valeur"]:
        assert acte["coefficient"] > 0, acte


def _montant(valeur_lettre: float, coefficient: float, quantite: int) -> float:
    return valeur_lettre * coefficient * quantite


def test_montant_se_calcule() -> None:
    entrees = entrees_config()
    valeurs_lettres = {
        c["code"]: c["valeur_unitaire"] for c in entrees["nomenclature_lettres_cles"]["valeur"]
    }
    actes_par_code = {a["code"]: a for a in entrees["nomenclature_actes"]["valeur"]}

    cas = [
        ("CONS-20", 1),
        ("CONS-30", 2),
        ("LAB-CB-01", 3),
        ("IMG-Z-01", 1),
    ]
    for code_acte, quantite in cas:
        acte = actes_par_code[code_acte]
        valeur_lettre = valeurs_lettres[acte["lettre_cle"]]
        attendu = valeur_lettre * acte["coefficient"] * quantite
        obtenu = _montant(valeur_lettre, acte["coefficient"], quantite)
        assert obtenu == attendu, (code_acte, quantite, obtenu, attendu)
        # la quantité multiplie bien le montant, pas seulement le coefficient
        assert _montant(valeur_lettre, acte["coefficient"], quantite * 2) == attendu * 2


def test_dette_soldee_et_partition() -> None:
    entrees = entrees_config()
    assert entrees["colonnes_differees"]["valeur"] == []

    correspondance = {
        (c["table"], c["colonne"])
        for c in entrees["correspondance_colonnes_nomenclatures"]["valeur"]
    }
    assert ("source.lignes_facture", "code_acte") in correspondance
    assert ("source.lignes_facture", "lettre_cle") in correspondance

    identifiants = {(c["table"], c["colonne"]) for c in entrees["colonnes_identifiants"]["valeur"]}
    differees = {(c["table"], c["colonne"]) for c in entrees["colonnes_differees"]["valeur"]}
    colonnes_registre = {(e["table"], e["colonne"]) for e in colonnes_code_registre()}

    assert identifiants.isdisjoint(differees)
    assert identifiants.isdisjoint(correspondance)
    assert differees.isdisjoint(correspondance)
    assert identifiants | differees | correspondance == colonnes_registre
    assert len(identifiants) + len(differees) + len(correspondance) == len(colonnes_registre)


def test_couverture_laboratoire() -> None:
    entrees = entrees_config()
    codes = [a["code"] for a in entrees["nomenclature_actes"]["valeur"]]

    for prefixe, minimum in PREFIXES_LABORATOIRE_NON_NUL.items():
        n = sum(1 for c in codes if c.startswith(prefixe))
        assert n >= minimum, (prefixe, n, minimum)

    for fragment in FRAGMENTS_LABORATOIRE_NUL:
        assert not any(fragment in c for c in codes), fragment


def test_interdits_couvrent_les_nouvelles_nomenclatures() -> None:
    entrees = entrees_config()

    fabrique = [
        *entrees["nomenclature_actes"]["valeur"],
        {
            "code": "X",
            "libelle": "Chirurgie générale",
            "lettre_cle": "Cs",
            "coefficient": 1,
            "type_rattachement": "service",
            "rattachement": "CE",
        },
    ]
    entrees_positives = dict(entrees)
    entrees_positives["nomenclature_actes"] = {**entrees["nomenclature_actes"], "valeur": fabrique}
    trouve = any(
        any(any(t in couple["libelle"].lower() for t in TERMES_INTERDITS) for couple in e["valeur"])
        for nom, e in entrees_positives.items()
        if nom.startswith("nomenclature_")
    )
    assert trouve, "le contrôle positif fabriqué (Chirurgie générale) n'a pas été détecté"

    for couple in entrees["nomenclature_actes"]["valeur"]:
        libelle_bas = couple["libelle"].lower()
        for terme in TERMES_INTERDITS:
            assert terme not in libelle_bas, (couple["code"], terme)

    for couple in entrees["nomenclature_lettres_cles"]["valeur"]:
        libelle_bas = couple["libelle"].lower()
        for terme in TERMES_INTERDITS:
            assert terme not in libelle_bas, (couple["code"], terme)
