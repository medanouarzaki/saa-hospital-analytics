-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists quarantaine.mouvements cascade;
create table quarantaine.mouvements (
    n_sejour text,
    n_ipp text,
    date_heure_admission text,
    mode_admission text,
    service_accueil text,
    lit text,
    n_mutation text,
    service_origine text,
    service_destination text,
    date_heure_mutation text,
    date_heure_sortie text,
    mode_sortie text,
    date_extraction text,
    rejet_motifs text,
    rejet_date_chargement timestamptz,
    rejet_partition text
);
