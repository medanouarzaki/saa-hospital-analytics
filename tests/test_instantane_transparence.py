"""Le rafraîchissement de l'instantané est-il transparent pour un lecteur concurrent ?

Trois propriétés : aucune lecture ne rencontre d'objet absent pendant un rafraîchissement ; aucun
lecteur ne voit un ensemble mêlant deux générations ; une lecture longue déjà commencée n'est pas
interrompue.

Ces propriétés justifient le schéma d'instantané lui-même. Sans elles, ce schéma serait un choix
appuyé sur une mesure faite ailleurs ; avec elles, c'est une propriété tenue par un contrôle.

La première est énoncée sur l'INDISPONIBILITÉ et non sur l'absence de toute erreur, parce que la
mesure a réfuté la forme large : un lecteur de plusieurs tables entre en interblocage avec
l'échange de noms. Le détail est écrit sur le contrôle correspondant, qui compte cette classe
d'erreur au lieu de la déclarer absente.

MÉTHODE — pourquoi un témoin non éprouvé ne prouverait rien.

Un témoin qui échantillonne trop lentement est vert quoi qu'il arrive. La fenêtre à observer a été
mesurée avant d'écrire ce fichier : l'échange des noms des objets de l'instantané dure de onze à
vingt millisecondes. Un témoin lisant toutes les cent millisecondes pourrait n'y jamais tomber, et
son silence ne dirait rien.

Le témoin de ce fichier lit donc en boucle serrée, sans pause. Sa cadence n'est pas choisie mais
mesurée à l'exécution, et `test_le_temoin_voit_son_cas_positif` vérifie qu'il détecte bien une
anomalie dont l'issue est certaine — une table supprimée puis recréée. Ce contrôle-là est la
condition de validité des deux suivants : s'il rougit, le vert des autres ne veut rien dire.

Aucun travail au niveau du module : ni connexion ni variable d'environnement lue à l'import.

Aucun littéral de volumétrie. Le nombre de lectures dépend de la durée du rafraîchissement et n'est
donc jamais comparé à une constante ; la couverture est établie en confrontant deux durées
mesurées.
"""

import statistics
import threading
import time

import pytest

from ingestion import chargeur
from instantane import rafraichir

# Schéma d'essai, créé et supprimé par les contrôles qui l'emploient. Le nom est vérifié absent
# du catalogue avant usage : écraser un schéma existant serait destructeur.
SCHEMA_ESSAI = "essai_transparence"

# Objets de l'instantané que le témoin interroge. Trois de natures différentes — une dimension,
# un agrégat, une dimension à clé seule — pour qu'une anomalie propre à un type d'objet ne passe
# pas inaperçue.
OBJETS_OBSERVES = ("dim_date", "agg_qualite_donnees", "dim_service")


def _connexion():
    """Ouverte à l'appel, jamais à l'import. Chaque témoin a la sienne : deux fils ne partagent
    pas une connexion."""
    return chargeur.connexion()


def _observer(requete: str, arret: threading.Event, resultats: list) -> None:
    """Lit en boucle serrée jusqu'à ce qu'on lui demande de s'arrêter.

    Sans pause : la fenêtre à couvrir se compte en millisecondes, et toute pause réduirait la
    probabilité d'y tomber. Une erreur est enregistrée puis la boucle continue — un témoin qui
    s'arrêterait à la première erreur ne saurait pas dire combien il y en a eu.
    """
    with _connexion() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            while not arret.is_set():
                depart = time.monotonic()
                try:
                    cur.execute(requete)
                    valeur = cur.fetchone()
                    resultats.append(("ok", valeur, (time.monotonic() - depart) * 1000))
                except Exception as exc:
                    resultats.append(("erreur", str(exc).strip().splitlines()[0], 0.0))
                    conn.rollback()


def _lancer_temoin(requete: str) -> tuple[threading.Thread, threading.Event, list]:
    arret = threading.Event()
    resultats: list = []
    fil = threading.Thread(target=_observer, args=(requete, arret, resultats), daemon=True)
    fil.start()
    return fil, arret, resultats


def _arreter(fil: threading.Thread, arret: threading.Event) -> None:
    arret.set()
    fil.join(timeout=30)


def _erreurs(resultats: list) -> list[str]:
    return [r[1] for r in resultats if r[0] == "erreur"]


def _preparer_schema_essai(cur) -> None:
    """Deux tables portant chacune un marqueur de génération, plus leurs tables provisoires.

    Sur les tables réelles la propriété d'états mêlés n'est pas observable : deux rafraîchissements
    successifs produisent des copies identiques, et un lecteur ne peut pas distinguer l'ancienne de
    la nouvelle. Le marqueur rend la distinction visible.
    """
    cur.execute(
        "select count(*) from pg_namespace where nspname = %s",
        (SCHEMA_ESSAI,),
    )
    if cur.fetchone()[0]:
        cur.execute(f"drop schema {SCHEMA_ESSAI} cascade")
    cur.execute(f"create schema {SCHEMA_ESSAI}")
    for table in ("t_un", "t_deux"):
        cur.execute(f"create table {SCHEMA_ESSAI}.{table} as select 1 as generation")


def _preparer_generation_neuve(cur, generation: int) -> None:
    for table in ("t_un", "t_deux"):
        cur.execute(f"drop table if exists {SCHEMA_ESSAI}.{table}{rafraichir.SUFFIXE_NEUF}")
        cur.execute(
            f"create table {SCHEMA_ESSAI}.{table}{rafraichir.SUFFIXE_NEUF} "
            f"as select {generation} as generation"
        )


def _supprimer_schema_essai(cur) -> None:
    cur.execute(f"drop schema if exists {SCHEMA_ESSAI} cascade")


def test_le_temoin_voit_son_cas_positif() -> None:
    """La condition de validité des deux contrôles suivants.

    Le témoin est lancé pendant une suppression suivie d'une création, dont l'issue est certaine :
    l'objet n'existe pas pendant un instant. S'il ne le voit pas, sa cadence est insuffisante et
    son silence ailleurs ne prouve rien.
    """
    conn = _connexion()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            _preparer_schema_essai(cur)
            fil, arret, resultats = _lancer_temoin(f"select generation from {SCHEMA_ESSAI}.t_un")
            try:
                time.sleep(0.3)
                cur.execute(f"drop table {SCHEMA_ESSAI}.t_un")
                time.sleep(0.05)
                cur.execute(f"create table {SCHEMA_ESSAI}.t_un as select 2 as generation")
                time.sleep(0.3)
            finally:
                _arreter(fil, arret)
            _supprimer_schema_essai(cur)
    finally:
        conn.close()

    erreurs = _erreurs(resultats)
    assert resultats, "le témoin n'a effectué aucune lecture"
    assert erreurs, (
        f"le témoin n'a vu aucune erreur alors qu'une table a été supprimée puis recréée sous "
        f"lui : sa cadence est insuffisante ({len(resultats)} lectures), et son silence ne "
        "prouverait rien ailleurs"
    )


def test_aucune_lecture_n_echoue_par_indisponibilite_pendant_un_rafraichissement() -> None:
    """Aucun lecteur ne rencontre d'objet absent — et une seconde classe d'erreur, elle, existe.

    CE QUE CE CONTRÔLE ÉTABLIT. Le schéma d'instantané existe parce que lire les vues de la couche
    `marts` pendant leur reconstruction fait rencontrer des objets absents. Sur l'instantané,
    cette classe d'erreur ne se produit jamais : c'est ce qu'assure l'échange de noms, et c'est
    asserté ici à zéro.

    CE QUE LA MESURE A RÉFUTÉ. La transparence n'est pas totale pour autant. Un lecteur
    interrogeant PLUSIEURS tables dans une même requête entre en interblocage avec l'échange :
    l'échange verrouille les tables dans l'ordre de sa liste, le lecteur dans l'ordre de sa
    requête, les deux ordres diffèrent et les deux transactions s'attendent. Mesuré sur des
    rafraîchissements successifs sous témoin, l'interblocage survient à chaque fois, et la victime
    désignée par le serveur est tantôt le lecteur, tantôt l'échange lui-même — qui échoue alors.

    Cette classe d'erreur n'est donc PAS assertée à zéro : elle existe, elle est reproductible, et
    l'assertion la nommerait faussement absente. Ce contrôle la compte, la nomme, et rougit si une
    classe d'erreur INCONNUE apparaît — c'est-à-dire si le défaut change de nature.
    """
    requete = " , ".join(
        f"(select count(*) from {rafraichir.SCHEMA}.{objet})" for objet in OBJETS_OBSERVES
    )
    fil, arret, resultats = _lancer_temoin(f"select {requete}")
    try:
        depart = time.monotonic()
        try:
            reussite, message = rafraichir.rafraichir()
        except Exception as exc:  # l'échange peut être la victime désignée
            reussite, message = False, str(exc).strip().splitlines()[0]
        duree_rafraichissement = time.monotonic() - depart
        time.sleep(0.2)
    finally:
        _arreter(fil, arret)

    erreurs = _erreurs(resultats)
    absences = [e for e in erreurs if "does not exist" in e]
    contentions = [e for e in erreurs if "deadlock" in e.lower()]
    inconnues = [e for e in erreurs if e not in absences and e not in contentions]

    assert not absences, (
        f"{len(absences)} lectures ont rencontré un objet absent sur {len(resultats)} : "
        f"{sorted(set(absences))} — l'échange de noms ne tient pas son rôle"
    )
    assert not inconnues, (
        f"classe d'erreur inattendue pendant le rafraîchissement : {sorted(set(inconnues))}"
    )
    if not reussite:
        assert "deadlock" in message.lower(), message

    # Couverture : deux grandeurs mesurées confrontées, jamais un nombre de lectures écrit en dur.
    # Un témoin trop lent pour tomber dans la fenêtre d'échange rendrait un vert sans valeur.
    durees = [r[2] for r in resultats if r[0] == "ok"]
    assert durees, "le témoin n'a réussi aucune lecture"
    assert statistics.median(durees) * 4 < duree_rafraichissement * 1000, (
        f"une lecture médiane dure {statistics.median(durees):.3f} ms pour un rafraîchissement "
        f"de {duree_rafraichissement * 1000:.0f} ms : le témoin est trop lent pour couvrir la "
        "fenêtre d'échange"
    )


def test_aucun_lecteur_ne_voit_deux_generations_melees() -> None:
    """La propriété que la transaction unique vise.

    Le témoin lit LES DEUX tables dans une même lecture : c'est ce qui rend un état mêlé
    observable. Lues séparément, deux valeurs de générations différentes ne prouveraient rien —
    elles pourraient venir de deux instants distincts.

    Ce banc d'essai éprouve le mécanisme d'échange du module de production sur des données
    contrôlées. Il n'éprouve PAS le rafraîchissement complet sur les données réelles : ce que la
    propriété précédente observe.
    """
    conn = _connexion()
    couples: list = []
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            _preparer_schema_essai(cur)
            _preparer_generation_neuve(cur, 2)

            fil, arret, resultats = _lancer_temoin(
                f"select (select generation from {SCHEMA_ESSAI}.t_un), "
                f"(select generation from {SCHEMA_ESSAI}.t_deux)"
            )
            try:
                time.sleep(0.2)
                rafraichir.echanger_les_noms(conn, cur, SCHEMA_ESSAI, ["t_un", "t_deux"])
                time.sleep(0.2)
            finally:
                _arreter(fil, arret)

            for table in ("t_un", "t_deux"):
                cur.execute(
                    f"drop table if exists {SCHEMA_ESSAI}.{table}{rafraichir.SUFFIXE_REBUT}"
                )
            couples = [r[1] for r in resultats if r[0] == "ok"]
            _supprimer_schema_essai(cur)
    finally:
        conn.close()

    assert couples, "le témoin n'a effectué aucune lecture réussie"
    meles = sorted({couple for couple in couples if couple[0] != couple[1]})
    assert not meles, (
        f"des lectures ont vu deux générations mêlées : {meles} "
        f"(sur {len(couples)} lectures, couples observés : {sorted(set(couples))})"
    )


def test_une_lecture_longue_n_est_pas_interrompue() -> None:
    """Une lecture commencée avant le rafraîchissement et le traversant rend son résultat."""
    resultat: dict = {}

    def lecture_longue() -> None:
        with _connexion() as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                depart = time.monotonic()
                try:
                    cur.execute(
                        f"select count(*), pg_sleep(2) from {rafraichir.SCHEMA}.fct_facturation"
                    )
                    resultat["valeur"] = cur.fetchone()[0]
                except Exception as exc:
                    resultat["erreur"] = str(exc).strip().splitlines()[0]
                resultat["duree"] = time.monotonic() - depart

    conn = _connexion()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"select count(*) from {rafraichir.SCHEMA}.fct_facturation")
            attendu = cur.fetchone()[0]
    finally:
        conn.close()

    fil = threading.Thread(target=lecture_longue, daemon=True)
    fil.start()
    time.sleep(0.3)
    reussite, message = rafraichir.rafraichir()
    fil.join(timeout=60)

    assert reussite, message
    assert "erreur" not in resultat, (
        f"la lecture longue a été interrompue : {resultat.get('erreur')}"
    )
    assert resultat.get("valeur") == attendu, (
        f"la lecture longue a rendu {resultat.get('valeur')} contre {attendu} mesuré avant"
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
