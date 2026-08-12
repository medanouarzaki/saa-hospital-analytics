-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists quarantaine.passages_urgences cascade;
create table quarantaine.passages_urgences (
    n_passage text,
    n_ipp text,
    date_heure_arrivee text,
    mode_arrivee text,
    motif_recours text,
    niveau_tri text,
    date_heure_pec_medicale text,
    date_heure_sortie text,
    orientation_sortie text,
    service_orientation text,
    motif_transfert text,
    consentement_transfert text,
    famille_informee text,
    inventaire_effets text,
    date_extraction text,
    rejet_motifs text,
    rejet_date_chargement timestamptz,
    rejet_partition text
);
