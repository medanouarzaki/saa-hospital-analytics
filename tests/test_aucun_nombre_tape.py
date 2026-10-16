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
from collections import Counter
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
    "url",
    "href",
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


# ------------------------------------------------------------------------------------------
# LES NOMBRES ÉCRITS EN LETTRES. Le motif ci-dessus ne voit que les chiffres : « cinq appareils »
# et « les huit activités » ont vieilli sans bruit. Un nombre écrit en lettres à partir de
# « trois » peut être une donnée — un décompte du dépôt, des données générées ou d'une mesure du
# projet — et une donnée passe par le registre. « Un » et « deux » relèvent de la langue courante
# plus que de la mesure, et ne sont pas examinés.
#
# Ce qui reste en lettres est déclaré ici, occurrence par occurrence, avec sa classe :
#   ÉNUMÉRATION  les éléments comptés sont nommés un à un dans la phrase, la suivante, ou le
#                tableau, la figure ou la liste qu'elle introduit ;
#   SOURCE       le nombre est repris d'une source citée dans la phrase, tel qu'elle le donne ;
#   STRUCTURE    structure du document ou d'une méthode fixe ;
#   LOCUTION     locution figée, ou rapport arithmétique sans donnée ;
#   PERSONNEL    passage d'écriture personnelle, gardé dans la forme de l'auteur.
# La liste casse dans les deux sens : une occurrence non déclarée rougit, une déclaration qui ne
# correspond plus à rien rougit aussi. L'abstract anglais est hors du périmètre des lettres.
# ------------------------------------------------------------------------------------------

_UNITES_EN_LETTRES = (
    r"trois|quatre|cinq|six|sept|huit|neuf|dix|onze|douze|treize|quatorze|quinze|seize|"
    r"vingts?|trente|quarante|cinquante|soixante|cents?|mille"
)
_NOMBRE_EN_LETTRES = re.compile(
    rf"(?<![\wÀ-ÿ-])(?:(?:deux|un|une)-(?:et-)?)?(?:{_UNITES_EN_LETTRES})"
    rf"(?:-(?:et-)?(?:{_UNITES_EN_LETTRES}|deux|un|une))*(?![\wÀ-ÿ-])",
    re.I,
)
_TEXTE_ANGLAIS = re.compile(r"\\begin\{otherlanguage\}\{english\}.*?\\end\{otherlanguage\}", re.S)

CLASSES_EN_LETTRES = ("ÉNUMÉRATION", "SOURCE", "STRUCTURE", "LOCUTION", "PERSONNEL")

EXEMPTIONS_LETTRES = (
    (
        "analyse-de-l-activite.tex",
        "Les délais y sont en jours. Les trois premières colonnes portent l'ensemble, les trois dernières le",  # noqa: E501
        "STRUCTURE",
        "« trois » : colonnes du tableau qui précède",
    ),
    (
        "analyse-de-l-activite.tex",
        "Les délais y sont en jours. Les trois premières colonnes portent l'ensemble, les trois dernières le",  # noqa: E501
        "STRUCTURE",
        "« trois » : colonnes du tableau qui précède",
    ),
    (
        "analyse-de-l-activite.tex",
        "en quatre états : honorés,",  # noqa: E501
        "ÉNUMÉRATION",
        "« quatre » : honorés, absences, annulations, encore ouverts, dans la phrase",
    ),
    (
        "analyse-de-l-activite.tex",
        "mesurer.} Les trois mesures portent sur rendez-vous à issue",  # noqa: E501
        "STRUCTURE",
        "« trois » : les trois formes de mesure de la méthode",
    ),
    (
        "analyse-de-l-activite.tex",
        "\\textbf{Sur le complément, les trois mesures se rapprochent de la relation",  # noqa: E501
        "STRUCTURE",
        "« trois » : les trois formes de mesure de la méthode",
    ),
    (
        "analyse-de-l-activite.tex",
        "trois groupes de gravité , et les données en portent .",  # noqa: E501
        "SOURCE",
        "« trois » : \\cite{s12} dans la phrase",
    ),
    (
        "analyse-de-l-activite.tex",
        "~\\%. Le règlement intérieur nomme les cinq issues du",  # noqa: E501
        "SOURCE",
        "« cinq » : \\cite{s27} dans la phrase",
    ),
    (
        "architecture-de-la-chaine.tex",
        "La chaîne va d'un dépôt de fichiers à un tableau de bord en cinq étapes (voir",  # noqa: E501
        "ÉNUMÉRATION",
        "« cinq » : étapes nommées dans la figure que la phrase introduit",
    ),
    (
        "architecture-de-la-chaine.tex",
        "Le serveur relationnel a été retenu pour trois propriétés que la chaîne utilise vraiment. Plusieurs",  # noqa: E501
        "ÉNUMÉRATION",
        "« trois » : les trois propriétés nommées dans les phrases qui suivent",
    ),
    (
        "architecture-de-la-chaine.tex",
        "mois s'échangeraient sans bruit onze fois sur douze. Les mesures faites sur la base avant d'écrire",  # noqa: E501
        "LOCUTION",
        "« onze » : rapport arithmétique jours sur mois",
    ),
    (
        "architecture-de-la-chaine.tex",
        "mois s'échangeraient sans bruit onze fois sur douze. Les mesures faites sur la base avant d'écrire",  # noqa: E501
        "LOCUTION",
        "« douze » : rapport arithmétique jours sur mois",
    ),
    (
        "architecture-de-la-chaine.tex",
        "les conversions ont aussi montré trois faits : la valeur manquante est toujours la chaîne vide et",  # noqa: E501
        "ÉNUMÉRATION",
        "« trois » : les trois faits nommés après les deux-points",
    ),
    (
        "architecture-de-la-chaine.tex",
        "de service. Un lecteur ne devrait jamais voir un instantané à moitié neuf, mais aucun contrôle du",  # noqa: E501
        "LOCUTION",
        "« neuf » : « neuf » adjectif (nouveau)",
    ),
    (
        "cadrage-et-methodologie.tex",
        "Le document lui-même ne figure pas au dépôt, mais trois de ses exigences y sont consignées. Tout",  # noqa: E501
        "ÉNUMÉRATION",
        "« trois » : les trois exigences énoncées dans les phrases qui suivent",
    ),
    (
        "cadrage-et-methodologie.tex",
        "Le projet se découpe en sept phases, nommées par ce qu'elles font",  # noqa: E501
        "ÉNUMÉRATION",
        "« sept » : les sept phases nommées au tableau que la phrase introduit",
    ),
    (
        "cadrage-et-methodologie.tex",
        "aux défauts connus, en sept phases de l'observation au poste jusqu'à la rédaction. Le",  # noqa: E501
        "STRUCTURE",
        "« sept » : les phases du projet, méthode fixe",
    ),
    (
        "conception-du-jeu-de-donnees.tex",
        "rattachent des épisodes de soin de trois familles : consultation externe, passage aux urgences et",  # noqa: E501
        "ÉNUMÉRATION",
        "« trois » : consultation externe, passage aux urgences, séjour, dans la phrase",
    ),
    (
        "conception-du-jeu-de-donnees.tex",
        "Les trois niveaux de l'identité donnent trois décomptes différents. La couche produite porte",  # noqa: E501
        "ÉNUMÉRATION",
        "« trois » : les trois décomptes donnés dans la phrase qui suit",
    ),
    (
        "conception-du-jeu-de-donnees.tex",
        "Les trois niveaux de l'identité donnent trois décomptes différents. La couche produite porte",  # noqa: E501
        "STRUCTURE",
        "« trois » : les trois niveaux du modèle de l'identité",
    ),
    (
        "conception-du-jeu-de-donnees.tex",
        "Ces défauts forment trois classes, selon ce qui les révèle. Une date au format invalide se voit sur",  # noqa: E501
        "ÉNUMÉRATION",
        "« trois » : les trois classes décrites dans les phrases qui suivent",
    ),
    (
        "conception-du-jeu-de-donnees.tex",
        "Une quatrième forme échappe aux trois : un champ renseigné et faux. Au poste, le numéro de",  # noqa: E501
        "STRUCTURE",
        "« trois » : renvoi aux trois classes de la méthode",
    ),
    (
        "conclusion.tex",
        "plusieurs centaines de milliers, réparties sur onze tables et deux ans et demi, avec leurs saisons,",  # noqa: E501
        "PERSONNEL",
        "« onze » : sous-section « Le volet professionnel »",
    ),
    (
        "conclusion.tex",
        "Le passage à des données réelles changerait la nature de trois choses. La vérité terrain",  # noqa: E501
        "ÉNUMÉRATION",
        "« trois » : les trois choses nommées dans les phrases qui suivent",
    ),
    (
        "conclusion.tex",
        "Trois conditions matérielles s'y ajouteraient. Une convention d'accès aux données serait nécessaire,",  # noqa: E501
        "ÉNUMÉRATION",
        "« Trois » : les trois conditions nommées dans les phrases qui suivent",
    ),
    (
        "introduction.tex",
        "établit un rapport annuel. Ces trois périodicités reposent sur une seule source, les données que",  # noqa: E501
        "ÉNUMÉRATION",
        "« trois » : mois, trimestre, année, nommés dans les deux phrases qui précèdent",
    ),
    (
        "introduction.tex",
        "un tableau de bord. Elle se construit en quatre temps.",  # noqa: E501
        "STRUCTURE",
        "« quatre » : les quatre temps de l'introduction",
    ),
    (
        "organisme-d-accueil.tex",
        "Il dépend du centre hospitalier préfectoral Mohammed~V, dont il est l'une des cinq structures",  # noqa: E501
        "SOURCE",
        "« cinq » : \\cite{s20, s29} dans la phrase",
    ),
    (
        "organisme-d-accueil.tex",
        "\\fbox{\\begin{minipage}{ }\\centering Centre hospitalier préfectoral Mohammed~V \\\\ \\footnotesize cinq structures\\end{minipage}}\\\\",  # noqa: E501
        "SOURCE",
        "« cinq » : nœud de la figure dont la légende cite s29",
    ),
    (
        "organisme-d-accueil.tex",
        "L' fixe les neuf missions du service , que le tableau~",  # noqa: E501
        "SOURCE",
        "« neuf » : \\cite{s27} dans la phrase",
    ),
    (
        "organisme-d-accueil.tex",
        "{@{}l@{}}{Les neuf activités dont le service d'accueil et d'admission est chargé} \\\\",  # noqa: E501
        "ÉNUMÉRATION",
        "« neuf » : les neuf activités numérotées dans le tableau",
    ),
    (
        "organisme-d-accueil.tex",
        "orientation de sortie ou une sortie d'hospitalisation aboutissent toutes trois à une facture. Une",  # noqa: E501
        "ÉNUMÉRATION",
        "« trois » : consultation, orientation de sortie, sortie d'hospitalisation, dans la phrase",
    ),
    (
        "organisme-d-accueil.tex",
        "du système d'information propose cinq profils applicatifs, et chacun ouvre un jeu de modules",  # noqa: E501
        "PERSONNEL",
        "« cinq » : passage d'écriture personnelle sur les profils du service, forme de l'auteur",
    ),
    (
        "organisme-d-accueil.tex",
        "distinct . Les profils ne sont donc pas cinq vues d'un même écran : ils",  # noqa: E501
        "PERSONNEL",
        "« cinq » : passage d'écriture personnelle sur les profils du service, forme de l'auteur",
    ),
    (
        "organisme-d-accueil.tex",
        "découpent l'activité du service en cinq processus.",  # noqa: E501
        "PERSONNEL",
        "« cinq » : passage d'écriture personnelle sur les profils du service, forme de l'auteur",
    ),
    (
        "organisme-d-accueil.tex",
        "L'observation conduite pour ce travail a porté sur un poste et sur un seul de ces cinq profils,",  # noqa: E501
        "PERSONNEL",
        "« cinq » : passage d'écriture personnelle sur les profils du service, forme de l'auteur",
    ),
    (
        "organisme-d-accueil.tex",
        "celui des rendez-vous : les quatre autres exigent des habilitations qu'un stagiaire ne reçoit",  # noqa: E501
        "PERSONNEL",
        "« quatre » : passage d'écriture personnelle sur les profils du service, forme de l'auteur",
    ),
    (
        "qualite-et-rapprochement.tex",
        "Parmi elles, sont renseignées à moins de cent pour cent, et",  # noqa: E501
        "LOCUTION",
        "« cent » : locution « cent pour cent »",
    ),
    (
        "qualite-et-rapprochement.tex",
        "Parmi elles, sont renseignées à moins de cent pour cent, et",  # noqa: E501
        "LOCUTION",
        "« cent » : locution « cent pour cent »",
    ),
    (
        "qualite-et-rapprochement.tex",
        "moyenne harmonique des deux, vaut . Les trois sont",  # noqa: E501
        "STRUCTURE",
        "« trois » : les trois mesures de l'évaluation, méthode fixe",
    ),
    (
        "recommandations.tex",
        "Cinq recommandations découlent des constats du travail. La question traitée est ce que le service",  # noqa: E501
        "STRUCTURE",
        "« Cinq » : structure du chapitre des recommandations",
    ),
    (
        "recommandations.tex",
        "Cinq recommandations portent sur les rendez-vous, les urgences, le recouvrement, le fichier patient",  # noqa: E501
        "STRUCTURE",
        "« Cinq » : structure du chapitre des recommandations",
    ),
    (
        "systeme-d-information-hospitalier.tex",
        "dans plus de trente hôpitaux répartis sur six pays .",  # noqa: E501
        "SOURCE",
        "« trente » : \\cite{s07} dans la phrase",
    ),
    (
        "systeme-d-information-hospitalier.tex",
        "dans plus de trente hôpitaux répartis sur six pays .",  # noqa: E501
        "SOURCE",
        "« six » : \\cite{s07} dans la phrase",
    ),
    (
        "systeme-d-information-hospitalier.tex",
        "Vingt-six modules se regroupent en trois paquets, Core, Clinic et Extension Packs . Le",  # noqa: E501
        "SOURCE",
        "« Vingt-six » : \\cite{s06} dans la phrase",
    ),
    (
        "systeme-d-information-hospitalier.tex",
        "Vingt-six modules se regroupent en trois paquets, Core, Clinic et Extension Packs . Le",  # noqa: E501
        "SOURCE",
        "« trois » : \\cite{s06} dans la phrase",
    ),
    (
        "systeme-d-information-hospitalier.tex",
        ". Quatre écrans ont été parcourus : l'écran de démarrage, la recherche d'identifiant",  # noqa: E501
        "ÉNUMÉRATION",
        "« Quatre » : les quatre écrans nommés après les deux-points",
    ),
    (
        "systeme-d-information-hospitalier.tex",
        "quatre couples d'auteur et d'horodatage, pour la création, la modification, la confirmation et",  # noqa: E501
        "ÉNUMÉRATION",
        "« quatre » : création, modification, confirmation, annulation, dans la phrase",
    ),
    (
        "systeme-d-information-hospitalier.tex",
        "depuis ce format. Une conversion absente ou fausse échangerait un jour et un mois onze fois sur",  # noqa: E501
        "LOCUTION",
        "« onze » : rapport arithmétique jours sur mois",
    ),
    (
        "systeme-d-information-hospitalier.tex",
        "douze sans qu'aucune valeur ne devienne invalide. Le chapitre~ reprend cette",  # noqa: E501
        "LOCUTION",
        "« douze » : rapport arithmétique jours sur mois",
    ),
    (
        "tableau-de-bord.tex",
        "Trois pages lui suffisent pour y répondre.",  # noqa: E501
        "ÉNUMÉRATION",
        "« Trois » : les trois pages du scénario, nommées dans les paragraphes qui suivent",
    ),
    (
        "tableau-de-bord.tex",
        "implémentation écrite séparément dans un autre langage. Les quatre valeurs affichées valent",  # noqa: E501
        "ÉNUMÉRATION",
        "« quatre » : occupation, durée moyenne, rotation, intervalle, dans la phrase",
    ),
    (
        "complements_techniques.tex",
        "\\fbox{\\begin{minipage}{ }\\centering \\textbf{Les six faits} \\\\",  # noqa: E501
        "ÉNUMÉRATION",
        "« six » : les six faits nommés dans la figure",
    ),
    (
        "complements_techniques.tex",
        "Trois contrôles vérifient ces versions à chaque construction. La fin d'une version non courante",  # noqa: E501
        "ÉNUMÉRATION",
        "« Trois » : les trois contrôles décrits dans la phrase qui suit",
    ),
)


def nombres_en_lettres(source: str) -> list[tuple[str, str]]:
    """(ligne dépouillée, nombre) pour chaque nombre écrit en lettres de la prose française."""
    depouille = depouiller(_TEXTE_ANGLAIS.sub(" ", source))
    trouves = []
    for ligne in depouille.splitlines():
        cle = " ".join(ligne.split())
        trouves.extend((cle, m.group(0)) for m in _NOMBRE_EN_LETTRES.finditer(cle))
    return trouves


def occurrences_en_lettres() -> Counter:
    compte: Counter = Counter()
    for chemin in fichiers_examines():
        for cle, _ in nombres_en_lettres(chemin.read_text(encoding="utf-8")):
            compte[(chemin.name, cle)] += 1
    return compte


def declarations_en_lettres() -> Counter:
    return Counter((fichier, ligne) for fichier, ligne, _, _ in EXEMPTIONS_LETTRES)


def test_tout_nombre_en_lettres_passe_par_le_registre_ou_est_declare() -> None:
    """Une occurrence non déclarée est une donnée écrite en clair : elle passe par \\chiffre."""
    trouvees, declarees = occurrences_en_lettres(), declarations_en_lettres()
    assert trouvees, "aucun nombre en lettres trouvé : le motif ne lit plus rien"
    manquantes = [
        f"{f} : {ligne[:110]} ({n - declarees[(f, ligne)]} non déclaré(s))"
        for (f, ligne), n in sorted(trouvees.items())
        if n > declarees[(f, ligne)]
    ]
    assert not manquantes, (
        f"{len(manquantes)} ligne(s) portent un nombre en lettres ni passé par le registre ni "
        "déclaré :\n  " + "\n  ".join(manquantes)
    )


def test_toute_exemption_en_lettres_correspond_a_une_occurrence() -> None:
    """L'autre sens : une exemption qui ne correspond plus à rien est une dette qui ment."""
    trouvees, declarees = occurrences_en_lettres(), declarations_en_lettres()
    perimees = [
        f"{f} : {ligne[:80]}"
        for (f, ligne), n in sorted(declarees.items())
        if n > trouvees[(f, ligne)]
    ]
    assert not perimees, (
        f"{len(perimees)} exemption(s) sans occurrence — retirez-les de EXEMPTIONS_LETTRES :\n  "
        + "\n  ".join(perimees)
    )


def test_chaque_exemption_porte_une_classe_et_un_motif() -> None:
    fautes = [
        f"{f} : {ligne[:60]} ({classe})"
        for f, ligne, classe, motif in EXEMPTIONS_LETTRES
        if classe not in CLASSES_EN_LETTRES or len(motif.strip()) < 15
    ]
    assert not fautes, "exemptions sans classe connue ou sans motif :\n  " + "\n  ".join(fautes)


@pytest.mark.parametrize(
    ("source", "attendus"),
    [
        (r"les huit activités", ["huit"]),
        (r"Vingt-deux tables et quatre-vingts fois plus", ["Vingt-deux", "quatre-vingts"]),
        (r"Trois questions en découlent", ["Trois"]),
        (r"onze fois sur douze", ["onze", "douze"]),
    ],
)
def test_le_motif_voit_un_nombre_en_lettres(source: str, attendus: list[str]) -> None:
    """Témoin positif, trait d'union et majuscule compris."""
    assert [mot for _, mot in nombres_en_lettres(source)] == attendus


@pytest.mark.parametrize(
    "source",
    [
        r"deux tables et un seul poste",
        r"la sixième, la troisième et la centième",
        r"les centres et les milliers de lignes, en septembre",
        r"il y a \chiffre{trois-tables} tables",
        "\\begin{otherlanguage}{english}\nthree tables, huit\n\\end{otherlanguage}",
        r"% les huit activités, en commentaire",
    ],
)
def test_le_motif_laisse_passer_ce_qui_n_est_pas_un_nombre_en_lettres(source: str) -> None:
    """Témoin négatif : ordinal, mot plus long, argument de commande, anglais, commentaire."""
    assert not nombres_en_lettres(source), f"forme prise pour un nombre en lettres : {source}"
