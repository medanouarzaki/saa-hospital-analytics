-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists quarantaine.rendez_vous cascade;
create table quarantaine.rendez_vous (
    n_rdv text,
    n_ipp text,
    agenda text,
    activite text,
    origine text,
    hopital_cs text,
    medecin_ext text,
    service_ext text,
    observations text,
    date_rendez_vous text,
    rdv_supplementaire text,
    type_attention text,
    etat text,
    duree text,
    date_reception text,
    imprimer_donnees text,
    cree_par text,
    date_creation text,
    modifie_par text,
    date_mod text,
    confirme_par text,
    date_conf text,
    annule_par text,
    date_annul text,
    liste_attente_service text,
    liste_attente_agenda text,
    liste_attente_activite text,
    date_extraction text,
    rejet_motifs text,
    rejet_date_chargement timestamptz,
    rejet_partition text
);
