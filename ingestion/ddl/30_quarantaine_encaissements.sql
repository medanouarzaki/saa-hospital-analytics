-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists quarantaine.encaissements cascade;
create table quarantaine.encaissements (
    n_encaissement text,
    n_facture text,
    date_encaissement text,
    mode_reglement text,
    montant text,
    regisseur text,
    billet_sortie_delivre text,
    date_extraction text,
    rejet_motifs text,
    rejet_date_chargement timestamptz,
    rejet_partition text
);
