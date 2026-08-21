"""Page « Données » : les lignes derrière les chiffres.

POURQUOI CETTE PAGE EXISTE. Les autres pages répondent à « combien » ; aucune ne répond à
« lesquels ». Un responsable qui lit qu'une part des passages aux urgences n'est pas facturée a
besoin, pour agir, de la liste de ces passages — et le seul chemin vers les lignes était jusqu'ici
le classeur produit par le graphe quotidien, qui n'est ni filtrable ni consultable à l'écran.

CE QU'ELLE MONTRE. Quatre tables de faits, choisies sur l'usage et non sur la curiosité : celles
qu'on consulte pour agir. Les agrégats en sont exclus — les autres pages les portent déjà — et
la dimension des patients aussi : la consulter ligne à ligne n'appelle aucune action, et l'exposer
en bloc n'est pas ce qu'un tableau de bord de pilotage a à faire.

CE QU'ELLE NE MONTRE PAS EN SILENCE. Le plus gros objet retenu porte plus de vingt-sept mille
lignes. La page en affiche au plus `PLAFOND_AFFICHAGE`, **le dit à l'écran**, et donne le décompte
complet de ce que le filtre retient AVANT le tableau : une page qui tronque sans le dire ment.

CE QUE LES FILTRES FONT. Chaque filtre porte une restriction réelle dans la requête, et la page
déclare, table par table, quelle colonne il vise. **Un filtre qui ne s'applique pas à la table
choisie est désactivé et le dit** : c'est la seule façon de ne pas reproduire le défaut d'un
indicateur annonçant une restriction qu'il n'appliquait pas.

LES LIBELLÉS. Là où le registre des libellés documente un code, il s'affiche avec son libellé par le
mécanisme partagé ; là où il ne le documente pas, le code reste nu. Rien n'est réinventé ici.
"""

from __future__ import annotations

import csv
import io

import streamlit as st

from dashboard import lecture, rendu

PAGE = "donnees"

# Le plafond d'affichage, dérivé et non choisi. Mesures : le plus gros tableau que le tableau de
# bord pousse déjà est l'activité journalière, 13 855 lignes pour 801 248 octets une fois
# sérialisée ; la plus large des tables retenues ici, la facturation et ses dix-sept colonnes,
# pèse 219 104 octets
# à mille lignes, soit 27 % de ce que la page la plus lourde pousse déjà. Au-delà, le poids croît
# linéairement — 647 744 octets à trois mille lignes — sans que la lisibilité y gagne : personne ne
# parcourt trois mille lignes à l'écran, on filtre.
PLAFOND_AFFICHAGE = 1000

# Une table par entrée : son libellé, l'objet lu, la colonne de date qui porte le filtre de période,
# la colonne de service et la colonne d'activité — `None` quand la table n'en porte pas, ce que la
# page affiche plutôt que de le taire. `dimension_service` et `dimension_activite` nomment l'entrée
# du registre des libellés à employer pour ces colonnes.
TABLES = {
    "Passages aux urgences": {
        "objet": "fct_passage_urgence",
        "colonne_date": "date_arrivee",
        "colonne_service": "code_service_orientation",
        "colonne_activite": None,
        "dimension_service": "service",
        "usage": "savoir quels passages ont été orientés où, et lesquels n'ont pas abouti",
    },
    "Factures": {
        "objet": "fct_facturation",
        "colonne_date": "date_facture",
        "colonne_service": "service_emetteur",
        "colonne_activite": None,
        "dimension_service": "service",
        "usage": "retrouver les factures d'un service sur une période, et leur état",
    },
    "Rendez-vous": {
        "objet": "fct_rendez_vous",
        "colonne_date": "date_rendez_vous",
        "colonne_service": None,
        "colonne_activite": "code_activite",
        "dimension_activite": "activite",
        "usage": "lister les rendez-vous manqués d'une activité pour rappeler les patients",
    },
    "Séjours": {
        "objet": "fct_sejour",
        "colonne_date": "jour_admission",
        "colonne_service": "service_accueil",
        "colonne_activite": None,
        "dimension_service": "service",
        "usage": "retrouver les séjours d'un service, et ceux qui ne sont pas clos",
    },
}

MENTION_TRONCATURE = (
    "Le tableau ci-dessous n'affiche que les **{plafond} premières lignes** de la sélection. "
    "Le décompte au-dessus porte, lui, sur **la totalité** de ce que le filtre retient : pour voir "
    "les autres lignes, resserrez la période, le service ou l'activité jusqu'à passer sous ce "
    "plafond — ou téléchargez la sélection, qui n'est pas tronquée."
)


def _espace(nombre: int) -> str:
    """Un nombre avec ses séparateurs de milliers, sans toucher au reste de la phrase."""
    return f"{nombre:,}".replace(",", " ")


def _bornes(objet: str, colonne_date: str) -> tuple:
    """Les bornes de période viennent des données, jamais d'une constante."""
    bornes = lecture.interroger(
        f"select min({colonne_date}) as debut, max({colonne_date}) as fin from {objet}"
    )
    return bornes["debut"][0], bornes["fin"][0]


def _valeurs_distinctes(objet: str, colonne: str) -> list[str]:
    tableau = lecture.interroger(
        f"select distinct {colonne} as valeur from {objet} "
        f"where {colonne} is not null order by {colonne}"
    )
    return [str(valeur) for valeur in tableau["valeur"]]


def _clause(configuration: dict, periode, service, activite) -> str:
    """La clause de restriction, construite des seuls filtres qui portent sur une colonne réelle.

    Un filtre dont la table ne porte pas la colonne ne produit AUCUNE clause, et la page a déjà dit
    à l'écran qu'il ne s'applique pas. C'est la même source pour les deux : ce qui est affiché et ce
    qui restreint ne peuvent pas diverger.
    """
    conditions = []
    debut, fin = periode
    conditions.append(
        f"{configuration['colonne_date']} between date '{debut:%Y-%m-%d}' and date '{fin:%Y-%m-%d}'"
    )
    if configuration["colonne_service"] and service:
        valeurs = ", ".join(f"'{valeur}'" for valeur in service)
        conditions.append(f"{configuration['colonne_service']} in ({valeurs})")
    if configuration["colonne_activite"] and activite:
        valeurs = ", ".join(f"'{valeur}'" for valeur in activite)
        conditions.append(f"{configuration['colonne_activite']} in ({valeurs})")
    return "where " + " and ".join(conditions)


def _en_csv(tableau) -> bytes:
    """Le format et l'encodage sont ceux des fichiers tabulaires du graphe, lus dans son module
    d'export et non redécidés ici : séparateur virgule, encodage universel avec marque d'ordre
    d'octets pour qu'un tableur ouvrant le fichier par double-clic n'abîme pas les accents."""
    tampon = io.StringIO(newline="")
    plume = csv.writer(tampon, delimiter=",")
    plume.writerow(list(tableau.columns))
    for ligne in tableau.itertuples(index=False):
        plume.writerow(["" if valeur is None else valeur for valeur in ligne])
    return tampon.getvalue().encode("utf-8-sig")


def rendre() -> None:
    rendu.en_tete("Données")

    st.caption(
        "Les autres pages répondent à « combien » ; celle-ci répond à « lesquels ». Elle "
        "donne les lignes derrière les chiffres, filtrables et téléchargeables."
    )

    nom_table = st.selectbox("Table à consulter", list(TABLES), index=0)
    configuration = TABLES[nom_table]
    objet = configuration["objet"]
    st.caption(f"Consultée pour : {configuration['usage']}.")

    rendu.titre_indicateur("donnees_lignes_filtrees")

    debut, fin = _bornes(objet, configuration["colonne_date"])
    colonnes_filtres = st.columns(3)

    with colonnes_filtres[0]:
        choix = st.date_input(
            "Période observée",
            value=(debut, fin),
            min_value=debut,
            max_value=fin,
            help=f"Restreint sur la colonne « {configuration['colonne_date']} ».",
        )
        periode = choix if isinstance(choix, tuple) and len(choix) == 2 else (debut, fin)

    with colonnes_filtres[1]:
        if configuration["colonne_service"]:
            codes = _valeurs_distinctes(objet, configuration["colonne_service"])
            service = st.multiselect(
                "Service",
                codes,
                format_func=lambda code: rendu.libelle_dimension(
                    configuration["dimension_service"], code
                ),
                help=f"Restreint sur la colonne « {configuration['colonne_service']} ».",
            )
        else:
            service = []
            st.multiselect(
                "Service", [], disabled=True, help="Cette table ne porte aucune colonne de service."
            )
            st.caption("↪ Sans effet ici : la table ne porte aucune colonne de service.")

    with colonnes_filtres[2]:
        if configuration["colonne_activite"]:
            codes = _valeurs_distinctes(objet, configuration["colonne_activite"])
            activite = st.multiselect(
                "Activité",
                codes,
                format_func=lambda code: rendu.libelle_dimension(
                    configuration["dimension_activite"], code
                ),
                help=f"Restreint sur la colonne « {configuration['colonne_activite']} ».",
            )
        else:
            activite = []
            st.multiselect(
                "Activité",
                [],
                disabled=True,
                help="Cette table ne porte aucune colonne d'activité.",
            )
            st.caption("↪ Sans effet ici : la table ne porte aucune colonne d'activité.")

    clause = _clause(configuration, periode, service, activite)

    retenues = int(lecture.interroger(f"select count(*) as n from {objet} {clause}")["n"][0])
    total = int(lecture.interroger(f"select count(*) as n from {objet}")["n"][0])
    st.metric("Lignes retenues par le filtre", _espace(retenues))
    st.caption(f"Sur {_espace(total)} lignes que porte la table entière.")

    lignes = lecture.interroger(f"select * from {objet} {clause} limit {PLAFOND_AFFICHAGE}")
    for colonne, dimension in (
        (configuration["colonne_service"], configuration.get("dimension_service")),
        (configuration["colonne_activite"], configuration.get("dimension_activite")),
    ):
        if colonne and dimension:
            lignes = rendu.avec_libelles(lignes, colonne, dimension)

    if retenues > PLAFOND_AFFICHAGE:
        st.warning(MENTION_TRONCATURE.format(plafond=PLAFOND_AFFICHAGE), icon="⚠️")
    st.dataframe(lignes, hide_index=True)

    if configuration["colonne_activite"]:
        rendu.mention_source_libelles(configuration["dimension_activite"])

    rendu.titre_indicateur("donnees_export_selection")
    complet = lecture.interroger(f"select * from {objet} {clause}")
    st.download_button(
        "Télécharger la sélection",
        data=_en_csv(complet),
        file_name=f"{objet}_{periode[0]:%Y-%m-%d}_{periode[1]:%Y-%m-%d}.csv",
        mime="text/csv",
        help="Séparateur virgule, encodage universel — le format des fichiers du livrable.",
    )
    # Les séparateurs de milliers sont posés sur les nombres seuls : appliquer le remplacement à
    # la phrase entière effacerait aussi ses virgules de ponctuation — mesuré à l'écran.
    st.caption(
        f"Le fichier porte **la totalité des {_espace(retenues)} lignes retenues**, et non les "
        f"{_espace(min(retenues, PLAFOND_AFFICHAGE))} affichées ci-dessus. C'est une extraction "
        "ponctuelle de ce qui est à l'écran : elle ne remplace pas le livrable complet que le "
        "graphe quotidien produit, qui porte toutes les tables sans filtre."
    )


rendre()
