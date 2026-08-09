-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists source.lignes_facture cascade;
create table source.lignes_facture (
    n_facture text,
    n_ligne text,
    code_acte text,
    libelle_acte text,
    lettre_cle text,
    coefficient text,
    quantite text,
    tarif_unitaire text,
    montant text,
    service_executant text,
    date_acte text,
    date_extraction text
);

comment on column source.lignes_facture.n_facture is
'provenance=DOC; preuve=S-09; type_metier=code; libelle=non_releve';
comment on column source.lignes_facture.n_ligne is
'provenance=DOC; preuve=S-09; type_metier=entier; libelle=non_releve';
comment on column source.lignes_facture.code_acte is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.lignes_facture.libelle_acte is
'provenance=DOC; preuve=S-17; type_metier=texte; libelle=non_releve';
comment on column source.lignes_facture.lettre_cle is
'provenance=DOC; preuve=S-17; type_metier=code; libelle=non_releve';
comment on column source.lignes_facture.coefficient is
'provenance=DOC; preuve=S-17; type_metier=decimal; libelle=non_releve';
comment on column source.lignes_facture.quantite is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=entier; libelle=non_releve';
comment on column source.lignes_facture.tarif_unitaire is
'provenance=DOC; preuve=S-17; type_metier=decimal; libelle=non_releve';
comment on column source.lignes_facture.montant is
'provenance=DOC; preuve=S-17; type_metier=decimal; libelle=non_releve';
comment on column source.lignes_facture.service_executant is
'provenance=DOC; preuve=S-09; type_metier=code; libelle=non_releve';
comment on column source.lignes_facture.date_acte is
'provenance=DOC; preuve=S-27; type_metier=date; libelle=non_releve';
comment on column source.lignes_facture.date_extraction is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=date; libelle=non_releve';
