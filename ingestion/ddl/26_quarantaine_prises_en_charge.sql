-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists quarantaine.prises_en_charge cascade;
create table quarantaine.prises_en_charge (
    n_prise_en_charge text,
    n_ipp text,
    n_episode text,
    type_episode text,
    organisme text,
    n_assure text,
    date_verification text,
    etat text,
    taux_prise_en_charge text,
    date_extraction text,
    rejet_motifs text,
    rejet_date_chargement timestamptz,
    rejet_partition text
);
