-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists source.passages cascade;
create table source.passages (
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
    date_extraction text
);

comment on column source.passages.n_passage is
'provenance=DOC; preuve=S-08; type_metier=code; libelle=non_releve';
comment on column source.passages.n_ipp is
'provenance=OBS; preuve=REL-PAT.D01; type_metier=code; libelle=N° IPP';
comment on column source.passages.type_passage is
'provenance=DOC; preuve=S-06; type_metier=code; libelle=non_releve';
comment on column source.passages.service is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.passages.activite is
'provenance=OBS; preuve=REL-RDV.R02; type_metier=code; libelle=Activité';
comment on column source.passages.n_rdv is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=code; libelle=non_releve';
comment on column source.passages.mode_prise_en_charge is
'provenance=DOC; preuve=S-18; type_metier=code; libelle=non_releve';
comment on column source.passages.date_heure_entree is
'provenance=DOC; preuve=S-08; type_metier=horodatage; libelle=non_releve';
comment on column source.passages.date_heure_sortie is
'provenance=DOC; preuve=S-08; type_metier=horodatage; libelle=non_releve';
comment on column source.passages.medecin is
'provenance=DOC; preuve=S-06; type_metier=texte; libelle=non_releve';
comment on column source.passages.cree_par is
'provenance=OBS; preuve=REL-RDV.C01; type_metier=texte; libelle=Créé par';
comment on column source.passages.date_creation is
'provenance=OBS; preuve=REL-RDV.C02; type_metier=horodatage; libelle=Date création';
comment on column source.passages.date_extraction is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=date; libelle=non_releve';
