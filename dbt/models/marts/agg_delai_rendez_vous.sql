{#
    Une ligne par code d'activité, agrégée depuis fct_rendez_vous.

    Population de référence pour la comparaison au paramètre de configuration
    (delai_rdv_par_specialite) : les rendez-vous à délai STRICTEMENT POSITIF, pas
    l'ensemble des rendez-vous. Le générateur court-circuite le tirage de la loi
    log-normale pour les rendez-vous pris le jour même (delai_obtention_jours = 0,
    est_jour_meme) : ce sont des délais nuls par décision de construction, pas des
    tirages de la loi -- les mélanger à la population de comparaison biaiserait la
    médiane observée vers le bas sans rapport avec le paramètre lui-même. Les deux
    catégories (jour même, délai positif) sont exhaustives et disjointes sur
    l'ensemble des rendez-vous, quel que soit leur état.

    percentile_cont : fonction d'agrégation à ensemble ordonné de PostgreSQL
    (pg_catalog.percentile_cont, "double precision ORDER BY double precision"),
    interpolation linéaire continue entre les valeurs adjacentes -- vérifié par
    requête témoin sur (1,2,3,4) : percentile_cont(0.5) rend 2.5 (interpolé),
    percentile_disc(0.5) rend 2 (une valeur réelle de l'ensemble, discrète). C'est la
    variante continue qui est employée ici.
#}

select
    code_activite,
    count(*) as n_rendez_vous,
    count(*) filter (where est_jour_meme) as n_jour_meme,
    count(*) filter (where not est_jour_meme) as n_delai_positif,
    count(*) filter (where est_jour_meme)::numeric / count(*) as part_jour_meme,
    percentile_cont(0.5) within group (
        order by delai_obtention_jours
    ) filter (where not est_jour_meme) as mediane_delai_positif_jours,
    percentile_cont(0.9) within group (
        order by delai_obtention_jours
    ) filter (where not est_jour_meme) as p90_delai_positif_jours,
    avg(delai_obtention_jours) filter (where not est_jour_meme) as moyenne_delai_positif_jours,
    stddev(ln(delai_obtention_jours)) filter (where not est_jour_meme) as ecart_type_log_delai_positif,
    percentile_cont(0.5) within group (order by delai_obtention_jours) as mediane_delai_tous,
    percentile_cont(0.9) within group (order by delai_obtention_jours) as p90_delai_tous
from {{ ref('fct_rendez_vous') }}
group by code_activite
