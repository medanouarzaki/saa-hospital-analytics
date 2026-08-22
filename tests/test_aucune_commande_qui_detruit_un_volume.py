"""Aucun fichier suivi ne porte une commande qui détruit un volume nommé.

Un volume nommé porte les données. Le conteneur qui l'emploie se jette et se refait ; le
volume, non. Une commande qui le supprime ne rend rien invisible : elle efface.

LE MOTIF EST MESURÉ, ET IL VIENT DE L'AUTRE DÉPÔT. La plateforme de traitement des
paiements portait `docker compose down -v` câblé dans sa cible `make down`, avec pour seule
description « Stop the local stack and remove volumes ». L'option était sans conséquence
tant qu'aucun volume n'existait ; le volume de la base de métadonnées existe depuis que le
projet a été migré, et la cible se lance par réflexe. Une commande destructrice cachée
derrière un verbe ordinaire — arrêter — est le motif exact que ce contrôle existe pour
empêcher de revenir.

CE CONTRÔLE NE PORTE QUE SUR CE DÉPÔT. Il lit `git ls-files`, donc l'arbre suivi de ce
dépôt et de lui seul. Il ne voit pas les deux autres dépôts du poste de travail, et ne
prétend pas les couvrir : leur balayage a été fait à la main, et c'est un balayage daté,
non une propriété.

CE QU'IL CHERCHE — QUATRE FORMES, ET SEULEMENT CELLES QUI EMPORTENT UN VOLUME.

  1. `docker compose down` assorti de `-v` ou `--volumes`. C'est la forme du défaut mesuré.
  2. `docker volume rm`.
  3. `docker volume prune`.
  4. `docker system prune` assorti de `--volumes`.

L'OPTION EST CHERCHÉE SUR LA MÊME LIGNE ET APRÈS LE VERBE. Un `-v` qui traîne ailleurs dans
un fichier ne rend pas ce fichier fautif, et une phrase qui écrit `docker compose down` puis
parle plus loin d'un `-v` sur une AUTRE ligne n'est pas une commande destructrice.

CE QU'IL NE CHERCHE PAS, ET POURQUOI.

  - `docker compose down` NU. Il arrête et retire les conteneurs, il ne touche à aucun
    volume. C'est la commande corrigée, et la faire rougir rendrait le contrôle inutilisable.
  - `docker compose stop`, `docker rm`, `docker image prune`, `docker builder prune`. Aucun
    n'emporte de volume. `docker builder prune` a été exécuté sur ce poste sans qu'aucun des
    trois volumes ne bouge, et c'est vérifié.
  - `docker system prune` NU. Sans `--volumes`, il épargne les volumes nommés. Il emporte
    des images et des conteneurs arrêtés, ce qui est une autre question et pas celle-ci.

PAR QUELLE VOIE UNE COMMANDE DESTRUCTRICE PASSERAIT-ELLE MALGRÉ TOUT ? Six voies ont été
cherchées. Deux sont fermées, quatre restent ouvertes et sont écrites ici plutôt que laissées
à découvrir.

  FERMÉES
  1. Casse différente, ou espaces multiples entre les mots de la commande. Fermée : la
     recherche replie la casse et réduit les suites d'espaces blancs à une espace simple.
  2. `docker-compose` avec un tiret, l'ancienne graphie de l'outil. Fermée : les deux
     graphies sont acceptées par le motif.

  OUVERTES, ET ASSUMÉES
  3. LA COMMANDE COUPÉE PAR UNE CONTINUATION DE LIGNE — le verbe sur une ligne, l'option
     reportée à la suivante par une barre oblique inverse en fin de ligne. Non fermée :
     recoller les lignes de continuation ferait se rejoindre des lignes qu'un fichier de
     commandes sépare pour d'autres raisons, et rendrait le contrôle rouge sur des suites
     accidentelles.
  4. LA COMMANDE CONSTRUITE PAR MORCEAUX — une variable qui porte `-v`, un nom de cible
     appelé depuis une autre. Non fermée : la fermer supposerait d'interpréter le fichier
     plutôt que de le lire.
  5. UN OUTIL AUTRE QUE `docker` — `podman`, `nerdctl`, un client écrit pour l'occasion.
     Non fermée : ce dépôt n'en emploie aucun, et les chercher tous rendrait le motif
     illisible pour un gain nul.
  6. UNE COMMANDE PRÉSENTE DANS L'HISTORIQUE mais plus dans l'arbre courant. Non fermée :
     ce contrôle lit `git ls-files`, donc l'arbre, jamais les révisions antérieures.

CE QU'IL NE PEUT PAS VOIR, ET QUI N'EST PAS UNE VOIE DE CONTOURNEMENT. Il ne voit que du
texte suivi. Une commande tapée à la main dans un terminal, un alias de l'utilisateur, un
bouton de l'interface graphique de Docker Desktop lui échappent entièrement. Il ne dit donc
pas « aucun volume ne sera jamais détruit » : il dit « aucun fichier suivi de ce dépôt
n'écrit une commande qui en détruirait un ».

Aucun accès à la base, aucune dépendance à un volume de données : ce fichier se collecte
et s'exécute sur un clone frais.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent

# Ce fichier écrit les commandes qu'il interdit — il ne peut pas se balayer lui-même, comme
# `tests/test_aucun_nom_de_personne.py` ne se balaye pas non plus.
FICHIERS_EXCLUS = frozenset({"tests/test_aucune_commande_qui_detruit_un_volume.py"})

# `docker compose` ou `docker-compose`, les deux graphies de l'outil (voie fermée 2).
_COMPOSE = r"docker[ -]compose\b"

# L'option qui emporte les volumes, cherchée comme un MOT ENTIER : `-v` ou `--volumes`.
# `-vv`, `--volume-driver` ou un `-v` collé à autre chose ne correspondent pas.
_EMPORTE_LES_VOLUMES = r"(?:-v|--volumes)(?![\w-])"

# Les quatre formes. Dans les deux premières, l'option est cherchée APRÈS le verbe et sur la
# MÊME ligne : `[^\n]*` ne franchit jamais un saut de ligne.
MOTIFS: tuple[tuple[str, str], ...] = (
    (
        "docker compose down avec suppression des volumes",
        rf"{_COMPOSE}[^\n]*\bdown\b[^\n]*{_EMPORTE_LES_VOLUMES}",
    ),
    (
        "docker system prune avec suppression des volumes",
        rf"docker\b[^\n]*\bsystem\s+prune\b[^\n]*{_EMPORTE_LES_VOLUMES}",
    ),
    ("docker volume rm", r"docker\b[^\n]*\bvolume\s+rm\b"),
    ("docker volume prune", r"docker\b[^\n]*\bvolume\s+prune\b"),
)

_COMPILES = tuple((libelle, re.compile(motif)) for libelle, motif in MOTIFS)

_ESPACES = re.compile(r"[^\S\n]+")


def normaliser(texte: str) -> str:
    """Casse repliée, espaces horizontaux réduits à une espace simple (voie fermée 1).

    Les sauts de ligne sont PRÉSERVÉS : c'est eux qui bornent la recherche de l'option à la
    ligne du verbe.
    """
    return _ESPACES.sub(" ", texte.casefold())


def commandes_trouvees(texte: str) -> list[str]:
    """Les libellés des formes destructrices présentes dans un texte."""
    normalise = normaliser(texte)
    return [libelle for libelle, motif in _COMPILES if motif.search(normalise)]


def fichiers_suivis() -> list[str]:
    sortie = subprocess.run(
        ["git", "-C", str(RACINE), "ls-files", "-z"],
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    return [chemin for chemin in sortie.split("\0") if chemin]


def lire(chemin: str) -> str:
    """Le contenu d'un fichier suivi, octets invalides tolérés."""
    return (RACINE / chemin).read_bytes().decode("utf-8", errors="replace")


def occurrences(chemins: list[str]) -> list[str]:
    """Les fichiers suivis fautifs, avec le NUMÉRO DE LIGNE et la forme trouvée.

    Le numéro de ligne est donné parce qu'un message qui nomme le fichier seul oblige à le
    relire en entier pour trouver ce qui est reproché.
    """
    fautifs = []
    for chemin in chemins:
        if chemin in FICHIERS_EXCLUS:
            continue
        for numero, ligne in enumerate(lire(chemin).splitlines(), start=1):
            for libelle in commandes_trouvees(ligne):
                fautifs.append(f"{chemin}:{numero} : {libelle}")
    return sorted(set(fautifs))


# --- les témoins, dans les deux sens ------------------------------------------------------------

TEMOINS_VUS = (
    ("la forme du défaut mesuré", "\tdocker compose down -v"),
    ("l'option longue", "docker compose down --volumes"),
    ("l'ancienne graphie de l'outil", "docker-compose down -v"),
    ("casse différente", "DOCKER COMPOSE DOWN -V"),
    ("espaces multiples", "docker  compose   down   -v"),
    ("d'autres options avant celle-ci", "docker compose down --remove-orphans -v"),
    ("un fichier de composition nommé", "docker compose -f docker/docker-compose.yml down -v"),
    ("dans une phrase de documentation", "`make down` runs `docker compose down -v`, which"),
    ("le nettoyage général avec les volumes", "docker system prune -a --volumes -f"),
    ("la suppression d'un volume nommé", "docker volume rm saa-hospital-analytics_postgres_data"),
    ("le nettoyage des volumes", "docker volume prune -f"),
)

TEMOINS_NON_VUS = (
    ("l'arrêt corrigé, sans option", "\tdocker compose down"),
    ("l'arrêt corrigé, avec une autre option", "docker compose down --remove-orphans"),
    ("l'arrêt qui ne retire même pas les conteneurs", "docker compose stop"),
    ("le démarrage", "docker compose up --wait"),
    ("le nettoyage général SANS les volumes", "docker system prune -a -f"),
    ("le cache de construction, qui n'emporte aucun volume", "docker builder prune -a -f"),
    ("les images, qui n'emportent aucun volume", "docker image prune -a"),
    ("l'inventaire des volumes, qui ne détruit rien", "docker volume ls"),
    ("l'inspection d'un volume", "docker volume inspect saa-hospital-analytics_postgres_data"),
    ("un montage lié, dont le -v n'est pas une suppression", "docker run -v /tmp:/tmp alpine"),
    ("une option qui commence comme celle-ci", "docker compose down --volume-driver local"),
    ("de la prose qui parle de volumes", "l'option détruit les volumes nommés : ne pas l'employer"),
    ("le verbe et l'option sur DEUX lignes — voie ouverte 3", "docker compose down\n-v ailleurs"),
)


@pytest.mark.parametrize(("libelle", "contenu"), TEMOINS_VUS)
def test_le_controle_voit_chaque_forme_destructrice(libelle: str, contenu: str) -> None:
    """Onze témoins positifs : un contrôle éprouvé sur une seule forme ne l'est pas."""
    assert commandes_trouvees(contenu), f"témoin « {libelle} » : la commande passe"


@pytest.mark.parametrize(("libelle", "contenu"), TEMOINS_NON_VUS)
def test_le_controle_ne_crie_sur_aucune_commande_inoffensive(libelle: str, contenu: str) -> None:
    """Treize témoins négatifs, dont l'arrêt corrigé — celui qui doit rester vert.

    Un contrôle qui rougirait sur `docker compose down` nu apprendrait à être ignoré, et
    c'est exactement la commande vers laquelle la correction fait aller.
    """
    vues = commandes_trouvees(contenu)
    assert not vues, f"témoin « {libelle} » : le contrôle crie à tort — {vues}"


def test_l_option_est_cherchee_sur_la_ligne_du_verbe() -> None:
    """Le témoin de la borne de ligne, et il porte l'arbitrage.

    `[^\\n]*` ne franchit pas un saut de ligne : un `-v` situé sur une autre ligne que le
    verbe ne rend pas le fichier fautif. C'est la voie ouverte 3, et elle est ici exécutée
    plutôt que seulement déclarée.
    """
    assert commandes_trouvees("docker compose down -v")
    assert not commandes_trouvees("docker compose down\nuv run pytest -v")


def test_le_fichier_de_controle_est_le_seul_ecarte() -> None:
    """Une exclusion, et une seule : ce fichier, qui écrit les commandes qu'il interdit.

    Toute autre exclusion serait une porte ouverte, et devrait porter son motif écrit.
    """
    assert len(FICHIERS_EXCLUS) == 1, f"exclusions inattendues : {sorted(FICHIERS_EXCLUS)}"
    assert "tests/test_aucune_commande_qui_detruit_un_volume.py" in FICHIERS_EXCLUS
    assert commandes_trouvees(lire("tests/test_aucune_commande_qui_detruit_un_volume.py")), (
        "ce fichier doit porter les commandes qu'il interdit, sans quoi son exclusion "
        "serait décorative et ses témoins positifs ne prouveraient rien"
    )


# --- la propriété ---------------------------------------------------------------------------------


def test_aucune_commande_qui_detruit_un_volume_dans_les_fichiers_suivis() -> None:
    fautifs = occurrences(fichiers_suivis())
    assert not fautifs, "Commande qui détruit un volume dans des fichiers suivis :\n" + "\n".join(
        fautifs
    )
