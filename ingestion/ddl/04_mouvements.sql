-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists source.mouvements cascade;
create table source.mouvements (
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
    date_extraction text
);

comment on column source.mouvements.n_sejour is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.mouvements.n_ipp is
'provenance=OBS; preuve=REL-PAT.D01; type_metier=code; libelle=N° IPP';
comment on column source.mouvements.date_heure_admission is
'provenance=DOC; preuve=S-27; type_metier=horodatage; libelle=non_releve';
comment on column source.mouvements.mode_admission is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.mouvements.service_accueil is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.mouvements.lit is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=texte; libelle=non_releve';
comment on column source.mouvements.n_mutation is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.mouvements.service_origine is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.mouvements.service_destination is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.mouvements.date_heure_mutation is
'provenance=DOC; preuve=S-27; type_metier=horodatage; libelle=non_releve';
comment on column source.mouvements.date_heure_sortie is
'provenance=DOC; preuve=S-27; type_metier=horodatage; libelle=non_releve';
comment on column source.mouvements.mode_sortie is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.mouvements.date_extraction is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=date; libelle=non_releve';
