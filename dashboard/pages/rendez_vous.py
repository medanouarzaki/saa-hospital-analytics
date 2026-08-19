"""Page des rendez-vous : les quatre indicateurs que le registre déclare pour elle.

Chaque requête recalcule depuis la table de faits de l'instantané. Les colonnes booléennes que la
couche intermédiaire a déjà calculées — rendez-vous honoré, absent, annulé — ne sont pas reprises :
les taux se recalculent depuis le code d'état brut, et ces colonnes servent de seconde mesure, ce
qui donne deux chemins réellement distincts plutôt qu'une variante du même.

Les taux se calculent sur le NOMBRE TOTAL de rendez-vous, non sur les seuls rendez-vous résolus.
C'est la convention de la chaîne de transformation, et s'en écarter ici rendrait deux chiffres du
même dépôt incomparables. Sa conséquence est écrite à l'écran : un code d'activité comptant
beaucoup de rendez-vous en instance porte des taux mécaniquement plus bas.

Les codes d'activité sont de type texte. Chacun porte désormais le libellé que la nomenclature
nationale des spécialités médicales lui donne, le code restant en tête : il conserve l'ordre de
tri des axes, qui est lexicographique, et le lien avec les exports, où seul le code figure.
"""

from __future__ import annotations

import streamlit as st

from dashboard import lecture, rendu

PAGE = "rendez_vous"

# L'état des rendez-vous, tel que la couche des faits le porte. La correspondance a été établie en
# confrontant les codes aux colonnes booléennes de la même table, et non supposée.
ETAT_ANNULE = "AN"
ETAT_ABSENCE = "CO"

REQUETES = {
    # Le délai porte sur les rendez-vous obtenus pour un autre jour que celui de la prise : un
    # rendez-vous du jour même a un délai nul par construction et écraserait la médiane. C'est la
    # même population que celle de l'agrégat correspondant, ce qui rend les deux comparables.
    "rendez_vous_delai_obtention": """
        select code_activite,
               count(*) as rendez_vous,
               count(*) filter (where delai_obtention_jours > 0) as avec_delai,
               percentile_cont(0.5) within group (order by delai_obtention_jours)
                   filter (where delai_obtention_jours > 0) as mediane_jours,
               percentile_cont(0.9) within group (order by delai_obtention_jours)
                   filter (where delai_obtention_jours > 0) as p90_jours
        from fct_rendez_vous
        {filtre}
        group by code_activite
        order by code_activite
    """,
    "rendez_vous_part_jour_meme": """
        select code_activite,
               count(*) as rendez_vous,
               count(*) filter (where date_prise = date_rendez_vous) as jour_meme,
               count(*) filter (where date_prise = date_rendez_vous)::numeric
                   / count(*) as part_jour_meme
        from fct_rendez_vous
        {filtre}
        group by code_activite
        order by code_activite
    """,
    "rendez_vous_taux_absence": f"""
        select code_activite,
               count(*) as rendez_vous,
               count(*) filter (where etat = '{ETAT_ABSENCE}') as absences,
               count(*) filter (where etat = '{ETAT_ABSENCE}')::numeric
                   / count(*) as taux_absence
        from fct_rendez_vous
        {{filtre}}
        group by code_activite
        order by code_activite
    """,
    "rendez_vous_taux_annulation": f"""
        select code_activite,
               count(*) as rendez_vous,
               count(*) filter (where etat = '{ETAT_ANNULE}') as annulations,
               count(*) filter (where etat = '{ETAT_ANNULE}')::numeric
                   / count(*) as taux_annulation
        from fct_rendez_vous
        {{filtre}}
        group by code_activite
        order by code_activite
    """,
}


def rendre() -> None:
    rendu.en_tete("Rendez-vous")
    bornes = lecture.interroger(
        "select min(date_rendez_vous) as debut, max(date_rendez_vous) as fin from fct_rendez_vous"
    )
    periode = rendu.filtre_de_page(PAGE, (bornes["debut"][0], bornes["fin"][0]))

    def q(identifiant: str):
        return lecture.interroger(
            REQUETES[identifiant].format(filtre=rendu.clause_periode(identifiant, periode))
        )

    rendu.titre_indicateur("rendez_vous_delai_obtention")
    delais = q("rendez_vous_delai_obtention")
    st.caption(
        "Les rendez-vous obtenus pour le jour même sont exclus du délai : leur délai est nul par "
        "construction. La médiane seule masquerait la queue de distribution, qui commande le "
        "dimensionnement ; le 90ᵉ centile est donc affiché à côté."
    )
    st.dataframe(rendu.avec_libelles(delais, "code_activite", "activite"), hide_index=True)
    st.bar_chart(
        rendu.avec_libelles(delais, "code_activite", "activite"),
        x="code_activite",
        y=["mediane_jours", "p90_jours"],
        x_label="Code d'activité",
        y_label="Jours",
    )

    rendu.titre_indicateur("rendez_vous_part_jour_meme")
    jour_meme = q("rendez_vous_part_jour_meme")
    st.bar_chart(
        rendu.avec_libelles(
            rendu.en_nombres(jour_meme, "part_jour_meme"), "code_activite", "activite"
        ),
        x="code_activite",
        y="part_jour_meme",
        x_label="Code d'activité",
        y_label="Part des rendez-vous du jour même",
    )

    gauche, droite = st.columns(2)
    with gauche:
        rendu.titre_indicateur("rendez_vous_taux_absence")
        absences = q("rendez_vous_taux_absence")
        st.bar_chart(
            rendu.avec_libelles(
                rendu.en_nombres(absences, "taux_absence"), "code_activite", "activite"
            ),
            x="code_activite",
            y="taux_absence",
            x_label="Code d'activité",
            y_label="Taux d'absentéisme",
        )
    with droite:
        rendu.titre_indicateur("rendez_vous_taux_annulation")
        annulations = q("rendez_vous_taux_annulation")
        st.bar_chart(
            rendu.avec_libelles(
                rendu.en_nombres(annulations, "taux_annulation"), "code_activite", "activite"
            ),
            x="code_activite",
            y="taux_annulation",
            x_label="Code d'activité",
            y_label="Taux d'annulation",
        )
    st.caption(
        "Les deux taux se calculent sur le nombre total de rendez-vous, en instance compris : un "
        "code d'activité comptant beaucoup de rendez-vous en instance porte donc des taux "
        "mécaniquement plus bas."
    )

    st.caption(
        "**Le croisement du délai et de l'absentéisme n'est plus sur cette page.** Les deux "
        "grandeurs — la comparaison des activités entre elles et l'écart mesuré à l'intérieur de "
        "chacune — sont des paramètres du modèle rendus visibles, et non des mesures de "
        "l'activité : elles siègent désormais page [Provenance et paramètres]"
        "(/provenance-et-parametres), sous « Évaluation de la chaîne »."
    )
    rendu.mention_source_libelles("activite")


rendre()
