"""Les marqueurs nominatifs du rapport s'accordent avec l'état que le document déclare.

C'est la propriété que le critère de terminaison du projet nomme, et la seule que le dépôt affirme
sur le CONTENU du rapport. Un rapport dont la page de garde porte un nom manquant se découvre à
l'impression, ou pire, à la soutenance.

ELLE N'EST PAS AFFAIBLIE, ELLE EST CONDITIONNÉE À UN ÉTAT ÉCRIT. Le fichier des marqueurs déclare
son état — `brouillon` ou `remise`, et rien d'autre — et le contrôle exige des cinq marqueurs qu'ils
soient TOUS vides dans le premier, TOUS renseignés dans le second. Trois choses en découlent, et
aucune n'est une abstention : l'état apparaît dans un diff, là où un contrôle qui se tairait ne
laisserait aucune trace ; l'oubli réaliste — quatre marqueurs sur cinq — est rouge dans les DEUX
états ; et le passage à la remise ne coûte qu'un mot, après quoi le contrôle nomme ce qui manque.

CE CONTRÔLE LIT LE FICHIER DES MARQUEURS, JAMAIS LE PDF. Une propriété qui dépend du rendu n'est pas
observable côté serveur — le projet l'a déjà mesuré sur ses graphiques — et un PDF n'est pas suivi
par le gestionnaire de versions. La source est donc le seul objet sur lequel la propriété se
vérifie.

UN MARQUEUR PEUT ÊTRE VIDE DE CINQ FAÇONS, et un motif textuel qui n'en verrait qu'une donnerait une
assurance fausse. Les cinq sont énumérées ci-dessous avec leur témoin positif, et quatre formes que
le motif ne doit PAS prendre pour un marqueur vide ont leur témoin négatif — dont une accolade vide
légitime ailleurs dans le fichier et un caractère de pourcentage échappé, qui n'introduit aucun
commentaire.

Aucun accès à la base, aucune dépendance à un volume de données : ce fichier se collecte et
s'exécute sur un clone frais.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
MARQUEURS = RACINE / "report" / "marqueurs.tex"

# Les marqueurs qui portent un nom de personne. Ce sont eux, et eux seuls, que le critère de
# terminaison exige renseignés : les marqueurs de contexte du même fichier — établissement, filière,
# année — n'en portent aucun et ne sont pas de son ressort.
NOMINATIFS = (
    "marqueurAuteur",
    "marqueurEncadrantAcademique",
    "marqueurEncadrantProfessionnel",
    "marqueurPresidentJury",
    "marqueurExaminateur",
)

# La commande qui porte l'état du document, et les deux seules valeurs qu'elle admet.
ETAT = "etatDuDocument"
BROUILLON = "brouillon"
REMISE = "remise"
ETATS_ADMIS = (BROUILLON, REMISE)

# Les valeurs d'attente : renseigner un marqueur avec l'une d'elles, c'est ne pas l'avoir renseigné.
VALEURS_D_ATTENTE = ("à compléter", "a completer", "todo", "xxx", "nom prénom", "nom prenom", "...")

# Un caractère de pourcentage ouvre un commentaire, SAUF s'il est échappé par une barre oblique
# inverse — laquelle n'est pas elle-même échappée. La ligne est coupée à cet endroit.
_COMMENTAIRE = re.compile(r"(?<!\\)(?:\\\\)*%")


def _sans_commentaire(ligne: str) -> str:
    trouve = _COMMENTAIRE.search(ligne)
    return ligne if trouve is None else ligne[: trouve.end() - 1]


def valeurs_des_marqueurs(source: str, noms: tuple[str, ...]) -> dict[str, str | None]:
    """Nom de marqueur -> valeur déclarée, ou None si aucune déclaration active ne le définit.

    Une déclaration commentée ne compte pas : elle ne définit rien à la compilation.
    """
    actives = "\n".join(_sans_commentaire(ligne) for ligne in source.splitlines())
    trouvees: dict[str, str | None] = dict.fromkeys(noms)
    for nom in noms:
        motif = re.compile(r"\\newcommand\{\\" + re.escape(nom) + r"\}\{(.*)\}\s*$", re.MULTILINE)
        correspondance = motif.search(actives)
        if correspondance is not None:
            trouvees[nom] = correspondance.group(1)
    return trouvees


def etat_declare(source: str) -> str | None:
    """L'état du document tel que le fichier le déclare, ou None si aucune déclaration active.

    La valeur est normalisée : les espaces qui l'entourent sont retirés et la casse est ramenée en
    minuscules. Une commande dont le nom de l'état est le PRÉFIXE n'est pas confondue avec lui — la
    recherche ancre le nom sur l'accolade qui le ferme.
    """
    valeur = valeurs_des_marqueurs(source, (ETAT,))[ETAT]
    return None if valeur is None else valeur.strip().lower()


def marqueurs_vides(source: str, noms: tuple[str, ...]) -> list[str]:
    """Les marqueurs non renseignés, avec la façon dont ils le sont."""
    manquants = []
    for nom, valeur in valeurs_des_marqueurs(source, noms).items():
        if valeur is None:
            manquants.append(f"{nom} : aucune déclaration active — commande absente ou commentée")
        elif valeur.strip() == "":
            manquants.append(f"{nom} : déclaré vide")
        elif valeur.strip().lower() in VALEURS_D_ATTENTE:
            manquants.append(f"{nom} : valeur d'attente « {valeur.strip()} »")
    return sorted(manquants)


# --- les témoins, dans les deux sens ------------------------------------------------------------

TEMOINS_VIDES = (
    ("accolades vides", r"\newcommand{\marqueurAuteur}{}"),
    ("accolades ne portant que des espaces", "\\newcommand{\\marqueurAuteur}{   }"),
    ("accolades ne portant qu'une tabulation", "\\newcommand{\\marqueurAuteur}{\t}"),
    ("commande absente", r"\newcommand{\marqueurAutreChose}{Un nom}"),
    ("commande commentée", r"% \newcommand{\marqueurAuteur}{Un nom}"),
    ("valeur d'attente", r"\newcommand{\marqueurAuteur}{À compléter}"),
)

TEMOINS_RENSEIGNES = (
    ("valeur ordinaire", r"\newcommand{\marqueurAuteur}{Un nom}"),
    (
        "accolade vide légitime ailleurs dans le fichier",
        "\\newcommand{\\marqueurAuteur}{Un nom}\n\\newcommand{\\autreCommande}{}",
    ),
    (
        "pourcentage échappé, qui n'ouvre aucun commentaire",
        "\\newcommand{\\marqueurAuteur}{Un taux de 40\\% de lits}",
    ),
    (
        "commentaire APRÈS une déclaration renseignée",
        r"\newcommand{\marqueurAuteur}{Un nom} % renseigné à la soutenance",
    ),
    (
        "déclaration commentée doublant une déclaration active",
        "% \\newcommand{\\marqueurAuteur}{ancienne valeur}\n\\newcommand{\\marqueurAuteur}{Un nom}",
    ),
)


@pytest.mark.parametrize(("libelle", "source"), TEMOINS_VIDES)
def test_le_motif_voit_chaque_forme_de_marqueur_vide(libelle: str, source: str) -> None:
    """Cinq formes de vacuité, cinq témoins : un motif éprouvé sur une seule forme ne l'est pas."""
    assert marqueurs_vides(source, ("marqueurAuteur",)), (
        f"témoin « {libelle} » : le motif ne voit pas ce marqueur vide"
    )


@pytest.mark.parametrize(("libelle", "source"), TEMOINS_RENSEIGNES)
def test_le_motif_ne_prend_aucune_forme_legitime_pour_un_marqueur_vide(
    libelle: str, source: str
) -> None:
    """Quatre formes qu'il ne doit pas voir, et une renseignée ordinaire."""
    vides = marqueurs_vides(source, ("marqueurAuteur",))
    assert not vides, f"témoin « {libelle} » : le motif crie à tort — {vides}"


# --- la propriété ---------------------------------------------------------------------------------


def test_le_fichier_des_marqueurs_existe_et_les_declare_tous() -> None:
    """Un marqueur retiré du fichier n'est pas un marqueur renseigné."""
    assert MARQUEURS.is_file(), f"fichier des marqueurs absent : {MARQUEURS}"
    source = MARQUEURS.read_text(encoding="utf-8")
    absents = [
        nom for nom, valeur in valeurs_des_marqueurs(source, NOMINATIFS).items() if valeur is None
    ]
    assert not absents, f"marqueurs nominatifs non déclarés dans {MARQUEURS.name} : {absents}"


def desaccords(source: str) -> list[str]:
    """Ce qui, dans une source, contredit l'état qu'elle déclare."""
    etat = etat_declare(source)
    if etat is None:
        return [
            f"aucune déclaration active de \\{ETAT} : l'état du document doit être écrit, "
            f"et valoir « {BROUILLON} » ou « {REMISE} »"
        ]
    if etat not in ETATS_ADMIS:
        return [
            f"état « {etat} » : les seules valeurs admises sont "
            + " et ".join(f"« {v} »" for v in ETATS_ADMIS)
        ]

    vides = marqueurs_vides(source, NOMINATIFS)
    if etat == REMISE:
        return [f"état « {REMISE} » : {ligne}" for ligne in vides]

    nommes_vides = {ligne.split(" :")[0] for ligne in vides}
    return [
        f"état « {BROUILLON} » : {nom} est renseigné, alors qu'un brouillon les porte tous vides"
        for nom in NOMINATIFS
        if nom not in nommes_vides
    ]


@pytest.mark.parametrize("etat", ETATS_ADMIS)
def test_le_motif_lit_chaque_valeur_d_etat_admise(etat: str) -> None:
    """Un témoin positif par valeur admise."""
    source = "\\newcommand{\\" + ETAT + "}{" + etat + "}"
    assert etat_declare(source) == etat, f"la valeur « {etat} » n'est pas lue"


TEMOINS_D_ETAT = (
    ("valeur entourée d'espaces", "{  brouillon  }", BROUILLON, "acceptée après normalisation"),
    ("casse différente", "{Brouillon}", BROUILLON, "acceptée après normalisation"),
    (
        "valeur tierce",
        "{provisoire}",
        "provisoire",
        "lue telle quelle, puis refusée par desaccords",
    ),
    ("déclaration commentée", None, None, "refusée : aucune déclaration active"),
)


@pytest.mark.parametrize(("libelle", "corps", "attendu", "traitement"), TEMOINS_D_ETAT)
def test_le_motif_traite_chaque_forme_d_etat_comme_annonce(
    libelle: str, corps: str | None, attendu: str | None, traitement: str
) -> None:
    """Quatre formes voisines, et ce que le contrôle fait de chacune — annoncé, puis prouvé."""
    declaration = "\\newcommand{\\" + ETAT + "}"
    source = f"% {declaration}{{brouillon}}" if corps is None else declaration + corps
    assert etat_declare(source) == attendu, f"témoin « {libelle} » ({traitement})"


def test_le_motif_ne_confond_pas_l_etat_avec_une_commande_dont_il_est_le_prefixe() -> None:
    """Témoin négatif : une commande dont le nom de l'état est le préfixe n'est pas l'état."""
    source = "\\newcommand{\\" + ETAT + "Precedent}{remise}"
    assert etat_declare(source) is None, "une commande préfixée a été prise pour l'état"


def test_une_valeur_tierce_est_refusee() -> None:
    """Elle est lue, puis refusée : le contrôle dit laquelle, et ce qu'il attendait."""
    source = "\\newcommand{\\" + ETAT + "}{provisoire}"
    ecarts = desaccords(source)
    assert ecarts and "provisoire" in ecarts[0], ecarts


def test_l_etat_declare_est_l_une_des_deux_valeurs_admises() -> None:
    """Sur le fichier réel : l'état est écrit, et il est admis."""
    etat = etat_declare(MARQUEURS.read_text(encoding="utf-8"))
    assert etat in ETATS_ADMIS, (
        f"état déclaré dans {MARQUEURS.name} : {etat!r} — attendu "
        + " ou ".join(f"« {v} »" for v in ETATS_ADMIS)
    )


def test_les_marqueurs_nominatifs_s_accordent_avec_l_etat_declare() -> None:
    """La propriété du critère de terminaison, conditionnée à l'état, sur le fichier réel."""
    ecarts = desaccords(MARQUEURS.read_text(encoding="utf-8"))
    assert not ecarts, (
        f"les marqueurs de {MARQUEURS.name} contredisent l'état déclaré :\n" + "\n".join(ecarts)
    )
