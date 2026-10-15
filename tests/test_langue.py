"""La langue de la prose du rapport : cinq propriétés de la charte de style, tenues partout.

CE CONTRÔLE N'OUVRE AUCUNE BASE. Il lit la prose des sources rédigées du rapport — la liste et le
dépouillement sont ceux du contrôle des nombres tapés, importés et non réécrits — et vérifie :

  (l1) aucune forme de « engendr- » : le projet écrit « générer » ;
  (l2) aucun mot ni aucune locution de la liste des mots bannis, sauf les emplois déclarés ;
  (l3) aucun « on », « l'on », « qu'on », « nous », « notre », « nos » : prose impersonnelle ;
  (l4) la première personne réservée aux remerciements et au volet professionnel de la conclusion ;
  (l5) chaque chapitre numéroté, sauf le dernier, finit sur un renvoi au chapitre qui le suit.

L'abstract est écrit en anglais : les propriétés (l1) à (l4) portent sur le français, et il en est
retiré. Le contrôle des nombres tapés, lui, l'examine toujours.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
RAPPORT = RACINE / "report" / "rapport.tex"
CHAPITRES = RACINE / "report" / "chapitres"

_TEXTE_ANGLAIS = re.compile(r"\\begin\{otherlanguage\}\{english\}.*?\\end\{otherlanguage\}", re.S)

# Les mots et locutions que la charte écarte de la prose. Une locution s'écrit avec ses espaces ;
# le motif accepte une espace, une espace insécable ou un retour à la ligne entre ses mots, et une
# apostrophe droite ou typographique.
MOTS_BANNIS = (
    "afférent",
    "idoine",
    "subséquent",
    "corpus",
    "nonobstant",
    "à l'aune de",
    "prégnant",
    "exhiber",
    "asymétrie",
    "disjoint",
    "instance",
    "dispositif",
    "appareil",
    "artefact",
    "témoin",
    "mutation",
    "il convient de",
    "il est important de",
    "crucial",
    "robuste",
    "en somme",
    "en définitive",
    "force est de constater",
    "dès lors",
    "en l'espèce",
)

# Les emplois légitimes d'un mot banni, un par un : (fichier, ligne dépouillée, motif). La liste
# casse dans les deux sens.
EXCEPTIONS_MOTS = (
    (
        "conception-du-jeu-de-donnees.tex",
        "& mouvement de séjour : admission, mutation ou sortie & \\\\",
        "« mutation » est le terme du domaine pour le mouvement de séjour, repris dans une cellule "
        "de tableau",
    ),
)

_LETTRE = r"\wÀ-ÿ"
_ENGENDRER = re.compile(r"engendr", re.I)
_IMPERSONNEL = re.compile(
    rf"(?<![{_LETTRE}'’])(?:on|nous|notre|nos)(?![{_LETTRE}'’])"
    rf"|(?<![{_LETTRE}])(?:l|qu)['’]on(?![{_LETTRE}])",
    re.I,
)
_PREMIERE_PERSONNE = re.compile(
    rf"(?<![{_LETTRE}'’])(?:je|me|mon|ma|mes|moi)(?![{_LETTRE}'’])"
    rf"|(?<![{_LETTRE}'’])[jm]['’](?=[{_LETTRE}])",
    re.I,
)
_APPORT_PERSONNEL = re.compile(
    r"\\subsection\*\{Le volet professionnel\}(.*?)(?=\\section\*\{|\Z)", re.S
)


def _nombres_tapes():
    import test_aucun_nombre_tape

    return test_aucun_nombre_tape


def _mot_banni(mot: str) -> re.Pattern:
    corps = r"[\s~]+".join(re.escape(m).replace("'", "['’]") for m in mot.split(" "))
    pluriel = "" if " " in mot else "[sx]?"
    return re.compile(rf"(?<![{_LETTRE}]){corps}{pluriel}(?![{_LETTRE}])", re.I)


def lignes_de_prose(source: str) -> list[str]:
    """Les lignes dépouillées de la prose française, espaces normalisées."""
    depouille = _nombres_tapes().depouiller(_TEXTE_ANGLAIS.sub(" ", source))
    return [" ".join(ligne.split()) for ligne in depouille.splitlines() if ligne.strip()]


def sources() -> list[Path]:
    return _nombres_tapes().fichiers_examines()


def premiere_personne_hors_place(chemin: Path) -> list[str]:
    source = chemin.read_text(encoding="utf-8")
    if chemin.name == "remerciements.tex":
        return []
    if chemin.name == "conclusion.tex":
        source = _APPORT_PERSONNEL.sub(" ", source)
    return [ligne for ligne in lignes_de_prose(source) if _PREMIERE_PERSONNE.search(ligne)]


def chapitres_numerotes() -> list[Path]:
    """Les chapitres numérotés, dans l'ordre où le document les inclut."""
    inclus = re.findall(r"\\input\{chapitres/([^}]+)\}", RAPPORT.read_text(encoding="utf-8"))
    chemins = [CHAPITRES / f"{nom}.tex" for nom in inclus]
    return [c for c in chemins if re.search(r"\\chapter\{", c.read_text(encoding="utf-8"))]


def etiquette_de_chapitre(source: str) -> str:
    return re.search(r"\\chapter\{[^}]*\}\\label\{([^}]+)\}", source).group(1)


def dernier_paragraphe(source: str) -> str:
    actif = _nombres_tapes().partie_active(source)
    paragraphes = [
        p
        for p in re.split(r"\n\s*\n", actif)
        if p.strip() and not p.strip().startswith(("\\begin", "\\end", "\\section", "\\caption"))
    ]
    return " ".join(paragraphes[-1].split())


def transition_manquante(source: str, etiquette_suivante: str) -> bool:
    return f"\\ref{{{etiquette_suivante}}}" not in dernier_paragraphe(source)


# --------------------------------------------------------------------------------------------
# Préconditions.
# --------------------------------------------------------------------------------------------


def test_le_perimetre_porte_des_fichiers_et_l_apport_personnel_est_repere() -> None:
    fichiers = sources()
    assert fichiers, "aucune source rédigée examinée"
    assert any(f.name == "remerciements.tex" for f in fichiers), "remerciements absents"
    conclusion = CHAPITRES / "conclusion.tex"
    assert _APPORT_PERSONNEL.search(conclusion.read_text(encoding="utf-8")), (
        "la sous-section « Le volet professionnel » n'est plus repérée dans la conclusion"
    )
    assert len(chapitres_numerotes()) > 1, (
        "moins de deux chapitres numérotés : (l5) ne vérifie rien"
    )


# --------------------------------------------------------------------------------------------
# (l1) à (l5).
# --------------------------------------------------------------------------------------------


def test_l1_aucune_forme_de_engendrer() -> None:
    fautes = [
        f"{f.name} : {ligne[:100]}"
        for f in sources()
        for ligne in lignes_de_prose(f.read_text(encoding="utf-8"))
        if _ENGENDRER.search(ligne)
    ]
    assert not fautes, "formes de « engendrer » :\n  " + "\n  ".join(fautes)


def occurrences_de_mots_bannis() -> Counter:
    motifs = [_mot_banni(m) for m in MOTS_BANNIS]
    compte: Counter = Counter()
    for f in sources():
        for ligne in lignes_de_prose(f.read_text(encoding="utf-8")):
            for motif in motifs:
                compte[(f.name, ligne)] += len(motif.findall(ligne))
    return +compte


def test_l2_aucun_mot_banni_hors_des_emplois_declares() -> None:
    trouves = occurrences_de_mots_bannis()
    declares = Counter((f, ligne) for f, ligne, _ in EXCEPTIONS_MOTS)
    fautes = [
        f"{f} : {ligne[:100]}" for (f, ligne), n in trouves.items() if n > declares[(f, ligne)]
    ]
    assert not fautes, "mots bannis :\n  " + "\n  ".join(fautes)


def test_l2_toute_exception_correspond_a_un_emploi() -> None:
    trouves = occurrences_de_mots_bannis()
    perimees = [f"{f} : {ligne[:80]}" for f, ligne, _ in EXCEPTIONS_MOTS if not trouves[(f, ligne)]]
    assert not perimees, "exceptions sans emploi — retirez-les :\n  " + "\n  ".join(perimees)


def test_l3_la_prose_est_impersonnelle() -> None:
    fautes = [
        f"{f.name} : {ligne[:100]}"
        for f in sources()
        for ligne in lignes_de_prose(f.read_text(encoding="utf-8"))
        if _IMPERSONNEL.search(ligne)
    ]
    assert not fautes, "« on », « nous », « notre » ou « nos » :\n  " + "\n  ".join(fautes)


def test_l4_la_premiere_personne_reste_a_sa_place() -> None:
    fautes = [
        f"{f.name} : {ligne[:100]}" for f in sources() for ligne in premiere_personne_hors_place(f)
    ]
    assert not fautes, "première personne hors des passages personnels :\n  " + "\n  ".join(fautes)


def test_l5_chaque_chapitre_renvoie_au_suivant() -> None:
    chapitres = chapitres_numerotes()
    fautes = []
    for courant, suivant in zip(chapitres, chapitres[1:], strict=False):
        etiquette = etiquette_de_chapitre(suivant.read_text(encoding="utf-8"))
        if transition_manquante(courant.read_text(encoding="utf-8"), etiquette):
            fautes.append(f"{courant.name} ne renvoie pas à {etiquette}")
    assert not fautes, "transitions manquantes :\n  " + "\n  ".join(fautes)


# --------------------------------------------------------------------------------------------
# Témoins.
# --------------------------------------------------------------------------------------------


def test_temoins_l1() -> None:
    assert _ENGENDRER.search("les données Engendrées par le programme")
    assert not _ENGENDRER.search("les données générées par le programme")


@pytest.mark.parametrize(
    "texte", ["un modèle robuste", "Dès lors, le taux", "à l’aune de la mesure", "deux artefacts"]
)
def test_temoins_positifs_l2(texte: str) -> None:
    assert any(_mot_banni(m).search(texte) for m in MOTS_BANNIS), texte


@pytest.mark.parametrize("texte", ["la courbe en témoigne", "un appareillage", "un témoignage"])
def test_temoins_negatifs_l2(texte: str) -> None:
    assert not any(_mot_banni(m).search(texte) for m in MOTS_BANNIS), texte


@pytest.mark.parametrize(
    "texte", ["on observe", "ce qu'on voit", "si l’on compte", "Nous", "nos tables"]
)
def test_temoins_positifs_l3(texte: str) -> None:
    assert _IMPERSONNEL.search(texte), texte


@pytest.mark.parametrize("texte", ["bon", "ils sont", "le nombre", "nosocomial", "nosologie"])
def test_temoins_negatifs_l3(texte: str) -> None:
    assert not _IMPERSONNEL.search(texte), texte


def test_l3_ne_lit_pas_l_abstract_anglais() -> None:
    source = "\\begin{otherlanguage}{english}\nThe data rest on volumes.\n\\end{otherlanguage}"
    assert not any(_IMPERSONNEL.search(ligne) for ligne in lignes_de_prose(source))


@pytest.mark.parametrize("texte", ["je pense", "j'ai compris", "mon travail", "m’a tenu", "Moi"])
def test_temoins_positifs_l4(texte: str) -> None:
    assert _PREMIERE_PERSONNE.search(texte), texte


@pytest.mark.parametrize("texte", ["la mesure", "mais", "en mai", "le même"])
def test_temoins_negatifs_l4(texte: str) -> None:
    assert not _PREMIERE_PERSONNE.search(texte), texte


def test_l4_admet_le_volet_professionnel() -> None:
    source = (
        "\\section*{Bilan}\nLe travail.\n\\subsection*{Le volet professionnel}\nJ'ai appris.\n"
        "\\section*{Perspectives}\nLa suite.\n"
    )
    assert not [
        ligne
        for ligne in lignes_de_prose(_APPORT_PERSONNEL.sub(" ", source))
        if _PREMIERE_PERSONNE.search(ligne)
    ]
    assert [ligne for ligne in lignes_de_prose(source) if _PREMIERE_PERSONNE.search(ligne)]


def test_temoins_l5() -> None:
    avec = "Texte.\n\nLe chapitre~\\ref{chap:suivant} décrit la suite.\n"
    sans = "Texte.\n\nLe chapitre suivant décrit la suite.\n"
    assert not transition_manquante(avec, "chap:suivant")
    assert transition_manquante(sans, "chap:suivant")


def test_le_dernier_chapitre_n_est_pas_examine() -> None:
    """Témoin négatif de (l5) : le dernier chapitre transite vers la conclusion, sans numéro."""
    dernier = chapitres_numerotes()[-1]
    assert "\\ref{chap:" not in dernier_paragraphe(dernier.read_text(encoding="utf-8"))
