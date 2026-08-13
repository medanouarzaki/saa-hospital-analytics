{#
    Réconciliation de fct_facturation. Trois propriétés, chacune l'égalité de deux
    quantités calculées indépendamment, aucun littéral de volumétrie. Une somme
    globale seule ne suffit pas : elle resterait vraie si deux factures divergeaient
    en sens opposé et de montant égal (l'une au-dessus, l'autre en-dessous de la
    somme de ses lignes), masquant une divergence individuelle réelle derrière une
    somme totale juste -- d'où les deux vérifications individuelles en plus de la
    globale.
#}

with total_montant_fait as (
    select sum(montant_total) as n from {{ ref('fct_facturation') }}
),

total_montant_lignes as (
    select sum(montant) as n from {{ ref('int_lignes_facture') }}
),

total_factures as (
    select count(*) as n from {{ ref('fct_facturation') }}
),

factures_montant_conforme as (
    select count(*) as n
    from {{ ref('fct_facturation') }}
    where montant_total = montant_lignes
),

factures_parts_conformes as (
    select count(*) as n
    from {{ ref('fct_facturation') }}
    where part_organisme + part_patient = montant_total
)

select
    total_montant_fait.n as montant_total_fait,
    total_montant_lignes.n as montant_total_lignes,
    total_factures.n as total_factures,
    factures_montant_conforme.n as factures_montant_conforme,
    factures_parts_conformes.n as factures_parts_conformes
from total_montant_fait
cross join total_montant_lignes
cross join total_factures
cross join factures_montant_conforme
cross join factures_parts_conformes
where
    total_montant_fait.n != total_montant_lignes.n
    or total_factures.n != factures_montant_conforme.n
    or total_factures.n != factures_parts_conformes.n
