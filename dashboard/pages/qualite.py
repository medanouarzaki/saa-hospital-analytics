"""Page de qualité : les trois indicateurs que le registre déclare pour elle.

**Aucun de ses indicateurs ne répond au filtre de période**, et la page n'en porte donc pas : elle
affiche à la place le motif que le registre donne. C'est la première page dans ce cas.

Aucun des trois n'est recalculé depuis les tables de faits — deux lisent la couche intermédiaire,
le troisième le catalogue des colonnes — et chacun l'affiche.

Les taux de mise en quarantaine sont affichés **avec leurs effectifs bruts en regard** : deux rejets
sur quarante et deux mille sur quarante mille donnent le même taux et n'appellent pas la même
décision.

La complétude porte sur cent soixante-quinze couples table-colonne, ce qui est trop pour une liste
lisible. La présentation retenue part de la distribution mesurée plutôt que d'un seuil écrit
d'avance : les couples parfaitement renseignés sont comptés, et seuls les autres sont détaillés.
C'est la mesure qui commande la présentation — cent trente-deux couples sur cent soixante-quinze
sont à cent pour cent, et les énumérer n'apprendrait rien.
"""

from __future__ import annotations

import streamlit as st

from dashboard import lecture, rendu

PAGE = "qualite"

PROVENANCES_LISIBLES = {
    "OBS": "Observée — relevée sur le système d'information",
    "DOC": "Documentée — établie par une source écrite",
    "HYP": "Hypothétique — posée faute de source",
}

REQUETES = {
    # La distribution d'abord : elle dit combien de couples sont parfaitement renseignés, et donc
    # combien méritent d'être détaillés. Aucun seuil n'est écrit ; le partage se fait sur la valeur
    # extrême que la complétude peut atteindre.
    "qualite_completude_champs": """
        select count(*) as couples_examines,
               count(*) filter (where taux_completude >= 1) as couples_complets,
               count(*) filter (where taux_completude < 1) as couples_incomplets,
               min(taux_completude) as taux_minimal,
               percentile_cont(0.5) within group (order by taux_completude) as taux_median,
               count(distinct nom_table) as tables_examinees
        from agg_qualite_donnees
    """,
    "qualite_taux_quarantaine": """
        select nom_table,
               max(lignes_examinees) as lignes_examinees,
               max(lignes_quarantaine) as lignes_quarantaine,
               max(taux_quarantaine) as taux_quarantaine
        from agg_qualite_donnees
        group by nom_table
        order by nom_table
    """,
    "qualite_provenance_champs": """
        select provenance, nb_colonnes, part_pourcent
        from agg_provenance_champs
        order by provenance
    """,
}

# Le détail des couples incomplets. Ce n'est pas un indicateur du registre mais la seconde moitié
# de l'affichage du premier : le dictionnaire ci-dessus n'est indexé que par des identifiants du
# registre, et un contrôle vérifie qu'il ne contient rien d'autre.
REQUETE_COMPLETUDE_DETAIL = """
    select nom_table, colonne, lignes_examinees, valeurs_renseignees, taux_completude
    from agg_qualite_donnees
    where taux_completude < 1
    order by taux_completude, nom_table, colonne
"""


def _pourcentage(valeur) -> str:
    return f"{100 * float(valeur):.2f} %".replace(".", ",")


def rendre() -> None:
    rendu.en_tete("Qualité des données")
    rendu.filtre_de_page(PAGE)

    rendu.titre_indicateur("qualite_completude_champs")
    resume = lecture.interroger(REQUETES["qualite_completude_champs"]).iloc[0]
    colonnes = st.columns(4)
    with colonnes[0]:
        st.metric("Couples table-colonne", f"{int(resume['couples_examines'])}")
    with colonnes[1]:
        st.metric("Tables examinées", f"{int(resume['tables_examinees'])}")
    with colonnes[2]:
        st.metric("Entièrement renseignés", f"{int(resume['couples_complets'])}")
    with colonnes[3]:
        st.metric("Partiellement renseignés", f"{int(resume['couples_incomplets'])}")
    st.caption(
        f"Sur {int(resume['couples_examines'])} couples table-colonne, "
        f"{int(resume['couples_complets'])} sont renseignés à 100 %. Les énumérer n'apprendrait "
        f"rien ; seuls les {int(resume['couples_incomplets'])} autres sont détaillés ci-dessous, "
        f"du moins renseigné au plus renseigné. Le taux le plus bas observé est "
        f"{_pourcentage(resume['taux_minimal'])}."
    )
    st.dataframe(lecture.interroger(REQUETE_COMPLETUDE_DETAIL), hide_index=True)

    rendu.titre_indicateur("qualite_taux_quarantaine")
    quarantaine = lecture.interroger(REQUETES["qualite_taux_quarantaine"])
    st.caption(
        "Les effectifs bruts sont affichés en regard des taux : deux rejets sur quarante et deux "
        "mille sur quarante mille donnent le même taux et n'appellent pas la même décision."
    )
    st.dataframe(quarantaine, hide_index=True)
    st.bar_chart(
        rendu.en_nombres(quarantaine, "taux_quarantaine"),
        x="nom_table",
        y="lignes_quarantaine",
        x_label="Table",
        y_label="Lignes mises en quarantaine",
    )

    rendu.titre_indicateur("qualite_provenance_champs")
    provenance = lecture.interroger(REQUETES["qualite_provenance_champs"])
    provenance = provenance.assign(
        libelle=provenance["provenance"].map(lambda code: PROVENANCES_LISIBLES.get(code, code))
    )
    st.bar_chart(
        rendu.en_nombres(provenance, "part_pourcent"),
        x="libelle",
        y="nb_colonnes",
        x_label="Provenance de la définition",
        y_label="Colonnes",
    )
    st.dataframe(provenance, hide_index=True)


rendre()
