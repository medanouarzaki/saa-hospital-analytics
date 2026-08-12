-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists quarantaine.passages cascade;
create table quarantaine.passages (
    n_passage text,
    n_ipp text,
    type_passage text,
    service text,
    activite text,
    n_rdv text,
    mode_prise_en_charge text,
    date_heure_entree text,
    date_heure_sortie text,
    medecin text,
    cree_par text,
    date_creation text,
    date_extraction text,
    rejet_motifs text,
    rejet_date_chargement timestamptz,
    rejet_partition text
);
