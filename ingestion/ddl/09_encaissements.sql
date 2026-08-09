-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists source.encaissements cascade;
create table source.encaissements (
    n_encaissement text,
    n_facture text,
    date_encaissement text,
    mode_reglement text,
    montant text,
    regisseur text,
    billet_sortie_delivre text,
    date_extraction text
);

comment on column source.encaissements.n_encaissement is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.encaissements.n_facture is
'provenance=DOC; preuve=S-27; type_metier=code; libelle=non_releve';
comment on column source.encaissements.date_encaissement is
'provenance=DOC; preuve=S-27; type_metier=horodatage; libelle=non_releve';
comment on column source.encaissements.mode_reglement is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=code; libelle=non_releve';
comment on column source.encaissements.montant is
'provenance=DOC; preuve=S-18; type_metier=decimal; libelle=non_releve';
comment on column source.encaissements.regisseur is
'provenance=DOC; preuve=S-20; type_metier=texte; libelle=non_releve';
comment on column source.encaissements.billet_sortie_delivre is
'provenance=DOC; preuve=S-27; type_metier=booleen; libelle=non_releve';
comment on column source.encaissements.date_extraction is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=date; libelle=non_releve';
