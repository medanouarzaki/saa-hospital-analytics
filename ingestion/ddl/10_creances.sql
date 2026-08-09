-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists source.creances cascade;
create table source.creances (
    n_creance text,
    n_facture text,
    date_naissance_creance text,
    montant_du text,
    montant_recouvre text,
    montant_restant text,
    type_debiteur text,
    motif_non_recouvrement text,
    date_extraction text
);

comment on column source.creances.n_creance is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.creances.n_facture is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.creances.date_naissance_creance is
'provenance=DOC; preuve=S-27; type_metier=date; libelle=non_releve';
comment on column source.creances.montant_du is
'provenance=DOC; preuve=S-20; type_metier=decimal; libelle=non_releve';
comment on column source.creances.montant_recouvre is
'provenance=DOC; preuve=S-20; type_metier=decimal; libelle=non_releve';
comment on column source.creances.montant_restant is
'provenance=DOC; preuve=S-20; type_metier=decimal; libelle=non_releve';
comment on column source.creances.type_debiteur is
'provenance=DOC; preuve=S-09; type_metier=code; libelle=non_releve';
comment on column source.creances.motif_non_recouvrement is
'provenance=DOC; preuve=S-20; type_metier=code; libelle=non_releve';
comment on column source.creances.date_extraction is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=date; libelle=non_releve';
