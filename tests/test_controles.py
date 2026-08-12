"""Contrôles sur `ingestion/controles.py`, sur cas fabriqués — aucune base de données.

Chaque famille de contrôle est vérifiée en attrapant un cas fabriqué et en laissant passer
un cas conforme, jamais l'un sans l'autre : un contrôle silencieux sur toutes les entrées ne
prouve rien sur ce qu'il est censé attraper.
"""

from ingestion import controles


def test_date_invalide_rejetee_et_valide_acceptee() -> None:
    assert controles.controler_ligne("patients", {"date_naissance": "13/45/2024"}) == [
        "typage_date:date_naissance:13/45/2024"
    ]
    assert controles.controler_ligne("patients", {"date_naissance": "01/01/1990"}) == []


def test_horodatage_invalide_rejete_et_valide_accepte() -> None:
    assert controles.controler_ligne(
        "rendez_vous", {"date_rendez_vous": "01/01/2024 25:00:00 XM"}
    ) == ["typage_horodatage:date_rendez_vous:01/01/2024 25:00:00 XM"]
    assert (
        controles.controler_ligne("rendez_vous", {"date_rendez_vous": "01/01/2024 10:00:00 AM"})
        == []
    )


def test_sentinel_rendez_vous_rejete_par_la_seule_plage_basse() -> None:
    motifs = controles.controler_ligne(
        "rendez_vous", {"date_rendez_vous": "01/01/1900 09:00:00 AM"}
    )
    assert motifs == ["plage_basse:date_rendez_vous:01/01/1900 09:00:00 AM"]


def test_date_naissance_trop_ancienne_rejetee() -> None:
    motifs = controles.controler_ligne(
        "patients", {"date_naissance": "01/01/1889", "date_extraction": "01/01/2024"}
    )
    assert motifs == ["plage_basse:date_naissance:01/01/1889"]


def test_date_naissance_posterieure_a_extraction_rejetee() -> None:
    motifs = controles.controler_ligne(
        "patients", {"date_naissance": "01/01/2025", "date_extraction": "01/01/2024"}
    )
    assert motifs == ["naissance_future:date_naissance:01/01/2025"]


def test_date_naissance_1898_acceptee() -> None:
    motifs = controles.controler_ligne(
        "patients", {"date_naissance": "01/01/1898", "date_extraction": "01/01/2024"}
    )
    assert motifs == []


def test_decimal_invalide_rejete_et_valide_accepte_y_compris_zero() -> None:
    assert controles.controler_ligne("creances", {"montant_du": "abc"}) == [
        "typage_decimal:montant_du:abc"
    ]
    assert controles.controler_ligne("creances", {"montant_du": "0.00"}) == []
    assert controles.controler_ligne("creances", {"montant_du": "123.45"}) == []


def test_entier_invalide_rejete_et_valide_accepte_y_compris_zero() -> None:
    assert controles.controler_ligne("rendez_vous", {"duree": "trente"}) == [
        "typage_entier:duree:trente"
    ]
    assert controles.controler_ligne("rendez_vous", {"duree": "0"}) == []
    assert controles.controler_ligne("rendez_vous", {"duree": "30"}) == []


def test_zero_est_effectivement_analyse_pas_seulement_absent_de_motifs(monkeypatch) -> None:
    """`{"duree": "0"} == []` est vrai à la fois si "0" est validé et passe, et si "0" est
    silencieusement traité comme vide (jamais analysé) : dans les deux cas, aucun motif
    n'est produit. Pour distinguer ces deux cas, on vérifie que la valeur atteint bien
    `int(...)`, pas seulement que la liste de motifs reste vide.
    """
    appels: list[str] = []
    entier_original = int

    def entier_espion(valeur, *args, **kwargs):
        appels.append(valeur)
        return entier_original(valeur, *args, **kwargs)

    monkeypatch.setattr(controles, "int", entier_espion, raising=False)
    controles.controler_ligne("rendez_vous", {"duree": "0"})
    assert appels == ["0"]


def test_booleen_hors_domaine_rejete_et_0_1_acceptes() -> None:
    assert controles.controler_ligne("patients", {"exitus": "2"}) == ["domaine_booleen:exitus:2"]
    assert controles.controler_ligne("patients", {"exitus": "0"}) == []
    assert controles.controler_ligne("patients", {"exitus": "1"}) == []


def test_vide_accepte_partout_ou_un_controle_de_valeur_s_applique() -> None:
    ligne_toute_vide = {
        "date_naissance": "",
        "date_extraction": "",
        "exitus": "",
    }
    assert controles.controler_ligne("patients", ligne_toute_vide) == []

    ligne_numerique_vide = {"montant_du": "", "montant_recouvre": "", "montant_restant": ""}
    assert controles.controler_ligne("creances", ligne_numerique_vide) == []

    ligne_entier_vide = {"duree": ""}
    assert controles.controler_ligne("rendez_vous", ligne_entier_vide) == []


def test_ligne_cumulant_deux_defauts_porte_les_deux_motifs() -> None:
    motifs = controles.controler_ligne(
        "rendez_vous",
        {"date_rendez_vous": "13/45/2024 99:99:99 XM", "duree": "trente"},
    )
    assert motifs == [
        "typage_horodatage:date_rendez_vous:13/45/2024 99:99:99 XM",
        "typage_entier:duree:trente",
    ]


def test_unicite_seconde_occurrence_seule_porte_le_motif() -> None:
    lignes = [
        {"n_ipp": "IPP-1"},
        {"n_ipp": "IPP-2"},
        {"n_ipp": "IPP-1"},
        {"n_ipp": "IPP-3"},
    ]
    motifs = controles.controler_unicite("patients", lignes)
    assert motifs == [
        [],
        [],
        ["unicite:n_ipp:IPP-1"],
        [],
    ]


def test_unicite_cle_composite_lignes_facture() -> None:
    lignes_diff = [
        {"n_facture": "FAC-1", "n_ligne": "1"},
        {"n_facture": "FAC-1", "n_ligne": "2"},
    ]
    assert controles.controler_unicite("lignes_facture", lignes_diff) == [[], []]

    lignes_identiques = [
        {"n_facture": "FAC-1", "n_ligne": "1"},
        {"n_facture": "FAC-1", "n_ligne": "1"},
    ]
    assert controles.controler_unicite("lignes_facture", lignes_identiques) == [
        [],
        ["unicite:n_facture,n_ligne:FAC-1|1"],
    ]


def test_unicite_cle_vide() -> None:
    lignes = [{"n_ipp": ""}]
    assert controles.controler_unicite("patients", lignes) == [["cle_vide:n_ipp"]]
