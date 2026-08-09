-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.

drop table if exists source.patients cascade;
create table source.patients (
    n_ipp text,
    nom text,
    nom_famille_1 text,
    nom_famille_2 text,
    sexe text,
    date_naissance text,
    type_piece_identite text,
    n_piece_identite text,
    etat_civil text,
    type_patient text,
    date_photo text,
    modifie_par text,
    cree_par text,
    date_attribution text,
    compagnie_assurance text,
    police text,
    n_assure text,
    profession text,
    num_inscription text,
    date_inscription text,
    type_domicile text,
    adresse text,
    code_postal text,
    etat text,
    ville text,
    quartier text,
    nationalite text,
    telephone_1 text,
    telephone_2 text,
    telephone_3 text,
    telephone_4 text,
    avertissements_sms text,
    email text,
    avertissements_email text,
    environnement text,
    nom_pere text,
    nom_mere text,
    etat_naissance text,
    ville_naissance text,
    pays_naissance text,
    quartier_naissance text,
    commentaire text,
    province text,
    exitus text,
    date_modification text,
    date_extraction text
);

comment on column source.patients.n_ipp is
'provenance=OBS; preuve=REL-PAT.D01; type_metier=code; libelle=N° IPP';
comment on column source.patients.nom is
'provenance=OBS; preuve=REL-PAT.D02; type_metier=texte; libelle=Nom';
comment on column source.patients.nom_famille_1 is
'provenance=OBS; preuve=REL-PAT.D03; type_metier=texte; libelle=Nom de famille 1';
comment on column source.patients.nom_famille_2 is
'provenance=OBS; preuve=REL-PAT.D04; type_metier=texte; libelle=Nom de famille 2';
comment on column source.patients.sexe is
'provenance=OBS; preuve=REL-PAT.D05; type_metier=code; libelle=Sexe';
comment on column source.patients.date_naissance is
'provenance=OBS; preuve=REL-PAT.D06; type_metier=date; libelle=D. Nai';
comment on column source.patients.type_piece_identite is
'provenance=OBS; preuve=REL-PAT.D09; type_metier=code; libelle=Type pièce d''identité';
comment on column source.patients.n_piece_identite is
'provenance=OBS; preuve=REL-PAT.D10; type_metier=texte; libelle=N° pièce d''identité';
comment on column source.patients.etat_civil is
'provenance=OBS; preuve=REL-PAT.D11; type_metier=code; libelle=E. Civil';
comment on column source.patients.type_patient is
'provenance=OBS; preuve=REL-PAT.D12; type_metier=code; libelle=Type patient';
comment on column source.patients.date_photo is
'provenance=OBS; preuve=REL-PAT.D13; type_metier=date; libelle=Date photo';
comment on column source.patients.modifie_par is
'provenance=OBS; preuve=REL-PAT.D14; type_metier=texte; libelle=Modifié par';
comment on column source.patients.cree_par is
'provenance=OBS; preuve=REL-PAT.D15; type_metier=texte; libelle=Créé par';
comment on column source.patients.date_attribution is
'provenance=OBS; preuve=REL-PAT.D16; type_metier=date; libelle=Date d''attribution';
comment on column source.patients.compagnie_assurance is
'provenance=OBS; preuve=REL-PAT.A01; type_metier=code; libelle=Compagnie d''assur.';
comment on column source.patients.police is
'provenance=OBS; preuve=REL-PAT.A02; type_metier=texte; libelle=Police';
comment on column source.patients.n_assure is
'provenance=OBS; preuve=REL-PAT.A03; type_metier=texte; libelle=N° Assu';
comment on column source.patients.profession is
'provenance=OBS; preuve=REL-PAT.A04; type_metier=texte; libelle=Profession';
comment on column source.patients.num_inscription is
'provenance=OBS; preuve=REL-PAT.A05; type_metier=texte; libelle=Num. inscription';
comment on column source.patients.date_inscription is
'provenance=OBS; preuve=REL-PAT.A06; type_metier=date; libelle=Date inscription';
comment on column source.patients.type_domicile is
'provenance=OBS; preuve=REL-PAT.H01; type_metier=code; libelle=Type';
comment on column source.patients.adresse is
'provenance=OBS; preuve=REL-PAT.H02; type_metier=texte; libelle=Adresse';
comment on column source.patients.code_postal is
'provenance=OBS; preuve=REL-PAT.H03; type_metier=texte; libelle=Code postal';
comment on column source.patients.etat is
'provenance=OBS; preuve=REL-PAT.H04; type_metier=code; libelle=État';
comment on column source.patients.ville is
'provenance=OBS; preuve=REL-PAT.H05; type_metier=code; libelle=Ville';
comment on column source.patients.quartier is
'provenance=OBS; preuve=REL-PAT.H06; type_metier=texte; libelle=Quartier';
comment on column source.patients.nationalite is
'provenance=OBS; preuve=REL-PAT.H07; type_metier=code; libelle=Nationalité';
comment on column source.patients.telephone_1 is
'provenance=OBS; preuve=REL-PAT.H08; type_metier=texte; libelle=Téléphone 1';
comment on column source.patients.telephone_2 is
'provenance=OBS; preuve=REL-PAT.H09; type_metier=texte; libelle=Téléphone 2';
comment on column source.patients.telephone_3 is
'provenance=OBS; preuve=REL-PAT.H10; type_metier=texte; libelle=Téléphone 3';
comment on column source.patients.telephone_4 is
'provenance=OBS; preuve=REL-PAT.H11; type_metier=texte; libelle=Téléphone 4';
comment on column source.patients.avertissements_sms is
'provenance=OBS; preuve=REL-PAT.H12; type_metier=booleen; libelle=Avertissements SMS';
comment on column source.patients.email is
'provenance=OBS; preuve=REL-PAT.H13; type_metier=texte; libelle=E-mail';
comment on column source.patients.avertissements_email is
'provenance=OBS; preuve=REL-PAT.H14; type_metier=booleen; libelle=Avertissements e-mail';
comment on column source.patients.environnement is
'provenance=OBS; preuve=REL-PAT.H15; type_metier=code; libelle=Environnement';
comment on column source.patients.nom_pere is
'provenance=OBS; preuve=REL-PAT.N01; type_metier=texte; libelle=Nom. Père';
comment on column source.patients.nom_mere is
'provenance=OBS; preuve=REL-PAT.N02; type_metier=texte; libelle=Nom. Mère';
comment on column source.patients.etat_naissance is
'provenance=OBS; preuve=REL-PAT.N03; type_metier=code; libelle=Lieu de naissance - État';
comment on column source.patients.ville_naissance is
'provenance=OBS; preuve=REL-PAT.N04; type_metier=code; libelle=Ville';
comment on column source.patients.pays_naissance is
'provenance=OBS; preuve=REL-PAT.N05; type_metier=code; libelle=Pays';
comment on column source.patients.quartier_naissance is
'provenance=OBS; preuve=REL-PAT.N06; type_metier=texte; libelle=Quartier';
comment on column source.patients.commentaire is
'provenance=OBS; preuve=REL-PAT.K01; type_metier=texte; libelle=Commentaire';
comment on column source.patients.province is
'provenance=OBS; preuve=REL-IPP.R09; type_metier=code; libelle=Province';
comment on column source.patients.exitus is
'provenance=OBS; preuve=REL-IPP.F04; type_metier=booleen; libelle=Exitus';
comment on column source.patients.date_modification is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=horodatage; libelle=non_releve';
comment on column source.patients.date_extraction is
'provenance=HYP; preuve=sans_preuve_externe; type_metier=date; libelle=non_releve';
