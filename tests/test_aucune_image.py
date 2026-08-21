"""Interdit toute image du système d'information dans les fichiers suivis.

TROIS PROPRIÉTÉS, ET LE PÉRIMÈTRE EST LE DÉPÔT ENTIER. Une version antérieure de ce
contrôle ne regardait que la racine et `report/` : un fichier image suivi sous
`dashboard/`, `docs/` ou `slides/` ne faisait rougir aucun contrôle. La propriété que
le projet veut tenir n'est pas « pas d'image sous le rapport » mais « pas d'image du
système observé, nulle part » ; le périmètre est donc l'ensemble des fichiers suivis.

DEUX RÉPERTOIRES SONT TOLÉRÉS, ET DEUX SEULEMENT :

  report/figures/logos/            le logotype de l'établissement de formation ;
  report/figures/tableau-de-bord/  les captures du tableau de bord PRODUIT par ce projet.

Aucune image du système d'information observé n'est admise, sous aucun de ces deux
préfixes ni ailleurs — c'est la décision `0010`, et ce contrôle ne peut pas la tenir
seul : il voit un chemin, jamais le contenu d'une image. C'est son point aveugle, et
il est déclaré ici plutôt que découvert.

LA BARRE OBLIQUE FINALE DE CHAQUE PRÉFIXE COMPTE. Sans elle, `str.startswith` accepte
`report/figures/logos-anciens/x.png`, qui n'est pas le répertoire toléré. Un témoin
négatif l'établit ci-dessous.

L'EXTENSION `.pdf` EST DÉLIBÉRÉMENT ABSENTE de la liste interdite, et le motif tient
en deux points : `.gitignore` ignore déjà `report/*.pdf` et `slides/*.pdf`, et la
composition PRODUIT des PDF — le rapport et la présentation. Interdire l'extension
ferait rougir ce contrôle sur un artefact légitime le jour où l'un d'eux serait suivi
par inadvertance, au lieu de le laisser au dispositif qui s'en occupe. La conséquence
est écrite : un logotype livré en `.pdf` sous un répertoire toléré passe ici sans être
vu, et c'est assumé.

Aucun accès à la base, aucune dépendance à un volume de données : ce fichier se
collecte et s'exécute sur un clone frais.
"""

import subprocess
from pathlib import Path, PurePosixPath

import pytest

RACINE = Path(__file__).resolve().parent.parent

# Les formats matriciels et vectoriels par lesquels une capture ou une photographie entre
# dans un dépôt. `.svg`, `.gif`, `.webp` et `.tif`/`.tiff` ont été ajoutés : un logotype
# arrive typiquement en `.svg`, et rien n'interdisait auparavant d'y glisser une capture.
EXTENSIONS_INTERDITES = {
    ".heic",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".webp",
    ".tif",
    ".tiff",
}

# Les deux répertoires tolérés. La barre oblique finale fait partie du préfixe.
PREFIXES_TOLERES: tuple[str, ...] = (
    "report/figures/logos/",
    "report/figures/tableau-de-bord/",
)


def fichiers_suivis() -> list[str]:
    sortie = subprocess.run(
        ["git", "-C", str(RACINE), "ls-files", "-z"],
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    return [chemin for chemin in sortie.split("\0") if chemin]


def est_fautif(chemin: str) -> bool:
    """Un chemin suivi est fautif s'il porte une extension interdite hors des deux préfixes.

    Aucune restriction de périmètre : tout fichier suivi est examiné.
    """
    return PurePosixPath(chemin).suffix.lower() in EXTENSIONS_INTERDITES and not chemin.startswith(
        PREFIXES_TOLERES
    )


# --- les témoins, dans les deux sens ------------------------------------------------------------

TEMOINS_FAUTIFS = (
    ("image à la racine", "capture.png"),
    ("image sous report/", "report/figures/ecran.png"),
    ("image sous un répertoire hors du rapport", "dashboard/apercu.png"),
    ("image sous docs/", "docs/decisions/photo.jpg"),
    ("extension en majuscules", "report/CAPTURE.HEIC"),
    ("extension nouvellement interdite", "docs/schema.svg"),
    ("préfixe toléré sans sa barre oblique", "report/figures/logos-anciens/x.png"),
    ("préfixe toléré en sous-chaîne, pas en début", "docs/report/figures/logos/x.png"),
)

TEMOINS_ADMIS = (
    ("logotype de l'école", "report/figures/logos/ecole.png"),
    ("capture du tableau de bord", "report/figures/tableau-de-bord/activite.png"),
    ("fichier de données de série", "report/figures/flux-mensuel.csv"),
    ("source de composition", "report/rapport.tex"),
    ("PDF, délibérément hors de la liste", "report/rapport.pdf"),
    ("nom qui contient une extension sans la porter", "docs/notes-png.md"),
)


@pytest.mark.parametrize(("libelle", "chemin"), TEMOINS_FAUTIFS)
def test_le_controle_voit_chaque_forme_fautive(libelle: str, chemin: str) -> None:
    """Huit formes, huit témoins : un contrôle éprouvé sur une seule ne l'est pas."""
    assert est_fautif(chemin), f"témoin « {libelle} » : {chemin} passe alors qu'il est fautif"


@pytest.mark.parametrize(("libelle", "chemin"), TEMOINS_ADMIS)
def test_le_controle_n_accuse_aucune_forme_legitime(libelle: str, chemin: str) -> None:
    """Six formes qu'il ne doit pas voir, dont les deux répertoires tolérés."""
    assert not est_fautif(chemin), f"témoin « {libelle} » : {chemin} est accusé à tort"


def test_les_deux_prefixes_toleres_portent_leur_barre_oblique() -> None:
    """Sans elle, un répertoire voisin dont le nom commence pareil serait toléré."""
    sans_barre = [prefixe for prefixe in PREFIXES_TOLERES if not prefixe.endswith("/")]
    assert not sans_barre, f"préfixes sans barre oblique finale : {sans_barre}"


# --- la propriété ---------------------------------------------------------------------------------


def test_aucune_image_du_systeme() -> None:
    fautifs = sorted(chemin for chemin in fichiers_suivis() if est_fautif(chemin))
    assert not fautifs, "Fichiers image suivis interdits : " + ", ".join(fautifs)
