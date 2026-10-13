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


# --------------------------------------------------------------------------------------------
# Les parties. Le fichier principal les compose par `\part{titre}` ; l'introduction les annonce par
# `\annoncePartie{titre}`, sans numéro : le rang d'une partie est son ordre d'apparition. La
# correspondance vaut dans les deux sens — même nombre, même ordre, titre exact — et chaque chapitre
# annoncé l'est sous l'annonce de la partie qui le contient dans le fichier principal, avant
# l'annonce de la suivante.
# --------------------------------------------------------------------------------------------

_PARTIE = re.compile(r"\\part\{([^}]*)\}")
_ANNONCE_PARTIE = re.compile(r"\\annoncePartie\{([\s\S]*?)\}")
# Les deux marques du fichier principal qui structurent le document, dans leur ordre d'apparition.
_STRUCTURE = re.compile(r"\\part\{([^}]*)\}|\\input\{chapitres/([a-z0-9-]+)\}")
# Les deux annonces de l'introduction, dans leur ordre d'apparition.
_ANNONCES = re.compile(r"\\annoncePartie\{([\s\S]*?)\}|\\annonceChapitre\{(\d+)\}\{[\s\S]*?\}")


def parties_reelles(principal: str, est_numerote) -> list[tuple[str, list[int]]]:
    """Les parties du fichier principal, chacune avec les numéros des chapitres qu'elle contient.

    `est_numerote(nom)` dit si le fichier de chapitre porte un `\\chapter` numéroté ; la
    numérotation suit l'ordre des inclusions, comme `chapitres_reels`.
    """
    parties: list[tuple[str, list[int]]] = []
    numero = 0
    for titre, nom in _STRUCTURE.findall(partie_active(principal)):
        if titre:
            parties.append((" ".join(titre.split()), []))
        elif est_numerote(nom):
            numero += 1
            if parties:
                parties[-1][1].append(numero)
    return parties


def parties_annoncees(introduction: str) -> list[tuple[str, list[int]]]:
    annonces: list[tuple[str, list[int]]] = []
    for titre, numero in _ANNONCES.findall(partie_active(introduction)):
        if titre:
            annonces.append((" ".join(titre.split()), []))
        elif annonces:
            annonces[-1][1].append(int(numero))
        else:
            annonces.append(("", [int(numero)]))
    return annonces


def _numerote(nom: str) -> bool:
    trouve = _CHAPITRE.search(
        partie_active((REPORT / "chapitres" / f"{nom}.tex").read_text(encoding="utf-8"))
    )
    return trouve is not None and trouve.group(1) == ""


TEMOINS_PARTIES = (
    (
        "deux parties, chapitres rattachés",
        "\\part{Un}\n\\input{chapitres/a}\n\\part{Deux}\n\\input{chapitres/b}\n\\input{chapitres/c}",
        [("Un", [1]), ("Deux", [2, 3])],
    ),
    ("partie commentée", "% \\part{Un}\n\\part{Deux}\n\\input{chapitres/a}", [("Deux", [1])]),
    ("commande homographe", "\\partie{Un}\n\\part{Deux}\n\\input{chapitres/a}", [("Deux", [1])]),
)


def test_le_motif_lit_les_parties_et_leur_rattachement() -> None:
    for nom, source, attendu in TEMOINS_PARTIES:
        assert parties_reelles(source, lambda _nom: True) == attendu, f"témoin « {nom} »"


TEMOINS_ANNONCES_DE_PARTIE = (
    (
        "annonces dans l'ordre",
        "\\annoncePartie{Un} \\annonceChapitre{1}{A} \\annoncePartie{Deux} \\annonceChapitre{2}{B}",
        [("Un", [1]), ("Deux", [2])],
    ),
    (
        "titre coupé par un retour à la ligne",
        "\\annoncePartie{Analyse et\nconception} \\annonceChapitre{1}{A}",
        [("Analyse et conception", [1])],
    ),
    (
        "annonce de partie commentée",
        "% \\annoncePartie{Un}\n\\annoncePartie{Deux} \\annonceChapitre{1}{A}",
        [("Deux", [1])],
    ),
    ("chapitre annoncé avant toute partie", "\\annonceChapitre{1}{A}", [("", [1])]),
)


def test_le_motif_lit_les_annonces_de_partie() -> None:
    for nom, source, attendu in TEMOINS_ANNONCES_DE_PARTIE:
        assert parties_annoncees(source) == attendu, f"témoin « {nom} »"


def test_les_parties_annoncees_sont_celles_du_document() -> None:
    """Même nombre, même ordre, titre exact, et chaque chapitre annoncé sous sa partie.

    Voie par laquelle la propriété serait vraie à tort : un document sans partie et une introduction
    sans annonce de partie seraient égaux. La garde exige au moins une partie de chaque côté.
    """
    reelles = parties_reelles(PRINCIPAL.read_text(encoding="utf-8"), _numerote)
    annoncees = parties_annoncees(INTRODUCTION.read_text(encoding="utf-8"))
    assert reelles, (
        "le fichier principal ne compose aucune partie : la propriété ne vérifierait rien"
    )
    assert any(titre for titre, _ in annoncees), "l'introduction n'annonce aucune partie"
    assert [t for t, _ in annoncees] == [t for t, _ in reelles], (
        f"parties annoncées {[t for t, _ in annoncees]}, parties du document "
        f"{[t for t, _ in reelles]}"
    )
    assert annoncees == reelles, (
        f"rattachement des chapitres annoncé {annoncees}, rattachement du document {reelles}"
    )


# --------------------------------------------------------------------------------------------
# Les renvois tapés. Un numéro de chapitre, de section ou d'annexe écrit à la main devient faux au
# premier chapitre inséré ; un renvoi passe donc par une étiquette. La recherche porte sur la
# partie active des fichiers de prose — chapitres et liminaires —, lignes jointes, pour qu'un
# renvoi coupé par un retour à la ligne soit vu.
# --------------------------------------------------------------------------------------------

# Le mot est lu sans égard à la casse ; la lettre d'annexe, elle, est une capitale isolée — sans
# quoi « le chapitre s'ouvre » serait pris pour un renvoi à une annexe.
_RENVOI_TAPE = re.compile(
    r"(?<![\w\\])(?i:chapitres?|sections?|annexes?)(?:~|\s)+(?:\d+(?:\.\d+)*|[A-Z])(?![\w'’])"
    r"|§\s*~?\d"
)

TEMOINS_RENVOI_VUS = (
    "voir le chapitre 4 pour la suite",
    "au chapitre~4",
    "la section~5.7 le montre",
    "un renvoi (§4.6) collé",
    "l'annexe B porte le relevé",
    "le chapitre\n4 coupé",
)

TEMOINS_RENVOI_NON_VUS = (
    "le chapitre de cadrage",
    "ce chapitre propose",
    "en \\chiffre{chapitres-numerotes} chapitres et",
    "au chapitre~\\ref{chap:cadrage}",
    "(§\\ref{sec:sensibilite})",
    "% voir le chapitre 4",
    "\\annonceChapitre{4}{Titre}",
    "le chapitre s'ouvre",
    "ce chapitre n'est pas",
    "Section d'un tableau",
)


def renvois_tapes(source: str) -> list[str]:
    return _RENVOI_TAPE.findall(" ".join(partie_active(source).splitlines()))


def test_le_motif_voit_chaque_forme_de_renvoi_tape() -> None:
    for temoin in TEMOINS_RENVOI_VUS:
        assert renvois_tapes(temoin), f"témoin positif « {temoin} » : le renvoi passe"


def test_le_motif_ne_prend_aucune_forme_legitime_pour_un_renvoi_tape() -> None:
    for temoin in TEMOINS_RENVOI_NON_VUS:
        assert not renvois_tapes(temoin), f"témoin négatif « {temoin} » : le motif crie"


def test_aucun_renvoi_tape_dans_la_prose() -> None:
    fichiers = sorted((REPORT / "chapitres").glob("*.tex")) + sorted(
        (REPORT / "liminaires").glob("*.tex")
    )
    assert fichiers, "aucun fichier de prose : la propriété ne vérifierait rien"
    fautes = [
        f"{chemin.relative_to(RACINE)} : {renvoi!r}"
        for chemin in fichiers
        for renvoi in renvois_tapes(chemin.read_text(encoding="utf-8"))
    ]
    assert not fautes, "renvois tapés (à remplacer par \\ref) :\n  " + "\n  ".join(fautes)


# --------------------------------------------------------------------------------------------
# Les références des outils. Dans le chapitre qui les nomme, chaque ligne des tableaux d'outils
# porte EXACTEMENT UNE commande de citation, et chaque clé citée existe au registre des sources.
# Le registre suffit : le contrôle de synchronisation existant garantit que le fichier
# bibliographique en est le rendu.
# --------------------------------------------------------------------------------------------

OUTILS = REPORT / "chapitres" / "environnement-et-outils.tex"
REGISTRE_DES_SOURCES = RACINE / "docs" / "sources" / "sources.yml"
_CORPS_DE_TABLEAU = re.compile(r"\\endhead([\s\S]*?)\\bottomrule")
_CITE = re.compile(r"\\cite\{([^}]*)\}")


def lignes_de_tableau(source: str) -> list[str]:
    lignes: list[str] = []
    for corps in _CORPS_DE_TABLEAU.findall(partie_active(source)):
        for ligne in corps.replace("\\addlinespace", "").split("\\\\"):
            if ligne.strip():
                lignes.append(" ".join(ligne.split()))
    return lignes


def cles_du_registre() -> set[str]:
    import yaml

    entrees = yaml.safe_load(REGISTRE_DES_SOURCES.read_text(encoding="utf-8"))
    return {entree["id"].lower().replace("-", "") for entree in entrees}


def test_le_motif_lit_les_lignes_de_tableau_et_leurs_citations() -> None:
    source = (
        "\\midrule\n\\endhead\nA\\cite{s1} & x \\\\\n\\addlinespace\nB & y \\\\\n"
        "C\\cite{s2, s3}\\cite{s4} & z \\\\\n\\bottomrule"
    )
    lignes = lignes_de_tableau(source)
    assert [len(_CITE.findall(ligne)) for ligne in lignes] == [1, 0, 2], lignes


def test_chaque_outil_porte_une_reference_du_registre() -> None:
    lignes = lignes_de_tableau(OUTILS.read_text(encoding="utf-8"))
    assert lignes, "aucune ligne de tableau d'outils : la propriété ne vérifierait rien"
    connues = cles_du_registre()
    fautes = []
    for ligne in lignes:
        citations = _CITE.findall(ligne)
        if len(citations) != 1:
            fautes.append(f"{len(citations)} citation(s) : {ligne[:60]}")
            continue
        absentes = sorted({c.strip() for c in citations[0].split(",")} - connues)
        if absentes:
            fautes.append(f"clés absentes du registre {absentes} : {ligne[:60]}")
    assert not fautes, "lignes d'outils fautives :\n  " + "\n  ".join(fautes)
