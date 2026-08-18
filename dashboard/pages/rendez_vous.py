"""Page des rendez-vous : les cinq indicateurs que le registre déclare pour elle.

Chaque requête recalcule depuis la table de faits de l'instantané. Les colonnes booléennes que la
couche intermédiaire a déjà calculées — rendez-vous honoré, absent, annulé — ne sont pas reprises :
les taux se recalculent depuis le code d'état brut, et ces colonnes servent de seconde mesure, ce
qui donne deux chemins réellement distincts plutôt qu'une variante du même.

Les taux se calculent sur le NOMBRE TOTAL de rendez-vous, non sur les seuls rendez-vous résolus.
C'est la convention de la chaîne de transformation, et s'en écarter ici rendrait deux chiffres du
même dépôt incomparables. Sa conséquence est écrite à l'écran : un code d'activité comptant
beaucoup de rendez-vous en instance porte des taux mécaniquement plus bas.

Les codes d'activité sont de type texte et n'ont aucun libellé documenté ; aucun n'est inventé.
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
    # Les deux séries croisées, et leur corrélation calculée par le serveur sur les mêmes points
    # que ceux qui sont tracés — une corrélation calculée sur une autre population que le nuage
    # qu'elle accompagne serait trompeuse.
    "rendez_vous_delai_et_absence": f"""
        with par_activite as (
            select code_activite,
                   percentile_cont(0.5) within group (order by delai_obtention_jours)
                       filter (where delai_obtention_jours > 0) as mediane_jours,
                   count(*) filter (where etat = '{ETAT_ABSENCE}')::numeric
                       / count(*) as taux_absence
            from fct_rendez_vous
            {{filtre}}
            group by code_activite
        )
        select code_activite, mediane_jours, taux_absence,
               count(*) over () as points,
               corr(mediane_jours, taux_absence) over () as correlation
        from par_activite
        where mediane_jours is not null
        order by code_activite
    """,
    # La contrepartie de la précédente, mesurée À L'INTÉRIEUR de chaque activité : deux populations
    # de la même activité comparées entre elles, et non deux activités comparées l'une à l'autre.
    # La population est celle des rendez-vous dont l'issue est connue — honoré ou absence — et dont
    # le délai est strictement positif : un rendez-vous pris pour le jour même porte un délai nul
    # par construction, et l'inclure ferait comparer une décision de construction à un tirage.
    "rendez_vous_delai_et_absence_intra_activite": """
        with retenus as (
            select code_activite, delai_obtention_jours as delai, est_honore, est_absence
            from fct_rendez_vous
            {filtre}
        )
        select code_activite,
               count(*) filter (where est_honore)  as n_honores,
               count(*) filter (where est_absence) as n_absences,
               percentile_cont(0.5) within group (order by delai)
                   filter (where est_honore  and delai > 0) as mediane_honores,
               percentile_cont(0.5) within group (order by delai)
                   filter (where est_absence and delai > 0) as mediane_absences
        from retenus
        group by code_activite
        order by code_activite
    """,
}


# Cette requête n'est PAS une entrée de `REQUETES` : ce dictionnaire associe un identifiant
# d'indicateur à sa requête, et un contrôle vérifie cette correspondance dans les deux sens.
# La forme agrégée résume la MÊME grandeur que `rendez_vous_delai_et_absence_intra_activite`,
# sur toutes les activités à la fois ; lui ouvrir une entrée au registre créerait une seconde
# définition pour un seul indicateur affiché.
#
# L'activité est retirée des deux grandeurs par CENTRAGE — chaque valeur moins la moyenne de son
# activité — de sorte que ce qui reste soit la relation interne aux activités, débarrassée du
# rangement des activités entre elles. La corrélation brute est rendue à côté, sur les mêmes
# lignes, pour que l'écart entre les deux se lise. Jointure à un agrégat, aucune sous-requête
# corrélée.
REQUETE_INTRA_AGREGEE = """
    with retenus as (
        select code_activite, delai_obtention_jours as delai, est_honore, est_absence
        from fct_rendez_vous
        {filtre}
    ),
    population as (
        select code_activite, delai,
               case when est_absence then 1.0 else 0.0 end as absence
        from retenus
        where (est_honore or est_absence) and delai > 0
    ),
    moyennes as (
        select code_activite, avg(delai) as m_delai, avg(absence) as m_absence
        from population
        group by code_activite
    )
    select count(*) as n_rendez_vous,
           corr(p.delai - m.m_delai, p.absence - m.m_absence) as correlation_intra,
           corr(p.delai, p.absence) as correlation_brute
    from population p
    join moyennes m using (code_activite)
"""


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
    st.dataframe(delais, hide_index=True)
    st.bar_chart(
        delais,
        x="code_activite",
        y=["mediane_jours", "p90_jours"],
        x_label="Code d'activité",
        y_label="Jours",
    )

    rendu.titre_indicateur("rendez_vous_part_jour_meme")
    jour_meme = q("rendez_vous_part_jour_meme")
    st.bar_chart(
        rendu.en_nombres(jour_meme, "part_jour_meme"),
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
            rendu.en_nombres(absences, "taux_absence"),
            x="code_activite",
            y="taux_absence",
            x_label="Code d'activité",
            y_label="Taux d'absentéisme",
        )
    with droite:
        rendu.titre_indicateur("rendez_vous_taux_annulation")
        annulations = q("rendez_vous_taux_annulation")
        st.bar_chart(
            rendu.en_nombres(annulations, "taux_annulation"),
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

    rendu.titre_indicateur("rendez_vous_delai_et_absence")
    croise = q("rendez_vous_delai_et_absence")
    points = int(croise["points"][0]) if len(croise) else 0
    correlation = croise["correlation"][0] if len(croise) else None
    st.caption(
        f"Corrélation calculée sur **{points} points** — un par code d'activité. "
        "Une corrélation portant sur si peu de points ne se lit pas comme une corrélation portant "
        "sur un grand nombre d'observations : elle indique une tendance, elle ne l'établit pas."
    )
    st.scatter_chart(
        rendu.en_nombres(croise, "taux_absence"),
        x="mediane_jours",
        y="taux_absence",
        color="code_activite",
        x_label="Délai médian d'obtention (jours)",
        y_label="Taux d'absentéisme",
    )
    st.dataframe(croise[["code_activite", "mediane_jours", "taux_absence"]], hide_index=True)
    st.caption(
        "Les codes d'activité sont du texte contenant des entiers : ils se trient donc dans "
        "l'ordre lexicographique, où « 4 » vient après « 30 ». Aucun libellé n'est documenté pour "
        "ces codes, et aucun n'est inventé ici."
    )

    rendu.titre_indicateur("rendez_vous_delai_et_absence_intra_activite")
    intra = q("rendez_vous_delai_et_absence_intra_activite")
    # La forme agrégée n'est pas un second indicateur : c'est la même grandeur, résumée sur toutes
    # les activités à la fois. Elle emprunte donc la clause de période de l'indicateur déclaré,
    # plutôt que d'ouvrir une entrée au registre qui serait une définition sans indicateur.
    agrege = lecture.interroger(
        REQUETE_INTRA_AGREGEE.format(
            filtre=rendu.clause_periode("rendez_vous_delai_et_absence_intra_activite", periode)
        )
    )
    intra = intra.assign(ecart_jours=intra["mediane_absences"] - intra["mediane_honores"])

    correlation_intra = agrege["correlation_intra"][0] if len(agrege) else None
    correlation_brute = agrege["correlation_brute"][0] if len(agrege) else None
    observations = int(agrege["n_rendez_vous"][0]) if len(agrege) else 0

    # Les deux grandeurs côte à côte, avec leurs deux signes. Elles sont volontairement placées
    # dans la même rangée : lues séparément, deux nombres de signes opposés se lisent comme une
    # contradiction ; lues ensemble sous la phrase qui suit, comme deux mesures distinctes.
    gauche, milieu, droite = st.columns(3)
    with gauche:
        st.metric(
            "Entre activités, sur 8 points",
            f"{float(correlation):.3f}" if correlation is not None else "—",
        )
    with milieu:
        # L'espace fine des milliers est posée sur le seul nombre : appliquer le remplacement à
        # l'ensemble du libellé effacerait aussi la virgule de la phrase.
        effectif = f"{observations:,}".replace(",", " ")
        st.metric(
            f"À l'intérieur des activités, sur {effectif} rendez-vous",
            f"{float(correlation_intra):+.3f}" if correlation_intra is not None else "—",
        )
    with droite:
        st.metric(
            "Sans distinguer les activités",
            f"{float(correlation_brute):+.3f}" if correlation_brute is not None else "—",
        )

    st.caption(
        "**Les deux premières grandeurs sont de signes opposés, et ce n'est pas une erreur : elles "
        "ne comparent pas les mêmes choses.** La première compare LES ACTIVITÉS ENTRE ELLES — huit "
        "points, un par activité — et dit que les activités aux délais les plus longs sont celles "
        "dont le taux d'absentéisme est le plus bas. La seconde compare, À L'INTÉRIEUR DE CHAQUE "
        "ACTIVITÉ, les rendez-vous manqués aux rendez-vous honorés, et dit qu'à activité donnée un "
        "rendez-vous obtenu de longue date est plus souvent manqué. Une grandeur peut décroître "
        "entre les groupes et croître à l'intérieur de chacun : c'est un effet de composition, et "
        "la troisième valeur le montre — sans distinguer les activités, la relation interne est "
        "presque entièrement effacée par le rangement des activités."
    )

    st.dataframe(
        intra[
            [
                "code_activite",
                "n_honores",
                "n_absences",
                "mediane_honores",
                "mediane_absences",
                "ecart_jours",
            ]
        ],
        hide_index=True,
    )
    st.bar_chart(
        rendu.en_nombres(intra, "ecart_jours"),
        x="code_activite",
        y="ecart_jours",
        x_label="Code d'activité",
        y_label="Jours de délai en plus pour les absents",
    )


rendre()
