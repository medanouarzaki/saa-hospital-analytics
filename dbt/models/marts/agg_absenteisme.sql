{#
    Une ligne par code d'activité, agrégée depuis fct_rendez_vous.

    L'état restant (EI, ni honoré, ni absence, ni annulation -- cf.
    fct_rendez_vous.sql) n'est fondu dans aucune des trois catégories ; son propre
    décompte est exposé séparément (n_etat_restant) pour que la ligne reste
    exhaustive sur le nombre total de rendez-vous sans rien lui attribuer par défaut.

    Les taux (taux_absenteisme, taux_annulation) se calculent sur n_rendez_vous, le
    nombre TOTAL de rendez-vous de la ligne -- pas sur le nombre de rendez-vous
    résolus (honorés + absences + annulations). Ils EXCLUENT donc implicitement les
    rendez-vous en instance (EI) de leur numérateur, sans les exclure de leur
    dénominateur : un code d'activité avec une forte proportion de rendez-vous en
    instance aura des taux mécaniquement plus bas que si le dénominateur était
    restreint aux seuls rendez-vous résolus.

    mediane_delai_positif_jours reprend exactement la même définition de population
    que agg_delai_rendez_vous (délai strictement positif, cf. sa description) : cette
    colonne permet de lire la relation entre délai d'obtention et absentéisme sans
    jointure supplémentaire vers agg_delai_rendez_vous.
#}

select
    code_activite,
    count(*) as n_rendez_vous,
    count(*) filter (where est_honore) as n_honores,
    count(*) filter (where est_absence) as n_absences,
    count(*) filter (where est_annule) as n_annulations,
    count(*) filter (where not est_honore and not est_absence and not est_annule) as n_etat_restant,
    count(*) filter (where est_absence)::numeric / count(*) as taux_absenteisme,
    count(*) filter (where est_annule)::numeric / count(*) as taux_annulation,
    percentile_cont(0.5) within group (
        order by delai_obtention_jours
    ) filter (where not est_jour_meme) as mediane_delai_positif_jours
from {{ ref('fct_rendez_vous') }}
group by code_activite
