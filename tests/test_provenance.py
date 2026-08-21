"""Contrôles bloquants sur la provenance des colonnes de la couche source.

Aucun test de ce module n'est sauté : si la base est injoignable, le test
échoue. Un test sauté est un succès qui ne mesure rien, et c'est le mode de
défaillance que ce projet a déjà rencontré deux fois.
"""

import importlib.util
import re
from pathlib import Path

import psycopg
import yaml

RACINE = Path(__file__).resolve().parent.parent
REGISTRE = RACINE / "docs" / "champs" / "registre_champs.yml"
RELEVE = RACINE / "docs" / "observation" / "releve_champs.yml"
SOURCES = RACINE / "docs" / "sources" / "sources.yml"
APPLIQUER_DDL = RACINE / "ingestion" / "appliquer_ddl.py"

TYPE_APPARENT_NAVIGATION = {"bouton", "onglet", "menu"}
PROVENANCES_AUTORISEES = {"OBS", "DOC", "HYP"}


def charger_module(chemin: Path):
    spec = importlib.util.spec_from_file_location(chemin.stem, chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def connexion() -> psycopg.Connection:
    variables = charger_module(APPLIQUER_DDL).charger_environnement()
    return psycopg.connect(
        host=variables["POSTGRES_HOST"],
        port=variables["POSTGRES_PORT"],
        dbname=variables["POSTGRES_DB"],
        user=variables["POSTGRES_USER"],
        password=variables["POSTGRES_PASSWORD"],
        connect_timeout=5,
    )


def charger_registre() -> list[dict]:
    with REGISTRE.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def charger_releve() -> dict[str, dict]:
    with RELEVE.open(encoding="utf-8") as f:
        donnees = yaml.safe_load(f)
    par_id = {}
    for ecran in donnees["ecrans"]:
        for champ in ecran["champs"]:
            par_id[champ["id"]] = champ
    return par_id


def charger_sources() -> dict[str, dict]:
    with SOURCES.open(encoding="utf-8") as f:
        donnees = yaml.safe_load(f)
    return {s["id"]: s for s in donnees}


def test_couverture_bidirectionnelle() -> None:
    registre = charger_registre()
    couples_registre = {(e["table"], e["colonne"]) for e in registre}

    with connexion() as conn:
        lignes = conn.execute(
            """
            select c.table_schema, c.table_name, c.column_name
            from information_schema.columns c
            join information_schema.tables t
              on t.table_schema = c.table_schema and t.table_name = c.table_name
            where c.table_schema in ('source', 'intermediate', 'marts')
              and t.table_type = 'BASE TABLE'
            """
        ).fetchall()

    couples_catalogue = {(f"{schema}.{table}", colonne) for schema, table, colonne in lignes}

    manquantes_au_catalogue = couples_registre - couples_catalogue
    manquantes_au_registre = couples_catalogue - couples_registre

    assert not manquantes_au_catalogue, (
        f"colonnes du registre absentes du catalogue : {sorted(manquantes_au_catalogue)}"
    )
    assert not manquantes_au_registre, (
        f"colonnes du catalogue absentes du registre : {sorted(manquantes_au_registre)}"
    )


def test_commentaires_provenance() -> None:
    registre = charger_registre()
    par_couple = {(e["table"], e["colonne"]): e for e in registre}

    with connexion() as conn:
        lignes = conn.execute(
            """
            select n.nspname, c.relname, a.attname, d.description
            from pg_catalog.pg_attribute a
            join pg_catalog.pg_class c on c.oid = a.attrelid
            join pg_catalog.pg_namespace n on n.oid = c.relnamespace
            left join pg_catalog.pg_description d
              on d.objoid = c.oid and d.objsubid = a.attnum
            where n.nspname = 'source' and a.attnum > 0 and not a.attisdropped
            """
        ).fetchall()

    compte: dict[str, int] = {}
    echecs = []
    for schema, table, colonne, description in lignes:
        cle_table = f"{schema}.{table}"
        entree = par_couple.get((cle_table, colonne))

        if description is None:
            echecs.append(f"{cle_table}.{colonne} : commentaire nul")
            continue

        correspondance_provenance = re.search(r"provenance=([A-Z]+);", description)
        correspondance_preuve = re.search(r"preuve=([^;]+);", description)
        if not correspondance_provenance or not correspondance_preuve:
            echecs.append(f"{cle_table}.{colonne} : commentaire mal formé ({description!r})")
            continue

        provenance_catalogue = correspondance_provenance.group(1)
        preuve_catalogue = correspondance_preuve.group(1)
        compte[provenance_catalogue] = compte.get(provenance_catalogue, 0) + 1

        if entree is None:
            echecs.append(f"{cle_table}.{colonne} : absente du registre")
            continue
        if provenance_catalogue != entree["provenance"]:
            echecs.append(
                f"{cle_table}.{colonne} : provenance catalogue={provenance_catalogue} "
                f"registre={entree['provenance']}"
            )
        if preuve_catalogue != entree["preuve"]:
            echecs.append(
                f"{cle_table}.{colonne} : preuve catalogue={preuve_catalogue} "
                f"registre={entree['preuve']}"
            )

    print(f"décompte de provenance issu du catalogue : {compte}")

    assert not echecs, "\n".join(echecs)


def test_coherence_preuves() -> None:
    registre = charger_registre()
    releve = charger_releve()
    sources = charger_sources()

    echecs = []
    for entree in registre:
        cle = f"{entree['table']}.{entree['colonne']}"
        provenance = entree["provenance"]
        preuve = entree["preuve"]
        note = entree["note"]
        libelle = entree["libelle_hosix"]

        if provenance not in PROVENANCES_AUTORISEES:
            echecs.append(f"{cle} : provenance '{provenance}' hors ensemble autorisé")
            continue

        if provenance == "OBS":
            champ = releve.get(preuve)
            if champ is None:
                echecs.append(f"{cle} : preuve OBS '{preuve}' absente du relevé de champs")
            elif champ["type_apparent"] in TYPE_APPARENT_NAVIGATION:
                echecs.append(
                    f"{cle} : preuve OBS '{preuve}' pointe vers "
                    f"type_apparent='{champ['type_apparent']}'"
                )
        elif provenance == "DOC":
            source = sources.get(preuve)
            if source is None:
                echecs.append(f"{cle} : preuve DOC '{preuve}' absente du registre des sources")
            elif source["verification"] != "contenu_lu":
                echecs.append(
                    f"{cle} : preuve DOC '{preuve}' a verification='{source['verification']}'"
                )
        elif provenance == "HYP":
            if preuve != "sans_preuve_externe":
                echecs.append(f"{cle} : preuve HYP '{preuve}' != 'sans_preuve_externe'")
            if len(note) < 120:
                echecs.append(f"{cle} : note HYP de {len(note)} caractères, sous 120")

        libelle_observe = libelle != "non_releve"
        if libelle_observe != (provenance == "OBS"):
            echecs.append(
                f"{cle} : libelle_hosix='{libelle}' incohérent avec provenance='{provenance}'"
            )

        if entree["type"] != "text":
            echecs.append(f"{cle} : type='{entree['type']}' au lieu de 'text'")

    assert not echecs, "\n".join(echecs)


def test_artefacts_synchrones(tmp_path: Path) -> None:
    generer_ddl = charger_module(RACINE / "docs" / "champs" / "generer_ddl.py")
    generer_schema_yml = charger_module(RACINE / "docs" / "champs" / "generer_schema_yml.py")
    generer_dictionnaire = charger_module(RACINE / "docs" / "champs" / "generer_dictionnaire.py")

    generer_ddl.generer(tmp_path)
    generer_schema_yml.generer(tmp_path)
    generer_dictionnaire.generer(tmp_path)

    dossier_ddl = RACINE / "ingestion" / "ddl"
    fichiers_a_comparer = sorted(dossier_ddl.glob("[0-1][0-9]_*.sql"))
    fichiers_a_comparer.append(RACINE / "dbt" / "models" / "sources" / "source.yml")
    fichiers_a_comparer.append(RACINE / "docs" / "champs" / "dictionnaire_donnees.md")
    fichiers_a_comparer.append(RACINE / "report" / "dictionnaire_donnees.tex")
    # La synthèse dérive du même registre par le même module. Sans cette ligne, elle pourrait
    # rester périmée après une modification du registre sans qu'aucun contrôle ne le voie : c'est
    # la seule voie par laquelle elle serait verte alors que sa source aurait changé.
    fichiers_a_comparer.append(RACINE / "report" / "dictionnaire_synthese.tex")

    echecs = []
    for committe in fichiers_a_comparer:
        relatif = committe.relative_to(RACINE)
        genere = tmp_path / relatif
        if not genere.exists():
            echecs.append(f"{relatif} : non régénéré")
            continue
        if committe.read_bytes() != genere.read_bytes():
            echecs.append(f"{relatif} : diffère du fichier régénéré")

    assert not echecs, "\n".join(echecs)
