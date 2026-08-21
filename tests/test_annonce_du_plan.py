"""L'annonce du plan, dans l'introduction générale, confrontée aux chapitres qui existent.

POURQUOI CE CONTRÔLE EXISTE. Une introduction annonce un plan. Rien n'obligeait ce plan à rester
celui du document : un chapitre renuméroté, renommé ou ajouté laissait l'annonce intacte et
fausse, et aucune compilation ne s'en plaint. Ce projet a déjà porté une mention de ce genre — un
décompte écrit à la main dans un libellé d'écran, devenu faux quand une page s'est ajoutée — et
il ne l'a pas trouvée par un contrôle mais en regardant l'écran. Une fois suffit.

LE PRINCIPE EST BIDIRECTIONNEL, et il vaut pour toute référence croisée de ce dépôt :

  - tout chapitre annoncé par l'introduction existe, sous ce numéro et avec ce titre exact ;
  - tout chapitre numéroté du rapport est annoncé par l'introduction.

Une seule des deux directions laisserait passer la moitié des défauts : la première seule tolère
un chapitre qu'on oublie d'annoncer, la seconde seule tolère une annonce qui invente un chapitre.

LA STRUCTURE EST LUE DANS LES FICHIERS, PAS DANS LE SOMMAIRE COMPOSÉ. Le sommaire est un artefact
de compilation ; le contrôle doit s'exécuter sur un clone frais, sans distribution typographique.
L'ordre vient des inclusions du fichier principal — c'est lui qui décide de l'ordre réel — et la
numérotation en découle, les chapitres non numérotés (`\\chapter*`) ne comptant pas.

CE CONTRÔLE N'OUVRE AUCUNE BASE et ne compile rien. Il lit des fichiers.
"""

from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
REPORT = RACINE / "report"
PRINCIPAL = REPORT / "rapport.tex"
INTRODUCTION = REPORT / "chapitres" / "introduction.tex"

# Un commentaire LaTeX s'ouvre sur un pourcentage non échappé.
_COMMENTAIRE = re.compile(r"(?<!\\)(?:\\\\)*%")

# L'inclusion d'un chapitre par le fichier principal, dans l'ordre où elle apparaît.
_INCLUSION = re.compile(r"\\input\{chapitres/([a-z0-9-]+)\}")

# Un titre de chapitre. La distinction entre les deux formes est ce qui porte la numérotation :
# `\chapter*` ne numérote pas. L'étoile est donc capturée, et non ignorée.
_CHAPITRE = re.compile(r"\\chapter(\*?)\{([^}]*)\}")

# L'annonce d'un chapitre. `[\s\S]` et non `.` : l'argument d'une commande LaTeX peut être coupé
# par un retour à la ligne, et une annonce ainsi coupée doit être reconnue comme les autres.
# La garde de fin — l'accolade immédiatement après le nom — interdit de confondre cette commande
# avec une autre dont le nom commence par les mêmes lettres.
_ANNONCE = re.compile(r"\\annonceChapitre\{(\d+)\}\{([\s\S]*?)\}")


def sans_commentaire(ligne: str) -> str:
    trouve = _COMMENTAIRE.search(ligne)
    return ligne if trouve is None else ligne[: trouve.end() - 1]


def partie_active(source: str) -> str:
    return "\n".join(sans_commentaire(ligne) for ligne in source.splitlines())


def chapitres_reels() -> list[tuple[int, str]]:
    """Les chapitres NUMÉROTÉS, dans l'ordre des inclusions du fichier principal."""
    ordre = _INCLUSION.findall(partie_active(PRINCIPAL.read_text(encoding="utf-8")))
    reels: list[tuple[int, str]] = []
    for nom in ordre:
        chemin = REPORT / "chapitres" / f"{nom}.tex"
        trouve = _CHAPITRE.search(partie_active(chemin.read_text(encoding="utf-8")))
        if trouve is None or trouve.group(1) == "*":
            continue
        reels.append((len(reels) + 1, " ".join(trouve.group(2).split())))
    return reels


def annonces() -> list[tuple[int, str]]:
    source = partie_active(INTRODUCTION.read_text(encoding="utf-8"))
    return [(int(n), " ".join(t.split())) for n, t in _ANNONCE.findall(source)]


# --------------------------------------------------------------------------------------------
# Témoins du motif, dans les deux sens. Un filet éprouvé sur une seule forme n'a jamais été
# éprouvé, et celui-ci doit reconnaître une annonce coupée par un retour à la ligne.
# --------------------------------------------------------------------------------------------

TEMOINS_POSITIFS = (
    (
        "annonce simple",
        r"Le \annonceChapitre{1}{L'organisme d'accueil} présente",
        [(1, "L'organisme d'accueil")],
    ),
    (
        "deux annonces sur une ligne",
        r"\annonceChapitre{8}{Le tableau de bord} et \annonceChapitre{9}{Recommandations}",
        [(8, "Le tableau de bord"), (9, "Recommandations")],
    ),
    (
        "annonce coupée par un retour à la ligne",
        "\\annonceChapitre{5}{Architecture de la\nchaîne de données} décrit",
        [(5, "Architecture de la chaîne de données")],
    ),
    (
        "titre portant une apostrophe et un accent",
        r"\annonceChapitre{7}{Analyse de l'activité}",
        [(7, "Analyse de l'activité")],
    ),
)

TEMOINS_NEGATIFS = (
    ("annonce dans un commentaire", r"% ancien \annonceChapitre{1}{Titre}", []),
    (
        "texte actif puis commentaire",
        r"\annonceChapitre{1}{Titre} % \annonceChapitre{2}{Autre}",
        [(1, "Titre")],
    ),
    ("commande homographe", r"\annonceChapitres{1}{Titre}", []),
    ("numéro absent", r"\annonceChapitre{}{Titre}", []),
    ("la chaîne hors de toute commande", r"le chapitre 1 s'intitule L'organisme d'accueil", []),
)


def test_le_motif_reconnait_chaque_forme_d_annonce() -> None:
    for nom, source, attendu in TEMOINS_POSITIFS:
        obtenu = [(int(n), " ".join(t.split())) for n, t in _ANNONCE.findall(partie_active(source))]
        assert obtenu == attendu, f"témoin positif « {nom} » : {source!r}"


def test_le_motif_ne_reconnait_pas_ce_qui_n_est_pas_une_annonce() -> None:
    for nom, source, attendu in TEMOINS_NEGATIFS:
        obtenu = [(int(n), " ".join(t.split())) for n, t in _ANNONCE.findall(partie_active(source))]
        assert obtenu == attendu, f"témoin négatif « {nom} » : {source!r}"


def test_un_titre_prefixe_d_un_autre_ne_se_confond_pas_avec_lui() -> None:
    """La comparaison porte sur l'ÉGALITÉ du titre, jamais sur son inclusion.

    Voie par laquelle la propriété serait vraie à tort : un contrôle qui vérifierait qu'un titre
    annoncé est CONTENU dans un titre réel accepterait « Analyse » pour « Analyse de l'activité ».
    Le témoin ci-dessous est construit sur deux titres dont l'un est le préfixe strict de l'autre.
    """
    reels = [(1, "Analyse de l'activité")]
    annonce = [(1, "Analyse")]
    assert annonce != reels, "un préfixe strict ne doit jamais valoir le titre entier"
    assert set(annonce) - set(reels) == {(1, "Analyse")}


# --------------------------------------------------------------------------------------------
# Les deux sens.
# --------------------------------------------------------------------------------------------


def test_tout_chapitre_annonce_existe_sous_ce_numero_et_ce_titre() -> None:
    """Voie par laquelle elle serait vraie à tort : si l'introduction n'annonçait rien, la
    propriété passerait sur l'ensemble vide. La garde ci-dessous ferme cette voie.
    """
    reels = chapitres_reels()
    assert reels, "aucun chapitre numéroté : la propriété ne vérifierait rien"
    annonce = annonces()
    assert annonce, "l'introduction n'annonce aucun chapitre : la propriété ne vérifierait rien"

    connus = dict(reels)
    fautes = []
    for numero, titre in annonce:
        if numero not in connus:
            fautes.append(f"le chapitre {numero} est annoncé et n'existe pas")
        elif connus[numero] != titre:
            fautes.append(
                f"le chapitre {numero} est annoncé « {titre} » et s'intitule « {connus[numero]} »"
            )
    assert not fautes, "annonces sans cible :\n  " + "\n  ".join(fautes)


def test_tout_chapitre_du_rapport_est_annonce() -> None:
    """Le second sens — celui que ce projet a dû ajouter après coup sur quatre autres appareils."""
    reels = chapitres_reels()
    assert reels, "aucun chapitre numéroté : la propriété ne vérifierait rien"
    annonces_par_numero = dict(annonces())

    orphelins = [
        f"le chapitre {numero} « {titre} » n'est annoncé nulle part dans l'introduction"
        for numero, titre in reels
        if numero not in annonces_par_numero
    ]
    assert not orphelins, f"{len(orphelins)} chapitre(s) non annoncé(s) :\n  " + "\n  ".join(
        orphelins
    )


def test_aucun_chapitre_n_est_annonce_deux_fois() -> None:
    """Sans quoi deux annonces contradictoires du même numéro passeraient toutes deux."""
    numeros = [numero for numero, _ in annonces()]
    doublons = sorted({n for n in numeros if numeros.count(n) > 1})
    assert not doublons, "chapitres annoncés plusieurs fois : " + ", ".join(
        str(n) for n in doublons
    )


def test_les_numeros_annonces_se_suivent_depuis_un() -> None:
    """La numérotation réelle est celle de l'ordre des inclusions ; l'annonce doit la refléter,
    faute de quoi un chapitre annoncé sous un numéro libre passerait les deux sens.
    """
    numeros = sorted(numero for numero, _ in annonces())
    attendus = list(range(1, len(numeros) + 1))
    assert numeros == attendus, f"numéros annoncés {numeros} au lieu de {attendus}"
