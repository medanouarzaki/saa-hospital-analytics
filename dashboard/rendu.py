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
LIBELLES = Path(__file__).resolve().parent / "libelles_dimensions.yml"

# Le séparateur entre le code et son libellé. Le code reste EN TÊTE, et ce n'est pas une
# question de goût : il porte l'ordre de tri des axes — les codes d'activité sont du texte,
# triés lexicographiquement, et les préfixer conserve exactement l'ordre rendu jusqu'ici —
# et il reste le lien avec les exports, où seul le code figure. Un lecteur qui retrouve
# « 20 » dans un fichier tabulaire doit pouvoir le rapprocher de ce qu'il voit à l'écran.
SEPARATEUR_LIBELLE = " — "


@functools.lru_cache(maxsize=1)
def registre() -> dict:
    return yaml.safe_load(REGISTRE.read_text(encoding="utf-8"))


@functools.lru_cache(maxsize=1)
def registre_libelles() -> dict:
    return yaml.safe_load(LIBELLES.read_text(encoding="utf-8"))


@functools.lru_cache(maxsize=1)
def _libelles_par_dimension() -> dict[str, dict[str, dict]]:
    """Les entrées du registre des libellés, indexées par dimension puis par code."""
    index: dict[str, dict[str, dict]] = {}
    for entree in registre_libelles()["libelles"]:
        index.setdefault(entree["dimension"], {})[str(entree["code"])] = entree
    return index


def libelle_dimension(dimension: str, code) -> str:
    """Le code, suivi de son libellé si — et seulement si — une source l'établit.

    Un code classé `non_documente` au registre est rendu tel quel. C'est la règle qui
    empêche l'invention : le mécanisme n'a aucun moyen de fabriquer un libellé, il ne sait
    que lire celui qu'une source a établi.

    Un code absent du registre est rendu tel quel lui aussi, et le contrôle dédié rougit :
    l'affichage ne doit pas décider à la place du registre, même pour se protéger.
    """
    entree = _libelles_par_dimension().get(dimension, {}).get(str(code))
    if entree is None or entree.get("categorie") != "documente":
        return str(code)
    return f"{code}{SEPARATEUR_LIBELLE}{entree['libelle']}"


def avec_libelles(tableau, colonne: str, dimension: str):
    """Rend une copie du tableau dont `colonne` porte le code suivi de son libellé."""
    if colonne not in tableau.columns:
        return tableau
    return tableau.assign(
        **{colonne: tableau[colonne].map(lambda code: libelle_dimension(dimension, code))}
    )


def mention_source_libelles(dimension: str) -> None:
    """Cite à l'écran la source qui établit les libellés d'une dimension.

    La version installée de la bibliothèque d'affichage accepte un paramètre `help` sur
    `st.caption` — lu dans sa signature : `caption(body, unsafe_allow_html=False, *,
    help=None, width='stretch', text_alignment='left')`. Le renvoi précis y est porté en
    infobulle, la ligne visible restant courte.

    N'émet rien si aucun code de la dimension n'est documenté : la page porte alors sa
    propre mention, qui dit que les codes sont nus.
    """
    documentes = [
        entree
        for entree in _libelles_par_dimension().get(dimension, {}).values()
        if entree.get("categorie") == "documente"
    ]
    if not documentes:
        return
    sources = sorted({entree["source"] for entree in documentes})
    renvois = sorted({f"{entree['source']} — {entree['renvoi']}" for entree in documentes})
    st.caption(
        f"Libellés établis par {', '.join(sources)} ; aucun n'est inventé. "
        f"{len(documentes)} code(s) documenté(s) sur {len(_libelles_par_dimension()[dimension])}.",
        help=" | ".join(renvois),
    )


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

# Ce qu'un indicateur lit réellement quand il n'est pas recalculé depuis les tables de faits. Le
# cadrage veut que tout indicateur le soit ; ceux qui ne le sont pas relèvent d'écarts consignés,
# faute de table de faits portant la matière. Sans cette mention, un lecteur ne pourrait pas
# distinguer un chiffre reconstruit d'un chiffre repris, et l'écart consigné resterait une
# déclaration sans effet visible.
#
# La correspondance est tenue ici et nulle part ailleurs ; le comportement se déduit du registre.
SOURCES_LISIBLES = {
    "couche_intermediaire": "la couche intermédiaire, aucune table de faits ne portant la matière",
    "catalogue": "le catalogue des colonnes, aucune table de faits ne portant de métadonnée",
    "dimension": "la dimension des patients, un recalcul depuis les faits portant sur une "
    "population strictement plus petite",
    "rapprochement": "les tables de rapprochement, dont aucune table de faits ne reprend le "
    "résultat",
    "faits_et_parametre": "les faits et un paramètre extérieur aux données observées",
}

MENTION_SOURCE = "Non recalculé depuis les tables de faits"

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

    **Sauf sur une page qui ne porte aucun filtre.** Une telle page affiche déjà en tête, par
    `absence_de_filtre`, que rien chez elle ne répond au filtre ; le répéter sous chaque indicateur
    n'apprend rien et noie l'écran sous des bandeaux identiques. La condition se déduit du
    registre, comme le reste : si aucun indicateur de la page n'est filtrable, il n'y a pas de
    filtre à l'écran, donc aucun chiffre qu'un lecteur puisse croire restreint. Sur une page mixte,
    au contraire, le marquage par indicateur est ce qui distingue les chiffres restreints des
    autres, et il est conservé.
    """
    declaration = entree(identifiant)
    valeur = declaration["filtrabilite"]
    if valeur == "oui":
        return
    if not page_porte_un_filtre(declaration["page"]):
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


def en_nombres(tableau, *colonnes: str):
    """Convertit en nombres à virgule les colonnes destinées à un graphique.

    Le serveur rend les grandeurs monétaires et les taux en décimal exact ; la bibliothèque
    d'affichage ne sait pas en déduire un type d'axe et retombe alors sur un axe catégoriel, ce
    qu'un avertissement signale. La conversion n'a lieu qu'à l'affichage : les valeurs qui entrent
    dans un contrôle restent exactes.
    """
    for colonne in colonnes:
        if colonne in tableau.columns:
            tableau = tableau.assign(**{colonne: tableau[colonne].astype(float)})
    return tableau


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


def source_de_valeur(identifiant: str) -> str:
    return entree(identifiant)["recalcule_depuis"]


def mention_de_source(identifiant: str) -> None:
    """Marque l'indicateur si, et seulement si, sa valeur ne vient pas des tables de faits."""
    source = source_de_valeur(identifiant)
    if source == "faits":
        return
    lisible = SOURCES_LISIBLES.get(source, source)
    st.caption(f"↪ {MENTION_SOURCE} : cette valeur lit {lisible}.")


def titre_indicateur(identifiant: str) -> None:
    """Le libellé, la définition, puis les deux mentions que l'indicateur mérite s'il y a lieu."""
    st.subheader(libelle(identifiant))
    st.caption(definition(identifiant))
    mention_de_source(identifiant)
    mention_de_filtrabilite(identifiant)


# --- les axes de temps, en français ---------------------------------------------------------------
# Les tracés intégrés de l'outil d'affichage composent leurs étiquettes de date par le moteur de
# graphiques sous-jacent, dont la locale est anglaise : une application française affichait ses mois
# en « Jan », « Feb », « Mar ».
#
# AUCUNE OPTION DE CONFIGURATION NE CHANGE CETTE LOCALE, et c'est mesuré plutôt que supposé :
# l'inventaire des options de l'outil ne porte aucune entrée de locale ni de format de date. La
# seule prise est l'expression d'étiquette du moteur de graphiques, qui s'écrit dans la
# spécification et s'évalue à chaque graduation.
#
# Les mois sont donc énumérés ici, et l'expression les indexe par le numéro de mois de la valeur de
# graduation. Elle ne dépend d'aucune locale : elle ne peut pas retomber en anglais.
MOIS_ABREGES = (
    "janv.",
    "févr.",
    "mars",
    "avr.",
    "mai",
    "juin",
    "juil.",
    "août",
    "sept.",
    "oct.",
    "nov.",
    "déc.",
)

# Une étiquette sur deux lignes — le mois, puis l'année —, forme que le moteur emploie lui-même
# pour un axe de temps. `month(...)` rend le numéro de mois de zéro à onze.
_ETIQUETTE_DE_TEMPS = f"[{list(MOIS_ABREGES)}[month(datum.value)], year(datum.value)]"


def tracer_temporel(
    tableau,
    *,
    x: str,
    y,
    couleur: str | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    forme: str = "line",
) -> None:
    """Un tracé dont l'axe des abscisses est une date, avec ses étiquettes en français.

    Même appel que les tracés intégrés — un tableau, une abscisse, une ou plusieurs ordonnées, une
    couleur facultative — et même rendu, à l'étiquette de date près.

    `y` accepte une liste : les colonnes sont alors repliées en deux, une de nom et une de valeur,
    et la couleur porte le nom. C'est ce que font les tracés intégrés lorsqu'on leur passe
    plusieurs ordonnées.
    """
    mesures = list(y) if isinstance(y, (list, tuple)) else [y]
    plusieurs = len(mesures) > 1

    encodage = {
        "x": {
            "field": x,
            "type": "temporal",
            "title": x_label,
            "axis": {"labelExpr": _ETIQUETTE_DE_TEMPS, "labelOverlap": True},
        },
        "y": {
            "field": "valeur" if plusieurs else mesures[0],
            "type": "quantitative",
            "title": y_label,
        },
    }

    champ_couleur = "mesure" if plusieurs else couleur
    if champ_couleur is not None:
        encodage["color"] = {"field": champ_couleur, "type": "nominal", "title": None}

    specification = {
        "mark": {"type": forme, "tooltip": True},
        "encoding": encodage,
    }
    if plusieurs:
        specification["transform"] = [{"fold": mesures, "as": ["mesure", "valeur"]}]

    st.vega_lite_chart(tableau, specification, use_container_width=True)
