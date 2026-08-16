"""Rafraîchissement du schéma d'instantané que lit le tableau de bord.

Le tableau de bord ne lit pas les vues de la couche `marts` directement : une reconstruction en
cours les fait disparaître pendant environ trois dixièmes de seconde, un lecteur concurrent y
rencontrant une erreur d'objet inexistant et non une attente (`docs/decisions/
0043-instantane-schema-dedie-du-tableau-de-bord.md`). Ce module construit et rafraîchit le schéma
de tables que le tableau de bord lit à la place.

Ce que l'instantané porte est une RÈGLE et non une liste écrite à la main : une copie de chaque
vue de `marts`, de chaque table de `linkage`, de la vue intermédiaire qui porte les créances, plus
deux tables de service. La liste effective se dérive du catalogue à chaque exécution, ce qui rend
la complétude vérifiable par une égalité entre deux décomptes calculés plutôt que par une
relecture.

Le rafraîchissement construit des tables neuves sous des noms provisoires, puis échange les noms.
Tous les échanges sont faits dans UNE SEULE transaction. L'intention est qu'un lecteur ne puisse
jamais voir un instantané mi-neuf mi-ancien, un objet d'une page ayant été échangé et l'autre pas.
Cette propriété n'est pas vérifiée ici : elle demande un témoin concurrent, et aucun test de ce
module ne l'établit. Elle est donc VISÉE par la transaction unique, et non prouvée.

Ne modifie aucun autre schéma. Ne supprime jamais un schéma, pas même le sien : il le crée s'il
manque, et travaille table par table.
"""

import argparse
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import psycopg
import yaml

from ingestion import chargeur

SCHEMA = "instantane"

# Les deux tables de service portent ce préfixe. Qu'aucun objet copié ne le porte est vérifié au
# catalogue par `verifier_noms()`, et non supposé : une collision ferait qu'un rafraîchissement
# écraserait silencieusement une table de service par une copie.
PREFIXE_SERVICE = "instantane_"
TABLE_ETAT = f"{PREFIXE_SERVICE}etat"
TABLE_PARAMETRES = f"{PREFIXE_SERVICE}parametres"

# Noms de travail. Un rafraîchissement interrompu peut en laisser ; le démarrage suivant les
# efface plutôt que d'échouer dessus.
# Durée de la dernière phase exclusive, en millisecondes : de la demande des verrous jusqu'à la
# validation de la transaction qui renomme. C'est la grandeur qu'un lecteur concurrent peut avoir à
# attendre, et un contrôle la compare à l'attente réellement observée. Remise à None au début de
# chaque rafraîchissement, pour qu'une valeur périmée ne puisse jamais être lue pour une neuve.
# Aucune décision du module n'en dépend.
DERNIERE_FENETRE_MS = None

ATTENTE_VERROU_MS = 200
TENTATIVES_ECHANGE = 10


def TEMPORISATION_S(tentative):
    return 0.05 * tentative


SUFFIXE_NEUF = "__neuf"
SUFFIXE_REBUT = "__rebut"

# Le fichier suivi où vit déjà la capacité litière, et la clé qui la porte. Le module la LIT ici
# et ne la redéclare nulle part : une seconde déclaration serait une source de vérité concurrente.
FICHIER_PARAMETRES = (
    Path(__file__).resolve().parent.parent / "generator" / "config" / "volumetrie.yml"
)
PARAMETRES_REPRIS = ("capacite_litiere_fonctionnelle",)

REQUETE_OBJETS = """
select n.nspname, c.relname
from pg_class c join pg_namespace n on n.oid = c.relnamespace
where (n.nspname = 'marts' and c.relkind in ('v', 'm'))
   or (n.nspname = 'linkage' and c.relkind = 'r')
   or (n.nspname = 'intermediate' and c.relname = 'int_creances')
order by 1, 2
"""


class EchangeImpossible(RuntimeError):
    """L'echange n'a pas obtenu ses verrous, toutes tentatives epuisees."""


def objets_a_copier(curseur) -> list[tuple[str, str]]:
    """La règle de peuplement, évaluée contre le catalogue. Jamais une liste écrite."""
    curseur.execute(REQUETE_OBJETS)
    return [(schema, nom) for schema, nom in curseur.fetchall()]


def verifier_noms(objets: list[tuple[str, str]]) -> None:
    """Deux collisions rendraient le peuplement silencieusement faux ; elles sont mesurées."""
    noms = [nom for _, nom in objets]
    doublons = sorted({nom for nom in noms if noms.count(nom) > 1})
    if doublons:
        raise ValueError(f"collision de noms entre les ensembles copiés : {doublons}")

    portant_le_prefixe = sorted(nom for nom in noms if nom.startswith(PREFIXE_SERVICE))
    if portant_le_prefixe:
        raise ValueError(
            f"des objets copiés portent le préfixe réservé aux tables de service : "
            f"{portant_le_prefixe}"
        )


def date_de_reference(curseur) -> str:
    """La dernière date d'extraction effectivement chargée, mesurée sur la couche source.

    Jamais l'horloge : quarante-six jours séparent l'une de l'autre sur ce jeu de données, et un
    indicateur d'ancienneté calculé sur l'horloge vide une tranche entière de sa population.

    `source` porte la date au format d'affichage du système observé, d'où la conversion.
    """
    curseur.execute(
        "select table_name from information_schema.columns "
        "where table_schema = 'source' and column_name = 'date_extraction' order by 1"
    )
    tables = [ligne[0] for ligne in curseur.fetchall()]
    if not tables:
        raise ValueError("aucune table de la couche source ne porte de date d'extraction")

    union = " union all ".join(
        f"select max(to_date(date_extraction, 'MM/DD/YYYY')) as d from source.{table}"
        for table in tables
    )
    curseur.execute(f"select max(d) from ({union}) as toutes")
    date = curseur.fetchone()[0]
    if date is None:
        raise ValueError("aucune date d'extraction chargée dans la couche source")
    return date.isoformat()


def parametres_repris() -> list[tuple[str, str, str, str]]:
    """(nom, valeur, fichier, clé) — la provenance est portée par la donnée, pas par un commentaire.

    Un test relit le fichier que cette colonne désigne et compare : c'est ce qui rend la
    provenance vérifiable plutôt que décorative.
    """
    contenu = yaml.safe_load(FICHIER_PARAMETRES.read_text(encoding="utf-8"))
    par_nom = {entree["nom"]: entree for entree in contenu["parametres"]}

    chemin = FICHIER_PARAMETRES.relative_to(FICHIER_PARAMETRES.parent.parent.parent).as_posix()
    lignes = []
    for nom in PARAMETRES_REPRIS:
        if nom not in par_nom:
            raise ValueError(f"paramètre absent du fichier de configuration : {nom}")
        lignes.append((nom, str(par_nom[nom]["valeur"]), chemin, f"parametres[nom={nom}].valeur"))
    return lignes


def _noms_de_travail(curseur) -> list[str]:
    curseur.execute(
        "select c.relname from pg_class c join pg_namespace n on n.oid = c.relnamespace "
        "where n.nspname = %s and c.relkind = 'r' and (c.relname like %s or c.relname like %s)",
        (SCHEMA, f"%{SUFFIXE_NEUF}", f"%{SUFFIXE_REBUT}"),
    )
    return [ligne[0] for ligne in curseur.fetchall()]


def echanger_les_noms(conn, curseur, schema: str, noms: list[str]) -> int:
    """Échange les noms courants et provisoires, TOUS dans une seule transaction.

    L'intention est qu'un lecteur ne puisse jamais voir un ensemble mi-neuf mi-ancien : soit tous
    les objets sont dans leur génération précédente, soit tous dans la nouvelle.

    Extrait en fonction pour être appelable isolément — sur le schéma d'instantané comme sur un
    schéma d'essai où la distinction entre deux générations est visible. Le comportement est
    identique à celui qu'avait ce bloc lorsqu'il était écrit dans le corps du rafraîchissement.

    Un nom sans table courante n'a rien à mettre au rebut : la condition ci-dessous couvre le
    premier échange, où aucune table courante n'existe encore.
    """
    curseur.execute(
        "select c.relname from pg_class c join pg_namespace n on n.oid = c.relnamespace "
        "where n.nspname = %s and c.relkind = 'r'",
        (schema,),
    )
    presentes = {ligne[0] for ligne in curseur.fetchall()}

    global DERNIERE_FENETRE_MS
    cibles = ", ".join(f"{schema}.{nom}" for nom in noms if nom in presentes)

    for tentative in range(1, TENTATIVES_ECHANGE + 1):
        conn.autocommit = False
        try:
            curseur.execute(f"set local lock_timeout = '{ATTENTE_VERROU_MS}ms'")
            # La phase exclusive commence ici : le chronomètre part juste avant la demande de
            # verrous et s'arrête à la validation. Il couvre donc l'attente des verrous, bornée
            # par le délai posé ci-dessus, et toute la durée pendant laquelle ils sont détenus.
            # C'est exactement ce qu'un lecteur peut avoir à attendre.
            depart = time.monotonic()
            if cibles:
                curseur.execute(f"lock table {cibles} in access exclusive mode")
            for nom in noms:
                if nom in presentes:
                    curseur.execute(f"alter table {schema}.{nom} rename to {nom}{SUFFIXE_REBUT}")
                curseur.execute(f"alter table {schema}.{nom}{SUFFIXE_NEUF} rename to {nom}")
            conn.commit()
            conn.autocommit = True
            DERNIERE_FENETRE_MS = (time.monotonic() - depart) * 1000
            return tentative
        except psycopg.errors.LockNotAvailable:
            conn.rollback()
            conn.autocommit = True
            time.sleep(TEMPORISATION_S(tentative))

    raise EchangeImpossible(
        f"l'echange n'a pas obtenu ses verrous en {TENTATIVES_ECHANGE} tentatives"
    )


def rafraichir() -> tuple[bool, str]:
    """Renvoie (réussite, message). Cinq temps : construire, échanger, nettoyer, dater, rendre."""
    global DERNIERE_FENETRE_MS
    DERNIERE_FENETRE_MS = None
    debut = time.monotonic()
    with chargeur.connexion() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"create schema if not exists {SCHEMA}")

            # Résidus d'un rafraîchissement interrompu : effacés au démarrage plutôt que
            # rencontrés au milieu. Sans cela, le `create table` sous nom provisoire échouerait
            # sur une table déjà là, et le module ne repartirait jamais seul.
            residus = _noms_de_travail(cur)
            for nom in residus:
                cur.execute(f"drop table if exists {SCHEMA}.{nom}")

            objets = objets_a_copier(cur)
            verifier_noms(objets)

            # 1. Construire les tables neuves, hors transaction d'échange : la construction est
            #    la partie longue, et rien n'exige qu'un lecteur l'attende.
            for schema, nom in objets:
                cur.execute(
                    f"create table {SCHEMA}.{nom}{SUFFIXE_NEUF} as select * from {schema}.{nom}"
                )

            # 2. Échanger tous les noms dans UNE SEULE transaction.
            #
            #    Si l'échange renonce, il n'a rien renommé : la transaction est annulée en bloc, et
            #    l'instantané reste dans sa génération précédente, cohérente. Le rafraîchissement
            #    rend alors un échec plutôt que de lever — c'est ce qui le rend journalisable et
            #    relançable par l'ordonnanceur, et c'est ce qui rend cet échec acceptable là où un
            #    échec de lecture ne le serait pas.
            try:
                tentatives = echanger_les_noms(conn, cur, SCHEMA, [nom for _, nom in objets])
            except EchangeImpossible as echec:
                for _, nom in objets:
                    cur.execute(f"drop table if exists {SCHEMA}.{nom}{SUFFIXE_NEUF}")
                return False, (
                    f"rafraichissement de {SCHEMA} : ECHEC - {echec} ; aucun renommage effectue, "
                    f"l'instantane reste dans sa generation precedente"
                )

            # 3. Supprimer les rebuts hors transaction : les tenir dans l'échange allongerait
            #    d'autant la fenêtre pendant laquelle le catalogue est verrouillé.
            for _, nom in objets:
                cur.execute(f"drop table if exists {SCHEMA}.{nom}{SUFFIXE_REBUT}")

            # 4. Les deux tables de service, écrites après coup : elles décrivent un état atteint.
            reference = date_de_reference(cur)
            fin = datetime.now(UTC)

            cur.execute(f"drop table if exists {SCHEMA}.{TABLE_ETAT}")
            cur.execute(
                f"create table {SCHEMA}.{TABLE_ETAT} ("
                "  rafraichi_le timestamptz not null,"
                "  date_reference_donnees date not null,"
                "  objet text not null,"
                "  lignes bigint not null)"
            )
            for _, nom in objets:
                cur.execute(f"select count(*) from {SCHEMA}.{nom}")
                cur.execute(
                    f"insert into {SCHEMA}.{TABLE_ETAT} values (%s, %s, %s, %s)",
                    (fin, reference, nom, cur.fetchone()[0]),
                )

            cur.execute(f"drop table if exists {SCHEMA}.{TABLE_PARAMETRES}")
            cur.execute(
                f"create table {SCHEMA}.{TABLE_PARAMETRES} ("
                "  nom text not null,"
                "  valeur text not null,"
                "  provenance_fichier text not null,"
                "  provenance_cle text not null)"
            )
            for ligne in parametres_repris():
                cur.execute(
                    f"insert into {SCHEMA}.{TABLE_PARAMETRES} values (%s, %s, %s, %s)", ligne
                )

            restants = _noms_de_travail(cur)

    duree = time.monotonic() - debut
    if restants:
        return False, (
            f"rafraichissement de {SCHEMA} : ECHEC - noms de travail subsistants {restants}"
        )
    return True, (
        f"rafraichissement de {SCHEMA} : OK - {len(objets)} objets copies, "
        f"{len(residus)} residus effaces au demarrage, {tentatives} tentative(s) d'echange, "
        f"date de reference {reference}, "
        f"duree {duree:.2f}s"
    )


def main() -> None:
    analyseur = argparse.ArgumentParser(
        description="Rafraichit le schema d'instantane que lit le tableau de bord : une copie "
        "de chaque objet publie, plus les deux tables de service."
    )
    analyseur.parse_args()

    reussite, message = rafraichir()
    print(message)
    if not reussite:
        sys.exit(1)


if __name__ == "__main__":
    main()
