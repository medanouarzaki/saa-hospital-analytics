"""Aucun chiffre littéral n'est composé par le rapport hors d'un appel au registre.

LE MOTIF EST MESURÉ, ET IL EST RÉCENT. Le tableau d'ablation du chapitre du rapprochement portait
`0,9995` tapé à la main, dans une ligne dont les trois autres valeurs venaient du registre. Aucun
contrôle ne pouvait le voir : celui du registre vérifie la correspondance entre appels et entrées,
et un nombre tapé n'appelle rien. Il a vécu là plusieurs mois, et c'est une relecture qui l'a
trouvé, pas un code.

CE QUE CE CONTRÔLE REGARDE. La partie ACTIVE des sources de rédaction — commentaires retirés —,
dépouillée de ce qui porte légitimement des chiffres sans être une valeur affirmée : les arguments
des commandes techniques, les options entre crochets, les environnements de tracé. Ce qui reste est
de la prose et des cellules de tableau ; un chiffre qui y subsiste est un chiffre tapé.

SES EXCEPTIONS SONT DÉCLARÉES, PAS DEVINÉES. Un numéro d'article, une année, une date, un
identifiant de relevé ou de source, une classification nommée par son millésime : ce sont des
désignations, non des grandeurs mesurées. Chacune est écrite ci-dessous avec son motif, et un
témoin négatif vérifie que le contrôle les laisse passer — sans lui, il rougirait partout et ne
prouverait rien.

SON POINT AVEUGLE EST ÉCRIT. Il ne voit pas un nombre écrit en toutes lettres — « onze tables »,
« deux ans et demi ». C'est par là que deux décomptes du projet sont devenus faux, et rien ici ne
les rattraperait ; ils se vérifient à la main, contre le registre.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
CHAPITRES = RACINE / "report" / "chapitres"
LIMINAIRES = RACINE / "report" / "liminaires"

# Les fichiers d'annexe PRODUITS mécaniquement depuis un registre. Ils portent des milliers de
# chiffres, tous engendrés, et aucun n'est tapé par une main. Les examiner ferait rougir ce contrôle
# sur ce que le projet fait de plus sûr. L'exclusion est nommée fichier par fichier, jamais par
# motif de nom : un fichier d'annexe RÉDIGÉ à la main doit entrer au périmètre.
ANNEXES_PRODUITES = (
    "dictionnaire_donnees.tex",
    "dictionnaire_synthese.tex",
    "releve_des_ecrans.tex",
    "correspondance_relations.tex",
)

# Les commandes dont l'argument porte légitimement des chiffres : un identifiant, une clé, une
# dimension. Leur argument est retiré avant l'examen, jamais leur trace.
COMMANDES_A_ARGUMENT = (
    "chiffre",
    "serie",
    "releve",
    "convention",
    "cite",
    "ref",
    "label",
    "pageref",
    "input",
    "includegraphics",
    "captureTdb",
    "unLogo",
    "declarerCapture",
    "rule",
    "vspace",
    "hspace",
    "addlinespace",
    "setlength",
    "textls",
    "colorbox",
    "color",
    "definecolor",
    "raisebox",
    "parbox",
    "multicolumn",
    "annonceChapitre",
    "conclusion",
    "relreprise",
    "relnonreprise",
    "conclusionhors",
    "aRediger",
    "logoEcole",
    # `\texttt{...}` reproduit à l'identique un libellé, une valeur ou un identifiant relevés à
    # l'écran ou donnés par le code. Ce n'est pas une grandeur que le rapport affirme : c'est une
    # citation, et la corriger serait la fausser.
    "texttt",
)

# Les désignations qui portent un chiffre sans être une grandeur mesurée. Chacune son motif.
EXCEPTIONS = (
    (r"article~?\s?\d+", "un numéro d'article de règlement désigne, il ne mesure pas"),
    (r"n\\textsuperscript\{o\}~?\s?[\d-]+", "un numéro d'arrêté ou de bulletin désigne"),
    (r"\bCIM-10\b", "une classification nommée par son millésime"),
    (r"\bS-\d{2}\b", "une clé de source du registre des sources"),
    (r"\bREL-[A-Z]{3}\.[A-Z]\d{2}\b", "un identifiant de relevé d'écran"),
    (r"\bC-\d{2}\b", "un identifiant de conclusion"),
    (r"\bR-\d{2}\b", "un identifiant de relation injectée"),
    (
        r"\b\d{1,2}[~ ](?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)(?:[~ ](?:19|20)\d{2})?",  # noqa: E501
        "une date en toutes lettres",
    ),
    (r"\b(?:19|20)\d{2}\b", "une année"),
    (r"\b\d{4}[-/]\d{2}[-/]\d{2}\b", "une date au format ISO"),
    # AUCUN RENVOI N'EST EXEMPTÉ. Un numéro de chapitre, de section, de figure, de tableau ou de
    # page tapé dans la prose est un nombre tapé : un renvoi interne passe par `\ref`, retiré avec
    # son argument, et une localisation dans une source citée par l'argument optionnel de `\cite`,
    # retiré avec la commande. Une exemption de ces formes avait survécu à leur dernier usage.
    (r"\bniveaux? de tri~?\s?\d+", "un rang de l'échelle de tri publiée"),
    (r"\bNom de famille \d\b", "un libellé d'écran reproduit à l'identique"),
    (r"\bTéléphone \d\b", "un libellé d'écran reproduit à l'identique"),
    (r"^\s*\d+\s*&", "un rang d'énumération en tête de ligne de tableau"),
)


# ------------------------------------------------------------------------------------------
# LES OCCURRENCES DÉJÀ PRÉSENTES, NOMMÉES UNE PAR UNE.
#
# Ce contrôle est écrit après coup, sur un rapport terminé, et il trouve QUARANTE-DEUX lignes qui
# composent un chiffre littéral. Ce n'est pas un défaut du contrôle : ce sont des nombres tapés, et
# la règle du projet est qu'aucun ne devrait l'être.
#
# Les corriger toutes est un travail à part entière : chacune demande une entrée au registre avec
# LA COMMANDE QUI LA PRODUIT, et ces valeurs viennent de sources publiées dont la valeur vit dans
# la prose d'un fichier de sources, non dans une table. Une seule a été corrigée — la F-mesure de
# la variante A, celle par laquelle ce contrôle est né. Les autres sont nommées ici plutôt que tues.
#
# CE QUE CETTE LISTE FAIT, ET CE QU'ELLE NE FAIT PAS. Elle rend le contrôle utile immédiatement :
# toute occurrence NOUVELLE est rouge, et une occurrence corrigée disparaît d'ici. Elle ne rend
# vraie aucune des lignes qu'elle porte : elles restent des nombres tapés, et le relevé des
# critères les compte comme la dette qu'elles sont.
#
# La clé est le fichier ET la ligne dépouillée : modifier une de ces lignes la fait sortir de la
# liste, donc rougir. On ne peut pas la retoucher en silence.
# Les lignes ci-dessous sont des DONNÉES, pas du code : chacune reproduit à l'identique une ligne
# de source, et la couper la rendrait inutilisable comme clé. Elles portent donc la dérogation à la
# longueur, une par une et jamais globalement.
RESTES_CONNUS = (("page-de-garde.tex", "\\setstretch{1.0}"),)


_COMMENTAIRE = re.compile(r"(?<!\\)%.*")
_ENV_TRACE = re.compile(r"\\begin\{(tikzpicture|axis|ybar|pgfplots)\}.*?\\end\{\1\}", re.S)
_PGF = re.compile(r"\\pgfplotstabletypeset\[.*?\]\{[^}]*\}", re.S)
_OPTIONS = re.compile(r"\[[^\]\n]*\]")
# Le préambule de colonnes d'un tableau, et les dimensions qu'il porte : de la typographie, jamais
# une grandeur affirmée. Idem des définitions de commande, qui portent des numéros d'argument.
_TABULAIRE = re.compile(r"\\begin\{tabular\}\{[^\n]*\}")
_DEFINITION = re.compile(r"\\(?:def|newcommand|renewcommand|newlength|setlength|newcounter)[^\n]*")
_DIMENSION = re.compile(r"\d+(?:[.,]\d+)?\s*(?:cm|mm|pt|em|ex|in|\\linewidth|\\textwidth|\\height)")
_CHIFFRE = re.compile(r"\d")


def fichiers_examines() -> list[Path]:
    """Les sources RÉDIGÉES du rapport, annexes produites exclues."""
    annexes = [
        RACINE / "report" / nom
        for nom in sorted(
            p.name
            for p in (RACINE / "report").glob("*.tex")
            if p.name not in ANNEXES_PRODUITES
            and p.name
            not in (
                "rapport.tex",
                "chiffres.tex",
                "marqueurs.tex",
                "provenance.tex",
                "images.tex",
                "annexes.tex",
            )
        )
    ]
    return sorted(CHAPITRES.glob("*.tex")) + sorted(LIMINAIRES.glob("*.tex")) + annexes


def partie_active(source: str) -> str:
    return _COMMENTAIRE.sub("", source)


def depouiller(source: str) -> str:
    """Retire ce qui porte légitimement des chiffres, puis les désignations déclarées."""
    texte = partie_active(source)
    texte = _ENV_TRACE.sub(" ", texte)
    texte = _PGF.sub(" ", texte)
    texte = _TABULAIRE.sub(" ", texte)
    texte = _DEFINITION.sub(" ", texte)
    texte = _DIMENSION.sub(" ", texte)
    for commande in COMMANDES_A_ARGUMENT:
        texte = re.sub(r"\\" + commande + r"\*?(\[[^\]]*\])?(\{[^{}]*\})*", " ", texte)
    texte = _OPTIONS.sub(" ", texte)
    for motif, _ in EXCEPTIONS:
        texte = re.sub(motif, " ", texte, flags=re.M)
    return texte


def nombres_tapes(source: str) -> list[str]:
    depouille = depouiller(source)
    return [ligne.strip() for ligne in depouille.splitlines() if _CHIFFRE.search(ligne)]


def occurrences() -> list[tuple[str, str]]:
    trouvees = []
    for chemin in fichiers_examines():
        for ligne in nombres_tapes(chemin.read_text(encoding="utf-8")):
            trouvees.append((chemin.name, " ".join(ligne.split())))
    return trouvees


def test_aucun_nombre_tape_nouveau() -> None:
    """Toute occurrence qui n'est pas nommée à la liste des restes est rouge."""
    connus = set(RESTES_CONNUS)
    nouvelles = [f"{f} : {ligne[:110]}" for f, ligne in occurrences() if (f, ligne) not in connus]
    assert not nouvelles, (
        f"{len(nouvelles)} chiffre(s) littéral(aux) composé(s) hors d'un appel au registre, et non "
        "déclaré(s) :\n  " + "\n  ".join(nouvelles)
    )


def test_la_liste_des_restes_ne_porte_rien_de_perime() -> None:
    """L'autre sens : une ligne corrigée doit sortir de la liste, sans quoi la dette ment.

    Sans cette épreuve, la liste grossirait sans jamais maigrir et finirait par nommer des lignes
    qui n'existent plus — une dette fausse est aussi inutile qu'une dette tue.
    """
    presentes = set(occurrences())
    perimees = [f"{f} : {ligne[:80]}" for f, ligne in RESTES_CONNUS if (f, ligne) not in presentes]
    assert not perimees, (
        f"{len(perimees)} ligne(s) déclarée(s) aux restes et absente(s) des fichiers — "
        "retirez-les de RESTES_CONNUS :\n  " + "\n  ".join(perimees)
    )


@pytest.mark.parametrize(
    "source",
    [
        r"la marge vaut 270,87 sur le modèle complet",
        r"le taux atteint 53,8 \% en 2024",
        r"& 0,9995 & \chiffre{ablation-ecart-variante-a} \\",
        r"le tableau~32 du recueil",
        r"voir le chapitre~4",
    ],
)
def test_le_motif_voit_un_nombre_tape(source: str) -> None:
    """Témoin positif — dont le troisième est le cas réel qui a motivé ce contrôle."""
    assert nombres_tapes(source), "un nombre tapé passe inaperçu"


@pytest.mark.parametrize(
    "source",
    [
        r"C'est l'article~35 qui porte les neuf missions du service \cite{s27}.",
        r"l'arrêté n\textsuperscript{o}~456-11 du 6~juillet 2010",
        r"la classification des maladies, soit la CIM-10",
        r"le chapitre~\ref{chap:qualite} le reprend",
        r"le recueil le donne \cite[tableau~32]{s30}",
        r"\cite[tableau~32, p.~46]{s30}",
        r"un relevé\releve{REL-PAT.D09} l'atteste",
        r"la chaîne compte \chiffre{modeles-total} modèles",
        r"\vspace{12mm}",
        r"% le tableau portait 0,9995 avant correction",
    ],
)
def test_le_motif_laisse_passer_ce_qui_n_est_pas_une_grandeur(source: str) -> None:
    """Témoin négatif — sans lui, le contrôle rougirait partout et ne prouverait rien."""
    assert not nombres_tapes(source), f"forme légitime prise pour un nombre tapé : {source}"
