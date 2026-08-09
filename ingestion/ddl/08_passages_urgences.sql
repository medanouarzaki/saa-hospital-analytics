-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists source.passages_urgences cascade;
create table source.passages_urgences (
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
    date_extraction text
);

comment on column source.passages_urgences.n_passage is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.passages_urgences.n_ipp is
'provenance=OBS; preuve=REL-PAT.D01; type_metier=code; libelle=N° IPP';
comment on column source.passages_urgences.date_heure_arrivee is
'provenance=DOC; preuve=S-27; type_metier=horodatage; libelle=non_releve';
comment on column source.passages_urgences.mode_arrivee is
'provenance=DOC; preuve=S-12; type_metier=code; libelle=non_releve';
comment on column source.passages_urgences.motif_recours is
'provenance=DOC; preuve=S-13; type_metier=code; libelle=non_releve';
comment on column source.passages_urgences.niveau_tri is
'provenance=DOC; preuve=S-12; type_metier=code; libelle=non_releve';
comment on column source.passages_urgences.date_heure_pec_medicale is
'provenance=DOC; preuve=S-27; type_metier=horodatage; libelle=non_releve';
comment on column source.passages_urgences.date_heure_sortie is
'provenance=DOC; preuve=S-27; type_metier=horodatage; libelle=non_releve';
comment on column source.passages_urgences.orientation_sortie is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.passages_urgences.service_orientation is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.passages_urgences.motif_transfert is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.passages_urgences.consentement_transfert is
'provenance=DOC; preuve=S-27; type_metier=booleen; libelle=non_releve';
comment on column source.passages_urgences.famille_informee is
'provenance=DOC; preuve=S-27; type_metier=booleen; libelle=non_releve';
comment on column source.passages_urgences.inventaire_effets is
'provenance=DOC; preuve=S-27; type_metier=booleen; libelle=non_releve';
comment on column source.passages_urgences.date_extraction is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=date; libelle=non_releve';
