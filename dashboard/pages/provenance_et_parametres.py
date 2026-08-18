"""Page de provenance et de paramètres : les trois indicateurs que le registre déclare pour elle.

**Cette page ne décrit pas l'activité du service : elle décrit la chaîne qui produit les chiffres.**
Ses trois grandeurs disent d'où vient ce que le tableau de bord affiche — sur quelle part
d'observation et quelle part d'hypothèse le modèle repose — et ce que valent deux grandeurs
entièrement fixées par des paramètres posés d'avance. Aucune décision de service n'en découle ;
elles servent à savoir ce qu'on lit ailleurs.

Les deux corrélations y sont placées ensemble et dans cet ordre, la comparaison entre activités
d'abord, l'écart interne ensuite : c'est leur juxtaposition qui fait la démonstration, et les
séparer laisserait deux nombres de signes opposés sans explication.

La provenance des champs y siège pour la même raison : elle compte des colonnes du modèle par
origine de définition, non des dossiers de patients.
"""

from __future__ import annotations

import streamlit as st

from dashboard import lecture, rendu

PAGE = "provenance_et_parametres"

PROVENANCES_LISIBLES = {
    "OBS": "Observée — relevée sur le système d'information",
    "DOC": "Documentée — établie par une source écrite",
    "HYP": "Hypothétique — posée faute de source",
}

# L'état des rendez-vous, tel que la couche des faits le porte. La correspondance a été établie en
# confrontant les codes aux colonnes booléennes de la même table, et non supposée.
ETAT_ABSENCE = "CO"

REQUETES = {
    "qualite_provenance_champs": """
        select provenance, nb_colonnes, part_pourcent
        from agg_provenance_champs
        order by provenance
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

# La mention que portent les deux corrélations. Elle reprend ce que le registre des relations
# injectées établit, et rien de plus : c'est lui qui fait foi, la page ne fait que le rendre
# visible là où un lecteur pourrait tirer une conclusion.
MENTION_CIRCULARITE = (
    "**Ces deux grandeurs sont marquées circulaires au registre des relations injectées.** La "
    "première est entièrement fixée par le rangement conjoint de deux tables de paramètres posées "
    "séparément ; la seconde reproduit la pente injectée. Ce que la chaîne démontre est qu'elle "
    "sait produire et distinguer les deux mesures, non ce que vaudrait la relation dans un "
    "établissement réel."
)


def rendre() -> None:
    rendu.en_tete("Provenance et paramètres")
    st.info(
        "Cette page s'adresse à qui veut savoir **ce que vaut ce que le tableau de bord montre** : "
        "sur quelle part d'observation le modèle repose, et quelles grandeurs affichées ailleurs "
        "ne sont que des paramètres rendus visibles. Aucun de ses chiffres ne commande une "
        "décision de service.",
        icon="ℹ️",
    )

    bornes = lecture.interroger(
        "select min(date_rendez_vous) as debut, max(date_rendez_vous) as fin from fct_rendez_vous"
    )
    periode = rendu.filtre_de_page(PAGE, (bornes["debut"][0], bornes["fin"][0]))

    def q(identifiant: str):
        return lecture.interroger(
            REQUETES[identifiant].format(filtre=rendu.clause_periode(identifiant, periode))
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

    rendu.titre_indicateur("rendez_vous_delai_et_absence")
    st.warning(MENTION_CIRCULARITE, icon="⚠️")
    croise = q("rendez_vous_delai_et_absence")
    points = int(croise["points"][0]) if len(croise) else 0
    correlation = croise["correlation"][0] if len(croise) else None
    st.caption(
        f"Corrélation calculée sur **{points} points** — un par code d'activité. "
        "Une corrélation portant sur si peu de points ne se lit pas comme une corrélation portant "
        "sur un grand nombre d'observations : elle indique une tendance, elle ne l'établit pas."
    )
    st.scatter_chart(
        rendu.avec_libelles(rendu.en_nombres(croise, "taux_absence"), "code_activite", "activite"),
        x="mediane_jours",
        y="taux_absence",
        color="code_activite",
        x_label="Délai médian d'obtention (jours)",
        y_label="Taux d'absentéisme",
    )
    st.dataframe(
        rendu.avec_libelles(
            croise[["code_activite", "mediane_jours", "taux_absence"]], "code_activite", "activite"
        ),
        hide_index=True,
    )
    st.caption(
        "Les codes d'activité sont du texte contenant des entiers : ils se trient donc dans "
        "l'ordre lexicographique, où « 4 » vient après « 30 ». Le libellé qui suit chaque code "
        "ne change pas cet ordre, puisque le code reste en tête ; aucun libellé n'est inventé, "
        "chacun vient de la nomenclature nationale des spécialités médicales."
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
        rendu.avec_libelles(
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
            "code_activite",
            "activite",
        ),
        hide_index=True,
    )
    st.bar_chart(
        rendu.avec_libelles(rendu.en_nombres(intra, "ecart_jours"), "code_activite", "activite"),
        x="code_activite",
        y="ecart_jours",
        x_label="Code d'activité",
        y_label="Jours de délai en plus pour les absents",
    )
    rendu.mention_source_libelles("activite")


rendre()
