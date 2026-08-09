-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists source.factures cascade;
create table source.factures (
    n_facture text,
    n_ipp text,
    n_episode text,
    type_episode text,
    code_diagnostic_cim10 text,
    date_facture text,
    type_facture text,
    service_emetteur text,
    etat text,
    montant_total text,
    part_organisme text,
    part_patient text,
    cree_par text,
    date_creation text,
    date_extraction text
);

comment on column source.factures.n_facture is
'provenance=DOC; preuve=S-09; type_metier=code; libelle=non_releve';
comment on column source.factures.n_ipp is
'provenance=OBS; preuve=REL-PAT.D01; type_metier=code; libelle=N° IPP';
comment on column source.factures.n_episode is
'provenance=DOC; preuve=S-09; type_metier=code; libelle=non_releve';
comment on column source.factures.type_episode is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.factures.code_diagnostic_cim10 is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.factures.date_facture is
'provenance=DOC; preuve=S-09; type_metier=date; libelle=non_releve';
comment on column source.factures.type_facture is
'provenance=DOC; preuve=S-09; type_metier=code; libelle=non_releve';
comment on column source.factures.service_emetteur is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.factures.etat is
'provenance=DOC; preuve=S-09; type_metier=code; libelle=non_releve';
comment on column source.factures.montant_total is
'provenance=DOC; preuve=S-17; type_metier=decimal; libelle=non_releve';
comment on column source.factures.part_organisme is
'provenance=DOC; preuve=S-18; type_metier=decimal; libelle=non_releve';
comment on column source.factures.part_patient is
'provenance=DOC; preuve=S-18; type_metier=decimal; libelle=non_releve';
comment on column source.factures.cree_par is
'provenance=OBS; preuve=REL-RDV.C01; type_metier=texte; libelle=Créé par';
comment on column source.factures.date_creation is
'provenance=OBS; preuve=REL-RDV.C02; type_metier=horodatage; libelle=Date création';
comment on column source.factures.date_extraction is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=date; libelle=non_releve';
