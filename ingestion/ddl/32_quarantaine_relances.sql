-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists quarantaine.relances cascade;
create table quarantaine.relances (
    n_relance text,
    n_creance text,
    date_relance text,
    canal text,
    resultat text,
    date_extraction text,
    rejet_motifs text,
    rejet_date_chargement timestamptz,
    rejet_partition text
);
