-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists quarantaine.lignes_facture cascade;
create table quarantaine.lignes_facture (
    n_facture text,
    n_ligne text,
    code_acte text,
    libelle_acte text,
    lettre_cle text,
    coefficient text,
    quantite text,
    tarif_unitaire text,
    montant text,
    service_executant text,
    date_acte text,
    date_extraction text,
    rejet_motifs text,
    rejet_date_chargement timestamptz,
    rejet_partition text
);
