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


def entree(identifiant: str) -> dict:
    for candidat in registre()["indicateurs"]:
        if candidat["identifiant"] == identifiant:
            return candidat
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


# Ce qu'affiche un indicateur qui ne répond pas au filtre de période, selon ce que le registre
# déclare. Le texte est construit à partir de la réserve ou du motif que le registre porte, jamais
# écrit dans une page : une page qui déciderait elle-même de ce qu'elle marque pourrait diverger du
# registre sans que rien ne le signale.
MOTIFS_LISIBLES = {
    "objet_sans_colonne_temporelle": (
        "l'objet qui porte cette grandeur ne comporte aucune date : elle décrit un état, "
        "non un flux"
    ),
    "grandeur_annualisee": (
        "cette grandeur rapporte un volume à une année de référence ; la restreindre à une "
        "sous-période est possible mais méthodologiquement faux"
    ),
    "date_hors_couche_des_faits": (
        "la date existe, mais dans une couche que le filtre appliqué aux faits n'atteint pas"
    ),
}

MENTION_HORS_FILTRE = "Non filtré par la période"
MENTION_SOUS_RESERVE = "Filtré par la période, sous réserve"


def filtrabilite(identifiant: str) -> str:
    return entree(identifiant)["filtrabilite"]


def page_porte_un_filtre(page: str) -> bool:
    """Une page ne porte un filtre que si au moins un de ses indicateurs y répond."""
    return any(indicateur["filtrabilite"] != "non" for indicateur in indicateurs_de(page))


def mention_de_filtrabilite(identifiant: str) -> None:
    """Marque l'indicateur si, et seulement si, le registre dit qu'il échappe au filtre.

    Un filtre présent à l'écran et sans effet sur un chiffre ferait lire ce chiffre comme s'il
    portait sur la période choisie. La mention est donc portée par l'indicateur lui-même, à côté de
    sa valeur, et non reléguée dans une note de bas de page.
    """
    declaration = entree(identifiant)
    valeur = declaration["filtrabilite"]
    if valeur == "oui":
        return
    if valeur == "oui_sous_reserve":
        st.warning(
            f"{MENTION_SOUS_RESERVE} — {' '.join(declaration['reserve'].split())}",
            icon="⚠️",
        )
        return
    motif = MOTIFS_LISIBLES.get(declaration.get("motif"), declaration.get("motif", ""))
    st.warning(f"{MENTION_HORS_FILTRE} — {motif}.", icon="⚠️")


def absence_de_filtre(page: str) -> None:
    """Affiché par une page dont aucun indicateur ne répond au filtre : dire pourquoi il n'y en a
    pas vaut mieux que de laisser un lecteur chercher un filtre absent."""
    motifs = sorted(
        {
            MOTIFS_LISIBLES.get(indicateur.get("motif"), indicateur.get("motif", ""))
            for indicateur in indicateurs_de(page)
        }
    )
    st.info(
        "Cette page ne porte pas de filtre de période : aucun de ses indicateurs n'y répond — "
        + " ; ".join(motifs)
        + ".",
        icon="ℹ️",
    )


def filtre_de_page(page: str, bornes: tuple | None = None) -> tuple | None:
    """Rend le filtre de période de la page, ou dit pourquoi il n'y en a pas.

    Le comportement se déduit du registre : une page dont aucun indicateur ne répond au filtre n'en
    porte pas, et affiche le motif. Une page qui en porte un le porte pour tous, chaque indicateur
    qui n'y répond pas étant marqué à côté de sa valeur.

    Les bornes viennent des données quand l'appelant les fournit, jamais d'une constante.
    """
    if not page_porte_un_filtre(page):
        absence_de_filtre(page)
        return None
    if bornes is None:
        return None
    debut, fin = bornes
    choix = st.date_input("Période observée", value=(debut, fin), min_value=debut, max_value=fin)
    if isinstance(choix, tuple) and len(choix) == 2:
        return choix
    return debut, fin


def clause_periode(identifiant: str, periode: tuple | None) -> str:
    """La clause de restriction d'un indicateur, vide s'il ne répond pas au filtre.

    C'est ici que la décision se matérialise : un indicateur déclaré non filtrable ne reçoit
    aucune clause, quelle que soit la période choisie à l'écran. Le marquage affiché et l'absence
    de clause viennent donc de la même source, et ne peuvent pas diverger.
    """
    declaration = entree(identifiant)
    if periode is None or declaration["filtrabilite"] == "non":
        return ""
    colonne = declaration.get("colonne_de_date")
    if not colonne:
        return ""
    debut, fin = periode
    return f"where {colonne} between date '{debut:%Y-%m-%d}' and date '{fin:%Y-%m-%d}'"


def titre_indicateur(identifiant: str) -> None:
    """Le libellé de l'indicateur, sa définition, puis sa mention de filtrabilité s'il en a une."""
    st.subheader(libelle(identifiant))
    st.caption(definition(identifiant))
    mention_de_filtrabilite(identifiant)
