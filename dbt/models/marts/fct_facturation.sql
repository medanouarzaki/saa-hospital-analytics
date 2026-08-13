{#
    Une facture par ligne, clé n_facture (unique, mesurée sans doublon sur
    int_factures). n_episode se raccorde à int_passages.n_passage à 100% pour les
    trois valeurs de type_episode (CE, HOS, UR) -- mesuré, la vue des passages est
    la cible pivot pour les trois, la vue des passages d'urgence n'étant qu'un
    raccordement additionnel valable pour UR, jamais nécessaire ici.

    code_diagnostic_cim10 : attribut sans dimension (aucune dim_diagnostic n'existe
    dans ce dépôt), conservé tel quel.

    nb_lignes et montant_lignes : calculés indépendamment depuis int_lignes_facture,
    pour rendre la réconciliation testable sans dépendre du montant_total déclaré
    par la facture elle-même.

    date_facture est déjà de type date (pas timestamp) dans int_factures : pas de
    colonne de jour séparée, date_facture sert directement de jour de rattachement.
#}

with lignes as (
    select
        n_facture,
        count(*) as nb_lignes,
        sum(montant) as montant_lignes
    from {{ ref('int_lignes_facture') }}
    group by n_facture
)

select
    f.n_facture,
    f.n_ipp,
    d.valide_de as patient_valide_de,
    f.type_episode,
    f.date_facture,
    f.type_facture,
    f.etat,
    f.montant_total,
    f.part_organisme,
    f.part_patient,
    f.date_creation,
    nullif(f.n_episode, '') as n_episode,
    nullif(f.code_diagnostic_cim10, '') as code_diagnostic_cim10,
    nullif(f.service_emetteur, '') as service_emetteur,
    coalesce(l.nb_lignes, 0) as nb_lignes,
    coalesce(l.montant_lignes, 0) as montant_lignes,
    nullif(f.cree_par, '') as agent_creation
from {{ ref('int_factures') }} as f
left join lignes as l on f.n_facture = l.n_facture
left join {{ ref('dim_patient') }} as d
    on
        f.n_ipp = d.n_ipp
        and f.date_facture >= d.valide_de
        and (f.date_facture < d.valide_jusqu_a or d.valide_jusqu_a is null)
