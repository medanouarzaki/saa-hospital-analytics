{#
    Un encaissement par ligne, clé n_encaissement (unique, mesurée sans doublon sur
    int_encaissements). n_ipp est DÉRIVÉ : il n'existe pas de colonne patient propre
    à int_encaissements, il est obtenu par le chemin
    int_encaissements.n_facture -> fct_facturation.n_facture -> fct_facturation.n_ipp
    (le raccordement n_facture est mesuré 100% couvert -- toute facture référencée
    existe dans fct_facturation).
#}

select
    e.n_encaissement,
    e.n_facture,
    f.n_ipp,
    d.valide_de as patient_valide_de,
    e.date_encaissement,
    e.date_encaissement::date as jour_encaissement,
    e.montant,
    e.billet_sortie_delivre,
    nullif(e.mode_reglement, '') as mode_reglement,
    nullif(e.regisseur, '') as regisseur
from {{ ref('int_encaissements') }} as e
left join {{ ref('fct_facturation') }} as f on e.n_facture = f.n_facture
left join {{ ref('dim_patient') }} as d
    on
        f.n_ipp = d.n_ipp
        and e.date_encaissement::date >= d.valide_de
        and (e.date_encaissement::date < d.valide_jusqu_a or d.valide_jusqu_a is null)
