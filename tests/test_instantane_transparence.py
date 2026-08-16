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

# La charge de déploiement, dérivée et non choisie. La rafale est le nombre d'indicateurs de la
# page la plus lourde, relevé au registre : huit. L'intervalle est la durée d'affichage d'une page,
# obtenue en divisant par sept la durée mesurée des sept pages contre les tables copiées ; c'est
# une borne basse volontairement pessimiste, un lecteur humain étant plus lent que l'écran. Le
# nombre de lecteurs est, lui, une HYPOTHÈSE de déploiement et non une mesure : le tableau de bord
# est un outil de service interne, non une application publique.
#
# Chaque lecture porte sur plusieurs tables dans une même requête : c'est cette forme, et elle
# seule, qui croise l'ordre d'acquisition de l'échange.
RAFALE = 8
INTERVALLE_S = 0.208
LECTEURS_DEPLOIEMENT = 4

# Nombre de rafraîchissements par passage de la propriété d'aboutissement. Il n'entre dans aucune
# assertion — celle-ci compare les lancés aux aboutis — et ne sert qu'à borner la durée du contrôle.
TOURS_DE_CHARGE = 3

# Nombre de tours servant à mesurer les deux ancres de la propriété de phase exclusive. Il
# n'entre dans aucune assertion : seules les médianes des durées mesurées y entrent.
TOURS_D_ANCRAGE = 7


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


def _observer_deploiement(requete: str, arret: threading.Event, resultats: list) -> None:
    """Une rafale de lectures, puis l'intervalle d'une page, jusqu'à l'arrêt."""
    with _connexion() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            while not arret.is_set():
                for _ in range(RAFALE):
                    if arret.is_set():
                        break
                    depart = time.monotonic()
                    try:
                        cur.execute(requete)
                        valeur = cur.fetchone()
                        resultats.append(("ok", valeur, (time.monotonic() - depart) * 1000))
                    except Exception as exc:
                        resultats.append(("erreur", str(exc).strip().splitlines()[0], 0.0))
                        conn.rollback()
                time.sleep(INTERVALLE_S)


def _lancer_charge_deploiement(requete: str):
    arret = threading.Event()
    resultats: list = []
    fils = [
        threading.Thread(
            target=_observer_deploiement, args=(requete, arret, resultats), daemon=True
        )
        for _ in range(LECTEURS_DEPLOIEMENT)
    ]
    for fil in fils:
        fil.start()
    return fils, arret, resultats


def _arreter_tous(fils, arret: threading.Event) -> None:
    arret.set()
    for fil in fils:
        fil.join(timeout=60)


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


def _empreintes() -> dict:
    """Décompte et empreinte de chaque objet copié, sous fuseau fixé.

    La même forme d'empreinte que celle des contrôles d'égalité : une somme de condensés de lignes,
    indépendante de l'ordre parce que l'addition est commutative, et évaluée sous fuseau fixé parce
    que six des objets portent des horodatages avec fuseau.
    """
    conn = _connexion()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("set time zone 'UTC'")
            cur.execute(rafraichir.REQUETE_OBJETS)
            noms = [nom for _, nom in cur.fetchall()]
            mesures = {}
            for nom in noms:
                cur.execute(
                    f"select count(*), sum(('x' || substr(md5(t::text), 1, 8))::bit(32)::bigint) "
                    f"from {rafraichir.SCHEMA}.{nom} t"
                )
                mesures[nom] = cur.fetchone()
            return mesures
    finally:
        conn.close()


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


def test_aucune_lecture_n_echoue_pendant_un_rafraichissement() -> None:
    """AUCUNE erreur de lecture, quelle qu'en soit la classe, pendant un rafraîchissement.

    CETTE PROPRIÉTÉ A ÉTÉ DURCIE. Elle assertait auparavant la seule absence d'objet manquant, en
    tolérant explicitement une classe d'erreur nommée — l'interblocage entre un lecteur de
    plusieurs tables et l'échange de noms, alors reproductible à chaque rafraîchissement. Elle
    n'admet plus aucune exception : toute erreur, quelle que soit sa classe, la fait rougir.

    En quoi la nouvelle formulation est plus forte : l'ancienne classait les erreurs et n'en
    interdisait qu'une sorte, si bien qu'un défaut de nature nouvelle mais rangeable dans la classe
    tolérée serait passé inaperçu. La nouvelle n'a pas de classe tolérée, donc rien à ranger : elle
    compare un décompte à zéro. Elle interdit aussi ce qu'elle tolérait, ce que le module ne peut
    tenir que depuis l'adoption de sa discipline de verrouillage.

    LA CHARGE EMPLOYÉE EST LE TÉMOIN EN BOUCLE SERRÉE, et non la charge de déploiement, parce que
    la clause qu'elle traduit exige zéro échec de lecture SOUS TOUTE CHARGE. C'est la seule
    propriété de ce fichier à employer le témoin : les autres portent sur ce que le module doit
    tenir en service, et emploient la charge de déploiement.
    """
    requete = " , ".join(
        f"(select count(*) from {rafraichir.SCHEMA}.{objet})" for objet in OBJETS_OBSERVES
    )
    fil, arret, resultats = _lancer_temoin(f"select {requete}")
    try:
        depart = time.monotonic()
        reussite, message = rafraichir.rafraichir()
        duree_rafraichissement = time.monotonic() - depart
        time.sleep(0.2)
    finally:
        _arreter(fil, arret)

    erreurs = _erreurs(resultats)
    assert not erreurs, (
        f"{len(erreurs)} lectures en erreur sur {len(resultats)} pendant le rafraîchissement : "
        f"{sorted(set(erreurs))}"
    )
    assert reussite, message

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


def test_le_rafraichissement_aboutit_sous_la_charge_de_deploiement() -> None:
    """La moitié du défaut qui avait été manquée : le rafraîchissement lui-même peut échouer.

    Rien ne vérifiait que le module aboutissait. Il pouvait être désigné victime d'un interblocage
    et échouer, sans qu'aucune propriété ne le voie — le contrôle observait le lecteur seulement.

    L'attendu est une égalité entre deux mesures — rafraîchissements lancés et rafraîchissements
    aboutis — et non un littéral : le nombre de tours ci-dessous peut changer sans que l'assertion
    devienne fausse ou creuse.

    LA CHARGE EMPLOYÉE EST CELLE DU DÉPLOIEMENT, parce que la clause qu'elle traduit ne porte que
    sur elle : sous une charge de lecture arbitrairement intense, un échange qui renonce plutôt que
    de disputer ne peut pas garantir d'aboutir, et l'exiger reviendrait à exiger l'impossible.
    """
    requete = " , ".join(
        f"(select count(*) from {rafraichir.SCHEMA}.{objet})" for objet in OBJETS_OBSERVES
    )
    fils, arret, resultats = _lancer_charge_deploiement(f"select {requete}")
    lances = aboutis = 0
    messages = []
    try:
        for _ in range(TOURS_DE_CHARGE):
            lances += 1
            reussite, message = rafraichir.rafraichir()
            if reussite:
                aboutis += 1
            else:
                messages.append(message)
    finally:
        _arreter_tous(fils, arret)

    assert aboutis == lances, (
        f"{aboutis} rafraîchissements aboutis sur {lances} lancés sous la charge de déploiement : "
        f"{messages}"
    )
    assert not _erreurs(resultats), (
        f"lectures en erreur sous la charge de déploiement : {sorted(set(_erreurs(resultats)))}"
    )


def test_un_renoncement_ne_renomme_rien_et_laisse_l_instantane_coherent() -> None:
    """La défaillance est propre — c'est cette clause qui rend un échec d'échange acceptable.

    Un échec de lecture est vu par l'utilisateur, sans recours. Un échec d'échange est vu par
    l'ordonnanceur, journalisé et relançable — mais cela ne vaut QUE si l'échec ne laisse aucun
    renommage partiel derrière lui. Sans cette propriété, l'asymétrie entre les deux classes
    d'échec ne tiendrait pas.

    Le renoncement est provoqué par un lecteur qui tient un verrou partagé pendant toute la durée
    de l'échange, ce qui fait échouer toutes les tentatives.
    """
    empreintes_avant = _empreintes()

    tenu, relacher = threading.Event(), threading.Event()

    def bloqueur() -> None:
        with _connexion() as conn:
            with conn.cursor() as cur:
                cur.execute(f"select count(*) from {rafraichir.SCHEMA}.{OBJETS_OBSERVES[0]}")
                tenu.set()
                relacher.wait(timeout=180)
            conn.rollback()

    fil = threading.Thread(target=bloqueur, daemon=True)
    fil.start()
    tenu.wait(timeout=30)
    try:
        reussite, message = rafraichir.rafraichir()
    finally:
        relacher.set()
        fil.join(timeout=60)

    assert not reussite, (
        "le rafraîchissement a abouti alors qu'un verrou était tenu pendant tout l'échange : "
        "le renoncement n'a pas été provoqué, et cette propriété ne prouve rien"
    )
    assert "aucun renommage" in message, message

    assert _empreintes() == empreintes_avant, (
        "le renoncement a laissé l'instantané dans un état différent"
    )

    conn = _connexion()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                "select c.relname from pg_class c join pg_namespace n on n.oid = c.relnamespace "
                f"where n.nspname = '{rafraichir.SCHEMA}' "
                f"and (c.relname like '%{rafraichir.SUFFIXE_NEUF}' "
                f"or c.relname like '%{rafraichir.SUFFIXE_REBUT}')"
            )
            residus = [ligne[0] for ligne in cur.fetchall()]
    finally:
        conn.close()
    assert not residus, f"noms de travail subsistants après un renoncement : {residus}"


def test_la_phase_exclusive_reste_une_operation_de_catalogue() -> None:
    """L'échange verrouille le temps d'écrire des noms, pas le temps de recopier des données.

    CE QUE CETTE PROPRIÉTÉ GARDE. Le schéma d'instantané existe pour qu'un lecteur ne subisse rien
    pendant la reconstruction. Les autres propriétés vérifient qu'il ne voit ni objet absent ni
    état mêlé ; aucune ne vérifiait qu'il n'ATTEND pas. Une conception qui recopierait les données
    en tenant les verrous les passerait toutes tout en faisant patienter le lecteur dix fois plus
    longtemps. C'est cette dimension-là que celle-ci mesure.

    POURQUOI ELLE PORTE SUR LA PHASE EXCLUSIVE ET NON SUR L'ATTENTE OBSERVÉE. L'attente d'un
    lecteur est bornée par le délai au bout duquel l'échange renonce, et non par le travail que
    l'échange accomplit : sous forte charge, un lecteur attend cette borne quelle que soit la
    conception, si bien que l'attente observée ne distingue plus rien. La durée de la phase
    exclusive, elle, mesure exactement le travail fait sous verrou.

    AUCUN LITTÉRAL. Le seuil n'est pas écrit : il est la moyenne géométrique de deux durées
    mesurées dans la même exécution, sur un schéma d'essai — le renommage d'une table, qui est une
    opération de catalogue, et la copie d'une table de taille comparable au plus gros objet copié,
    qui est une opération de données. Ces deux ancres sont séparées de plus d'un ordre de grandeur,
    et leur moyenne géométrique est le point qui les sépare sans privilégier l'une ni l'autre.
    Comparer le temps passé sous verrou par objet à ce point, c'est demander : ce que fait
    l'échange sous verrou ressemble-t-il plutôt à écrire un nom, ou plutôt à recopier une table ?
    """
    conn = _connexion()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            _preparer_schema_essai(cur)
            cur.execute(
                "select relname from pg_stat_user_tables "
                f"where schemaname = '{rafraichir.SCHEMA}' order by n_live_tup desc limit 1"
            )
            plus_gros = cur.fetchone()[0]
            cur.execute(
                f"create table {SCHEMA_ESSAI}.socle as "
                f"select * from {rafraichir.SCHEMA}.{plus_gros}"
            )

            renommages, copies = [], []
            for tour in range(TOURS_D_ANCRAGE):
                depart = time.monotonic()
                cur.execute(f"alter table {SCHEMA_ESSAI}.socle rename to socle_{tour}")
                renommages.append((time.monotonic() - depart) * 1000)

                depart = time.monotonic()
                cur.execute(
                    f"create table {SCHEMA_ESSAI}.copie_{tour} as "
                    f"select * from {SCHEMA_ESSAI}.socle_{tour}"
                )
                copies.append((time.monotonic() - depart) * 1000)

                cur.execute(f"drop table {SCHEMA_ESSAI}.copie_{tour}")
                cur.execute(f"alter table {SCHEMA_ESSAI}.socle_{tour} rename to socle")

            cur.execute(rafraichir.REQUETE_OBJETS)
            objets = len(cur.fetchall())
            _supprimer_schema_essai(cur)
    finally:
        conn.close()

    ancre_catalogue = statistics.median(renommages)
    ancre_donnees = statistics.median(copies)
    assert ancre_donnees > ancre_catalogue, (
        f"les deux ancres ne sont pas séparées — catalogue {ancre_catalogue:.3f} ms, "
        f"données {ancre_donnees:.3f} ms — le seuil qu'elles encadrent n'aurait aucun sens"
    )
    seuil = (ancre_catalogue * ancre_donnees) ** 0.5

    reussite, message = rafraichir.rafraichir()
    assert reussite, message
    phase = rafraichir.DERNIERE_FENETRE_MS
    assert phase is not None, "le module n'a pas rendu la durée de sa phase exclusive"

    par_objet = phase / objets
    assert par_objet < seuil, (
        f"la phase exclusive dure {phase:.2f} ms pour {objets} objets, soit {par_objet:.3f} ms "
        f"par objet, au-dessus du point {seuil:.3f} ms qui sépare une opération de catalogue "
        f"({ancre_catalogue:.3f} ms) d'une opération de données ({ancre_donnees:.3f} ms) : "
        "l'échange recopie sous verrou au lieu de se contenter d'échanger des noms"
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
