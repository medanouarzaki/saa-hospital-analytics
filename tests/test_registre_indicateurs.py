"""Contrôle du registre des indicateurs : `dashboard/indicateurs.yml`.

Une fonction de test par propriété, pour qu'une altération du registre puisse
faire rougir la propriété qu'elle vise et elle seule. Une fonction qui
vérifierait plusieurs propriétés rendrait indiscernables les causes d'échec.

Aucun travail au niveau du module : le registre n'est pas chargé à l'import, la
connexion n'est pas ouverte à l'import, et aucune variable d'environnement n'est
lue à l'import. Le fichier se collecte sur un clone frais sans base ni variable
exportée -- c'est ce que vérifie le garde-fou de collecte, qui compte les
fonctions collectées par pytest sans les exécuter.

Aucun littéral de volumétrie. Chaque décompte attendu est une égalité entre deux
calculs indépendants : l'un depuis les entrées, l'autre depuis l'en-tête du
registre. Écrire `assert len(entrees) == 37` ferait passer le test pour vert
alors qu'il ne comparerait qu'une constante à elle-même.

La propriété qui confronte les objets cités au catalogue exige une base où la
couche `marts` est construite. Elle est donc placée à l'emplacement
d'intégration continue qui démarre un service PostgreSQL et exécute la
construction dbt ; les sept autres propriétés n'exigent rien d'autre que le
fichier et s'exécutent au même endroit, pour que le registre ne soit pas contrôlé
à deux endroits différents.
"""

import re
from pathlib import Path

import psycopg
import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
REGISTRE = RACINE / "dashboard" / "indicateurs.yml"
APPLIQUER_DDL = RACINE / "ingestion" / "appliquer_ddl.py"

CLES_OBLIGATOIRES = (
    "identifiant",
    "page",
    "libelle",
    "definition",
    "decision_servie",
    "objets_lus",
    "filtrabilite",
    "recalcule_depuis",
)

CLES_EN_TETE = ("examen_initial", "composition", "filtrabilite_attendue", "pages", "indicateurs")

VALEURS_FILTRABILITE = ("oui", "oui_sous_reserve", "non")

MOTIFS_NON_FILTRABLE = (
    "objet_sans_colonne_temporelle",
    "grandeur_annualisee",
    "date_hors_couche_des_faits",
)

# Un identifiant de la forme « une lettre suivie d'un chiffre » évoquerait une
# numérotation d'étape plutôt qu'un nom d'indicateur. Le filet permanent du dépôt
# ne couvre pas cette forme sur un identifiant ; ce contrôle la couvre ici.
#
# Le motif s'applique aux SEGMENTS de l'identifiant, séparés par le tiret bas, et
# non à la chaîne entière : le tiret bas est un caractère de mot, si bien qu'une
# limite de mot ne se place pas entre lui et la lettre qui le suit. Un motif
# appliqué à la chaîne entière laisserait donc passer la forme la plus probable,
# celle d'un segment ajouté en fin d'identifiant.
MOTIF_SEGMENT_INTERDIT = re.compile(r"^[A-Za-z][0-9]+$")

# Une définition d'une seule phrase : le texte se termine par un point unique et
# ne porte aucun point suivi d'une espace puis d'une majuscule ou d'un chiffre.
# Cette formulation tolère les abréviations et les décimales à l'intérieur de la
# phrase (« 90e centile », « 0,5 »), qui ne sont pas des fins de phrase.
MOTIF_NOUVELLE_PHRASE = re.compile(r"\.\s+[A-ZÀÉÈÊÎÔÛ0-9]")


def _registre() -> dict:
    """Chargé à l'appel, jamais à l'import."""
    return yaml.safe_load(REGISTRE.read_text(encoding="utf-8"))


def _entrees() -> list[dict]:
    return _registre()["indicateurs"]


def _charger_module(chemin: Path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(chemin.stem, chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _connexion() -> psycopg.Connection:
    """Ouverte à l'appel, jamais à l'import. Même mécanisme que les autres tests
    de ce répertoire qui exigent une base."""
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
            f"connexion impossible à la base ({exc}) : la couche marts doit être "
            "construite avant ce test"
        )


def test_registre_se_charge_et_porte_ses_cles_d_en_tete() -> None:
    registre = _registre()
    manquantes = [cle for cle in CLES_EN_TETE if cle not in registre]
    assert not manquantes, f"clés absentes de l'en-tête du registre : {manquantes}"
    assert registre["indicateurs"], "le registre ne porte aucune entrée"


def test_identifiants_uniques_et_sans_forme_de_numerotation() -> None:
    identifiants = [entree["identifiant"] for entree in _entrees()]

    doublons = sorted({i for i in identifiants if identifiants.count(i) > 1})
    assert not doublons, f"identifiants en doublon : {doublons}"

    fautifs = [
        identifiant
        for identifiant in identifiants
        if any(MOTIF_SEGMENT_INTERDIT.match(segment) for segment in identifiant.split("_"))
    ]
    assert not fautifs, f"identifiants portant un segment lettre suivie de chiffres : {fautifs}"


def test_chaque_entree_porte_toutes_les_cles_obligatoires_non_vides() -> None:
    fautifs = []
    for entree in _entrees():
        identifiant = entree.get("identifiant", "<sans identifiant>")
        for cle in CLES_OBLIGATOIRES:
            if cle not in entree:
                fautifs.append(f"{identifiant} : clé '{cle}' absente")
            elif not entree[cle]:
                fautifs.append(f"{identifiant} : clé '{cle}' vide")
    assert not fautifs, "clés obligatoires manquantes ou vides : " + " | ".join(fautifs)


def test_chaque_definition_est_une_seule_phrase() -> None:
    fautifs = []
    for entree in _entrees():
        definition = " ".join(entree["definition"].split())
        if not definition.endswith("."):
            fautifs.append(f"{entree['identifiant']} : la définition ne finit pas par un point")
        elif MOTIF_NOUVELLE_PHRASE.search(definition):
            fautifs.append(f"{entree['identifiant']} : la définition compte plus d'une phrase")
    assert not fautifs, "définitions non conformes : " + " | ".join(fautifs)


def test_chaque_page_est_declaree_et_toutes_les_pages_sont_representees() -> None:
    registre = _registre()
    declarees = set(registre["pages"])
    employees = {entree["page"] for entree in registre["indicateurs"]}

    inconnues = sorted(employees - declarees)
    assert not inconnues, f"pages employées mais non déclarées : {inconnues}"

    vides = sorted(declarees - employees)
    assert not vides, f"pages déclarées mais sans aucune entrée : {vides}"


def test_filtrabilite_valide_avec_motif_ou_reserve() -> None:
    fautifs = []
    for entree in _entrees():
        identifiant = entree["identifiant"]
        valeur = entree["filtrabilite"]

        if valeur not in VALEURS_FILTRABILITE:
            fautifs.append(
                f"{identifiant} : filtrabilité '{valeur}' hors des trois valeurs admises"
            )
            continue

        if valeur == "non":
            motif = entree.get("motif")
            if motif not in MOTIFS_NON_FILTRABLE:
                fautifs.append(f"{identifiant} : motif '{motif}' hors des trois motifs admis")
        elif valeur == "oui_sous_reserve":
            if not entree.get("reserve"):
                fautifs.append(f"{identifiant} : filtrabilité sous réserve sans réserve écrite")
        elif not entree.get("colonne_de_date"):
            fautifs.append(f"{identifiant} : filtrable sans colonne de date nommée")

    assert not fautifs, "filtrabilité non conforme : " + " | ".join(fautifs)


def test_chaque_objet_cite_existe_au_catalogue() -> None:
    cites = sorted({objet for entree in _entrees() for objet in entree["objets_lus"]})

    connexion = _connexion()
    try:
        with connexion.cursor() as curseur:
            curseur.execute(
                "select n.nspname || '.' || c.relname "
                "from pg_class c join pg_namespace n on n.oid = c.relnamespace "
                "where c.relkind in ('r', 'v', 'm')"
            )
            catalogue = {ligne[0] for ligne in curseur.fetchall()}
    finally:
        connexion.close()

    absents = [objet for objet in cites if objet not in catalogue]
    assert not absents, f"objets cités au registre et absents du catalogue : {absents}"


def test_les_deux_reconciliations_de_l_en_tete_se_verifient() -> None:
    registre = _registre()
    entrees = registre["indicateurs"]
    examen = registre["examen_initial"]
    composition = registre["composition"]
    attendue = registre["filtrabilite_attendue"]

    # Composition : le nombre d'entrées se retrouve par deux chemins indépendants
    # -- le décompte des entrées d'une part, l'arithmétique de l'en-tête d'autre part.
    calculee = examen["elements_examines"] - composition["exclus"] + composition["dedoubles"]
    assert calculee == composition["entrees_attendues"], (
        f"l'arithmétique de composition de l'en-tête ne se referme pas : "
        f"{examen['elements_examines']} - {composition['exclus']} + {composition['dedoubles']} "
        f"= {calculee}, annoncé {composition['entrees_attendues']}"
    )
    assert len(entrees) == composition["entrees_attendues"], (
        f"{len(entrees)} entrées au registre, {composition['entrees_attendues']} annoncées "
        "par l'en-tête"
    )

    # Filtrabilité : les décomptes mesurés sur les entrées contre ceux de l'en-tête.
    mesuree = {valeur: 0 for valeur in VALEURS_FILTRABILITE}
    for entree in entrees:
        mesuree[entree["filtrabilite"]] += 1

    ecarts = [
        f"{valeur} : {mesuree[valeur]} mesuré contre {attendue[valeur]} annoncé"
        for valeur in VALEURS_FILTRABILITE
        if mesuree[valeur] != attendue[valeur]
    ]
    assert not ecarts, "décomptes de filtrabilité divergents : " + " | ".join(ecarts)

    assert sum(mesuree.values()) == len(entrees), (
        f"la somme des filtrabilités vaut {sum(mesuree.values())} pour {len(entrees)} entrées"
    )

    # Le mouvement de reclassement se referme lui aussi, par deux chemins.
    filtrables_attendus = (
        examen["filtrables"] + composition["dedoubles"] + composition["reclasses_filtrables"]
    )
    non_attendus = (
        examen["non_filtrables"] - composition["exclus"] - composition["reclasses_filtrables"]
    )
    assert mesuree["oui"] + mesuree["oui_sous_reserve"] == filtrables_attendus, (
        f"{mesuree['oui'] + mesuree['oui_sous_reserve']} entrées filtrables mesurées contre "
        f"{filtrables_attendus} attendues par les mouvements de l'en-tête"
    )
    assert mesuree["non"] == non_attendus, (
        f"{mesuree['non']} entrées non filtrables mesurées contre {non_attendus} attendues "
        "par les mouvements de l'en-tête"
    )
