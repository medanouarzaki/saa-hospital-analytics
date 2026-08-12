-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists quarantaine.factures cascade;
create table quarantaine.factures (
    n_facture text,
    n_ipp text,
    n_episode text,
    type_episode text,
    code_diagnostic_cim10 text,
    date_facture text,
    type_facture text,
    service_emetteur text,
    etat text,
    montant_total text,
    part_organisme text,
    part_patient text,
    cree_par text,
    date_creation text,
    date_extraction text,
    rejet_motifs text,
    rejet_date_chargement timestamptz,
    rejet_partition text
);
