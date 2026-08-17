"""Page des urgences : les cinq indicateurs que le registre déclare pour elle.

La part relevant d'une consultation ordinaire est le point sensible de cette page. Plusieurs
définitions opérationnelles sont concevables — par niveau de tri, par orientation de sortie, par
durée de passage — et elles ne donnent pas le même chiffre, l'éventail ayant été mesuré à un
facteur proche de cinq. Un tel chiffre affiché sans sa définition serait ininterprétable, et
indéfendable devant quiconque en tirerait une conclusion. La définition retenue est donc celle que
le registre porte, affichée à côté de la valeur, et elle n'est pas réécrite ici.

Les niveaux de tri sont du texte ; aucun libellé n'est documenté pour eux et aucun n'est inventé.
Le tri se fait sur la valeur textuelle, qui est ici l'ordre numérique parce que tous les niveaux
tiennent sur un seul caractère.
"""

from __future__ import annotations

import streamlit as st

from dashboard import lecture, rendu

PAGE = "urgences"

# Les deux niveaux de tri les moins graves, au sens du registre. La liste est établie depuis les
# valeurs présentes, et non écrite : les deux derniers niveaux dans l'ordre croissant.
NIVEAUX_MOINS_GRAVES = 2

REQUETES = {
    "urgences_passages_par_niveau": """
        select date_arrivee as jour, niveau_tri, count(*) as passages
        from fct_passage_urgence
        {filtre}
        group by date_arrivee, niveau_tri
        order by date_arrivee, niveau_tri
    """,
    "urgences_delai_prise_en_charge": """
        select niveau_tri,
               count(*) as passages,
               count(delai_pec_minutes) as avec_delai,
               percentile_cont(0.5) within group (order by delai_pec_minutes) as mediane_minutes,
               percentile_cont(0.9) within group (order by delai_pec_minutes) as p90_minutes
        from fct_passage_urgence
        {filtre}
        group by niveau_tri
        order by niveau_tri
    """,
    "urgences_orientation_sortie": """
        select orientation_sortie,
               count(*) as passages,
               count(*)::numeric / sum(count(*)) over () as part
        from fct_passage_urgence
        {filtre}
        group by orientation_sortie
        order by orientation_sortie
    """,
    # La population est définie par le NIVEAU DE TRI seul, quelle que soit l'orientation de sortie,
    # conformément à la définition que le registre porte.
    "urgences_consultation_ordinaire": f"""
        with niveaux as (
            select distinct niveau_tri from fct_passage_urgence where niveau_tri is not null
        ),
        moins_graves as (
            select niveau_tri from niveaux order by niveau_tri desc limit {NIVEAUX_MOINS_GRAVES}
        )
        select count(*) as passages,
               count(*) filter (where niveau_tri in (select niveau_tri from moins_graves))
                   as relevant_consultation,
               count(*) filter (where niveau_tri in (select niveau_tri from moins_graves))::numeric
                   / count(*) as part,
               (select string_agg(niveau_tri, ', ' order by niveau_tri) from moins_graves)
                   as niveaux_retenus
        from fct_passage_urgence
        {{filtre}}
    """,
    "urgences_duree_passage": """
        select niveau_tri,
               count(*) as passages,
               percentile_cont(0.5) within group (order by duree_minutes) as mediane_minutes,
               percentile_cont(0.9) within group (order by duree_minutes) as p90_minutes
        from fct_passage_urgence
        {filtre}
        group by niveau_tri
        order by niveau_tri
    """,
}


def rendre() -> None:
    rendu.en_tete("Urgences")
    bornes = lecture.interroger(
        "select min(date_arrivee) as debut, max(date_arrivee) as fin from fct_passage_urgence"
    )
    periode = rendu.filtre_de_page(PAGE, (bornes["debut"][0], bornes["fin"][0]))

    def q(identifiant: str):
        return lecture.interroger(
            REQUETES[identifiant].format(filtre=rendu.clause_periode(identifiant, periode))
        )

    rendu.titre_indicateur("urgences_passages_par_niveau")
    passages = q("urgences_passages_par_niveau")
    st.line_chart(
        passages,
        x="jour",
        y="passages",
        color="niveau_tri",
        x_label="Jour",
        y_label="Passages",
    )
    totaux = (
        passages.groupby("niveau_tri", as_index=False)["passages"].sum().sort_values("niveau_tri")
    )
    st.dataframe(totaux, hide_index=True)

    rendu.titre_indicateur("urgences_delai_prise_en_charge")
    delais = q("urgences_delai_prise_en_charge")
    st.caption(
        "Médiane et 90ᵉ centile sont affichés ensemble : la médiane seule masquerait la queue de "
        "distribution, qui est ce qui se voit en salle d'attente."
    )
    st.dataframe(delais, hide_index=True)
    st.bar_chart(
        delais,
        x="niveau_tri",
        y=["mediane_minutes", "p90_minutes"],
        x_label="Niveau de tri",
        y_label="Minutes",
    )

    rendu.titre_indicateur("urgences_orientation_sortie")
    orientation = q("urgences_orientation_sortie")
    st.bar_chart(
        orientation,
        x="orientation_sortie",
        y="passages",
        x_label="Orientation de sortie",
        y_label="Passages",
    )
    st.dataframe(orientation, hide_index=True)
    st.caption(
        "Les codes d'orientation sont affichés tels quels : aucun libellé n'est documenté pour "
        "eux, et aucun n'est inventé ici."
    )

    rendu.titre_indicateur("urgences_consultation_ordinaire")
    ordinaire = q("urgences_consultation_ordinaire")
    part = float(ordinaire["part"][0])
    st.metric("Part relevant d'une consultation ordinaire", f"{100 * part:.1f} %".replace(".", ","))
    st.caption(
        f"Définition opérationnelle retenue : les passages classés aux niveaux de tri "
        f"**{ordinaire['niveaux_retenus'][0]}**, soit les {NIVEAUX_MOINS_GRAVES} niveaux les moins "
        f"graves, quelle que soit leur orientation de sortie — "
        f"{int(ordinaire['relevant_consultation'][0])} passages sur "
        f"{int(ordinaire['passages'][0])}. D'autres définitions sont concevables et ne donnent pas "
        "le même chiffre ; celle-ci est celle que porte le registre des indicateurs."
    )

    rendu.titre_indicateur("urgences_duree_passage")
    durees = q("urgences_duree_passage")
    st.dataframe(durees, hide_index=True)
    st.bar_chart(
        durees,
        x="niveau_tri",
        y=["mediane_minutes", "p90_minutes"],
        x_label="Niveau de tri",
        y_label="Minutes",
    )


rendre()
