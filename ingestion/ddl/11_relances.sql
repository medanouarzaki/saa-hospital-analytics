-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists source.relances cascade;
create table source.relances (
    n_relance text,
    n_creance text,
    date_relance text,
    canal text,
    resultat text,
    date_extraction text
);

comment on column source.relances.n_relance is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=code; libelle=non_releve';
comment on column source.relances.n_creance is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=code; libelle=non_releve';
comment on column source.relances.date_relance is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=date; libelle=non_releve';
comment on column source.relances.canal is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=code; libelle=non_releve';
comment on column source.relances.resultat is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=code; libelle=non_releve';
comment on column source.relances.date_extraction is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=date; libelle=non_releve';
