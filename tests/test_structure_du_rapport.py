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
