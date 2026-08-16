"""Éléments d'affichage partagés par les pages.

Deux règles y sont tenues une fois pour toutes, plutôt que répétées dans chaque page.

La définition d'un indicateur vient du registre, jamais du code de la page. Écrire une définition
en dur créerait une seconde source de vérité, qui divergerait du registre sans que rien ne le
signale ; le registre est déjà vérifié par ses propres contrôles, et c'est lui qui fait foi.

Chaque page date ce qu'elle affiche. Quarante-six jours séparent l'horloge de la dernière date
d'extraction chargée : un écran qui n'affiche pas cette date laisse croire à des données du jour.
La date de référence et l'horodatage du rafraîchissement sont donc rendus par la même fonction que
le titre, de sorte qu'une page ne puisse pas les omettre par distraction.
"""

from __future__ import annotations

import functools
from pathlib import Path

import streamlit as st
import yaml

from dashboard import lecture

REGISTRE = Path(__file__).resolve().parent / "indicateurs.yml"


@functools.lru_cache(maxsize=1)
def registre() -> dict:
    return yaml.safe_load(REGISTRE.read_text(encoding="utf-8"))


def indicateurs_de(page: str) -> list[dict]:
    return [entree for entree in registre()["indicateurs"] if entree["page"] == page]


def definition(identifiant: str) -> str:
    """La définition telle que le registre la porte. Absente du registre, elle lève."""
    for entree in registre()["indicateurs"]:
        if entree["identifiant"] == identifiant:
            return " ".join(entree["definition"].split())
    raise KeyError(f"indicateur absent du registre : {identifiant}")


def libelle(identifiant: str) -> str:
    for entree in registre()["indicateurs"]:
        if entree["identifiant"] == identifiant:
            return entree["libelle"]
    raise KeyError(f"indicateur absent du registre : {identifiant}")


def en_tete(titre: str) -> dict:
    """Titre de la page, puis la date des données et celle du rafraîchissement."""
    st.title(titre)
    etat = lecture.etat()
    date_reference = etat["date_reference"]
    rafraichi_le = etat["rafraichi_le"]
    st.caption(
        f"Données arrêtées au {date_reference:%d/%m/%Y} — "
        f"état constitué le {rafraichi_le:%d/%m/%Y à %H:%M} (UTC)"
    )
    return etat


def titre_indicateur(identifiant: str) -> None:
    """Le libellé de l'indicateur, puis sa définition, tous deux lus au registre."""
    st.subheader(libelle(identifiant))
    st.caption(definition(identifiant))
