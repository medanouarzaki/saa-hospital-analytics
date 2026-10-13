"""Tout fichier de source du rapport est inclus, et tout fichier inclus existe.

Le retrait d'une inclusion ne se voit nulle part : la compilation réussit, le document est
simplement plus court d'un chapitre, et aucun contrôle ne bronche — mesuré, c'est ce qui a motivé
l'écriture de ce fichier. Un chapitre écrit puis décroché par inadvertance disparaîtrait du rapport
sans qu'aucun signal ne le dise, et la relecture d'un document de plusieurs dizaines de pages n'est
pas un mécanisme de détection.

LA CORRESPONDANCE EST VÉRIFIÉE DANS LES DEUX SENS, comme toute référence croisée de ce dépôt : un
fichier présent et non inclus est un contenu perdu, un fichier inclus et absent est une compilation
qui échouera. Les deux sont des propriétés distinctes, et une seule direction ne prouve pas l'autre.

CE CONTRÔLE LIT LES SOURCES, JAMAIS LE PDF : il ne compile rien, ne dépend d'aucune distribution
typographique, et s'exécute donc partout — y compris là où aucune n'est installée.
"""

from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
REPORT = RACINE / "report"
PRINCIPAL = REPORT / "rapport.tex"

# Les fichiers de `report/` qui ne sont pas des sources à inclure : le document principal lui-même,
# et le fichier bibliographique, que biblatex charge par son propre mécanisme.
# Les sources de `report/` que le document n'inclut pas, et le motif de chacune.
#
# `rapport.tex` est le document lui-même ; `biblio.bib` entre par `\addbibresource`, non par
# `\input`.
#
# `dictionnaire_donnees.tex` est produit mécaniquement depuis le registre des champs, et le rapport
# ne le compose plus : il occupait près d'un quart du document pour un tableau qui ne se lit pas
# d'un bout à l'autre, et l'annexe porte désormais sa synthèse — produite par le même module — avec
# un renvoi au dictionnaire complet. Le fichier reste un artefact du dépôt, et
# `tests/test_provenance.py` le régénère pour le comparer au registre dont il dérive. Son absence
# d'inclusion est donc une décision, et elle est écrite ici plutôt que découverte.
HORS_INCLUSION = {"rapport.tex", "biblio.bib", "dictionnaire_donnees.tex"}

# `\input{chemin}` — le chemin est relatif au répertoire du document et sans extension. Un `\input`
# commenté n'inclut rien : le caractère de pourcentage ouvre un commentaire, sauf s'il est échappé.
_COMMENTAIRE = re.compile(r"(?<!\\)(?:\\\\)*%")
_INPUT = re.compile(r"\\input\{([^}]+)\}")


def _sans_commentaire(ligne: str) -> str:
    trouve = _COMMENTAIRE.search(ligne)
    return ligne if trouve is None else ligne[: trouve.end() - 1]


def _inclusions(depuis: Path, vues: set[Path] | None = None) -> set[Path]:
    """Les fichiers inclus, transitivement : un fichier inclus peut en inclure d'autres."""
    vues = set() if vues is None else vues
    if depuis in vues or not depuis.is_file():
        return vues
    vues.add(depuis)
    actives = "\n".join(
        _sans_commentaire(ligne) for ligne in depuis.read_text(encoding="utf-8").splitlines()
    )
    for chemin in _INPUT.findall(actives):
        cible = (REPORT / chemin).with_suffix(".tex")
        _inclusions(cible, vues)
    return vues


def _sources_presentes() -> set[Path]:
    return {chemin for chemin in REPORT.rglob("*.tex") if chemin.name not in HORS_INCLUSION}


def test_chaque_source_du_rapport_est_incluse() -> None:
    """Premier sens : aucun fichier écrit ne reste décroché du document."""
    incluses = _inclusions(PRINCIPAL) - {PRINCIPAL}
    orphelines = sorted(
        chemin.relative_to(RACINE).as_posix() for chemin in _sources_presentes() - incluses
    )
    assert not orphelines, (
        f"sources présentes sous report/ mais incluses par aucun fichier : {orphelines}"
    )


def test_chaque_inclusion_du_rapport_existe() -> None:
    """Second sens : aucune inclusion ne pointe dans le vide."""
    manquantes = sorted(
        chemin.relative_to(RACINE).as_posix()
        for chemin in _inclusions(PRINCIPAL)
        if not chemin.is_file()
    )
    assert not manquantes, f"fichiers inclus par le rapport et absents du disque : {manquantes}"


# L'annonce d'un chapitre dans l'introduction, hors commentaire. Le même motif que celui du contrôle
# de l'annonce du plan : la garde de fin interdit une commande homographe.
_ANNONCE_CHAPITRE = re.compile(r"\\annonceChapitre\{(\d+)\}")


def test_les_chapitres_presents_sont_ceux_que_l_introduction_annonce() -> None:
    """Le document porte bien la structure du plan, et non une partie d'elle.

    AUCUN DÉCOMPTE N'EST ÉCRIT ICI. La propriété est une égalité entre deux mesures : le nombre de
    fichiers de chapitres numérotés sous `report/chapitres/` et le nombre de chapitres que
    l'introduction annonce. Un nombre écrit en dur devenait faux au premier chapitre ajouté, et
    rougissait sur un document juste ; l'égalité suit le document. Ce qu'elle ajoute aux deux
    propriétés précédentes est que le répertoire n'a pas été vidé ni grossi d'un fichier que le
    plan ignore — deux fichiers absents des deux côtés passeraient les deux autres.
    """
    chapitres = sorted(p.name for p in (REPORT / "chapitres").glob("*.tex"))
    assert "introduction.tex" in chapitres, "l'introduction générale manque"
    assert "conclusion.tex" in chapitres, "la conclusion générale manque"
    numerotes = [n for n in chapitres if n not in {"introduction.tex", "conclusion.tex"}]
    introduction = (REPORT / "chapitres" / "introduction.tex").read_text(encoding="utf-8")
    actives = "\n".join(_sans_commentaire(ligne) for ligne in introduction.splitlines())
    annonces = _ANNONCE_CHAPITRE.findall(actives)
    assert annonces, "l'introduction n'annonce aucun chapitre : l'égalité ne vérifierait rien"
    assert len(numerotes) == len(annonces), (
        f"{len(numerotes)} chapitres numérotés sous report/chapitres/, l'introduction en annonce "
        f"{len(annonces)} : {numerotes}"
    )


# --------------------------------------------------------------------------------------------
# Les figures et les tableaux. Une figure est un environnement `figure`, un tableau un environnement
# `table` ou `longtable` ; chacun porte exactement un `\caption` et un `\label` de préfixe `fig:` ou
# `tab:`, chacun est appelé par au moins un `\ref` HORS de son propre flottant — un renvoi posé dans
# son titre ne l'appelle pas —, et tout `\ref` vers `fig:` ou `tab:` désigne une étiquette qui
# existe.
# La prose ne désigne aucun objet par sa position (« ci-dessous » et ses variantes), et aucune macro
# ne compose « Figure » ou « Tableau » devant un compteur tenu hors de la classe : un tel compteur
# numérotait à part les objets qu'il composait, et les tenait hors des listes.
# --------------------------------------------------------------------------------------------

_FLOTTANT = re.compile(r"\\begin\{(figure|table|longtable)\*?\}(.*?)\\end\{\1\*?\}", re.S)
_CAPTION = re.compile(r"\\caption(?![a-zA-Z])")
_ETIQUETTE = re.compile(r"\\label\{((?:fig|tab):[^}]*)\}")
_TOUTE_ETIQUETTE = re.compile(r"\\label\{([^}]*)\}")
_APPEL = re.compile(r"\\ref\{((?:fig|tab):[^}]*)\}")
_CI = re.compile(r"(?i)\bci-(?:dessous|dessus|après|contre)\b")
_NUMERO_HORS_CLASSE = re.compile(r"\b(?:Figure|Tableau)\s*~?\s*\\(?:the[a-zA-Z@]+|arabic\{)")


def _active(source: str) -> str:
    return "\n".join(_sans_commentaire(ligne) for ligne in source.splitlines())


def flottants(source: str) -> list[tuple[str, int, int, str]]:
    """Les flottants de la partie active : genre, début, fin, corps."""
    return [(m.group(1), m.start(), m.end(), m.group(2)) for m in _FLOTTANT.finditer(source)]


def fautes_de_flottant(source: str) -> list[str]:
    fautes = []
    for genre, _, _, corps in flottants(source):
        legendes = len(_CAPTION.findall(corps))
        etiquettes = _ETIQUETTE.findall(corps)
        if legendes != 1 or len(etiquettes) != 1:
            fautes.append(f"{genre} : {legendes} \\caption, étiquettes fig:/tab: {etiquettes}")
    return fautes


def appels_hors_de_leur_flottant(source: str) -> set[str]:
    """Les étiquettes appelées par un `\\ref` qui n'est pas dans le flottant qui la porte."""
    porte = {}
    for _, debut, fin, corps in flottants(source):
        for etiquette in _ETIQUETTE.findall(corps):
            porte[etiquette] = (debut, fin)
    appelees = set()
    for m in _APPEL.finditer(source):
        debut, fin = porte.get(m.group(1), (-1, -1))
        if not debut <= m.start() < fin:
            appelees.add(m.group(1))
    return appelees


def positions_designees(source: str) -> list[str]:
    """Les « ci-dessous » et variantes de la partie active, coupure après le tiret comprise."""
    return _CI.findall(re.sub(r"-[ \t]*\n[ \t]*", "-", _active(source)))


def _sources_redigees() -> list[Path]:
    """Les sources .tex de `report/` écrites à la main.

    Les fichiers produits par un générateur sont ceux que `tests/test_aucun_nombre_tape.py` nomme,
    et le rendu du registre des chiffres.
    """
    from test_aucun_nombre_tape import ANNEXES_PRODUITES

    produits = set(ANNEXES_PRODUITES) | {"chiffres.tex"}
    return sorted(p for p in REPORT.rglob("*.tex") if p.name not in produits)


TEMOIN_FLOTTANTS = r"""
\begin{figure}[htbp]\centering X \caption{Un titre}\label{fig:a}\end{figure}
\begin{table}[htbp]\centering\caption{Sans étiquette} Y \end{table}
\begin{figure}[htbp] Z \end{figure}
\begin{longtable}{ll}\caption[court]{Titre {imbriqué}}\label{tab:b}\\ a & b \end{longtable}
\begin{table}\caption{Un}\caption{Deux}\label{tab:c}\end{table}
% \begin{figure} commentée \end{figure}
"""


def test_le_motif_voit_chaque_flottant_fautif() -> None:
    fautes = fautes_de_flottant(_active(TEMOIN_FLOTTANTS))
    assert len(flottants(_active(TEMOIN_FLOTTANTS))) == 5, "un flottant témoin n'est pas vu"
    assert len(fautes) == 3, fautes


TEMOIN_APPELS = r"""
Le texte appelle la première (voir figure~\ref{fig:a}).
\begin{figure}X\caption{Titre}\label{fig:a}\end{figure}
\begin{table}\caption{Renvoi dans son propre titre, tableau~\ref{tab:b}}\label{tab:b}\end{table}
\begin{figure}Y\caption{Z, qui renvoie à la figure~\ref{fig:a}}\label{fig:c}\end{figure}
% le commentaire cite \ref{fig:c}
"""


def test_un_renvoi_dans_son_propre_titre_n_appelle_pas_l_objet() -> None:
    appelees = appels_hors_de_leur_flottant(_active(TEMOIN_APPELS))
    assert appelees == {"fig:a"}, appelees


TEMOINS_POSITION_VUS = (
    "le tableau ci-dessous",
    "Ci-dessus",
    "voir ci-\naprès",
    "la carte ci-contre",
)
TEMOINS_POSITION_NON_VUS = ("% le tableau ci-dessous", "ici, dessous", "ci après", "voici-dessous")


def test_le_motif_voit_chaque_designation_par_position() -> None:
    for temoin in TEMOINS_POSITION_VUS:
        assert positions_designees(temoin), f"témoin positif « {temoin} »"
    for temoin in TEMOINS_POSITION_NON_VUS:
        assert not positions_designees(temoin), f"témoin négatif « {temoin} »"


TEMOINS_NUMERO_VUS = (
    r"\footnotesize Figure~\thecapturetdb~— #1\label{#2}",
    r"Tableau \arabic{montableau} :",
)
TEMOINS_NUMERO_NON_VUS = (r"(voir figure~\ref{fig:x})", r"\caption{Figure de style}", r"Tableau 3")


def test_le_motif_voit_un_numero_compose_hors_de_la_classe() -> None:
    for temoin in TEMOINS_NUMERO_VUS:
        assert _NUMERO_HORS_CLASSE.search(temoin), f"témoin positif « {temoin} »"
    for temoin in TEMOINS_NUMERO_NON_VUS:
        assert not _NUMERO_HORS_CLASSE.search(temoin), f"témoin négatif « {temoin} »"


def test_chaque_figure_et_chaque_tableau_porte_un_titre_et_une_etiquette() -> None:
    chapitres = sorted((REPORT / "chapitres").glob("*.tex"))
    tous = [(c, _active(c.read_text(encoding="utf-8"))) for c in chapitres]
    assert any(flottants(texte) for _, texte in tous), "aucun flottant : la propriété serait vide"
    fautes = [f"{c.name} : {f}" for c, texte in tous for f in fautes_de_flottant(texte)]
    assert not fautes, "flottants sans titre ou sans étiquette unique :\n  " + "\n  ".join(fautes)


def test_chaque_figure_et_chaque_tableau_est_appele_et_tout_appel_a_sa_cible() -> None:
    textes = {p: _active(p.read_text(encoding="utf-8")) for p in _sources_redigees()}
    definies = {e for t in textes.values() for e in _TOUTE_ETIQUETTE.findall(t)}
    objets = {
        e for t in textes.values() for _, _, _, c in flottants(t) for e in _ETIQUETTE.findall(c)
    }
    assert objets, "aucune étiquette fig: ou tab: : la propriété serait vide"
    appelees = set().union(*(appels_hors_de_leur_flottant(t) for t in textes.values()))
    sans_appel = sorted(objets - appelees)
    assert not sans_appel, f"objets jamais appelés hors de leur flottant : {sans_appel}"
    cibles = {m for t in textes.values() for m in _APPEL.findall(t)}
    sans_cible = sorted(cibles - definies)
    assert not sans_cible, f"renvois vers une étiquette inexistante : {sans_cible}"


def test_aucune_designation_par_position_dans_la_prose() -> None:
    sources = _sources_redigees()
    assert any(p.name == "annexes.tex" for p in sources), "le périmètre a perdu les annexes"
    fautes = [
        f"{p.relative_to(RACINE)} : {m!r}"
        for p in sources
        for m in positions_designees(p.read_text(encoding="utf-8"))
    ]
    assert not fautes, "désignations par position (appeler l'objet par \\ref) :\n  " + "\n  ".join(
        fautes
    )


def test_aucune_macro_ne_numerote_un_objet_hors_de_la_classe() -> None:
    fautes = [
        f"{p.relative_to(RACINE)} : {m.group(0)!r}"
        for p in _sources_redigees()
        for m in _NUMERO_HORS_CLASSE.finditer(_active(p.read_text(encoding="utf-8")))
    ]
    assert not fautes, "numéro composé hors de la classe :\n  " + "\n  ".join(fautes)
