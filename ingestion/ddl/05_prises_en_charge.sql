-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists source.prises_en_charge cascade;
create table source.prises_en_charge (
    n_prise_en_charge text,
    n_ipp text,
    n_episode text,
    type_episode text,
    organisme text,
    n_assure text,
    date_verification text,
    etat text,
    taux_prise_en_charge text,
    date_extraction text
);

comment on column source.prises_en_charge.n_prise_en_charge is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.prises_en_charge.n_ipp is
'provenance=OBS; preuve=REL-PAT.D01; type_metier=code; libelle=N° IPP';
comment on column source.prises_en_charge.n_episode is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.prises_en_charge.type_episode is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.prises_en_charge.organisme is
'provenance=DOC; preuve=S-15; type_metier=code; libelle=non_releve';
comment on column source.prises_en_charge.n_assure is
'provenance=OBS; preuve=REL-PAT.A03; type_metier=texte; libelle=N° Assu';
comment on column source.prises_en_charge.date_verification is
'provenance=DOC; preuve=S-27; type_metier=horodatage; libelle=non_releve';
comment on column source.prises_en_charge.etat is
'provenance=DOC; preuve=S-19; type_metier=code; libelle=non_releve';
comment on column source.prises_en_charge.taux_prise_en_charge is
'provenance=DOC; preuve=S-18; type_metier=decimal; libelle=non_releve';
comment on column source.prises_en_charge.date_extraction is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=date; libelle=non_releve';
