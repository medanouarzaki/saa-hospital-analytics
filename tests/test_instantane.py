"""Contrôle du schéma d'instantané : le contenu qu'il porte égale-t-il celui qu'il copie ?

Une fonction par propriété, pour qu'une altération du module de rafraîchissement fasse rougir la
propriété qu'elle vise et elle seule.

Aucun travail au niveau du module : ni chargement, ni connexion, ni lecture de variable
d'environnement à l'import. Le fichier se collecte sur un clone frais sans base ni variable
exportée.

Aucun littéral de volumétrie. Chaque attendu est une égalité entre deux calculs indépendants —
l'un sur l'instantané, l'autre sur les objets d'origine ou sur le fichier suivi que la donnée
désigne. Écrire `assert nombre_de_tables == 26` ferait passer le contrôle pour vert alors qu'il ne
comparerait qu'une constante à elle-même.

Ces contrôles supposent un instantané rafraîchi. Ils ne l'héritent pas de l'environnement : la
fixture ci-dessous exécute le rafraîchissement une fois par session, ce qui rend le fichier
exécutable seul sur une base où seule la couche `marts` est construite.
"""

from pathlib import Path

import pytest

from ingestion import chargeur
from instantane import rafraichir

RACINE = Path(__file__).resolve().parent.parent

# L'empreinte de contenu, en une expression.
#
# `md5(t::text)` condense la ligne ENTIÈRE — toutes ses colonnes, dans l'ordre du tuple, que la
# copie préserve. Un décompte égal ne prouve rien sur les valeurs ; celle-ci les compare.
#
# La somme rend l'empreinte indépendante de l'ORDRE DES LIGNES : l'addition est commutative, et
# ni la vue ni la table copiée ne garantissent un ordre. Vérifié par mesure, la même table lue en
# ordre croissant puis décroissant rendant la même valeur.
#
# L'indépendance au FUSEAU est obtenue en le fixant, et non en l'espérant. La mesure a établi que
# six des objets copiés portent des colonnes horodatées avec fuseau et que, sous un fuseau autre
# que celui du serveur, la vue et sa copie rendent des instants distincts : les vues construisent
# leur horodatage depuis du texte, et l'interprètent dans le fuseau de la session, tandis que la
# copie fige l'interprétation faite au moment où elle a été prise. L'empreinte n'a donc de sens
# que sous un fuseau fixé, et chaque contrôle le fixe explicitement.
EMPREINTE = "sum(('x' || substr(md5(t::text), 1, 8))::bit(32)::bigint)"

FUSEAU = "UTC"


def _empreintes() -> dict:
    """Décompte et empreinte de chaque objet copié, sous fuseau fixé.

    Même forme d'empreinte que celle employée pour l'égalité de l'instantané : indépendante de
    l'ordre parce que l'addition est commutative, et évaluée sous fuseau fixé parce que six des
    objets portent des horodatages avec fuseau.
    """
    conn = _connexion()
    try:
        with conn.cursor() as curseur:
            curseur.execute("set time zone 'UTC'")
            curseur.execute(rafraichir.REQUETE_OBJETS)
            noms = [nom for _, nom in curseur.fetchall()]
            mesures = {}
            for nom in noms:
                curseur.execute(f"select count(*), {EMPREINTE} from {rafraichir.SCHEMA}.{nom} t")
                mesures[nom] = curseur.fetchone()
            return mesures
    finally:
        conn.close()


def _connexion():
    """Ouverte à l'appel, jamais à l'import."""
    conn = chargeur.connexion()
    with conn.cursor() as cur:
        cur.execute(f"set time zone '{FUSEAU}'")
    return conn


@pytest.fixture(scope="session")
def instantane_rafraichi() -> None:
    """La précondition est établie par le test, non héritée de l'environnement."""
    reussite, message = rafraichir.rafraichir()
    if not reussite:
        pytest.fail(
            f"le rafraichissement a échoué, les contrôles n'ont rien à vérifier : {message}"
        )


def _objets_copies(cur) -> list[tuple[str, str]]:
    return rafraichir.objets_a_copier(cur)


def _valeur(cur, requete: str):
    cur.execute(requete)
    return cur.fetchone()[0]


def test_le_peuplement_est_complet(instantane_rafraichi) -> None:
    """Les deux membres sont calculés depuis le catalogue, aucun n'est écrit.

    Le membre attendu est calculé par une requête PROPRE À CE CONTRÔLE, et non par la fonction
    que le module emploie lui-même pour dresser sa liste : dériver les deux membres de la même
    fonction reviendrait à comparer un résultat à lui-même, et un module qui omettrait un objet
    verrait son omission répercutée dans l'attendu. La règle de peuplement est donc réécrite ici,
    indépendamment, et c'est ce qui rend l'omission détectable.
    """
    conn = _connexion()
    try:
        with conn.cursor() as cur:
            observees = _valeur(
                cur,
                "select count(*) from pg_class c join pg_namespace n on n.oid = c.relnamespace "
                f"where n.nspname = '{rafraichir.SCHEMA}' and c.relkind = 'r'",
            )
            attendues = (
                _valeur(
                    cur,
                    "select count(*) from pg_class c "
                    "join pg_namespace n on n.oid = c.relnamespace "
                    "where n.nspname = 'marts' and c.relkind in ('v', 'm')",
                )
                + _valeur(
                    cur,
                    "select count(*) from pg_class c "
                    "join pg_namespace n on n.oid = c.relnamespace "
                    "where n.nspname = 'linkage' and c.relkind = 'r'",
                )
                + 1  # la vue intermédiaire qui porte les créances
                + 2  # les deux tables de service
            )
    finally:
        conn.close()

    assert observees == attendues, (
        f"{observees} tables dans l'instantané, {attendues} attendues "
        "(objets dérivés du catalogue, plus les deux tables de service)"
    )


def test_chaque_objet_copie_a_le_meme_nombre_de_lignes_que_son_origine(
    instantane_rafraichi,
) -> None:
    conn = _connexion()
    ecarts = []
    try:
        with conn.cursor() as cur:
            for schema, nom in _objets_copies(cur):
                origine = _valeur(cur, f"select count(*) from {schema}.{nom}")
                copie = _valeur(cur, f"select count(*) from {rafraichir.SCHEMA}.{nom}")
                if origine != copie:
                    ecarts.append(f"{schema}.{nom} : {copie} copié contre {origine} à l'origine")
    finally:
        conn.close()

    assert not ecarts, "décomptes divergents : " + " | ".join(ecarts)


def test_chaque_objet_copie_a_le_meme_contenu_que_son_origine(instantane_rafraichi) -> None:
    """Au-delà du décompte : deux tables de même taille peuvent porter des valeurs différentes."""
    conn = _connexion()
    ecarts = []
    try:
        with conn.cursor() as cur:
            for schema, nom in _objets_copies(cur):
                origine = _valeur(cur, f"select {EMPREINTE} from {schema}.{nom} t")
                copie = _valeur(cur, f"select {EMPREINTE} from {rafraichir.SCHEMA}.{nom} t")
                if origine != copie:
                    ecarts.append(f"{schema}.{nom} : empreinte {copie} copiée contre {origine}")
    finally:
        conn.close()

    assert not ecarts, "contenus divergents à décompte possiblement égal : " + " | ".join(ecarts)


def test_chaque_objet_cite_par_le_registre_existe_dans_l_instantane(instantane_rafraichi) -> None:
    """La propriété qui lie le registre des indicateurs au schéma que les pages liront."""
    import pathlib

    import yaml

    racine = pathlib.Path(rafraichir.__file__).resolve().parent.parent
    registre = yaml.safe_load(
        (racine / "dashboard" / "indicateurs.yml").read_text(encoding="utf-8")
    )
    cites = sorted({objet for entree in registre["indicateurs"] for objet in entree["objets_lus"]})

    conn = _connexion()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "select c.relname from pg_class c join pg_namespace n on n.oid = c.relnamespace "
                f"where n.nspname = '{rafraichir.SCHEMA}' and c.relkind = 'r'"
            )
            presentes = {ligne[0] for ligne in cur.fetchall()}
    finally:
        conn.close()

    absents = [objet for objet in cites if objet.split(".", 1)[1] not in presentes]
    assert not absents, f"objets cités par le registre et absents de l'instantané : {absents}"


def test_la_date_de_reference_est_celle_des_donnees_et_non_de_l_horloge(
    instantane_rafraichi,
) -> None:
    """Mesurée indépendamment sur la couche source, sans passer par le module."""
    conn = _connexion()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "select table_name from information_schema.columns "
                "where table_schema = 'source' and column_name = 'date_extraction'"
            )
            tables = [ligne[0] for ligne in cur.fetchall()]
            union = " union all ".join(
                f"select max(to_date(date_extraction, 'MM/DD/YYYY')) as d from source.{t}"
                for t in tables
            )
            attendue = _valeur(cur, f"select max(d) from ({union}) as toutes")
            portee = _valeur(
                cur,
                f"select max(date_reference_donnees) from "
                f"{rafraichir.SCHEMA}.{rafraichir.TABLE_ETAT}",
            )
    finally:
        conn.close()

    assert portee == attendue, (
        f"date de référence {portee} portée par l'instantané, {attendue} mesurée sur la couche "
        "source"
    )


def test_le_parametre_egale_la_valeur_du_fichier_que_sa_provenance_designe(
    instantane_rafraichi,
) -> None:
    """Le contrôle relit le fichier que la donnée elle-même désigne : la provenance est
    vérifiable, et non décorative. Une provenance qui pointerait ailleurs ferait rougir ceci."""
    import pathlib

    import yaml

    conn = _connexion()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"select nom, valeur, provenance_fichier, provenance_cle from "
                f"{rafraichir.SCHEMA}.{rafraichir.TABLE_PARAMETRES}"
            )
            lignes = cur.fetchall()
    finally:
        conn.close()

    assert lignes, "la table de paramètres est vide"

    racine = pathlib.Path(rafraichir.__file__).resolve().parent.parent
    ecarts = []
    for nom, valeur, fichier, cle in lignes:
        chemin = racine / fichier
        if not chemin.exists():
            ecarts.append(f"{nom} : la provenance désigne {fichier}, qui n'existe pas")
            continue
        contenu = yaml.safe_load(chemin.read_text(encoding="utf-8"))
        attendue = {e["nom"]: e["valeur"] for e in contenu["parametres"]}.get(nom)
        if attendue is None:
            ecarts.append(f"{nom} : absent de {fichier}, que sa provenance désigne")
        elif str(attendue) != valeur:
            ecarts.append(f"{nom} : {valeur} porté contre {attendue} dans {fichier}")
        elif nom not in cle:
            ecarts.append(f"{nom} : la clé de provenance '{cle}' ne désigne pas ce paramètre")

    assert not ecarts, "provenance non vérifiée : " + " | ".join(ecarts)


def test_deux_rafraichissements_concurrents_laissent_l_instantane_coherent() -> None:
    """Deux invocations simultanées : la seconde renonce, l'instantané reste cohérent.

    Sans verrou, les deux se heurtaient sur la création de leurs tables provisoires et l'une levait
    une exception non traitée — mesuré sur trois paires lancées sur trois. La tâche étant désormais
    branchée à une chaîne quotidienne, deux exécutions peuvent se recouvrir, et le défaut cesse
    d'être théorique.

    Le contrôle vérifie trois choses : aucune des deux invocations ne lève, exactement une renonce,
    et l'instantané est intact après — décomptes et empreintes de ses objets inchangés.
    """
    import threading

    from instantane import rafraichir

    avant = _empreintes()

    resultats: dict[str, tuple] = {}

    def lancer(nom: str) -> None:
        try:
            resultats[nom] = rafraichir.rafraichir()
        except Exception as echec:  # une exception non traitée est précisément le défaut
            resultats[nom] = ("exception", f"{type(echec).__name__}: {echec}")

    fils = [threading.Thread(target=lancer, args=(nom,)) for nom in ("premier", "second")]
    for fil in fils:
        fil.start()
    for fil in fils:
        fil.join(timeout=300)

    exceptions = [message for issue, message in resultats.values() if issue == "exception"]
    assert not exceptions, f"une invocation a levé au lieu de renoncer : {exceptions}"

    renoncements = [
        message
        for issue, message in resultats.values()
        if issue is False and rafraichir.MARQUE_RENONCEMENT in message
    ]
    reussites = [message for issue, message in resultats.values() if issue is True]
    assert len(renoncements) == 1, (
        f"{len(renoncements)} renoncement(s) pour deux invocations concurrentes : "
        f"{list(resultats.values())}"
    )
    assert len(reussites) == 1, (
        f"{len(reussites)} réussite(s) pour deux invocations concurrentes : "
        f"{list(resultats.values())}"
    )

    assert _empreintes() == avant, "deux invocations concurrentes ont modifié l'instantané"


def test_le_renoncement_rend_un_code_de_sortie_distinct_de_l_echec() -> None:
    """Le code de sortie sépare « un autre était en cours » d'une défaillance.

    Un ordonnanceur qui ne verrait qu'un code non nul confondrait les deux. Le contrôle tient le
    verrou depuis une session tierce, puis invoque le module en ligne de commande.
    """
    import subprocess
    import sys

    from ingestion import chargeur
    from instantane import rafraichir

    conn = chargeur.connexion()
    conn.autocommit = True
    try:
        with conn.cursor() as curseur:
            curseur.execute("select pg_try_advisory_lock(%s)", (rafraichir.CLE_VERROU,))
            assert curseur.fetchone()[0], (
                "le verrou est déjà détenu : le contrôle ne prouverait rien"
            )

        empeche = subprocess.run(
            [sys.executable, "-m", "instantane.rafraichir"],
            capture_output=True,
            text=True,
            cwd=RACINE,
            check=False,
        )
    finally:
        conn.close()

    assert empeche.returncode == rafraichir.CODE_RENONCEMENT, (
        f"code {empeche.returncode} pour un renoncement, "
        f"{rafraichir.CODE_RENONCEMENT} attendu : {empeche.stdout.strip()}"
    )
    assert rafraichir.MARQUE_RENONCEMENT in empeche.stdout, empeche.stdout

    libre = subprocess.run(
        [sys.executable, "-m", "instantane.rafraichir"],
        capture_output=True,
        text=True,
        cwd=RACINE,
        check=False,
    )
    assert libre.returncode == 0, (
        f"le verrou étant libre, le rafraîchissement devait aboutir : {libre.stdout.strip()}"
    )


def test_deux_rafraichissements_consecutifs_laissent_le_meme_etat(instantane_rafraichi) -> None:
    """Idempotence : décomptes, empreintes, et absence de tout nom de travail."""
    conn = _connexion()
    try:
        with conn.cursor() as cur:
            objets = _objets_copies(cur)
            avant = {
                nom: (
                    _valeur(cur, f"select count(*) from {rafraichir.SCHEMA}.{nom}"),
                    _valeur(cur, f"select {EMPREINTE} from {rafraichir.SCHEMA}.{nom} t"),
                )
                for _, nom in objets
            }
    finally:
        conn.close()

    reussite, message = rafraichir.rafraichir()
    assert reussite, message

    conn = _connexion()
    try:
        with conn.cursor() as cur:
            apres = {
                nom: (
                    _valeur(cur, f"select count(*) from {rafraichir.SCHEMA}.{nom}"),
                    _valeur(cur, f"select {EMPREINTE} from {rafraichir.SCHEMA}.{nom} t"),
                )
                for _, nom in objets
            }
            cur.execute(
                "select c.relname from pg_class c join pg_namespace n on n.oid = c.relnamespace "
                f"where n.nspname = '{rafraichir.SCHEMA}' "
                f"and (c.relname like '%{rafraichir.SUFFIXE_NEUF}' "
                f"or c.relname like '%{rafraichir.SUFFIXE_REBUT}')"
            )
            residus = [ligne[0] for ligne in cur.fetchall()]
    finally:
        conn.close()

    divergents = sorted(nom for nom in avant if avant[nom] != apres[nom])
    assert not divergents, f"objets modifiés par un second rafraîchissement : {divergents}"
    assert not residus, f"noms de travail subsistants après rafraîchissement : {residus}"
