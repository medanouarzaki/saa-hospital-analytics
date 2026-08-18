"""Contrôle d'idempotence de l'application de la définition de schéma.

POURQUOI CE FICHIER EXISTE.

`ingestion/appliquer_ddl.py` applique les fichiers de `ingestion/ddl/` dans l'ordre alphabétique,
en validation automatique : chaque instruction est validée séparément, et un échec en cours de route
ne s'annule pas. Vingt-deux de ces fichiers commencent par `drop table if exists ... cascade`. Une
seconde application qui échouerait après avoir traversé ces vingt-deux fichiers laisserait donc une
base amputée sans rien pouvoir reprendre. La chaîne doit pouvoir démarrer deux fois.

CE QUE CE FICHIER VÉRIFIE : que trois applications successives sur une base vierge réussissent, et
que le catalogue est identique après la deuxième et après la troisième qu'après la première.

CE QU'IL NE VÉRIFIE PAS : que les objets créés soient les bons. C'est l'affaire des contrôles de
provenance et de schéma de quarantaine, qui interrogent le catalogue pour lui-même.

CE QU'IL NE PEUT PAS VÉRIFIER, et il faut le dire : qu'une garde ne soit pas silencieusement
inopérante. Une création sous condition d'absence -- `create table if not exists` -- laisse en place
une définition ancienne sans rien signaler ; deux applications successives des mêmes fichiers
rendraient alors le même catalogue, et ce contrôle passerait. Ce n'est donc pas lui qui écarte
cette forme de garde, c'est le choix de forme lui-même, et le couple `drop ... if exists` puis
`create` que les fichiers emploient tous.

OÙ IL S'EXÉCUTE, ET COMMENT IL ÉTABLIT QU'IL NE VISE PAS LA BASE DU PROJET.

Appliquer la définition de schéma détruit les données de la couche source. Ce contrôle ne peut donc
pas se contenter d'une base « probablement jetable » : il s'en **fabrique** une. Il ouvre une
connexion de maintenance, crée une base neuve sous un nom tiré au hasard, y travaille, puis la
supprime. La base désignée par l'environnement n'est jamais celle sur laquelle la définition est
appliquée -- elle ne sert qu'à ouvrir la connexion qui crée la base jetable.

Avant la première écriture, la cible est établie par la **conjonction** de la base et du serveur :
`current_database()` doit valoir le nom que ce contrôle vient de tirer, et `system_identifier` --
l'identifiant de grappe inscrit au fichier de contrôle à l'initialisation, que deux grappes
distinctes ne peuvent pas partager -- doit valoir celui relevé sur la connexion de maintenance. Le
port ne participe pas à cette vérification : `inet_server_port()` rapporte le port interne du
serveur, qui ne renseigne en rien sur la cible atteinte.

Aucun travail au niveau du module : ni connexion, ni lecture de variable d'environnement, ni
chargement de fichier à l'import. Le fichier se collecte sur un clone frais sans base ni variable
exportée.

Aucun littéral de volumétrie : l'empreinte de catalogue est comparée à elle-même d'un passage à
l'autre, et aucun nombre d'objets, de colonnes ou de fichiers n'est écrit ici.
"""

from __future__ import annotations

import secrets
from pathlib import Path

import psycopg
import pytest

RACINE = Path(__file__).resolve().parent.parent
APPLIQUER_DDL = RACINE / "ingestion" / "appliquer_ddl.py"

SCHEMAS_DECRITS = ("source", "intermediate", "marts", "quarantaine")

# L'empreinte ne lit NI horodatage NI identifiant interne d'objet. C'est délibéré : supprimer puis
# recréer un objet à l'identique lui attribue un nouvel `oid` et un nouveau fichier physique, sans
# que sa définition change. Une empreinte qui les inclurait différerait à chaque passage alors même
# que l'idempotence tiendrait, et ne prouverait donc rien.
REQUETE_EMPREINTE = """
with objets as (
    select n.nspname as sch, c.relname as obj, c.relkind::text as genre
    from pg_class c join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = any(%(schemas)s) and c.relkind in ('r', 'v', 'm')
),
colonnes as (
    select n.nspname as sch, c.relname as obj, a.attname as col,
           format_type(a.atttypid, a.atttypmod) as typ, a.attnum::text as rang,
           coalesce(d.description, '') as commentaire
    from pg_attribute a
    join pg_class c on c.oid = a.attrelid
    join pg_namespace n on n.oid = c.relnamespace
    left join pg_description d on d.objoid = c.oid and d.objsubid = a.attnum
    where n.nspname = any(%(schemas)s) and c.relkind in ('r', 'v', 'm')
      and a.attnum > 0 and not a.attisdropped
),
vues as (
    select n.nspname as sch, c.relname as obj, pg_get_viewdef(c.oid, true) as definition
    from pg_class c join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = any(%(schemas)s) and c.relkind in ('v', 'm')
),
schemas as (
    select nspname as sch from pg_namespace where nspname = any(%(schemas)s)
)
select ligne from (
    select 'SCHEMA|' || sch as ligne from schemas
    union all select 'OBJET|' || sch || '|' || obj || '|' || genre from objets
    union all select 'COLONNE|' || sch || '|' || obj || '|' || rang || '|' || col || '|'
                     || typ || '|' || commentaire from colonnes
    union all select 'VUE|' || sch || '|' || obj || '|' || definition from vues
) t order by ligne
"""


def _charger_module(chemin: Path):
    import importlib.util  # noqa: PLC0415

    spec = importlib.util.spec_from_file_location(chemin.stem, chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _connexion(variables: dict[str, str], base: str) -> psycopg.Connection:
    """Ouverte à l'appel, jamais à l'import. Même mécanisme que les autres contrôles qui
    exigent une base."""
    try:
        return psycopg.connect(
            host=variables["POSTGRES_HOST"],
            port=variables["POSTGRES_PORT"],
            dbname=base,
            user=variables["POSTGRES_USER"],
            password=variables.get("POSTGRES_PASSWORD", ""),
            autocommit=True,
        )
    except psycopg.OperationalError as exc:
        pytest.fail(f"connexion impossible à la base « {base} » ({exc})")


def _identite(connexion: psycopg.Connection) -> tuple[str, str]:
    """La base et le serveur, ensemble. Ni l'un ni l'autre ne suffit seul."""
    with connexion.cursor() as curseur:
        curseur.execute(
            "select current_database(), (select system_identifier::text from pg_control_system())"
        )
        base, grappe = curseur.fetchone()
    return base, grappe


def _empreinte(connexion: psycopg.Connection) -> tuple[str, ...]:
    with connexion.cursor() as curseur:
        curseur.execute(REQUETE_EMPREINTE, {"schemas": list(SCHEMAS_DECRITS)})
        return tuple(ligne for (ligne,) in curseur.fetchall())


@pytest.fixture
def base_jetable(monkeypatch) -> str:
    """Fabrique une base neuve, la désigne à l'environnement, et la supprime après coup.

    C'est ce qui garantit que le contrôle ne vise jamais la base du projet : il n'applique pas la
    définition de schéma sur la base qu'on lui a donnée, mais sur une base qu'il vient de créer.
    """
    module = _charger_module(APPLIQUER_DDL)
    variables = module.charger_environnement()
    manquantes = [
        cle
        for cle in ("POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER")
        if not variables.get(cle)
    ]
    if manquantes:
        pytest.fail(f"variables de connexion manquantes : {', '.join(manquantes)}")

    nom = f"ddl_idempotence_{secrets.token_hex(8)}"
    maintenance = _connexion(variables, variables["POSTGRES_DB"])
    try:
        base_maintenance, grappe_maintenance = _identite(maintenance)
        with maintenance.cursor() as curseur:
            curseur.execute(f'create database "{nom}"')
    finally:
        maintenance.close()

    # PRÉCONDITION, éprouvée avant toute écriture : la conjonction base + serveur.
    travail = _connexion(variables, nom)
    base_atteinte, grappe_atteinte = _identite(travail)
    if base_atteinte != nom or grappe_atteinte != grappe_maintenance:
        travail.close()
        pytest.fail(
            "la cible n'est pas la base jetable attendue : "
            f"base attendue « {nom} », atteinte « {base_atteinte} » ; "
            f"grappe attendue « {grappe_maintenance} », atteinte « {grappe_atteinte} ». "
            "Aucune définition de schéma n'a été appliquée."
        )
    if _empreinte(travail):
        travail.close()
        pytest.fail(
            f"la base jetable « {nom} » n'est pas vierge : elle porte déjà des objets dans les "
            f"schémas {', '.join(SCHEMAS_DECRITS)}. Aucune définition de schéma n'a été appliquée."
        )
    travail.close()

    monkeypatch.setenv("POSTGRES_DB", nom)
    try:
        yield nom
    finally:
        monkeypatch.undo()
        menage = _connexion(variables, variables["POSTGRES_DB"])
        try:
            with menage.cursor() as curseur:
                curseur.execute(f'drop database if exists "{nom}" with (force)')
        finally:
            menage.close()

    assert base_maintenance == variables["POSTGRES_DB"]


def test_appliquer_la_definition_de_schema_est_rejouable(base_jetable: str) -> None:
    """Trois applications successives réussissent, et laissent le catalogue identique.

    Le troisième passage n'est pas une redondance : une propriété qui ne tiendrait qu'au second
    passage n'en serait pas une, le second pouvant n'avoir fait que rattraper un état particulier
    laissé par le premier.
    """
    module = _charger_module(APPLIQUER_DDL)

    empreintes: list[tuple[str, ...]] = []
    for rang in (1, 2, 3):
        try:
            module.main([])
        except Exception as exc:  # noqa: BLE001
            libelle = f"{type(exc).__name__}: {exc}"
            assert rang == 1, (
                f"l'application n° {rang} de la définition de schéma a échoué sur une base où les "
                f"{rang - 1} précédentes avaient réussi — {libelle}. Une instruction de création "
                "n'est pas protégée contre une seconde application."
            )
            pytest.fail(f"la première application de la définition de schéma a échoué — {libelle}")
        connexion = _connexion(module.charger_environnement(), base_jetable)
        try:
            empreintes.append(_empreinte(connexion))
        finally:
            connexion.close()

    assert empreintes[0], "le catalogue est vide après la première application"

    for rang, empreinte in enumerate(empreintes[1:], start=2):
        ecarts = sorted(set(empreinte) ^ set(empreintes[0]))
        assert empreinte == empreintes[0], (
            f"le catalogue diffère après l'application n° {rang} de ce qu'il était après la "
            f"première : {len(ecarts)} ligne(s) d'écart, dont "
            f"{'; '.join(ecarts[:5])}"
        )
