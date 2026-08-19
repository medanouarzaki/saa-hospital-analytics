{#
    Conservation de fct_sejour face à int_mouvements : le nombre de séjours du fait
    doit égaler le nombre d'identifiants de séjour distincts de la vue des
    mouvements, et la somme du nombre de lignes de mouvement portées par chaque
    séjour doit égaler le nombre total de lignes de la vue des mouvements. Quatre
    sous-requêtes indépendantes, jamais un littéral de volumétrie. La première
    interdit de perdre ou d'inventer un séjour, la seconde interdit de perdre ou de
    compter deux fois une ligne dans l'agrégation.

    Troisième propriété, ajoutée après mesure qu'aucun autre test ne la couvrait
    (règle de vérification par mutation) : la dérivation de service_sortie -- destination de
    mutation quand le séjour en porte une, service d'accueil sinon -- recalculée ici
    indépendamment de fct_sejour.sql et comparée à sa valeur publiée. Seul fichier de
    test singulier autorisé ici ; cette propriété affirmée par fct_sejour.yml
    n'avait aucune preuve avant cet ajout.
#}

with decompte_sejours_fait as (
    select count(*) as n from {{ ref('fct_sejour') }}
),

decompte_sejours_source as (
    select count(distinct n_sejour) as n from {{ ref('int_mouvements') }}
),

lignes_agregees_fait as (
    select sum(nb_lignes_mouvement) as n from {{ ref('fct_sejour') }}
),

lignes_source as (
    select count(*) as n from {{ ref('int_mouvements') }}
),

service_sortie_attendu as (
    select
        n_sejour,
        max(nullif(service_destination, '')) as service_destination,
        max(nullif(service_accueil, '')) as service_accueil
    from {{ ref('int_mouvements') }}
    group by n_sejour
),

service_sortie_divergent as (
    select f.n_sejour
    from {{ ref('fct_sejour') }} as f
    inner join service_sortie_attendu as a on f.n_sejour = a.n_sejour
    where f.service_sortie is distinct from coalesce(a.service_destination, a.service_accueil)
)

select
    decompte_sejours_fait.n as sejours_fait,
    decompte_sejours_source.n as sejours_source,
    lignes_agregees_fait.n as lignes_agregees,
    lignes_source.n as lignes_source,
    (select count(*) from service_sortie_divergent) as sejours_service_sortie_divergent
from decompte_sejours_fait
cross join decompte_sejours_source
cross join lignes_agregees_fait
cross join lignes_source
where
    decompte_sejours_fait.n != decompte_sejours_source.n
    or lignes_agregees_fait.n != lignes_source.n
    or exists (select 1 from service_sortie_divergent)
