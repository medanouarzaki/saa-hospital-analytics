-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists quarantaine.creances cascade;
create table quarantaine.creances (
    n_creance text,
    n_facture text,
    date_naissance_creance text,
    montant_du text,
    montant_recouvre text,
    montant_restant text,
    type_debiteur text,
    motif_non_recouvrement text,
    date_extraction text,
    rejet_motifs text,
    rejet_date_chargement timestamptz,
    rejet_partition text
);
