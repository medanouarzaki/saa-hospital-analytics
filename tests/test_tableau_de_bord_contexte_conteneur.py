"""Rendu des pages du tableau de bord dans le contexte d'import du service.

POURQUOI CE FICHIER EXISTE, ET POURQUOI LES AUTRES CONTROLES NE SUFFISENT PAS.

Les contrôles de `tests/test_tableau_de_bord.py` importent `dashboard.lecture`, `dashboard.rendu`
et les modules de page depuis le processus pytest. Or `pyproject.toml` déclare
`pythonpath = ["."]` : la racine du dépôt est en tête du chemin d'import de ce processus, et
`from dashboard import ...` y réussit toujours. Le service, lui, n'a pas cette propriété — la
bibliothèque d'affichage place en tête le répertoire du SCRIPT PRINCIPAL, `<racine>/dashboard`, et
le projet déclare `package = false`, donc n'est installé nulle part. Un contrôle exécuté dans le
contexte de pytest ne peut donc structurellement pas voir un défaut d'import propre au service :
il observe un autre chemin d'import que celui qu'il prétend observer.

Ce fichier se place de l'autre côté. Chaque page est rendue dans un processus fils lancé en mode
isolé (`python -I`, qui « isolate Python from the user's environment (implies -E, -P and -s) » —
aide de l'interpréteur installé), donc SANS répertoire courant, SANS répertoire du script et SANS
`PYTHONPATH` hérités. Le chemin d'import du fils est ensuite reconstruit à l'identique de celui du
service, et cette reconstruction est DERIVEE DES FICHIERS DE CONSTRUCTION ET DE COMPOSITION, jamais
écrite en dur ici : c'est ce qui fait que le contrôle rougit quand ces fichiers cessent de rendre
la racine du dépôt visible au service.

CE QUE CE CONTROLE COUVRE : que chaque page déclarée à la navigation s'exécute jusqu'au bout et
produise des éléments d'affichage, sous le chemin d'import que les fichiers de `docker/` donnent
au service.

CE QU'IL NE COUVRE PAS : ni la mise en page telle qu'un navigateur la compose, ni le contenu
chiffré des indicateurs (`tests/test_tableau_de_bord.py` s'en charge, en confrontant chaque
indicateur à une seconde mesure), ni le comportement du serveur en réseau (démarrage, sonde de
bonne santé, session websocket). Il exerce le contexte d'import du service, pas le service.
"""

from __future__ import annotations

import ast
import json
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
APP = RACINE / "dashboard" / "app.py"
DOCKERFILE = RACINE / "docker" / "dashboard.Dockerfile"
COMPOSE = RACINE / "docker" / "docker-compose.yml"

# Répertoire de travail du service dans l'image, et sa correspondance sur l'arbre de travail. Le
# contrôle s'exécute sur l'arbre de travail ; seule la STRUCTURE du chemin d'import est reprise du
# service, pas ses chemins absolus.
WORKDIR_IMAGE = "/app"


def _instruction_dockerfile(mot_cle: str) -> str | None:
    """Dernière instruction `mot_cle` du fichier de construction, continuations recollées."""
    lignes: list[str] = []
    tampon = ""
    for brute in DOCKERFILE.read_text(encoding="utf-8").splitlines():
        depouillee = brute.strip()
        if not depouillee or depouillee.startswith("#"):
            continue
        tampon += depouillee[:-1] + " " if depouillee.endswith("\\") else depouillee
        if not depouillee.endswith("\\"):
            lignes.append(tampon)
            tampon = ""
    retenues = [ligne for ligne in lignes if ligne.upper().startswith(mot_cle.upper() + " ")]
    return retenues[-1][len(mot_cle) + 1 :].strip() if retenues else None


def _jetons_de_la_commande() -> list[str]:
    """Les jetons de l'instruction CMD, que sa forme soit une liste JSON ou une ligne shell."""
    commande = _instruction_dockerfile("CMD")
    if commande is None:
        return []
    if commande.startswith("["):
        return [str(jeton) for jeton in json.loads(commande)]
    return shlex.split(commande)


def _pythonpath_de_la_composition() -> list[str]:
    """Valeurs de PYTHONPATH que la composition donne au service, s'il y en a.

    Lu ligne à ligne plutôt qu'avec un analyseur YAML : le fichier de composition n'est pas une
    dépendance du projet, et cette lecture n'a besoin que de repérer une affectation.
    """
    if not COMPOSE.is_file():
        return []
    valeurs = []
    for brute in COMPOSE.read_text(encoding="utf-8").splitlines():
        depouillee = brute.strip()
        if depouillee.startswith("#") or not depouillee.startswith("PYTHONPATH:"):
            continue
        valeurs.extend(
            part for part in depouillee.split(":", 1)[1].strip().strip("\"'").split(":") if part
        )
    return valeurs


def chemin_import_du_service() -> list[str]:
    """Le chemin d'import que les fichiers de `docker/` donnent au service, transposé ici.

    Deux entrées possibles, et une seule est acquise :

    - le répertoire du script principal, que la bibliothèque d'affichage place TOUJOURS en tête,
      quelle que soit la façon dont le service est lancé ;
    - le répertoire de travail de l'image, qui n'y figure QUE si le service est lancé par
      `python -m …` (la forme `-m` place le répertoire courant en tête du chemin) ou si la
      composition l'inscrit dans `PYTHONPATH`. L'exécutable `streamlit` seul ne le fait pas.
    """
    entrees = [str(APP.parent)]
    jetons = _jetons_de_la_commande()
    lance_par_module = any(
        jeton == "-m" and index > 0 and Path(jetons[index - 1]).name.startswith("python")
        for index, jeton in enumerate(jetons)
    )
    if lance_par_module:
        entrees.append(str(RACINE))
    for valeur in _pythonpath_de_la_composition():
        transpose = RACINE if valeur.rstrip("/") == WORKDIR_IMAGE else Path(valeur)
        if str(transpose) not in entrees:
            entrees.append(str(transpose))
    return entrees


def pages_declarees() -> list[tuple[str, str]]:
    """Les pages de la navigation, lues dans `app.py` sans l'importer : (titre, chemin relatif)."""
    arbre = ast.parse(APP.read_text(encoding="utf-8"))
    pages: list[tuple[str, str]] = []
    for noeud in ast.walk(arbre):
        est_page = (
            isinstance(noeud, ast.Call)
            and isinstance(noeud.func, ast.Attribute)
            and noeud.func.attr == "Page"
        )
        if not est_page or not noeud.args:
            continue
        chemin = noeud.args[0]
        titre = next(
            (mc.value.value for mc in noeud.keywords if mc.arg == "title"),
            None,
        )
        if isinstance(chemin, ast.Constant):
            pages.append((str(titre), str(chemin.value)))
    return pages


# Les fonctions de graphique de la bibliothèque d'affichage. **Définies une seule fois**, ici, et
# injectées dans le pilote à son écriture : le pilote les instrumente pour compter les lignes
# transmises, et ce fichier les cherche dans le code des pages pour savoir lesquelles doivent
# tracer. Deux listes séparées auraient dérivé l'une de l'autre sans que rien ne le signale.
FONCTIONS_DE_GRAPHIQUE = ("area_chart", "bar_chart", "line_chart", "scatter_chart")


def graphiques_declares(page: str) -> list[str]:
    """Les appels de graphique que le CODE d'une page déclare, lus sans l'exécuter.

    Le registre des indicateurs ne dit rien des graphiques — ses clés sont l'identifiant, la page,
    le libellé, la définition, la décision servie, les objets lus, la filtrabilité, la section et
    ce dont la valeur est recalculée, et aucune ne porte la forme d'affichage. Il ne peut donc pas
    fournir cette information, et la déduire du code de la page est la seule dérivation
    disponible. Ce qui compte est qu'aucun nom de page ne soit écrit ici : une page qui change de
    nom, de section ou de contenu est suivie sans retouche.
    """
    chemin = APP.parent / page
    arbre = ast.parse(chemin.read_text(encoding="utf-8"))
    return [
        noeud.func.attr
        for noeud in ast.walk(arbre)
        if isinstance(noeud, ast.Call)
        and isinstance(noeud.func, ast.Attribute)
        and noeud.func.attr in FONCTIONS_DE_GRAPHIQUE
    ]


# Le pilote est exécuté par le processus fils. Il fixe lui-même le chemin d'import — le fils étant
# lancé en mode isolé, rien ne s'y ajoute dans son dos — puis rend la page demandée.
PILOTE = '''
import json, sys, time

entrees, app, page = json.loads(sys.argv[1]), sys.argv[2], sys.argv[3]
sys.path[:] = entrees + sys.path

def compter_les_lignes_transmises(st, journal):
    """Enregistre, a chaque appel de graphique, le nombre de lignes que la page lui transmet."""

    def enveloppe(nom, original):
        def appel(data=None, *args, **kwargs):
            try:
                lignes = len(data)
            except TypeError:
                lignes = -1
            journal.append({"fonction": nom, "lignes": lignes})
            return original(data, *args, **kwargs)

        return appel

    for nom in FONCTIONS_DE_GRAPHIQUE:
        original = getattr(st, nom, None)
        if original is not None:
            setattr(st, nom, enveloppe(nom, original))


def graphiques(at):
    """Le type d'axe de chaque encodage, lu dans ce que le serveur a emis pour le navigateur.

    La specification vega-lite est portee par le message de l'element : c'est elle qui decide du
    trace, et non ce que la page croit transmettre. Le jeu de donnees, lui, voyage a cote sous
    forme binaire ; il n'est PAS decode ici, sa lecture ayant fait tomber l'interprete sur
    l'executeur d'integration. Le nombre de lignes est donc releve a l'appel, et le type d'axe
    dans le message : les deux grandeurs viennent chacune de la source ou elle est fiable.
    """
    releves = []
    for element in at.main:
        if "vega" not in element.type:
            continue
        specification = json.loads(element.proto.spec)
        # Les encodages sont a la racine pour un graphique simple, et sous `layer` des que la
        # bibliotheque en superpose plusieurs — c'est le cas des courbes. Les deux sont lus.
        couches = [specification] + list(specification.get("layer", []))
        encodages = []
        marques = []
        for couche in couches:
            marque = couche.get("mark")
            if isinstance(marque, dict):
                marques.append(marque.get("type"))
            elif isinstance(marque, str):
                marques.append(marque)
            for canal, valeur in (couche.get("encoding") or {}).items():
                if canal == "tooltip" or not isinstance(valeur, dict) or "field" not in valeur:
                    continue
                encodages.append(
                    {
                        "canal": canal,
                        "champ": str(valeur["field"]),
                        "type_axe": valeur.get("type"),
                    }
                )
        releves.append({"marques": sorted(set(marques)), "encodages": encodages})
    return releves


resultat = {"chemin_import": sys.path[: len(entrees)]}
try:
    import streamlit

    from streamlit.testing.v1 import AppTest

    journal = []
    compter_les_lignes_transmises(streamlit, journal)

    at = AppTest.from_file(app, default_timeout=120)
    at.switch_page(page)
    debut = time.perf_counter()
    at.run()
    resultat["duree_ms"] = round((time.perf_counter() - debut) * 1000, 1)
    resultat["exception"] = str(at.exception[0].value) if at.exception else None
    resultat["elements"] = len(at.main)
    resultat["graphiques"] = graphiques(at)
    resultat["appels"] = journal
except BaseException as erreur:  # noqa: BLE001
    resultat["exception"] = f"{type(erreur).__name__}: {erreur}"
    resultat["elements"] = 0
    resultat["graphiques"] = []
    resultat["appels"] = []

print("RESULTAT_JSON:" + json.dumps(resultat))
'''


def rendre_dans_le_contexte_du_service(page: str, pilote: Path) -> dict:
    """Rend une page dans un processus fils isolé, sous le chemin d'import du service."""
    pilote.write_text(
        f"FONCTIONS_DE_GRAPHIQUE = {FONCTIONS_DE_GRAPHIQUE!r}\n" + PILOTE, encoding="utf-8"
    )
    acheve = subprocess.run(
        [
            sys.executable,
            "-I",
            str(pilote),
            json.dumps(chemin_import_du_service()),
            str(APP),
            page,
        ],
        capture_output=True,
        text=True,
        cwd=RACINE,
        timeout=600,
        check=False,
    )
    marqueur = "RESULTAT_JSON:"
    for ligne in acheve.stdout.splitlines():
        if ligne.startswith(marqueur):
            return json.loads(ligne[len(marqueur) :])
    raise AssertionError(
        "le processus fils n'a rien rendu d'exploitable\n"
        f"code de sortie : {acheve.returncode}\n"
        f"sortie standard :\n{acheve.stdout}\n"
        f"sortie d'erreur :\n{acheve.stderr}"
    )


@pytest.fixture(scope="session", autouse=True)
def instantane_pret() -> None:
    """Précondition établie ici, non héritée de l'ordre des étapes qui précèdent.

    Les pages lisent le schéma d'instantané ; sans lui, elles échoueraient sur une table absente
    et non sur la propriété que ce fichier vérifie. L'établir depuis le processus pytest est
    légitime : c'est la mise en place, pas la propriété contrôlée — celle-ci se joue tout entière
    dans le processus fils, sous le chemin d'import du service.
    """
    from dashboard import lecture  # noqa: PLC0415

    try:
        etat = lecture.etat()
    except Exception:
        etat = None
    if etat is None or etat.get("rafraichi_le") is None:
        from instantane import rafraichir  # noqa: PLC0415

        reussite, message = rafraichir.rafraichir()
        if not reussite:
            pytest.fail(f"l'instantané ne peut être constitué : {message}")


@pytest.mark.parametrize(("titre", "page"), pages_declarees(), ids=lambda v: v)
def test_chaque_page_rend_dans_le_contexte_d_import_du_service(
    titre: str, page: str, tmp_path: Path
) -> None:
    """Chaque page de la navigation s'exécute et produit des éléments, comme dans le service."""
    resultat = rendre_dans_le_contexte_du_service(page, tmp_path / "pilote.py")

    assert resultat["exception"] is None, (
        f"la page « {titre} » ({page}) ne rend pas sous le chemin d'import du service.\n"
        f"chemin d'import employe : {resultat['chemin_import']}\n"
        f"exception levee : {resultat['exception']}\n"
        "Ce chemin est derive de docker/dashboard.Dockerfile et docker/docker-compose.yml : si la "
        "racine du depot n'y figure pas, le service ne peut pas importer le paquet dashboard, que "
        "les controles executes depuis pytest trouvent pourtant toujours."
    )
    assert resultat["elements"] > 0, (
        f"la page « {titre} » ({page}) s'execute sans erreur mais ne produit aucun element"
    )


# Les canaux qui PLACENT une marque dans le cadre. Un axe catégoriel y interdit toute position
# continue. Les canaux d'apparence — couleur au premier chef — en sont exclus à dessein : un code
# d'activité y est légitimement catégoriel, alors même que ses valeurs se lisent comme des nombres.
CANAUX_POSITIONNELS = frozenset({"x", "y", "theta", "radius"})


@pytest.mark.parametrize(("titre", "page"), pages_declarees(), ids=lambda v: v)
def test_chaque_graphique_recoit_des_donnees_placables_sur_ses_axes(
    titre: str, page: str, tmp_path: Path
) -> None:
    """Chaque graphique reçoit des lignes, et aucun de ses axes de position ne dégénère.

    **Sur les pages qui en tracent.** Une page peut légitimement n'en tracer aucun ; ce que la
    propriété tient alors est que son code n'en déclare aucun non plus, l'accord entre les deux
    étant vérifié dans les deux sens avant tout le reste.

    Compter les éléments rendus ne suffit pas : **un graphique vide est un élément rendu**. Cette
    propriété-ci descend d'un cran et observe, d'une part le nombre de lignes que la page transmet
    à chaque appel, d'autre part le type d'axe que le serveur a réellement émis pour le navigateur.

    Sur le second point, la dégénérescence à surveiller est précise. Les fonctions de graphique
    forcent l'axe ORDONNÉ pour une catégorie portée par un axe de position — le code le fait
    explicitement pour l'abscisse d'un diagramme en barres verticales et pour l'ordonnée d'un
    diagramme en barres horizontales. Sur un axe de position, l'axe CATÉGORIEL ne peut donc venir
    que de la déduction de type, c'est-à-dire d'une colonne dont la nature n'a pas été reconnue :
    le décimal exact que rend le serveur en est une, et le texte issu du repliement de plusieurs
    colonnes en est une autre. Dans les deux cas l'axe perd son échelle continue, et le graphique
    conserve son cadre, ses titres et sa légende sans tracer la moindre marque.

    Les canaux d'apparence — la couleur au premier chef — sont exclus à dessein : un code
    d'activité y est légitimement catégoriel, alors même que ses valeurs se lisent comme des
    nombres.
    """
    resultat = rendre_dans_le_contexte_du_service(page, tmp_path / "pilote.py")
    assert resultat["exception"] is None, (
        f"la page « {titre} » ({page}) ne rend pas : {resultat['exception']}"
    )

    # Une page sans graphique n'est PAS un défaut. La propriété porte sur les graphiques qu'une
    # page trace, et une page qui n'en trace aucun n'en a aucun à vérifier : la page des lignes
    # répond à « lesquels » et non à « combien », elle montre des dossiers et non des formes.
    # Exiger un graphique de toute page ferait de ce choix d'affichage une faute.
    #
    # Ce qui reste à tenir est l'accord entre ce que la page DÉCLARE et ce qu'elle REND, dans les
    # deux sens : une page dont le code appelle une fonction de graphique doit en tracer au moins
    # un — sans quoi l'appel est dans une branche jamais prise et le contrôle passerait à vide —
    # et une page dont le code n'en appelle aucune ne doit pas en produire. Les deux membres sont
    # calculés chacun de son côté, l'un par lecture statique du code de la page, l'autre par
    # observation du rendu dans le processus fils.
    appels = resultat["appels"]
    declares = graphiques_declares(page)
    assert bool(appels) == bool(declares), (
        f"page « {titre} » ({page}) : le code déclare {len(declares)} appel(s) de graphique "
        f"({', '.join(sorted(set(declares))) or 'aucun'}) et le rendu en observe {len(appels)}.\n"
        "Une page qui déclare un graphique doit en tracer au moins un, et une page qui n'en "
        "déclare aucun ne doit pas en produire."
    )
    vides = [(rang, appel) for rang, appel in enumerate(appels, 1) if appel["lignes"] <= 0]
    assert not vides, (
        f"page « {titre} » ({page}) : un graphique ne recoit aucune ligne, il n'y a rien a "
        f"tracer.\n"
        + "\n".join(
            f"  appel {rang} — st.{a['fonction']} : {a['lignes']} ligne(s)" for rang, a in vides
        )
    )

    degeneres = [
        (i, encodage)
        for i, graphique in enumerate(resultat["graphiques"], 1)
        for encodage in graphique["encodages"]
        if encodage["canal"] in CANAUX_POSITIONNELS and encodage["type_axe"] == "nominal"
    ]
    assert not degeneres, (
        f"page « {titre} » ({page}) : un axe de position a degenere en axe categoriel, et le "
        f"graphique ne tracera aucune marque.\n"
        + "\n".join(
            f"  graphique {i} — canal {e['canal']!r} sur la colonne {e['champ']!r} : "
            f"axe {e['type_axe']!r}"
            for i, e in degeneres
        )
    )
