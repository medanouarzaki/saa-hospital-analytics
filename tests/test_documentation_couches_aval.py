"""Contrôle de la documentation des couches `intermediate` et `marts`.

POURQUOI CE FICHIER EXISTE.

Le contrôle de provenance (`tests/test_provenance.py::test_couverture_bidirectionnelle`) nomme les
trois schémas `source`, `intermediate` et `marts`, mais joint `information_schema.tables` en
filtrant `table_type = 'BASE TABLE'`. Or les deux couches aval sont matérialisées en vues. La
requête ne retient donc que la couche source, et **aucune colonne des deux couches aval n'est
vérifiée par lui**. Ce n'est pas un défaut de ce contrôle — le filtre est la conséquence voulue de
la matérialisation en vues — mais de ce qui lui était prêté. Ce fichier-ci porte la propriété
manquante.

CE QUE CE FICHIER VÉRIFIE : que toute colonne réellement présente au catalogue, dans ces deux
couches, est déclarée à un fichier de propriétés, et que toute colonne déclarée porte une
description non vide qui ne soit pas la mention d'absence de documentation.

CE QU'IL NE VÉRIFIE PAS : la justesse d'une description. Une description fausse le passe ; c'est la
relecture humaine qui l'attrape. Il ne vérifie pas non plus la couche source, déjà couverte par le
registre des champs et le contrôle de provenance.

Aucun travail au niveau du module : ni connexion, ni lecture de variable d'environnement, ni
chargement de fichier à l'import. Le fichier se collecte sur un clone frais sans base ni variable
exportée.

Aucun littéral de volumétrie : les deux ensembles comparés sont calculés chacun de son côté, l'un
depuis le catalogue de la base, l'autre depuis les fichiers de propriétés.
"""

from __future__ import annotations

from pathlib import Path

import psycopg
import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
MODELES = RACINE / "dbt" / "models"
APPLIQUER_DDL = RACINE / "ingestion" / "appliquer_ddl.py"

COUCHES = ("intermediate", "marts")

# La mention que porte le dictionnaire du classeur pour une colonne sans description. Une
# description qui vaudrait cette mention documenterait l'absence de documentation ; elle est donc
# traitée comme une absence, et non comme une description.
MENTION_ABSENCE = "Non documentée"


def _charger_module(chemin: Path):
    import importlib.util  # noqa: PLC0415

    spec = importlib.util.spec_from_file_location(chemin.stem, chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _connexion() -> psycopg.Connection:
    """Ouverte à l'appel, jamais à l'import. Même mécanisme que les autres contrôles qui
    exigent une base."""
    variables = _charger_module(APPLIQUER_DDL).charger_environnement()
    try:
        return psycopg.connect(
            host=variables["POSTGRES_HOST"],
            port=variables["POSTGRES_PORT"],
            dbname=variables["POSTGRES_DB"],
            user=variables["POSTGRES_USER"],
            password=variables.get("POSTGRES_PASSWORD", ""),
        )
    except psycopg.OperationalError as exc:
        pytest.fail(
            f"connexion impossible à la base ({exc}) : les couches intermediate et marts doivent "
            "être construites avant ce contrôle"
        )


def _colonnes_du_catalogue() -> dict[str, set[str]]:
    """Les colonnes réellement présentes, par objet, dans les deux couches aval.

    Aucun filtre sur le type d'objet : c'est précisément ce filtre qui rend le contrôle de
    provenance aveugle à ces deux couches, matérialisées en vues.
    """
    connexion = _connexion()
    try:
        with connexion.cursor() as curseur:
            curseur.execute(
                "select table_name, column_name from information_schema.columns "
                "where table_schema = any(%s)",
                (list(COUCHES),),
            )
            lignes = curseur.fetchall()
    finally:
        connexion.close()

    par_objet: dict[str, set[str]] = {}
    for objet, colonne in lignes:
        par_objet.setdefault(objet, set()).add(colonne)
    return par_objet


def _colonnes_declarees() -> dict[str, dict[str, str]]:
    """Les colonnes déclarées aux fichiers de propriétés, avec leur description, par modèle.

    Le fichier de sources est exclu : il porte la couche source, engendrée depuis le registre des
    champs, et non les modèles des couches aval.
    """
    declare: dict[str, dict[str, str]] = {}
    for couche in COUCHES:
        for fichier in sorted((MODELES / couche).glob("*.yml")):
            contenu = yaml.safe_load(fichier.read_text(encoding="utf-8")) or {}
            for modele in contenu.get("models", []) or []:
                colonnes = modele.get("columns") or []
                declare[modele["name"]] = {
                    colonne["name"]: (colonne.get("description") or "") for colonne in colonnes
                }
    return declare


def test_toute_colonne_reelle_des_couches_aval_est_declaree() -> None:
    """Aucune colonne du catalogue ne manque à son fichier de propriétés.

    Les deux ensembles sont construits indépendamment : les colonnes réelles viennent du catalogue
    de la base, les colonnes déclarées de la lecture des fichiers. Une colonne ajoutée à un modèle
    sans être déclarée fait rougir ici, et le message la nomme.
    """
    catalogue = _colonnes_du_catalogue()
    assert catalogue, "le catalogue ne rend aucune colonne pour les couches intermediate et marts"
    declare = _colonnes_declarees()

    manquantes: dict[str, list[str]] = {}
    for objet, colonnes in sorted(catalogue.items()):
        absentes = sorted(colonnes - set(declare.get(objet, {})))
        if absentes:
            manquantes[objet] = absentes

    total = sum(len(noms) for noms in manquantes.values())
    detail = "\n".join(
        f"  {objet} : {len(noms)} colonne(s) non déclarée(s) — {', '.join(noms)}"
        for objet, noms in manquantes.items()
    )
    assert not manquantes, (
        f"{total} colonne(s) réelle(s) ne sont déclarées dans aucun fichier de propriétés, "
        f"réparties sur {len(manquantes)} modèle(s) :\n{detail}"
    )


def test_toute_colonne_declaree_porte_une_description() -> None:
    """Aucune colonne déclarée n'est laissée sans description.

    Une description vide, ou réduite à la mention d'absence de documentation que le classeur
    emploie, ne documente rien : les deux sont traitées de la même façon.
    """
    declare = _colonnes_declarees()
    assert declare, "aucun fichier de propriétés n'a été lu"

    sans_description: dict[str, list[str]] = {}
    for modele, colonnes in sorted(declare.items()):
        fautives = sorted(
            nom
            for nom, description in colonnes.items()
            if not description.strip() or description.strip() == MENTION_ABSENCE
        )
        if fautives:
            sans_description[modele] = fautives

    total = sum(len(noms) for noms in sans_description.values())
    detail = "\n".join(
        f"  {modele} : {len(noms)} colonne(s) sans description — {', '.join(noms)}"
        for modele, noms in sans_description.items()
    )
    assert not sans_description, (
        f"{total} colonne(s) déclarée(s) ne portent aucune description, "
        f"réparties sur {len(sans_description)} modèle(s) :\n{detail}"
    )
