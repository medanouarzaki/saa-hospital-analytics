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

CE QUE LE CONTRÔLE CHERCHE : DES NOMS, ET NON DES MOTS. Il cherche toute SUITE D'AU
MOINS DEUX MOTS CONSÉCUTIFS du nom — pour « Prénom Second Nom », les trois suites
« prénom second », « second nom » et « prénom second nom ». Un mot isolé n'est pas
cherché.

POURQUOI LA PROPRIÉTÉ A CHANGÉ, ET POURQUOI L'ANCIENNE ÉTAIT FAUSSE. Ce contrôle
cherchait auparavant chaque mot du nom PRIS ISOLÉMENT, dès quatre caractères. Cette
propriété n'était pas seulement bruyante, elle était FAUSSE : un mot isolé n'identifie
personne. Mesuré au moment de la corriger, sur les deux noms réels du projet, l'ancienne
propriété rougissait sur douze fichiers, et aucun ne portait de nom :

  - dix fois sur un prénom très répandu que le dépôt porte comme NOM D'UN AUTRE HÔPITAL
    du centre hospitalier, et comme prénom de fiches du jeu de données engendré ;
  - deux fois sur des morceaux du nom de compte contenus dans L'ADRESSE DU DÉPÔT
    elle-même.

Un contrôle qui rougit là où rien n'est fautif n'est pas prudent : il apprend à être
ignoré. La propriété corrigée cherche ce que le contrôle existe pour interdire — un nom
de personne écrit dans un fichier suivi.

L'ÉLARGISSEMENT NE PASSE PAS PAR UN MÉCANISME NEUF. Le contrôle en porte déjà un,
`EXCLUSIONS_PAR_VARIABLE`, qui écarte un fichier NOMMÉMENT et POUR UN SEUL DES DEUX NOMS.
Il sert au fichier de licence, et il continue de servir : mesuré, `LICENSE` porte bien le
nom complet de l'auteur, et l'exclusion y est donc encore nécessaire — elle n'est pas
décorative. Aucun autre fichier n'a eu besoin d'y être ajouté : la propriété corrigée rend
zéro fautif sur l'arbre.

LE CONTRÔLE NE PORTE PAS LES NOMS QU'IL INTERDIT — voir plus haut.

PAR QUELLE VOIE UN NOM COMPLET PASSERAIT-IL MALGRÉ TOUT ? Neuf voies ont été cherchées.
Quatre sont fermées, cinq restent ouvertes et sont écrites ici plutôt que laissées à
découvrir.

  FERMÉES
  1. Casse différente — « nom » contre « Nom ». Fermée : la comparaison passe par
     `casefold()`.
  2. Accents composés autrement — « é » en un caractère contre « e » suivi d'un accent
     combinant. Fermée : les deux côtés sont normalisés en NFD puis dépouillés de leurs
     marques combinantes, ce qui rend aussi « Zaki » et « Zàki » identiques.
  3. Espaces multiples, tabulation ou saut de ligne entre les mots du nom. Fermée : les
     suites d'espaces blancs sont réduites à une espace simple des deux côtés.
  4. Fichier binaire ou d'encodage inattendu, où une lecture stricte lèverait et
     ferait passer le fichier pour vide. Fermée : la lecture est faite en octets puis
     décodée en tolérant les octets invalides.

  OUVERTES, ET ASSUMÉES — cinq voies, et les trois premières sont le prix EXACT de la
  propriété corrigée. Les fermer ramènerait la recherche par mot isolé, donc les douze
  faux positifs mesurés ci-dessus.
  5. LES MOTS DU NOM ÉCRITS SANS SÉPARATEUR — « prenomnom », un nom de compte, un
     identifiant, une adresse. Le contrôle cherche des mots séparés par une espace et ne
     les y trouve pas. C'est le cas de l'adresse de ce dépôt, et c'est ASSUMÉ : cette
     adresse est publique par nature, et la fermer reviendrait à chercher des sous-mots,
     c'est-à-dire à revenir à la propriété fausse.
  6. UN SÉPARATEUR AUTRE QU'UNE ESPACE entre deux mots du nom — « Prénom, Nom »,
     « Prénom-Nom », « Prénom.Nom ». La normalisation ne touche pas à la ponctuation :
     la retirer ferait se rejoindre des mots que rien ne joignait, et rendrait le
     contrôle rouge sur des suites accidentelles.
  7. L'ORDRE DES MOTS INVERSÉ — « Nom Prénom » là où la variable porte « Prénom Nom ».
     Non fermée : trier les mots avant de comparer, comme le fait la normalisation du
     rapprochement d'identités, rendrait la recherche insensible à l'ordre mais
     multiplierait les suites cherchées sans qu'aucune ne corresponde à une écriture
     attestée dans ce dépôt.
  8. Un nom coupé par une césure ou par un retour à la ligne À L'INTÉRIEUR d'un mot.
     Non fermée : la fermer supposerait de savoir où un mot peut se couper.
  9. Un nom présent dans l'HISTORIQUE du dépôt mais plus dans l'arbre courant. Non
     fermée : ce contrôle lit `git ls-files`, donc l'arbre, jamais les révisions
     antérieures. Un nom déjà commis exige une réécriture d'historique, que ce contrôle
     ne peut ni faire ni voir.

CE QUE LE CONTRÔLE NE PEUT PAS VOIR, ET QUI N'EST PAS UNE VOIE DE CONTOURNEMENT. Il ne
voit qu'un nom ÉCRIT. Une personne désignée sans être nommée — « l'auteur », une adresse
électronique, une photographie, une signature manuscrite dans une image, un nom porté par
les métadonnées d'un fichier binaire plutôt que par son texte — lui échappe entièrement.
Il ne dit donc pas « personne n'est identifiable » : il dit « aucun des deux noms déclarés
n'est écrit en toutes lettres dans un fichier suivi ».

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

# Une suite d'au moins DEUX mots consécutifs du nom : c'est ce qui identifie une personne,
# quand un mot isolé ne le fait pas.
LONGUEUR_MINIMALE_D_UNE_SUITE = 2

# Le seul cas où un mot isolé est cherché : un nom qui n'en compte qu'un. Il est alors le nom
# complet, et non un fragment. Le seuil de quatre caractères le protège d'un nom d'un ou deux
# caractères, qui rougirait sur n'importe quelle prose.
LONGUEUR_MINIMALE_D_UN_NOM_D_UN_SEUL_MOT = 4

# Ce fichier se nomme lui-même : il cite les variables, jamais les valeurs. Il est
# néanmoins exclu du balayage, comme tout fichier qui pourrait légitimement porter le
# mot cherché sans porter le nom.
FICHIERS_EXCLUS = frozenset({"tests/test_aucun_nom_de_personne.py"})

# UNE EXCLUSION PAR NOM, ET NON UNE EXCLUSION GÉNÉRALE. `LICENSE` porte le nom de l'auteur dans sa
# ligne de droit d'auteur, et c'est la fonction même d'une licence : elle nomme le titulaire des
# droits. Le retirer viderait le fichier de son sens.
#
# L'exclusion est donc étroite. Elle vaut pour le nom de l'AUTEUR et pour lui seul ; le nom de
# l'encadrant reste cherché dans `LICENSE` comme partout ailleurs, et l'y déposer est rouge. Une
# exclusion générale du fichier aurait ouvert une porte pour les deux noms au lieu d'un.
EXCLUSIONS_PAR_VARIABLE: dict[str, frozenset[str]] = {
    "RAPPORT_AUTEUR": frozenset({"LICENSE"}),
}

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


def suites_a_chercher(noms: list[str]) -> list[str]:
    """Toute suite d'au moins deux mots CONSÉCUTIFS du nom, normalisée.

    Pour « Prénom Second Nom » : « prénom second », « second nom », « prénom second nom ».
    Un mot isolé n'est jamais rendu — c'est la propriété même de ce contrôle, et le motif
    est écrit en tête de fichier.

    Le seul mot isolé possible est celui d'un nom qui n'en compte qu'un : il est alors le
    nom complet.
    """
    cherchees: set[str] = set()
    for nom in noms:
        complet = normaliser(nom)
        if not complet:
            continue
        mots = complet.split(" ")
        if len(mots) < LONGUEUR_MINIMALE_D_UNE_SUITE:
            if len(mots[0]) >= LONGUEUR_MINIMALE_D_UN_NOM_D_UN_SEUL_MOT:
                cherchees.add(mots[0])
            continue
        for debut in range(len(mots)):
            for fin in range(debut + LONGUEUR_MINIMALE_D_UNE_SUITE, len(mots) + 1):
                cherchees.add(" ".join(mots[debut:fin]))
    return sorted(cherchees)


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


def occurrences(par_variable: dict[str, list[str]], chemins: list[str]) -> list[str]:
    """Les fichiers suivis qui portent une suite de mots du nom, variable par variable.

    Le balayage est fait PAR VARIABLE et non sur l'union des suites : c'est ce qui permet
    d'exclure un fichier pour un nom sans l'exclure pour l'autre.

    LE MESSAGE NE RECOPIE PAS LA SUITE TROUVÉE, il en donne le nombre de mots. Recopier la
    suite ferait apparaître le nom dans la sortie du contrôle, donc au journal de
    l'intégration continue — ce que ce contrôle existe précisément pour empêcher.
    """
    trouvees = []
    for chemin in chemins:
        if chemin in FICHIERS_EXCLUS:
            continue
        contenu = lire(chemin)
        for variable, suites in par_variable.items():
            if chemin in EXCLUSIONS_PAR_VARIABLE.get(variable, frozenset()):
                continue
            for suite in suites:
                if suite in contenu:
                    mots = len(suite.split(" "))
                    trouvees.append(f"{chemin} : porte {mots} mot(s) consécutif(s) de {variable}")
    return sorted(set(trouvees))


# --- les témoins, dans les deux sens ------------------------------------------------------------

# CE NOM D'ESSAI PORTE TROIS MOTS, ET LE TROISIÈME N'EST PAS DÉCORATIF : un nom de deux mots
# ne rend qu'une seule suite, et n'aurait pas éprouvé la recherche des suites INTERNES —
# « second nom » sans le premier mot. Le témoin correspondant est plus bas.
TEMOIN_NOM = "Zéphyrin Casimir Machinchouette"

TEMOINS_VUS = (
    ("nom complet tel quel", "signé Zéphyrin Casimir Machinchouette, 2026"),
    ("casse différente", "signé zéphyrin CASIMIR machinchouette"),
    ("accent décomposé", "signé Zéphyrin Casimir Machinchouette"),
    ("accent absent", "signé Zephyrin Casimir Machinchouette"),
    ("espaces multiples", "signé Zéphyrin    Casimir  Machinchouette"),
    ("saut de ligne entre deux mots", "signé Zéphyrin Casimir\nMachinchouette"),
    ("les deux premiers mots seulement", "signé Zéphyrin Casimir, 2026"),
    ("les deux derniers mots seulement", "l'encadrant Casimir Machinchouette a relu"),
    ("suite du nom suivie d'un suffixe", "voir casimir machinchouettes.txt"),
    ("suite du nom précédée d'un préfixe", "signé parCasimir Machinchouette"),
)

# LES DEUX DERNIERS TÉMOINS DISENT UN PARTI PRIS : une suite du nom EN SOUS-CHAÎNE d'un texte
# plus long fait rougir le contrôle. Sur-détecter coûte une vérification à la main ;
# sous-détecter laisse passer un nom. C'est le seul parti pris conservé de la propriété
# précédente.

TEMOINS_NON_VUS = (
    ("aucun mot du nom", "signé un encadrant anonyme"),
    ("prose ordinaire du dépôt", "le tableau de bord porte neuf pages"),
    # LES QUATRE TÉMOINS QUI SUIVENT SONT LE CŒUR DE LA PROPRIÉTÉ CORRIGÉE. Chacun était VU
    # par la propriété précédente, et chacun devait cesser de l'être : aucun ne nomme
    # personne. Ce sont eux qui distinguent un changement de NATURE d'un simple
    # rétrécissement de portée.
    ("un seul mot du nom, isolé", "l'hôpital Casimir V, quarante lits"),
    ("un autre mot du nom, isolé", "Zéphyrin a relu"),
    ("un mot du nom dans un mot plus long", "voir machinchouettes.txt"),
    ("les mots du nom collés, comme dans une adresse", "https://exemple.org/zephyrincasimir/"),
    # Les trois suivants sont des voies OUVERTES, écrites en tête de fichier sous les
    # numéros 6 et 7. Ce sont des témoins de ce que le contrôle NE VOIT PAS, et ils sont ici
    # pour que cette limite soit exécutée plutôt que seulement déclarée.
    ("séparateur autre qu'une espace — voie ouverte 6", "signé Zéphyrin, Casimir, Machinchouette"),
    ("mots joints par un tiret — voie ouverte 6", "signé Zéphyrin-Casimir-Machinchouette"),
    ("ordre des mots inversé — voie ouverte 7", "signé Machinchouette Casimir Zéphyrin"),
)


@pytest.mark.parametrize(("libelle", "contenu"), TEMOINS_VUS)
def test_le_controle_voit_chaque_forme_du_nom(libelle: str, contenu: str) -> None:
    """Dix formes, dix témoins : un contrôle éprouvé sur une seule ne l'est pas."""
    suites = suites_a_chercher([TEMOIN_NOM])
    normalise = normaliser(contenu)
    assert any(s in normalise for s in suites), f"témoin « {libelle} » : le nom passe"


@pytest.mark.parametrize(("libelle", "contenu"), TEMOINS_NON_VUS)
def test_le_controle_ne_crie_sur_aucune_forme_legitime(libelle: str, contenu: str) -> None:
    """Neuf formes qu'il ne doit pas voir, dont les quatre que la correction a libérées."""
    suites = suites_a_chercher([TEMOIN_NOM])
    normalise = normaliser(contenu)
    vus = [s for s in suites if s in normalise]
    assert not vus, f"témoin « {libelle} » : le contrôle crie à tort — {len(vus)} suite(s)"


def test_aucun_mot_isole_n_est_cherche() -> None:
    """LE TÉMOIN DE LA PROPRIÉTÉ, et il vaut d'être lu.

    Aucune des suites cherchées ne compte un seul mot. C'est la différence entre chercher
    un nom et chercher un mot, et c'est elle qui a fait passer le contrôle de douze faux
    positifs à zéro sur l'arbre réel.
    """
    suites = suites_a_chercher([TEMOIN_NOM])
    d_un_seul_mot = [s for s in suites if " " not in s]
    assert not d_un_seul_mot, f"des mots isolés sont cherchés : {len(d_un_seul_mot)}"
    assert len(suites) == 3, suites


def test_les_suites_internes_sont_cherchees() -> None:
    """Un nom de trois mots rend aussi la suite qui saute le premier.

    Sans elle, « Second Nom » écrit sans le prénom passerait, et c'est pourtant un nom.
    """
    suites = suites_a_chercher(["Alpha Beta Gamma"])
    assert set(suites) == {"alpha beta", "beta gamma", "alpha beta gamma"}, suites


def test_un_nom_d_un_seul_mot_est_cherche_entier() -> None:
    """Le seul cas où un mot isolé est cherché : quand il EST le nom complet.

    Le seuil de quatre caractères le protège d'un nom trop court pour être cherché seul.
    """
    assert suites_a_chercher(["Machinchouette"]) == ["machinchouette"]
    assert suites_a_chercher(["Li"]) == [], "un nom de deux caractères ne se cherche pas seul"


def test_l_abstention_est_declaree_et_non_silencieuse() -> None:
    """Sans variable, `noms_a_chercher` rend une liste vide : l'abstention est visible."""
    assert suites_a_chercher([]) == [], "une liste vide de noms ne doit rien chercher"


# --- la propriété ---------------------------------------------------------------------------------


def noms_declares() -> dict[str, str]:
    return {nom: valeur for nom in VARIABLES if (valeur := os.environ.get(nom, "").strip())}


def test_l_exclusion_de_licence_ne_vaut_que_pour_l_auteur() -> None:
    """Le témoin de l'étroitesse de l'exclusion, et il porte l'arbitrage.

    `LICENSE` est écarté pour le nom de l'auteur, parce qu'une licence nomme le titulaire des
    droits. Il ne l'est pour aucun autre : le nom de l'encadrant y est cherché comme partout.
    """
    ecartes = EXCLUSIONS_PAR_VARIABLE.get("RAPPORT_AUTEUR", frozenset())
    assert "LICENSE" in ecartes, "l'exclusion de LICENSE pour l'auteur a disparu"
    assert "LICENSE" not in EXCLUSIONS_PAR_VARIABLE.get("RAPPORT_ENCADRANT", frozenset()), (
        "LICENSE serait écarté pour l'encadrant : l'exclusion cesserait d'être étroite"
    )

    temoin = ["LICENSE", "README.md"]
    par_variable = {"RAPPORT_ENCADRANT": suites_a_chercher([TEMOIN_NOM])}
    contenu_licence = lire("LICENSE")
    assert TEMOIN_NOM.split()[0].lower() not in contenu_licence, (
        "le nom d'essai figure dans LICENSE : ce témoin ne prouverait rien"
    )
    assert occurrences(par_variable, temoin) == [], (
        "le témoin doit être muet tant que le nom d'essai n'est nulle part"
    )


def test_aucun_nom_de_personne_dans_les_fichiers_suivis() -> None:
    noms = noms_declares()
    if not noms:
        pytest.skip(
            "abstention déclarée : ni "
            + " ni ".join(VARIABLES)
            + " n'est renseignée. Ce contrôle ne porte pas les noms qu'il interdit ; "
            "sans elles il ne peut rien chercher, et il le dit plutôt que de passer."
        )
    par_variable = {variable: suites_a_chercher([valeur]) for variable, valeur in noms.items()}
    fautifs = occurrences(par_variable, fichiers_suivis())
    assert not fautifs, "Nom de personne trouvé dans des fichiers suivis :\n" + "\n".join(fautifs)
