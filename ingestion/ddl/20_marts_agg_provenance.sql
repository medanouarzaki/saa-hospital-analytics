-- Vue de répartition de la provenance des colonnes de la couche source.
--
-- C'est une vue et non une table alimentée par un script, parce qu'une
-- table alimentée peut diverger du catalogue qu'elle prétend décrire,
-- tandis qu'une vue ne le peut pas : elle est recalculée à chaque lecture,
-- directement sur pg_catalog. C'est ce qui rend le chiffre du rapport non
-- recopiable.
--
-- Une seule granularité est retenue, une ligne par étiquette de provenance :
-- mélanger dans la même vue une ligne par provenance et une ligne par table
-- nuirait à la lisibilité d'un select * sans clause de filtre.

create schema if not exists marts;

-- La vue est supprimée avant d'être recréée, et non créée sous condition
-- d'absence : une création conditionnelle laisserait en place une définition
-- ancienne sans rien signaler, tandis que ce couple applique toujours la
-- définition ci-dessous. Aucun objet de la base n'en dépend : le mode
-- restrict, qui s'applique par défaut, suffit donc, et si une dépendance
-- apparaissait un jour la suppression échouerait bruyamment plutôt que
-- d'emporter l'objet dépendant sans le dire.
drop view if exists marts.agg_provenance_champs;

create view marts.agg_provenance_champs as
with commentaires as (
    select (regexp_match(d.description, 'provenance=([A-Z]+);'))[1] as provenance
    from pg_catalog.pg_description as d
    inner join pg_catalog.pg_class as c on d.objoid = c.oid
    inner join pg_catalog.pg_namespace as n on c.relnamespace = n.oid
    where n.nspname = 'source' and d.objsubid > 0
)

select
    provenance,
    count(*) as nb_colonnes,
    round(100.0 * count(*) / sum(count(*)) over (), 1) as part_pourcent
from commentaires
group by provenance;
