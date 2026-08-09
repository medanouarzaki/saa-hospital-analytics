-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists source.rendez_vous cascade;
create table source.rendez_vous (
    n_rdv text,
    n_ipp text,
    agenda text,
    activite text,
    origine text,
    hopital_cs text,
    medecin_ext text,
    service_ext text,
    observations text,
    date_rendez_vous text,
    rdv_supplementaire text,
    type_attention text,
    etat text,
    duree text,
    date_reception text,
    imprimer_donnees text,
    cree_par text,
    date_creation text,
    modifie_par text,
    date_mod text,
    confirme_par text,
    date_conf text,
    annule_par text,
    date_annul text,
    liste_attente_service text,
    liste_attente_agenda text,
    liste_attente_activite text,
    date_extraction text
);

comment on column source.rendez_vous.n_rdv is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=code; libelle=non_releve';
comment on column source.rendez_vous.n_ipp is
'provenance=OBS; preuve=REL-RDV.I01; type_metier=code; libelle=N° IPP';
comment on column source.rendez_vous.agenda is
'provenance=OBS; preuve=REL-RDV.R01; type_metier=code; libelle=Agenda';
comment on column source.rendez_vous.activite is
'provenance=OBS; preuve=REL-RDV.R02; type_metier=code; libelle=Activité';
comment on column source.rendez_vous.origine is
'provenance=OBS; preuve=REL-RDV.R03; type_metier=code; libelle=Origine';
comment on column source.rendez_vous.hopital_cs is
'provenance=OBS; preuve=REL-RDV.R04; type_metier=code; libelle=Hôpital/C.S.';
comment on column source.rendez_vous.medecin_ext is
'provenance=OBS; preuve=REL-RDV.R05; type_metier=texte; libelle=Médecin ext.';
comment on column source.rendez_vous.service_ext is
'provenance=OBS; preuve=REL-RDV.R06; type_metier=texte; libelle=Service ext.';
comment on column source.rendez_vous.observations is
'provenance=OBS; preuve=REL-RDV.R07; type_metier=texte; libelle=Observations';
comment on column source.rendez_vous.date_rendez_vous is
'provenance=OBS; preuve=REL-RDV.R08; type_metier=horodatage; libelle=Date rendez-vous';
comment on column source.rendez_vous.rdv_supplementaire is
'provenance=OBS; preuve=REL-RDV.R09; type_metier=booleen; libelle=Rendez-vous supplémentaire';
comment on column source.rendez_vous.type_attention is
'provenance=OBS; preuve=REL-RDV.R10; type_metier=code; libelle=Type d''attention';
comment on column source.rendez_vous.etat is
'provenance=OBS; preuve=REL-RDV.R11; type_metier=code; libelle=État';
comment on column source.rendez_vous.duree is
'provenance=OBS; preuve=REL-RDV.R12; type_metier=entier; libelle=Durée';
comment on column source.rendez_vous.date_reception is
'provenance=OBS; preuve=REL-RDV.R13; type_metier=horodatage; libelle=Date réception';
comment on column source.rendez_vous.imprimer_donnees is
'provenance=OBS; preuve=REL-RDV.R14; type_metier=booleen; libelle=Imprimer données';
comment on column source.rendez_vous.cree_par is
'provenance=OBS; preuve=REL-RDV.C01; type_metier=texte; libelle=Créé par';
comment on column source.rendez_vous.date_creation is
'provenance=OBS; preuve=REL-RDV.C02; type_metier=horodatage; libelle=Date création';
comment on column source.rendez_vous.modifie_par is
'provenance=OBS; preuve=REL-RDV.C03; type_metier=texte; libelle=Modifié par';
comment on column source.rendez_vous.date_mod is
'provenance=OBS; preuve=REL-RDV.C04; type_metier=horodatage; libelle=Date mod.';
comment on column source.rendez_vous.confirme_par is
'provenance=OBS; preuve=REL-RDV.C05; type_metier=texte; libelle=Confirmé par';
comment on column source.rendez_vous.date_conf is
'provenance=OBS; preuve=REL-RDV.C06; type_metier=horodatage; libelle=Date conf.';
comment on column source.rendez_vous.annule_par is
'provenance=OBS; preuve=REL-RDV.C07; type_metier=texte; libelle=Annulé par';
comment on column source.rendez_vous.date_annul is
'provenance=OBS; preuve=REL-RDV.C08; type_metier=horodatage; libelle=Date annul.';
comment on column source.rendez_vous.liste_attente_service is
'provenance=OBS; preuve=REL-RDV.L01; type_metier=code; libelle=Service';
comment on column source.rendez_vous.liste_attente_agenda is
'provenance=OBS; preuve=REL-RDV.L02; type_metier=code; libelle=Agenda';
comment on column source.rendez_vous.liste_attente_activite is
'provenance=OBS; preuve=REL-RDV.L03; type_metier=code; libelle=Activité';
comment on column source.rendez_vous.date_extraction is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=date; libelle=non_releve';
