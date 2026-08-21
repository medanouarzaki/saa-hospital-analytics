"""Les marqueurs nominatifs du rapport s'accordent avec l'état que le document déclare.

C'est la seule propriété que le dépôt affirme sur le CONTENU du rapport. Un rapport dont la page de
garde porte un nom manquant se découvre à l'impression.

DEUX MARQUEURS, ET DEUX SEULEMENT. Le document est un rapport de stage d'application : il a un
auteur et un encadrant de stage, chef du service. Il n'a pas d'encadrant académique, pas de
président de jury, pas d'examinateur. Ces trois marqueurs-là ont existé et ont été RETIRÉS du
fichier, non laissés vides — un marqueur vide est un oubli qui attend. Une propriété ci-dessous
vérifie qu'aucun ne revient.

LA PROPRIÉTÉ EST PERMANENTE, ET CE CONTRÔLE NE CHANGERA PLUS. `report/marqueurs.tex` déclare
l'état `brouillon` et ses deux marqueurs nominatifs vides — toujours. Le passage à la remise ne se
fait pas en modifiant ce fichier : il se fait en déposant `report/noms.tex`, qui n'est jamais
commis et qui redéfinit les deux noms ET l'état.

C'EST LA LEVÉE D'UNE CONTRADICTION, ET ELLE VAUT D'ÊTRE DITE. Ce contrôle exigeait auparavant,
en état de remise, que le fichier commis porte les deux noms ; une autre règle du projet
interdisait au dépôt de les porter. Les deux ne pouvaient pas être vraies ensemble, et la
contradiction était consignée sans être tranchée. Elle l'est : l'état sort du dépôt avec les noms
qu'il commande, et le fichier commis n'a plus qu'un seul état légitime.

CE QU'IL NE PEUT PAS VOIR. Il ne voit rien de `noms.tex` — ni les noms, ni l'état qu'il pose. Un
document composé avec un `noms.tex` mal formé se remettrait sans nom sans qu'aucun contrôle ne
bronche. La seule chose qui l'établirait est la lecture du document composé, que le dépôt ne suit
pas.

CE CONTRÔLE LIT LE FICHIER DES MARQUEURS, JAMAIS LE PDF. Une propriété qui dépend du rendu n'est pas
observable côté serveur — le projet l'a déjà mesuré sur ses graphiques — et un PDF n'est pas suivi
par le gestionnaire de versions. La source est donc le seul objet sur lequel la propriété se
vérifie.

UN MARQUEUR PEUT ÊTRE VIDE DE SIX FAÇONS, et un motif textuel qui n'en verrait qu'une donnerait une
assurance fausse. Les six sont énumérées ci-dessous avec leur témoin positif, et cinq formes que le
motif ne doit PAS prendre pour un marqueur vide ont leur témoin négatif — dont une accolade vide
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

# Les marqueurs qui portent un nom de personne. Ce sont eux, et eux seuls, que la propriété exige
# renseignés en état de remise : les marqueurs de contexte du même fichier — établissement, filière,
# année, organisme d'accueil, date de soutenance — n'en portent aucun et ne sont pas de son ressort.
NOMINATIFS = (
    "marqueurAuteur",
    "marqueurEncadrantProfessionnel",
)

# Les trois marqueurs RETIRÉS. Le document n'a ni encadrant académique, ni jury nommé. Ils sont
# énumérés ici pour qu'un retour, par copie d'un ancien fichier ou par réflexe, soit rouge et non
# silencieux : un marqueur laissé vide sur une page de garde compose une ligne vide, et c'est
# exactement ce que le retrait évite.
RETIRES = (
    "marqueurEncadrantAcademique",
    "marqueurPresidentJury",
    "marqueurExaminateur",
)

# La commande qui porte l'état du document. `brouillon` est la SEULE valeur que le fichier commis
# ait le droit de déclarer ; `remise` reste une valeur du mécanisme typographique, posée par
# `noms.tex`, que ce contrôle ne lit pas et n'a pas à connaître.
ETAT = "etatDuDocument"
BROUILLON = "brouillon"
ETATS_ADMIS = (BROUILLON,)

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
        r"\newcommand{\marqueurAuteur}{Un nom} % renseigné à la remise",
    ),
    (
        "déclaration commentée doublant une déclaration active",
        "% \\newcommand{\\marqueurAuteur}{ancienne valeur}\n\\newcommand{\\marqueurAuteur}{Un nom}",
    ),
)


@pytest.mark.parametrize(("libelle", "source"), TEMOINS_VIDES)
def test_le_motif_voit_chaque_forme_de_marqueur_vide(libelle: str, source: str) -> None:
    """Six formes de vacuité, six témoins : un motif éprouvé sur une seule forme ne l'est pas."""
    assert marqueurs_vides(source, ("marqueurAuteur",)), (
        f"témoin « {libelle} » : le motif ne voit pas ce marqueur vide"
    )


@pytest.mark.parametrize(("libelle", "source"), TEMOINS_RENSEIGNES)
def test_le_motif_ne_prend_aucune_forme_legitime_pour_un_marqueur_vide(
    libelle: str, source: str
) -> None:
    """Quatre formes qu'il ne doit pas voir, et une renseignée ordinaire — cinq témoins."""
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


def test_les_trois_marqueurs_retires_ne_reviennent_pas() -> None:
    """Ils sont RETIRÉS, pas laissés vides : une déclaration, même vide, est rouge.

    Le motif est celui du retrait lui-même. Un `\marqueurPresidentJury` déclaré vide fait
    composer à la page de garde une ligne « Président du jury » sans valeur, et une ligne vide
    se remarque là où une ligne absente ne se remarque pas. Le contrôle porte donc sur la
    PRÉSENCE de la déclaration, pas sur sa valeur.
    """
    source = MARQUEURS.read_text(encoding="utf-8")
    revenus = [
        nom for nom, valeur in valeurs_des_marqueurs(source, RETIRES).items() if valeur is not None
    ]
    assert not revenus, (
        f"marqueurs retirés redéclarés dans {MARQUEURS.name} : {revenus}. "
        "Le document est un rapport de stage d'application : il n'a ni encadrant académique, "
        "ni président de jury, ni examinateur."
    )


def desaccords(source: str) -> list[str]:
    """Ce qui, dans le fichier commis, contredit la propriété permanente.

    Deux façons de la contredire, et une seule branche pour chacune : l'état déclaré n'est pas
    `brouillon` — absent, mal orthographié, ou porté à `remise` dans le fichier commis —, ou l'un
    des deux marqueurs nominatifs y est renseigné.
    """
    etat = etat_declare(source)
    if etat is None:
        return [
            f"aucune déclaration active de \\{ETAT} : l'état du document doit être écrit, "
            f"et valoir « {BROUILLON} »"
        ]
    if etat not in ETATS_ADMIS:
        return [
            f"état « {etat} » : le fichier commis ne déclare que « {BROUILLON} ». "
            "La remise se pose dans `report/noms.tex`, qui n'est pas suivi, et jamais ici."
        ]

    vides = marqueurs_vides(source, NOMINATIFS)
    nommes_vides = {ligne.split(" :")[0] for ligne in vides}
    return [
        f"état « {BROUILLON} » : {nom} est renseigné, alors que le fichier commis les porte "
        "tous deux vides"
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
    (
        "l'état de remise, écrit dans le fichier commis",
        "{remise}",
        "remise",
        "lu telle quelle, puis refusé par desaccords : il ne se pose que dans noms.tex",
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


def test_l_etat_de_remise_est_refuse_dans_le_fichier_commis() -> None:
    """Le témoin qui porte l'arbitrage : la remise ne s'écrit pas ici.

    Sans cette propriété, basculer le fichier commis à `remise` passerait, et les deux noms
    devraient alors y être écrits — ce que le projet interdit par ailleurs. C'est la
    contradiction levée, et elle est éprouvée plutôt que déclarée.
    """
    source = "\\newcommand{\\" + ETAT + "}{remise}"
    ecarts = desaccords(source)
    assert ecarts, "l'état de remise passe dans le fichier commis"
    assert "noms.tex" in ecarts[0], ecarts


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
