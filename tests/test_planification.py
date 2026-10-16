"""La planification du projet : la figure, ses phases et ses dates.

Trois propriétés, sans base :

(g1) `report/figures/planification.tex` est, octet à octet, le rendu de
     `docs/planification/to_tex.py` sur le fichier de données de la série « planification » : la
     figure n'est jamais retouchée à la main ;
(g2) les phases de `docs/planification/planification.yml` sont exactement celles du tableau des
     phases du chapitre de cadrage, sous le même nom et dans le même ordre, et la série porte les
     mêmes, dans le même ordre ;
(g3) chaque ligne de la série tient dans la période du stage, la date du jalon aussi, et le jalon
     tombe dans la barre de la phase à laquelle il appartient.

LE TABLEAU DES PHASES EST LU, JAMAIS ÉCRIT. Il appartient à un passage d'écriture personnelle :
ce contrôle en lit la première cellule de chaque ligne, entre l'étiquette du tableau et sa règle
de fin, et ne propose aucune autre source pour les noms.

Ce que ce contrôle ne prouve pas : que les semaines de la série soient celles de l'historique du
dépôt. Cela relève de `docs/chiffres/mesurer.py --verifier`, qui recalcule l'empreinte de la série
depuis sa commande ; le présent contrôle part du fichier de données.
"""

from __future__ import annotations

import csv
import importlib.util
import re
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
CONFIGURATION = RACINE / "docs" / "planification" / "planification.yml"
GENERATEUR = RACINE / "docs" / "planification" / "to_tex.py"
SERIE = RACINE / "report" / "figures" / "planification.csv"
FIGURE = RACINE / "report" / "figures" / "planification.tex"
CHAPITRE = RACINE / "report" / "chapitres" / "cadrage-et-methodologie.tex"

JALON = "jalon"

_TABLEAU = re.compile(r"\\label\{tab:phases\}.*?\\midrule(.*?)\\bottomrule", re.S)
_LIGNE = re.compile(r"^\s*([^&\\%][^&]*?)\s*&", re.M)


def noms_du_tableau(source: str) -> list[str]:
    """La première cellule de chaque ligne du tableau des phases, dans l'ordre."""
    trouve = _TABLEAU.search(source)
    if trouve is None:
        return []
    return [nom.strip() for nom in _LIGNE.findall(trouve.group(1))]


def configuration() -> dict:
    return yaml.safe_load(CONFIGURATION.read_text(encoding="utf-8"))


def serie() -> list[dict]:
    with SERIE.open(encoding="utf-8", newline="") as fichier:
        return list(csv.DictReader(fichier))


def generateur():
    spec = importlib.util.spec_from_file_location("planification_to_tex", GENERATEUR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def semaine(date) -> int:
    return date.isocalendar()[1]


# Témoins du motif de lecture du tableau, dans les deux sens.
TABLEAU_TEMOIN = r"""
\caption{Les phases}\label{tab:phases}
\begin{tabular}{@{}p{4.6cm}p{4.6cm}@{}}
\toprule
Phase & Objectif \\
\midrule
Comprendre le service & savoir \\
\addlinespace
% Une ligne commentée & ne compte pas \\
Rédiger & rendre compte \\
\bottomrule
\end{tabular}
"""


def test_le_motif_lit_chaque_ligne_du_tableau() -> None:
    assert noms_du_tableau(TABLEAU_TEMOIN) == ["Comprendre le service", "Rédiger"]


def test_le_motif_ne_lit_ni_l_en_tete_ni_un_autre_tableau() -> None:
    sans_etiquette = TABLEAU_TEMOIN.replace(r"\label{tab:phases}", r"\label{tab:autre}")
    assert noms_du_tableau(sans_etiquette) == [], "un autre tableau ne porte pas les phases"
    assert "Phase" not in noms_du_tableau(TABLEAU_TEMOIN), "l'en-tête n'est pas une phase"


def test_la_figure_est_le_rendu_du_generateur() -> None:
    """(g1)"""
    module = generateur()
    attendu = module.rendre(module.charger(SERIE))
    assert FIGURE.read_text(encoding="utf-8") == attendu, (
        "report/figures/planification.tex diffère du rendu de docs/planification/to_tex.py : "
        "relancer le générateur plutôt que retoucher la figure"
    )


def test_les_phases_sont_celles_du_chapitre() -> None:
    """(g2)"""
    chapitre = noms_du_tableau(CHAPITRE.read_text(encoding="utf-8"))
    assert chapitre, "le tableau des phases est introuvable : la propriété ne vérifierait rien"
    declarees = [phase["nom"] for phase in configuration()["phases"]]
    assert declarees == chapitre, (
        f"phases de planification.yml {declarees} ; tableau du chapitre {chapitre}"
    )
    tracees = [ligne["phase"] for ligne in serie() if ligne["origine"] != JALON]
    assert tracees == declarees, f"phases de la série {tracees} ; planification.yml {declarees}"


def test_tout_tient_dans_la_periode_et_le_jalon_dans_sa_phase() -> None:
    """(g3)"""
    conf = configuration()
    debut, fin = conf["stage"]["debut"], conf["stage"]["fin"]
    premiere, derniere = semaine(debut), semaine(fin)
    jalon = conf["jalon"]
    assert debut <= jalon["date"] <= fin, f"le jalon ({jalon['date']}) sort de la période du stage"

    lignes = serie()
    hors = [
        f"{ligne['phase']} : semaines {ligne['debut']}–{ligne['fin']}"
        for ligne in lignes
        if not premiere <= int(ligne["debut"]) <= int(ligne["fin"]) <= derniere
    ]
    periode = f"{premiere}–{derniere}"
    assert not hors, f"hors de la période du stage ({periode}) :\n  " + "\n  ".join(hors)

    jalons = [ligne for ligne in lignes if ligne["origine"] == JALON]
    assert len(jalons) == 1, f"{len(jalons)} jalon(s) dans la série, un attendu"
    barre = [ligne for ligne in lignes if ligne["phase"] == jalon["phase"]]
    assert barre, f"la phase du jalon, « {jalon['phase']} », n'a pas de barre"
    position = int(jalons[0]["debut"])
    assert int(barre[0]["debut"]) <= position <= int(barre[0]["fin"]), (
        f"le jalon (semaine {position}) tombe hors de la barre de « {jalon['phase']} » "
        f"({barre[0]['debut']}–{barre[0]['fin']})"
    )
