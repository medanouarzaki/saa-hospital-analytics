"""Interdit toute trace de vocabulaire d'outil génératif et toute numérotation
interne d'étape dans les fichiers suivis.

Deux contrôles. Le premier porte sur un motif volontairement limité à trois
catégories de vocabulaire GÉNÉRIQUE et PUBLIC : noms de fournisseurs d'outils
génératifs, formules de co-signature automatique, formules d'attribution de
génération. Le second porte sur la numérotation interne d'étape de ce projet :
le mot désignant un bloc ou un lot de travail suivi d'un nombre, le mot
désignant une étape suivi d'un nombre (avec ou sans le préfixe bloc/lot), et
un identifiant de sous-étape combinant un chiffre et une lettre. Aucun de ces
motifs n'énumère un terme de la nomenclature interne autre que sa forme : un
test qui énumérerait ce vocabulaire interne serait lui-même la fuite qu'il
prétend empêcher. La détection de ce vocabulaire interne reste une revue
manuelle, plus large, exécutée avant chaque publication — ce test-ci est un
filet permanent, pas un remplacement.

Le motif d'étape seule (sans préfixe bloc/lot) a été élargi après qu'une revue
manuelle, pas ce filet, a trouvé trois notes de configuration référençant une
étape numérotée sans ce préfixe : le filet ne couvrait alors que la forme
préfixée. Quatre catégories d'emploi légitime du mot « étape » ou « passe »
existent dans le dépôt et doivent rester vertes après cet élargissement : la
clé `steps` du workflow CI (vocabulaire de la plateforme, ne contient pas le
mot « étape », hors motif par construction), une procédure réglementaire de
sortie citée dans la documentation (« étapes » n'y est jamais suivi d'un
chiffre, hors motif par construction), les commentaires décrivant un
algorithme à deux passes dans `generator/parcours.py` et son test (le mot
« passe », pas « étape », hors motif par construction), et ce fichier
lui-même (exclusion déclarée ci-dessous, seule catégorie qui ne doit sa
sécurité qu'à une exclusion explicite plutôt qu'à la forme du motif).

Ce fichier est nécessairement exclu de son propre parcours : il contient les
motifs recherchés en tant que données, pas en tant que trace. C'est
l'exclusion déclarée mentionnée ci-dessus.
"""

import re
import subprocess
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
CE_FICHIER = Path(__file__).resolve().relative_to(RACINE).as_posix()

# Les cinq formes sous lesquelles la numérotation interne de travail se présente. Chacune a son
# témoin positif ci-dessous, et le motif d'ensemble a ses témoins négatifs : un filet éprouvé sur
# une seule forme est un filet qui n'a jamais été éprouvé.
#
# `\s+` et non un espace littéral, et la recherche porte sur le FICHIER ENTIER et non ligne à
# ligne : une référence coupée par un retour à la ligne — « touchées par ce \n lot » — échappait
# aux deux à la fois. Six occurrences étaient dans ce cas.
MOTIFS_NUMEROTATION = {
    # le mot de travail suivi d'un nombre
    "unité de travail numérotée": re.compile(r"\b(bloc|lot)\W{0,3}[0-9]", re.IGNORECASE),
    # le mot de travail qualifié, sans nombre
    "unité de travail nommée": re.compile(
        r"\b(lot|bloc)\s+de\s+"
        r"(correction|vraisemblance|consolidation|travail|publication|rapport|mesure)\b",
        re.IGNORECASE,
    ),
    # Le mot de travail désigné par un déterminant. **Le mot « lot » seul, jamais « bloc ».**
    # Mesuré : « bloc » précédé d'un déterminant a quarante emplois dans ce dépôt — bloc
    # opératoire, bloc de code, bloc SQL — tous légitimes, et aucun emploi de travail sans
    # nombre ; le prendre ici ferait effacer quarante références vraies. Comme unité de
    # travail, « bloc » n'apparaît que suivi d'un nombre, ce que la première forme couvre déjà.
    #
    # L'exclusion porte sur les emplois métier du mot « lot » : un lot de factures, un lot de
    # données, un lot de lignes.
    "unité de travail désignée": re.compile(
        r"\b(ce|cet|cette|le|la|du|de\s+la|au|un|une)\s+lots?\b"
        r"(?!\s+de\s+(factures?|donn[ée]es?|lignes?))",
        re.IGNORECASE,
    ),
    # l'étape numérotée, sous ses deux graphies
    "étape numérotée": re.compile(r"\b[ée]tape[s]?\W{0,3}[0-9]", re.IGNORECASE),
    # le renvoi décimal interne : « relevé au 1.2 », « mesure du 1.3 »
    "renvoi décimal interne": re.compile(
        r"\b(relev[ée]|mesur[ée]?|vu|point)\s+(au|du|[aà])\s+[0-9]+\.[0-9]", re.IGNORECASE
    ),
    # la sous-étape combinant un chiffre et une lettre
    "sous-étape chiffre-lettre": re.compile(r"\b[0-9]+\.[A-Za-z]\b"),
}

# Les témoins du motif, portés PAR LE CONTRÔLE et non par un rapport : sans eux, la vérification
# disparaîtrait avec le travail qui l'a faite. Une forme par témoin positif, une catégorie de faux
# positif plausible par témoin négatif.
TEMOINS_POSITIFS = {
    "unité de travail numérotée": "Corrige au lot 12, et repris au bloc 3.",
    "unité de travail nommée": (
        "Ajoute au lot de correction : avant, la colonne valait une constante."
    ),
    "unité de travail désignée": "Ce lot ajoute la colonne ; le bloc suivant la supprimera.",
    "étape numérotée": "Ecart documente a l'etape 3, et vu a l'Etape 5.",
    "renvoi décimal interne": "Colonne a valeur unique (releve au 1.2), mesure du 1.3.",
    "sous-étape chiffre-lettre": "Voir le point 6.a du releve.",
}

# Ce que le filet ne doit PAS voir. Un filet qui effacerait une référence légitime serait pire
# qu'un filet aveugle : il produirait des erreurs au lieu d'en laisser passer.
TEMOINS_NEGATIFS = {
    "numéro de version": "DuckDB est installé en version 1.5.5, et dbt en 1.12.0.",
    "article de règlement": (
        "L'article 27 du règlement intérieur prescrit un département de chirurgie."
    ),
    "référence de source": "Le tableau 76 page 102 de `S-30` donne la capacité litière.",
    "enregistrement de décision": "La règle vient de l'ADR `0020`, précisée par `0050`.",
    "chapitre du rapport": "Un constat à retenir pour le chapitre 9, et un autre au chapitre 1.",
    "emploi métier du mot": (
        "Le bloc operatoire n'existe pas ; un lot de factures part chaque mois."
    ),
    "bloc de code": "Le bloc SQL ci-dessous est repris du bloc precedent, sans le bloc CTE.",
}

MOTIFS_INTERDITS = [
    # Noms de fournisseurs d'outils génératifs
    "claude",
    "anthropic",
    "chatgpt",
    "openai",
    "gpt-3",
    "gpt-4",
    "gpt-5",
    "copilot",
    "gemini",
    "bard",
    "llama",
    "mistral ai",
    # Formules de co-signature automatique
    "co-authored-by",
    # Formules d'attribution de génération
    "generated by ai",
    "ai-generated",
    "ai generated",
    "ai-assisted",
    "ai assisted",
    "written by ai",
    "created with ai",
]


def fichiers_suivis() -> list[str]:
    sortie = subprocess.run(
        ["git", "-C", str(RACINE), "ls-files", "-z"],
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    return [chemin for chemin in sortie.split("\0") if chemin]


def test_aucune_trace_processus_generatif() -> None:
    fautifs = []
    for chemin in fichiers_suivis():
        if chemin == CE_FICHIER:
            continue
        chemin_absolu = RACINE / chemin
        if not chemin_absolu.is_file():
            continue
        try:
            contenu = chemin_absolu.read_text(encoding="utf-8").lower()
        except (UnicodeDecodeError, OSError):
            continue
        for motif in MOTIFS_INTERDITS:
            if motif in contenu:
                fautifs.append(f"{chemin} : motif '{motif}'")

    assert not fautifs, "Trace de vocabulaire d'outil génératif : " + " | ".join(fautifs)


def test_le_motif_reconnait_chaque_forme() -> None:
    """Chaque forme que le filet doit voir a son témoin positif, et il le reconnaît.

    C'est la moitié de l'épreuve, et c'est celle qui manquait : le filet ne cherchait qu'une forme
    sur cinq et a été cru sur son silence.
    """
    muets = [
        forme
        for forme, temoin in TEMOINS_POSITIFS.items()
        if not MOTIFS_NUMEROTATION[forme].search(temoin)
    ]
    assert not muets, "formes que le motif ne reconnaît plus : " + ", ".join(muets)


def test_le_motif_ne_reconnait_aucune_reference_legitime() -> None:
    """Aucune référence légitime n'est prise pour une numérotation de travail.

    L'autre moitié de l'épreuve. Un numéro de version, un article de règlement, une référence de
    source, un identifiant d'enregistrement de décision, un renvoi de chapitre et l'emploi métier
    du mot doivent tous passer : un filet qui les attraperait ferait effacer des références vraies.
    """
    faux_positifs = [
        f"{categorie} : '{motif.search(temoin).group(0)}' dans « {temoin} »"
        for categorie, temoin in TEMOINS_NEGATIFS.items()
        for motif in MOTIFS_NUMEROTATION.values()
        if motif.search(temoin)
    ]
    assert not faux_positifs, "le motif est trop large : " + " | ".join(faux_positifs)


def test_aucune_numerotation_interne() -> None:
    """Aucun fichier suivi ne porte de numérotation interne de travail, sous aucune des formes.

    La recherche porte sur le contenu ENTIER de chaque fichier, et non ligne à ligne : une
    référence coupée par un retour à la ligne échapperait autrement. Le numéro de ligne est
    reconstitué depuis la position de la correspondance, pour que le message reste actionnable.
    """
    fautifs = []
    for chemin in fichiers_suivis():
        # exclusion declaree : ce fichier porte les motifs ci-dessus comme donnees de test,
        # jamais comme trace reelle (voir le docstring du module).
        if chemin == CE_FICHIER:
            continue
        chemin_absolu = RACINE / chemin
        if not chemin_absolu.is_file():
            continue
        try:
            contenu = chemin_absolu.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for forme, motif in MOTIFS_NUMEROTATION.items():
            for correspondance in motif.finditer(contenu):
                numero_ligne = contenu[: correspondance.start()].count("\n") + 1
                trouve = " ".join(correspondance.group(0).split())
                fautifs.append(f"{chemin}:{numero_ligne} [{forme}] : '{trouve}'")

    assert not fautifs, "Numérotation interne de travail : " + " | ".join(fautifs)
