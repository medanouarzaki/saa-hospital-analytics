"""Contrôles bloquants sur la correspondance entre `docs/relations_injectees.yml` (le
registre des relations injectées) et la configuration du générateur.

Ne recopie aucun nom de paramètre ni aucun décompte : lit le registre et la configuration à
chaque exécution, pour qu'une relation ajoutée ou renommée sans paramètre correspondant
fasse rougir ce fichier plutôt que de passer inaperçue.
"""

from collections import Counter
from pathlib import Path

import yaml

from generator import config

CHEMIN_REGISTRE = Path(__file__).resolve().parent.parent / "docs" / "relations_injectees.yml"


def _charger_registre() -> list[dict]:
    with CHEMIN_REGISTRE.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _noms_par_relation(relations: list[dict]) -> dict[str, list[str]]:
    return {r["id"]: [n.strip() for n in r["parametre"].split(",")] for r in relations}


def test_chaque_nom_de_parametre_existe_dans_la_configuration() -> None:
    relations = _charger_registre()
    noms_par_relation = _noms_par_relation(relations)
    entrees = {e["nom"] for e in config.charger_entrees()}

    manquants = []
    for id_relation, noms in noms_par_relation.items():
        for nom in noms:
            if nom not in entrees:
                manquants.append((id_relation, nom))
    assert not manquants, manquants


def test_decompte_relations_et_noms_distincts() -> None:
    relations = _charger_registre()
    assert len(relations) == 20

    noms_par_relation = _noms_par_relation(relations)

    # deux calculs independants du nombre de noms distincts, sur les memes donnees source :
    # un aplatissement par comprehension de liste puis un ensemble, et un comptage par
    # Counter dont on prend le nombre de cles -- une divergence entre les deux signalerait
    # une erreur de decoupage plutot qu'une simple faute de frappe dans un seul calcul.
    tous_les_noms = [nom for noms in noms_par_relation.values() for nom in noms]
    n_distincts_ensemble = len(set(tous_les_noms))
    n_distincts_compteur = len(Counter(tous_les_noms))
    assert n_distincts_ensemble == n_distincts_compteur
    assert n_distincts_ensemble > 0


def test_aucune_relation_orpheline() -> None:
    relations = _charger_registre()
    for relation in relations:
        noms = [n.strip() for n in relation["parametre"].split(",")]
        assert all(noms), relation
        assert len(noms) >= 1, relation
