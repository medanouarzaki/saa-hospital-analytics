"""Contrôles structurels, hors ligne, sur docs/relations_injectees.yml.

Dette explicite, non traitée ici : la correspondance bidirectionnelle
complète — vérifier que tout paramètre du générateur créant une relation
figure dans ce registre, et qu'aucune conclusion des sources LaTeX ne repose
sur une relation listée sans être marquée comme circulaire — exige que le
générateur (bloc 3) et les sources LaTeX (bloc 10) existent. Ces deux
contrôles sont des dettes explicites de ces blocs, nommées ici et non écrites
avant qu'ils existent.
"""

import re
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
RELATIONS = RACINE / "docs" / "relations_injectees.yml"
SOURCES = RACINE / "docs" / "sources" / "sources.yml"

STATUT_AUTORISES = {"DOC", "HYP"}
ID_PATTERN = re.compile(r"^R-\d{2}$")

CHAMPS_OBLIGATOIRES = [
    "id",
    "relation",
    "parametre",
    "statut",
    "consequence",
    "ou_apparait",
]

LONGUEUR_MIN_CONSEQUENCE = 80


def charger_relations() -> list[dict]:
    with open(RELATIONS, encoding="utf-8") as f:
        return yaml.safe_load(f)


def charger_identifiants_sources() -> set[str]:
    with open(SOURCES, encoding="utf-8") as f:
        sources = yaml.safe_load(f)
    return {s["id"] for s in sources}


def test_completude_relations() -> None:
    relations = charger_relations()

    identifiants = [r.get("id") for r in relations]
    doublons = {i for i in identifiants if identifiants.count(i) > 1}
    assert not doublons, f"Identifiants dupliqués : {sorted(doublons)}"

    for relation in relations:
        ident = relation.get("id", "<sans id>")

        assert ID_PATTERN.match(ident or ""), (
            f"{ident} : identifiant hors du format 'R-<deux chiffres>'"
        )

        for champ in CHAMPS_OBLIGATOIRES:
            assert champ in relation, f"{ident} : champ obligatoire manquant '{champ}'"
            valeur = relation[champ]
            assert isinstance(valeur, str) and valeur.strip(), f"{ident} : champ '{champ}' vide"

        assert relation["statut"] in STATUT_AUTORISES, (
            f"{ident} : statut '{relation['statut']}' hors ensemble autorisé {STATUT_AUTORISES}"
        )

        source = relation.get("source", "")
        if relation["statut"] == "DOC":
            assert isinstance(source, str) and source.strip(), (
                f"{ident} : statut 'DOC' exige une source non vide"
            )

        assert len(relation["consequence"]) >= LONGUEUR_MIN_CONSEQUENCE, (
            f"{ident} : consequence trop courte "
            f"({len(relation['consequence'])} caractères, minimum "
            f"{LONGUEUR_MIN_CONSEQUENCE})"
        )


def test_sources_referencees_existent() -> None:
    """Seul contrôle croisé possible aujourd'hui : toute valeur de `source`
    non vide doit désigner un identifiant existant de docs/sources/sources.yml.
    """
    relations = charger_relations()
    identifiants_sources = charger_identifiants_sources()

    for relation in relations:
        source = relation.get("source", "")
        if isinstance(source, str) and source.strip():
            assert source in identifiants_sources, (
                f"{relation['id']} : source='{source}' ne désigne aucun "
                f"identifiant existant de docs/sources/sources.yml"
            )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
