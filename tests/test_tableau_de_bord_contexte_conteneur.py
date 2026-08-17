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


# Le pilote est exécuté par le processus fils. Il fixe lui-même le chemin d'import — le fils étant
# lancé en mode isolé, rien ne s'y ajoute dans son dos — puis rend la page demandée.
PILOTE = '''
import io, json, sys, time

entrees, app, page = json.loads(sys.argv[1]), sys.argv[2], sys.argv[3]
sys.path[:] = entrees + sys.path


def graphiques(at):
    """Chaque graphique rendu : sa marque, son jeu de donnees, et le type d'axe de chaque encodage.

    Rien n'est deduit de la page : tout est lu dans ce que le serveur a effectivement emis pour le
    navigateur — la specification vega-lite et le jeu de donnees au format arrow, tous deux portes
    par le message de l'element.
    """
    import pyarrow
    from pandas.api.types import infer_dtype

    numeriques = {"floating", "integer", "mixed-integer-float", "decimal", "complex"}

    def porte_des_nombres(colonne, nature):
        """La colonne transporte-t-elle des grandeurs, quel que soit le type sous lequel ?

        La nature seule ne suffit pas : quand la bibliotheque replie plusieurs colonnes en une
        seule serie de valeurs, une colonne de decimal exact melangee a une colonne d'entiers
        ressort en TEXTE. Les grandeurs sont toujours la, sous forme de chaines, et un axe
        categoriel les accueille sans rien tracer. Une colonne de texte dont toutes les valeurs
        se lisent comme des nombres est donc traitee ici comme une colonne de grandeurs.
        """
        if nature in numeriques:
            return True
        if nature not in {"string", "mixed", "bytes", "unicode"}:
            return False
        valeurs = colonne.dropna().tolist()[:200]
        if not valeurs:
            return False
        try:
            for valeur in valeurs:
                float(valeur)
        except (TypeError, ValueError):
            return False
        return True

    releves = []
    for element in at.main:
        if "vega" not in element.type:
            continue
        specification = json.loads(element.proto.spec)
        tableau = None
        for jeu in element.proto.datasets:
            if jeu.data.data:
                tableau = pyarrow.ipc.open_stream(io.BytesIO(jeu.data.data)).read_pandas()
                break
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
                champ = valeur["field"]
                nature = "ABSENT"
                nombres = False
                if tableau is not None and champ in tableau.columns:
                    nature = infer_dtype(tableau[champ])
                    nombres = porte_des_nombres(tableau[champ], nature)
                encodages.append(
                    {
                        "canal": canal,
                        "champ": champ,
                        "type_axe": valeur.get("type"),
                        "nature_colonne": nature,
                        "porte_des_nombres": nombres,
                    }
                )
        releves.append(
            {
                "marques": sorted(set(marques)),
                "lignes": -1 if tableau is None else len(tableau),
                "colonnes": [] if tableau is None else [str(c) for c in tableau.columns],
                "encodages": encodages,
            }
        )
    return releves


resultat = {"chemin_import": sys.path[: len(entrees)]}
try:
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(app, default_timeout=120)
    at.switch_page(page)
    debut = time.perf_counter()
    at.run()
    resultat["duree_ms"] = round((time.perf_counter() - debut) * 1000, 1)
    resultat["exception"] = str(at.exception[0].value) if at.exception else None
    resultat["elements"] = len(at.main)
    resultat["graphiques"] = graphiques(at)
except BaseException as erreur:  # noqa: BLE001
    resultat["exception"] = f"{type(erreur).__name__}: {erreur}"
    resultat["elements"] = 0
    resultat["graphiques"] = []

print("RESULTAT_JSON:" + json.dumps(resultat))
'''


def rendre_dans_le_contexte_du_service(page: str, pilote: Path) -> dict:
    """Rend une page dans un processus fils isolé, sous le chemin d'import du service."""
    pilote.write_text(PILOTE, encoding="utf-8")
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
    """Chaque graphique reçoit un jeu de données non vide, et aucun de ses axes ne dégénère.

    Compter les éléments rendus ne suffit pas : **un graphique vide est un élément rendu**. Cette
    propriété-ci descend d'un cran et observe ce que le serveur a réellement émis pour chaque
    graphique — le jeu de données au format arrow et le type d'axe de chaque encodage.

    Elle vérifie deux choses. D'abord qu'un jeu de données non vide accompagne le graphique : sans
    lignes, il n'y a rien à tracer. Ensuite qu'aucune colonne de valeurs numériques ne se retrouve
    encodée en axe CATÉGORIEL. C'est la dégénérescence à surveiller : la bibliothèque ne sait pas
    déduire un type d'axe de certaines natures de colonne — le décimal exact que rend le serveur en
    est une — et retombe alors silencieusement sur un axe catégoriel, où aucune marque n'est
    placée. Le graphique conserve son cadre, ses titres et sa légende, et ne trace rien.

    Un axe catégoriel ou ordonné sur une colonne de texte est légitime et n'est pas signalé ; c'est
    la conjonction « colonne numérique » et « axe catégoriel » qui ne l'est jamais.
    """
    resultat = rendre_dans_le_contexte_du_service(page, tmp_path / "pilote.py")
    assert resultat["exception"] is None, (
        f"la page « {titre} » ({page}) ne rend pas : {resultat['exception']}"
    )

    graphiques = resultat["graphiques"]
    vides = [i for i, g in enumerate(graphiques, 1) if g["lignes"] <= 0]
    assert not vides, (
        f"page « {titre} » ({page}) : le ou les graphiques {vides} ne portent aucune ligne de "
        f"donnees. Detail : {[graphiques[i - 1] for i in vides]}"
    )

    degeneres = [
        (i, encodage)
        for i, graphique in enumerate(graphiques, 1)
        for encodage in graphique["encodages"]
        if encodage["canal"] in CANAUX_POSITIONNELS
        and encodage["porte_des_nombres"]
        and encodage["type_axe"] == "nominal"
    ]
    assert not degeneres, (
        f"page « {titre} » ({page}) : un axe de position portant des grandeurs a degenere en axe "
        f"categoriel, et le graphique ne tracera aucune marque.\n"
        + "\n".join(
            f"  graphique {i} — canal {e['canal']!r} sur la colonne {e['champ']!r} : "
            f"colonne de nature {e['nature_colonne']!r} portant des nombres, encodee en axe "
            f"{e['type_axe']!r}"
            for i, e in degeneres
        )
    )
