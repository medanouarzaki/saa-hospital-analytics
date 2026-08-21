"""Aucun fichier suivi ne porte l'un des deux noms de personne du projet.

Le rapport porte deux noms : l'auteur et l'encadrant de stage. Ils ne sont commis
NULLE PART. `report/marqueurs.tex` déclare les deux marqueurs vides ; `report/noms.tex`
les redéfinit à la compilation et n'est pas suivi ; l'intégration continue écrit ce
fichier depuis deux variables de dépôt. Ce contrôle tient l'autre bout de la chaîne :
que rien, dans l'arbre suivi, ne les écrive.

LE CONTRÔLE NE PORTE PAS LES NOMS QU'IL INTERDIT. Il les lit dans deux VARIABLES
D'ENVIRONNEMENT, `RAPPORT_AUTEUR` et `RAPPORT_ENCADRANT`. Écrire les valeurs ici
reviendrait à commettre exactement ce que le contrôle existe pour empêcher.

D'OÙ SON POINT AVEUGLE PRINCIPAL, DÉCLARÉ ET NON DÉCOUVERT : sans les variables, il ne
peut rien chercher. Il ne passe alors pas en silence — il SE DÉCLARE ABSTENU, par un
`pytest.skip` dont le message dit ce qui manque. Un contrôle vert sans avoir rien
regardé serait une assurance fausse ; un contrôle sauté apparaît dans la sortie de
pytest et se compte. C'est l'état ordinaire en intégration continue tant que les
variables ne sont pas posées, et c'est assumé.

PAR QUELLE VOIE CE CONTRÔLE SERAIT-IL VERT ALORS QU'UN NOM SERAIT PRÉSENT ? Sept ont
été cherchées avant d'écrire une ligne. Quatre sont fermées, trois restent ouvertes et
sont écrites ici plutôt que laissées à découvrir.

  FERMÉES
  1. Casse différente — « nom » contre « Nom ». Fermée : la comparaison passe par
     `casefold()`.
  2. Accents composés autrement — « é » en un caractère contre « e » suivi d'un accent
     combinant. Fermée : les deux côtés sont normalisés en NFD puis dépouillés de leurs
     marques combinantes, ce qui rend aussi « Zaki » et « Zàki » identiques.
  3. Espaces multiples, tabulation ou saut de ligne entre prénom et nom. Fermée : les
     suites d'espaces blancs sont réduites à une espace simple des deux côtés.
  4. Fichier binaire ou d'encodage inattendu, où une lecture stricte lèverait et
     ferait passer le fichier pour vide. Fermée : la lecture est faite en octets puis
     décodée en tolérant les octets invalides.

  OUVERTES, ET ASSUMÉES
  5. Un nom coupé par une césure ou par un retour à la ligne À L'INTÉRIEUR d'un mot.
     Non fermée : la fermer supposerait de savoir où un mot peut se couper.
  6. Un nom présent dans l'HISTORIQUE du dépôt mais plus dans l'arbre courant. Non
     fermée : ce contrôle lit `git ls-files`, donc l'arbre, jamais les révisions
     antérieures. Un nom déjà commis exige une réécriture d'historique, que ce contrôle
     ne peut ni faire ni voir.
  7. Un fragment de nom de trois caractères ou moins. Non fermée : chercher « Ali » ou
     « Ben » ferait rougir le contrôle sur des mots ordinaires du français ou sur des
     identifiants de code. Le seuil est de quatre caractères, et il est écrit.

Aucun accès à la base, aucune dépendance à un volume de données : ce fichier se collecte
et s'exécute sur un clone frais.
"""

from __future__ import annotations

import os
import re
import subprocess
import unicodedata
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent

# Les deux variables d'environnement qui portent les noms à chercher. Elles portent les
# mêmes noms que les variables de dépôt lues par le travail de composition.
VARIABLES = ("RAPPORT_AUTEUR", "RAPPORT_ENCADRANT")

# En deçà de cette longueur, un fragment de nom n'est pas cherché seul : voir le point 7.
LONGUEUR_MINIMALE_D_UN_FRAGMENT = 4

# Ce fichier se nomme lui-même : il cite les variables, jamais les valeurs. Il est
# néanmoins exclu du balayage, comme tout fichier qui pourrait légitimement porter le
# mot cherché sans porter le nom — il n'y en a aucun autre aujourd'hui.
FICHIERS_EXCLUS = frozenset({"tests/test_aucun_nom_de_personne.py"})

_ESPACES = re.compile(r"\s+")


def normaliser(texte: str) -> str:
    """Casse repliée, accents retirés, espaces blancs réduits à une espace simple.

    Les trois normalisations ferment les points 1, 2 et 3 ci-dessus. Elles sont
    appliquées des DEUX côtés : au texte cherché comme au texte fouillé.
    """
    sans_accent = "".join(
        c for c in unicodedata.normalize("NFD", texte) if not unicodedata.combining(c)
    )
    return _ESPACES.sub(" ", sans_accent.casefold()).strip()


def fragments_a_chercher(noms: list[str]) -> list[str]:
    """Le nom complet normalisé, et chacun de ses mots d'au moins quatre caractères."""
    cherches: set[str] = set()
    for nom in noms:
        complet = normaliser(nom)
        if not complet:
            continue
        cherches.add(complet)
        cherches.update(
            mot for mot in complet.split(" ") if len(mot) >= LONGUEUR_MINIMALE_D_UN_FRAGMENT
        )
    return sorted(cherches)


def fichiers_suivis() -> list[str]:
    sortie = subprocess.run(
        ["git", "-C", str(RACINE), "ls-files", "-z"],
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    return [chemin for chemin in sortie.split("\0") if chemin]


def lire(chemin: str) -> str:
    """Le contenu normalisé d'un fichier suivi, octets invalides tolérés (point 4)."""
    brut = (RACINE / chemin).read_bytes()
    return normaliser(brut.decode("utf-8", errors="replace"))


def occurrences(fragments: list[str], chemins: list[str]) -> list[str]:
    trouvees = []
    for chemin in chemins:
        if chemin in FICHIERS_EXCLUS:
            continue
        contenu = lire(chemin)
        for fragment in fragments:
            if fragment in contenu:
                trouvees.append(f"{chemin} : porte un fragment de {len(fragment)} caractères")
    return sorted(set(trouvees))


# --- les témoins, dans les deux sens ------------------------------------------------------------

# Un nom d'essai qui n'est celui de personne, et qui n'apparaît nulle part ailleurs.
TEMOIN_NOM = "Zéphyrin Machinchouette"

TEMOINS_VUS = (
    ("nom complet tel quel", "signé Zéphyrin Machinchouette, 2026"),
    ("casse différente", "signé zéphyrin MACHINCHOUETTE"),
    ("accent décomposé", "signé Zéphyrin Machinchouette"),
    ("accent absent", "signé Zephyrin Machinchouette"),
    ("espaces multiples", "signé Zéphyrin    Machinchouette"),
    ("saut de ligne entre les deux mots", "signé Zéphyrin\nMachinchouette"),
    ("nom de famille seul", "l'encadrant Machinchouette a relu"),
    ("prénom seul", "Zéphyrin a relu"),
    ("au milieu d'un mot plus long", "voir machinchouettes.txt"),
    ("mot dont le nom cherché est le préfixe", "signé Zéphyrine Machinchose"),
)

# Le dernier témoin est délibéré, et il dit un parti pris : un mot DONT LE NOM CHERCHÉ EST
# UN SOUS-MOT fait rougir le contrôle. « Zéphyrine » n'est pas « Zéphyrin », mais le
# contrôle ne fait pas la différence, et c'est le bon sens : sur-détecter coûte une
# vérification à la main, sous-détecter laisse passer un nom. Le même parti pris rend
# `machinchouettes.txt` fautif.

TEMOINS_NON_VUS = (
    ("aucun des deux mots", "signé un encadrant anonyme"),
    ("fragment de trois caractères seulement", "le mot mac est ordinaire"),
    ("mot voisin sans être un sur-ensemble", "signé Zéphir Machinchose"),
    ("prose ordinaire du dépôt", "le tableau de bord porte neuf pages"),
)


@pytest.mark.parametrize(("libelle", "contenu"), TEMOINS_VUS)
def test_le_controle_voit_chaque_forme_du_nom(libelle: str, contenu: str) -> None:
    """Neuf formes, neuf témoins : un contrôle éprouvé sur une seule ne l'est pas."""
    fragments = fragments_a_chercher([TEMOIN_NOM])
    normalise = normaliser(contenu)
    assert any(f in normalise for f in fragments), f"témoin « {libelle} » : le nom passe"


@pytest.mark.parametrize(("libelle", "contenu"), TEMOINS_NON_VUS)
def test_le_controle_ne_crie_sur_aucune_forme_legitime(libelle: str, contenu: str) -> None:
    """Quatre formes qu'il ne doit pas voir, dont le fragment trop court du point 7."""
    fragments = fragments_a_chercher([TEMOIN_NOM])
    normalise = normaliser(contenu)
    vus = [f for f in fragments if f in normalise]
    assert not vus, f"témoin « {libelle} » : le contrôle crie à tort — {vus}"


def test_le_seuil_de_longueur_ecarte_les_fragments_courts() -> None:
    """Témoin négatif du point 7 : un mot de trois caractères n'est pas cherché seul."""
    fragments = fragments_a_chercher(["Ali Ben Machinchouette"])
    assert "ali" not in fragments and "ben" not in fragments, fragments
    assert "machinchouette" in fragments, fragments


def test_l_abstention_est_declaree_et_non_silencieuse() -> None:
    """Sans variable, `noms_a_chercher` rend une liste vide : l'abstention est visible."""
    assert fragments_a_chercher([]) == [], "une liste vide de noms ne doit rien chercher"


# --- la propriété ---------------------------------------------------------------------------------


def noms_declares() -> list[str]:
    return [valeur for nom in VARIABLES if (valeur := os.environ.get(nom, "").strip())]


def test_aucun_nom_de_personne_dans_les_fichiers_suivis() -> None:
    noms = noms_declares()
    if not noms:
        pytest.skip(
            "abstention déclarée : ni "
            + " ni ".join(VARIABLES)
            + " n'est renseignée. Ce contrôle ne porte pas les noms qu'il interdit ; "
            "sans elles il ne peut rien chercher, et il le dit plutôt que de passer."
        )
    fautifs = occurrences(fragments_a_chercher(noms), fichiers_suivis())
    assert not fautifs, "Nom de personne trouvé dans des fichiers suivis :\n" + "\n".join(fautifs)
