"""Contrôle de non-régression sur le coût du chargement de la configuration.

Ne porte pas sur une durée, instable sur un coureur partagé, mais sur le
nombre de lectures du fichier de configuration pendant une charge.
"""

from datetime import date, timedelta

import yaml

from generator import calendrier, config, temporel


def test_configuration_lue_une_seule_fois_par_repertoire(monkeypatch) -> None:
    config.vider_cache()
    compte = {"n": 0}
    original_safe_load = yaml.safe_load

    def safe_load_compte(*args, **kwargs):
        compte["n"] += 1
        return original_safe_load(*args, **kwargs)

    monkeypatch.setattr(yaml, "safe_load", safe_load_compte)

    nb_fichiers = len(config.fichiers_configuration())
    jours = [date(2024, 1, 1) + timedelta(days=i) for i in range(5)]

    for _ in range(3000):
        for jour in jours:
            calendrier.est_ferie(jour)
            temporel.poids_jour(jour, "programme")

    assert compte["n"] == nb_fichiers


def test_structure_rendue_non_partagee() -> None:
    config.vider_cache()
    entrees_a = config.charger_entrees()
    valeur_originale = entrees_a[0]["valeur"]
    entrees_a[0]["valeur"] = "mutee_par_le_test"

    entrees_b = config.charger_entrees()

    assert entrees_b[0]["valeur"] == valeur_originale


def test_repertoires_distincts_dans_le_meme_processus(tmp_path) -> None:
    dossier_a = tmp_path / "a"
    dossier_a.mkdir()
    dossier_b = tmp_path / "b"
    dossier_b.mkdir()

    entree_type = {
        "unite": "unités",
        "provenance": "HYP",
        "preuve": "sans_preuve_externe",
        "note": "n",
    }
    (dossier_a / "x.yml").write_text(
        yaml.safe_dump({"parametres": [{"nom": "p", "valeur": 1, **entree_type}]}),
        encoding="utf-8",
    )
    (dossier_b / "x.yml").write_text(
        yaml.safe_dump({"parametres": [{"nom": "p", "valeur": 2, **entree_type}]}),
        encoding="utf-8",
    )

    entrees_a = config.charger_entrees(dossier_a)
    entrees_b = config.charger_entrees(dossier_b)

    assert entrees_a[0]["valeur"] == 1
    assert entrees_b[0]["valeur"] == 2
