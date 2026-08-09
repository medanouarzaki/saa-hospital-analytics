# Dictionnaire des données

## source.patients

| colonne | type_metier | libelle_hosix | provenance | preuve | note |
|---|---|---|---|---|---|
| n_ipp | code | N° IPP | OBS | REL-PAT.D01 | Relevé de champs, fiche patient, bloc Données principales. |
| nom | texte | Nom | OBS | REL-PAT.D02 | Relevé de champs, fiche patient, bloc Données principales. |
| nom_famille_1 | texte | Nom de famille 1 | OBS | REL-PAT.D03 | Relevé de champs, fiche patient, bloc Données principales. |
| nom_famille_2 | texte | Nom de famille 2 | OBS | REL-PAT.D04 | Relevé de champs, fiche patient, bloc Données principales. |
| sexe | code | Sexe | OBS | REL-PAT.D05 | Relevé de champs, fiche patient, bloc Données principales. |
| date_naissance | date | D. Nai | OBS | REL-PAT.D06 | Relevé de champs, fiche patient, bloc Données principales. |
| type_piece_identite | code | Type pièce d'identité | OBS | REL-PAT.D09 | Relevé de champs, fiche patient, bloc Données principales. |
| n_piece_identite | texte | N° pièce d'identité | OBS | REL-PAT.D10 | Relevé de champs, fiche patient, bloc Données principales. |
| etat_civil | code | E. Civil | OBS | REL-PAT.D11 | Relevé de champs, fiche patient, bloc Données principales. |
| type_patient | code | Type patient | OBS | REL-PAT.D12 | Relevé de champs, fiche patient, bloc Données principales. |
| date_photo | date | Date photo | OBS | REL-PAT.D13 | Relevé de champs, fiche patient, bloc Données principales. |
| modifie_par | texte | Modifié par | OBS | REL-PAT.D14 | Relevé de champs, fiche patient, bloc Données principales. |
| cree_par | texte | Créé par | OBS | REL-PAT.D15 | Relevé de champs, fiche patient, bloc Données principales. |
| date_attribution | date | Date d'attribution | OBS | REL-PAT.D16 | Relevé de champs, fiche patient, bloc Données principales. |
| compagnie_assurance | code | Compagnie d'assur. | OBS | REL-PAT.A01 | Relevé de champs, fiche patient, bloc Compagnie d'assurance. |
| police | texte | Police | OBS | REL-PAT.A02 | Relevé de champs, fiche patient, bloc Compagnie d'assurance. |
| n_assure | texte | N° Assu | OBS | REL-PAT.A03 | Relevé de champs, fiche patient, bloc Compagnie d'assurance. |
| profession | texte | Profession | OBS | REL-PAT.A04 | Relevé de champs, fiche patient, bloc Compagnie d'assurance. |
| num_inscription | texte | Num. inscription | OBS | REL-PAT.A05 | Relevé de champs, fiche patient, bloc Compagnie d'assurance. |
| date_inscription | date | Date inscription | OBS | REL-PAT.A06 | Relevé de champs, fiche patient, bloc Compagnie d'assurance. |
| type_domicile | code | Type | OBS | REL-PAT.H01 | Relevé de champs, fiche patient, bloc Domicile. |
| adresse | texte | Adresse | OBS | REL-PAT.H02 | Relevé de champs, fiche patient, bloc Domicile. |
| code_postal | texte | Code postal | OBS | REL-PAT.H03 | Relevé de champs, fiche patient, bloc Domicile. |
| etat | code | État | OBS | REL-PAT.H04 | Relevé de champs, fiche patient, bloc Domicile. |
| ville | code | Ville | OBS | REL-PAT.H05 | Relevé de champs, fiche patient, bloc Domicile. |
| quartier | texte | Quartier | OBS | REL-PAT.H06 | Relevé de champs, fiche patient, bloc Domicile. |
| nationalite | code | Nationalité | OBS | REL-PAT.H07 | Relevé de champs, fiche patient, bloc Domicile. |
| telephone_1 | texte | Téléphone 1 | OBS | REL-PAT.H08 | Relevé de champs, fiche patient, bloc Domicile. |
| telephone_2 | texte | Téléphone 2 | OBS | REL-PAT.H09 | Relevé de champs, fiche patient, bloc Domicile. |
| telephone_3 | texte | Téléphone 3 | OBS | REL-PAT.H10 | Relevé de champs, fiche patient, bloc Domicile. |
| telephone_4 | texte | Téléphone 4 | OBS | REL-PAT.H11 | Relevé de champs, fiche patient, bloc Domicile. |
| avertissements_sms | booleen | Avertissements SMS | OBS | REL-PAT.H12 | Relevé de champs, fiche patient, bloc Domicile. |
| email | texte | E-mail | OBS | REL-PAT.H13 | Relevé de champs, fiche patient, bloc Domicile. |
| avertissements_email | booleen | Avertissements e-mail | OBS | REL-PAT.H14 | Relevé de champs, fiche patient, bloc Domicile. |
| environnement | code | Environnement | OBS | REL-PAT.H15 | Relevé de champs, fiche patient, bloc Domicile. |
| nom_pere | texte | Nom. Père | OBS | REL-PAT.N01 | Relevé de champs, fiche patient, bloc Né. |
| nom_mere | texte | Nom. Mère | OBS | REL-PAT.N02 | Relevé de champs, fiche patient, bloc Né. |
| etat_naissance | code | Lieu de naissance - État | OBS | REL-PAT.N03 | Relevé de champs, fiche patient, bloc Né. |
| ville_naissance | code | Ville | OBS | REL-PAT.N04 | Relevé de champs, fiche patient, bloc Né. |
| pays_naissance | code | Pays | OBS | REL-PAT.N05 | Relevé de champs, fiche patient, bloc Né. |
| quartier_naissance | texte | Quartier | OBS | REL-PAT.N06 | Relevé de champs, fiche patient, bloc Né. |
| commentaire | texte | Commentaire | OBS | REL-PAT.K01 | Relevé de champs, fiche patient, bloc Commentaire. |
| province | code | Province | OBS | REL-IPP.R09 | Relevé de champs, recherche d'IPP, colonne de résultat. La colonne n'apparaît pas au bloc Domicile de la fiche patient, où figurent État, Ville et Quartier ; elle est établie par la liste de résultats de la recherche, qui la restitue. |
| exitus | booleen | Exitus | OBS | REL-IPP.F04 | Relevé de champs, recherche d'IPP, filtre de population. L'existence d'un filtre sur les patients décédés établit qu'un indicateur de décès est stocké sur la fiche, bien qu'aucun champ de ce nom n'ait été relevé sur l'écran de la fiche patient. |
| date_modification | horodatage | non_releve | HYP | sans_preuve_externe | L'écran de la fiche patient porte un champ Modifié par sans horodatage adjacent, là où l'écran de rendez-vous appareille chaque agent à sa date. La colonne est posée parce que l'historisation de la dimension patient en type 2 exige un instant de changement. Si l'extraction réelle ne la fournissait pas, l'historisation se rabattrait sur la date d'extraction de la partition, à la granularité du jour au lieu de la seconde, et les changements survenus le même jour seraient confondus. |
| date_extraction | date | non_releve | HYP | sans_preuve_externe | Colonne technique de la zone d'atterrissage, absente du système observé. Elle porte la date de l'extraction dont la ligne provient et rend le rechargement d'une partition idempotent. Si une extraction réelle ne la fournissait pas, elle serait dérivée du nom du fichier partitionné, sans perte d'information. |

## source.rendez_vous

| colonne | type_metier | libelle_hosix | provenance | preuve | note |
|---|---|---|---|---|---|
| n_rdv | code | non_releve | HYP | sans_preuve_externe | Aucun identifiant de rendez-vous n'apparaît à l'écran Donner rendez-vous, dont la barre d'actions comporte pourtant Enregistrer, Supprimer et Chercher, trois opérations qui supposent une clé. La colonne est posée parce que la table des passages porte une référence de rendez-vous nullable, qui n'aurait pas de cible sans elle. Si le système en place clé le rendez-vous par un couple agenda et horodatage plutôt que par un numéro, la structure logique du modèle est inchangée et seule la forme de la clé diffère. |
| n_ipp | code | N° IPP | OBS | REL-RDV.I01 | Relevé de champs, écran Donner rendez-vous, bloc Identification du patient. |
| agenda | code | Agenda | OBS | REL-RDV.R01 | Relevé de champs, écran Donner rendez-vous, bloc Rendez-vous. |
| activite | code | Activité | OBS | REL-RDV.R02 | Relevé de champs, écran Donner rendez-vous, bloc Rendez-vous. |
| origine | code | Origine | OBS | REL-RDV.R03 | Relevé de champs, écran Donner rendez-vous, bloc Rendez-vous. |
| hopital_cs | code | Hôpital/C.S. | OBS | REL-RDV.R04 | Relevé de champs, écran Donner rendez-vous, bloc Rendez-vous. |
| medecin_ext | texte | Médecin ext. | OBS | REL-RDV.R05 | Relevé de champs, écran Donner rendez-vous, bloc Rendez-vous. |
| service_ext | texte | Service ext. | OBS | REL-RDV.R06 | Relevé de champs, écran Donner rendez-vous, bloc Rendez-vous. |
| observations | texte | Observations | OBS | REL-RDV.R07 | Relevé de champs, écran Donner rendez-vous, bloc Rendez-vous. |
| date_rendez_vous | horodatage | Date rendez-vous | OBS | REL-RDV.R08 | Relevé de champs, écran Donner rendez-vous, bloc Rendez-vous. |
| rdv_supplementaire | booleen | Rendez-vous supplémentaire | OBS | REL-RDV.R09 | Relevé de champs, écran Donner rendez-vous, bloc Rendez-vous. |
| type_attention | code | Type d'attention | OBS | REL-RDV.R10 | Relevé de champs, écran Donner rendez-vous, bloc Rendez-vous. |
| etat | code | État | OBS | REL-RDV.R11 | Relevé de champs, écran Donner rendez-vous, bloc Rendez-vous. |
| duree | entier | Durée | OBS | REL-RDV.R12 | Relevé de champs, écran Donner rendez-vous, bloc Rendez-vous. Durée exprimée en minutes, valeur nulle sur le rendez-vous observé. |
| date_reception | horodatage | Date réception | OBS | REL-RDV.R13 | Relevé de champs, écran Donner rendez-vous, bloc Rendez-vous. |
| imprimer_donnees | booleen | Imprimer données | OBS | REL-RDV.R14 | Relevé de champs, écran Donner rendez-vous, bloc Rendez-vous. |
| cree_par | texte | Créé par | OBS | REL-RDV.C01 | Relevé de champs, écran Donner rendez-vous, bloc Contrôle de modifications. |
| date_creation | horodatage | Date création | OBS | REL-RDV.C02 | Relevé de champs, écran Donner rendez-vous, bloc Contrôle de modifications. L'écart entre cette colonne et la date du rendez-vous est le délai d'obtention, grandeur centrale de l'analyse. Sur le rendez-vous observé, il valait une seconde. |
| modifie_par | texte | Modifié par | OBS | REL-RDV.C03 | Relevé de champs, écran Donner rendez-vous, bloc Contrôle de modifications. |
| date_mod | horodatage | Date mod. | OBS | REL-RDV.C04 | Relevé de champs, écran Donner rendez-vous, bloc Contrôle de modifications. |
| confirme_par | texte | Confirmé par | OBS | REL-RDV.C05 | Relevé de champs, écran Donner rendez-vous, bloc Contrôle de modifications. Avec la colonne d'annulation, ce couple sépare une annulation déclarée d'une absence non prévenue ; sans lui, les deux se confondent. |
| date_conf | horodatage | Date conf. | OBS | REL-RDV.C06 | Relevé de champs, écran Donner rendez-vous, bloc Contrôle de modifications. |
| annule_par | texte | Annulé par | OBS | REL-RDV.C07 | Relevé de champs, écran Donner rendez-vous, bloc Contrôle de modifications. |
| date_annul | horodatage | Date annul. | OBS | REL-RDV.C08 | Relevé de champs, écran Donner rendez-vous, bloc Contrôle de modifications. |
| liste_attente_service | code | Service | OBS | REL-RDV.L01 | Relevé de champs, écran Donner rendez-vous, bloc Liste d'attente des consultations. |
| liste_attente_agenda | code | Agenda | OBS | REL-RDV.L02 | Relevé de champs, écran Donner rendez-vous, bloc Liste d'attente des consultations. |
| liste_attente_activite | code | Activité | OBS | REL-RDV.L03 | Relevé de champs, écran Donner rendez-vous, bloc Liste d'attente des consultations. |
| date_extraction | date | non_releve | HYP | sans_preuve_externe | Colonne technique de la zone d'atterrissage, absente du système observé. Elle porte la date de l'extraction dont la ligne provient et rend le rechargement d'une partition idempotent. Si une extraction réelle ne la fournissait pas, elle serait dérivée du nom du fichier partitionné, sans perte d'information. |

## source.passages

| colonne | type_metier | libelle_hosix | provenance | preuve | note |
|---|---|---|---|---|---|
| n_passage | code | non_releve | DOC | S-08 | Le module Consultas de l'éditeur documente la gestion des consultations et la production de leurs listings, ce qui suppose un identifiant de passage. |
| n_ipp | code | N° IPP | OBS | REL-PAT.D01 | Relevé de champs, fiche patient, bloc Données principales. |
| type_passage | code | non_releve | DOC | S-06 | La liste de travail du module Médicos regroupe les patients par type d'épisode : hospitalisés, consultation, urgences. Le système type donc ses épisodes. |
| service | code | non_releve | DOC | S-27 | Article 27 du règlement intérieur : l'hôpital s'organise en services, et l'activité s'y rattache. |
| activite | code | Activité | OBS | REL-RDV.R02 | Relevé de champs, écran Donner rendez-vous, bloc Rendez-vous. Le même référentiel d'activités qualifie le rendez-vous et le passage qui l'honore. |
| n_rdv | code | non_releve | HYP | sans_preuve_externe | La colonne rattache le passage au rendez-vous qui l'a programmé, et hérite du caractère hypothétique de l'identifiant de rendez-vous lui-même, qui n'apparaît sur aucun écran. Elle est nullable : un passage peut survenir sans rendez-vous préalable. Si le système en place ne conservait pas ce rattachement, le délai d'obtention resterait mesurable sur la table des rendez-vous, mais le taux d'honoration des rendez-vous ne le serait plus. |
| mode_prise_en_charge | code | non_releve | DOC | S-18 | Le tiers payant distingue les modes de prise en charge selon le régime et le caractère ambulatoire ou hospitalier de la prestation. |
| date_heure_entree | horodatage | non_releve | DOC | S-08 | Le module Consultas gère la programmation et le déroulement de la consultation, dont l'heure d'entrée. |
| date_heure_sortie | horodatage | non_releve | DOC | S-08 | Idem, borne de fin du passage. |
| medecin | texte | non_releve | DOC | S-06 | Le module Médicos rattache l'épisode au praticien qui le prend en charge. |
| cree_par | texte | Créé par | OBS | REL-RDV.C01 | Relevé de champs, écran Donner rendez-vous, bloc Contrôle de modifications. Le même bloc d'audit est reproduit d'un écran à l'autre. |
| date_creation | horodatage | Date création | OBS | REL-RDV.C02 | Relevé de champs, écran Donner rendez-vous, bloc Contrôle de modifications. Le même bloc d'audit est reproduit d'un écran à l'autre. |
| date_extraction | date | non_releve | HYP | sans_preuve_externe | Colonne technique de la zone d'atterrissage, absente du système observé. Elle porte la date de l'extraction dont la ligne provient et rend le rechargement d'une partition idempotent. Si une extraction réelle ne la fournissait pas, elle serait dérivée du nom du fichier partitionné, sans perte d'information. |

## source.mouvements

| colonne | type_metier | libelle_hosix | provenance | preuve | note |
|---|---|---|---|---|---|
| n_sejour | code | non_releve | DOC | S-27 | Article 40 : les formalités d'admission ouvrent un dossier de séjour identifié. |
| n_ipp | code | N° IPP | OBS | REL-PAT.D01 | Relevé de champs, fiche patient, bloc Données principales. |
| date_heure_admission | horodatage | non_releve | DOC | S-27 | Article 40, formalités d'admission ordinaire. |
| mode_admission | code | non_releve | DOC | S-27 | Articles 40, 42 et 45 : l'admission est ordinaire ou en urgence, et les formalités diffèrent. |
| service_accueil | code | non_releve | DOC | S-27 | Article 44 : l'hospitalisation est ordonnée vers un service. |
| lit | texte | non_releve | HYP | sans_preuve_externe | Aucune source ne documente l'identification du lit occupé, alors que la capacité litière fonctionnelle est publiée par établissement et que l'article 42 impose l'admission même en cas d'indisponibilité de lits, ce qui suppose un suivi de l'occupation. La colonne est posée parce que le taux d'occupation du tableau de bord se recalcule depuis les journées d'hospitalisation, non depuis les lits ; si elle était fausse ou absente, aucun indicateur du chapitre sur l'activité ne changerait. |
| n_mutation | code | non_releve | DOC | S-27 | Article 35 : le service gère les effectifs des patients et leurs mouvements à l'intérieur de l'hôpital. |
| service_origine | code | non_releve | DOC | S-27 | Article 35, mouvements internes. |
| service_destination | code | non_releve | DOC | S-27 | Article 35, mouvements internes. |
| date_heure_mutation | horodatage | non_releve | DOC | S-27 | Article 35, mouvements internes. |
| date_heure_sortie | horodatage | non_releve | DOC | S-27 | Article 79 : les formalités de sortie closent le séjour. |
| mode_sortie | code | non_releve | DOC | S-27 | Articles 79 et 80 : sortie régulière avec billet, sortie à l'insu du personnel, décès. |
| date_extraction | date | non_releve | HYP | sans_preuve_externe | Colonne technique de la zone d'atterrissage, absente du système observé. Elle porte la date de l'extraction dont la ligne provient et rend le rechargement d'une partition idempotent. Si une extraction réelle ne la fournissait pas, elle serait dérivée du nom du fichier partitionné, sans perte d'information. |

## source.prises_en_charge

| colonne | type_metier | libelle_hosix | provenance | preuve | note |
|---|---|---|---|---|---|
| n_prise_en_charge | code | non_releve | DOC | S-27 | Article 79 : les formalités de sortie comportent la signature des documents de prise en charge, document identifié. |
| n_ipp | code | N° IPP | OBS | REL-PAT.D01 | Relevé de champs, fiche patient, bloc Données principales. |
| n_episode | code | non_releve | DOC | S-27 | Article 79 : la prise en charge se rattache à l'épisode qu'elle couvre. |
| type_episode | code | non_releve | DOC | S-27 | Article 36 : taxonomie réglementaire des modes d'utilisation de l'hôpital. |
| organisme | code | non_releve | DOC | S-15 | Les régimes de l'assurance maladie obligatoire sont distincts et l'organisme gestionnaire diffère de l'un à l'autre. |
| n_assure | texte | N° Assu | OBS | REL-PAT.A03 | Relevé de champs, fiche patient, bloc Compagnie d'assurance. |
| date_verification | horodatage | non_releve | DOC | S-27 | Article 40 : le patient présente les documents exigés selon son statut de couverture, ce qui date la vérification. |
| etat | code | non_releve | DOC | S-19 | Aucune demande de prise en charge préalable n'est exigée dans le secteur public : l'état constate l'ouverture des droits, il n'enregistre pas un accord. Valeurs retenues : droits ouverts, droits fermés, non vérifié. |
| taux_prise_en_charge | decimal | non_releve | DOC | S-18 | Cent pour cent de la tarification nationale de référence en hospitalisation et en hôpital de jour, quatre-vingts pour cent en ambulatoire au-delà de deux cents dirhams. |
| date_extraction | date | non_releve | HYP | sans_preuve_externe | Colonne technique de la zone d'atterrissage, absente du système observé. Elle porte la date de l'extraction dont la ligne provient et rend le rechargement d'une partition idempotent. Si une extraction réelle ne la fournissait pas, elle serait dérivée du nom du fichier partitionné, sans perte d'information. |

## source.factures

| colonne | type_metier | libelle_hosix | provenance | preuve | note |
|---|---|---|---|---|---|
| n_facture | code | non_releve | DOC | S-09 | Le module Facturación de Hosix Core documente l'émission de factures et de listings personnalisés, ce qui suppose un identifiant de facture. |
| n_ipp | code | N° IPP | OBS | REL-PAT.D01 | Relevé de champs, fiche patient, bloc Données principales. |
| n_episode | code | non_releve | DOC | S-09 | Le module Facturación récupère dans chacun des autres modules l'information nécessaire à la facturation en captant les mouvements générés, ce qui suppose un identifiant d'épisode rattaché. |
| type_episode | code | non_releve | DOC | S-27 | L'article 36 du règlement intérieur des hôpitaux établit une taxonomie réglementaire des modes d'utilisation de l'hôpital, que la facture doit porter. |
| code_diagnostic_cim10 | code | non_releve | DOC | S-27 | L'article 35 du règlement intérieur impose d'établir la facturation sur la base de la classification des maladies, soit la CIM-10. |
| date_facture | date | non_releve | DOC | S-09 | Le module Facturación de l'éditeur documente l'émission de factures, ce qui suppose une date d'émission. |
| type_facture | code | non_releve | DOC | S-09 | Le module Facturación admet la facturation aux entités publiques, aux entités privées et particuliers, et aux mutuelles d'accidents. |
| service_emetteur | code | non_releve | DOC | S-27 | L'article 35 du règlement intérieur charge le service d'accueil et d'admission d'établir la facturation, ce qui rattache chaque facture à un service émetteur. |
| etat | code | non_releve | DOC | S-09 | Le module Facturación contrôle explicitement l'état des activités réalisées : facturées, en attente de facturation, et autres états. |
| montant_total | decimal | non_releve | DOC | S-17 | Le montant se calcule sur la grille des lettres clés de la tarification nationale de référence du secteur public. |
| part_organisme | decimal | non_releve | DOC | S-18 | Les taux de prise en charge de la tarification nationale de référence fixent la part organisme à 100 % en hospitalisation et hôpital de jour, et à 80 % en ambulatoire au-delà de 200 dirhams. |
| part_patient | decimal | non_releve | DOC | S-18 | La part patient est le complément de la part organisme, sauf pour les bénéficiaires du régime AMO-Tadamon en structure publique où l'État prend en charge le ticket modérateur et où la part patient devient nulle, comme l'établit une seconde source (S-15). |
| cree_par | texte | Créé par | OBS | REL-RDV.C01 | Relevé de champs, écran Donner rendez-vous, bloc Contrôle de modifications. Le même bloc d'audit est reproduit d'un écran à l'autre. |
| date_creation | horodatage | Date création | OBS | REL-RDV.C02 | Relevé de champs, écran Donner rendez-vous, bloc Contrôle de modifications. Le même bloc d'audit est reproduit d'un écran à l'autre. |
| date_extraction | date | non_releve | HYP | sans_preuve_externe | Colonne technique de la zone d'atterrissage, absente du système observé. Elle porte la date de l'extraction dont la ligne provient et rend le rechargement d'une partition idempotent. Si une extraction réelle ne la fournissait pas, elle serait dérivée du nom du fichier partitionné, sans perte d'information. |

## source.lignes_facture

| colonne | type_metier | libelle_hosix | provenance | preuve | note |
|---|---|---|---|---|---|
| n_facture | code | non_releve | DOC | S-09 | Le module Facturación de l'éditeur documente l'émission de factures composées de lignes. |
| n_ligne | entier | non_releve | DOC | S-09 | Le module Facturación produit une documentation et des listings personnalisés composés de lignes détaillées. |
| code_acte | code | non_releve | DOC | S-27 | L'article 35 du règlement intérieur impose une facturation sur la base des nomenclatures des actes, et la grille des lettres clés du secteur public rattache un code à chaque acte. |
| libelle_acte | texte | non_releve | DOC | S-17 | La grille des lettres clés de la tarification nationale de référence du secteur public porte un libellé pour chaque acte, en complément de la nomenclature imposée par l'article 35 du règlement intérieur. |
| lettre_cle | code | non_releve | DOC | S-17 | La tarification nationale de référence rémunère l'acte par une lettre clé et un coefficient. |
| coefficient | decimal | non_releve | DOC | S-17 | La tarification nationale de référence rémunère l'acte par une lettre clé et un coefficient. |
| quantite | entier | non_releve | HYP | sans_preuve_externe | La structure d'une ligne de facturation hospitalière comporte usuellement une quantité distincte du coefficient de la lettre clé, mais aucune des sources ouvertes ne la documente pour le secteur public marocain. La colonne est posée parce que sans elle un acte répété le même jour se confondrait avec un acte unique. Si elle était absente du système réel, les montants resteraient exacts et seul le dénombrement des actes par ligne serait affecté. |
| tarif_unitaire | decimal | non_releve | DOC | S-17 | Le tarif unitaire se lit sur la grille des lettres clés de la tarification nationale de référence. |
| montant | decimal | non_releve | DOC | S-17 | Le montant de la ligne se calcule sur la grille des lettres clés de la tarification nationale de référence. |
| service_executant | code | non_releve | DOC | S-09 | Le module Facturación rattache chaque activité facturable au service qui l'a exécutée. |
| date_acte | date | non_releve | DOC | S-27 | L'article 42 du règlement intérieur dispose qu'aux urgences la facturation n'est entamée qu'après l'engagement de la prise en charge médicale, ce qui date l'acte facturé. |
| date_extraction | date | non_releve | HYP | sans_preuve_externe | Colonne technique de la zone d'atterrissage, absente du système observé. Elle porte la date de l'extraction dont la ligne provient et rend le rechargement d'une partition idempotent. Si une extraction réelle ne la fournissait pas, elle serait dérivée du nom du fichier partitionné, sans perte d'information. |

## source.passages_urgences

| colonne | type_metier | libelle_hosix | provenance | preuve | note |
|---|---|---|---|---|---|
| n_passage | code | non_releve | DOC | S-27 | L'article 45 du règlement intérieur prescrit que les formalités d'admission en urgence sont enregistrées, ce qui identifie chaque passage. |
| n_ipp | code | N° IPP | OBS | REL-PAT.D01 | Relevé de champs, fiche patient, bloc Données principales. |
| date_heure_arrivee | horodatage | non_releve | DOC | S-27 | L'article 42 du règlement intérieur fait de l'accueil aux urgences l'acte fondateur du passage. |
| mode_arrivee | code | non_releve | DOC | S-12 | Le mode d'arrivée aux urgences est documenté par la protection civile, l'ambulance SMUR, les moyens propres et le transport privé. |
| motif_recours | code | non_releve | DOC | S-13 | L'étude sur le recours non approprié aux urgences classe les motifs de consultation par chapitre de la CIM-10. |
| niveau_tri | code | non_releve | DOC | S-12 | Les chiffres du ministère répartissent les passages entre urgences vitales, environ 10 %, et consultations médicales non urgentes, 64 %, le solde de 26 % correspondant aux urgences réelles non vitales. Réserve : cette source ne distingue que trois groupes de gravité, tandis que le modèle retient cinq niveaux ; la colonne existe, c'est son échelle qui reste ouverte. |
| date_heure_pec_medicale | horodatage | non_releve | DOC | S-27 | L'article 42 du règlement intérieur dispose que la procédure de facturation n'est entamée qu'après l'engagement de la prise en charge médicale, ce qui date cet engagement. |
| date_heure_sortie | horodatage | non_releve | DOC | S-27 | L'article 43 du règlement intérieur impose au patient admis aux urgences de s'acquitter des frais avant sa sortie, ce que le règlement précède. |
| orientation_sortie | code | non_releve | DOC | S-27 | Les articles 42, 44, 46 et 47 du règlement intérieur distinguent le retour à domicile, l'hospitalisation, le transfert, la sortie contre avis médical et le décès comme issues du passage. |
| service_orientation | code | non_releve | DOC | S-27 | L'article 44 du règlement intérieur dispose que l'hospitalisation d'urgence est ordonnée vers un service. |
| motif_transfert | code | non_releve | DOC | S-27 | L'article 47 du règlement intérieur prévoit le transfert lorsque les soins requis relèvent d'une discipline ou d'une technique n'existant pas à l'hôpital. |
| consentement_transfert | booleen | non_releve | DOC | S-27 | L'article 47 du règlement intérieur exige le consentement écrit du patient pour un transfert, sauf extrême urgence. |
| famille_informee | booleen | non_releve | DOC | S-27 | Les articles 47 et 67 du règlement intérieur imposent d'informer la famille, lors d'un transfert comme pour un patient mineur, incapable ou inconscient. |
| inventaire_effets | booleen | non_releve | DOC | S-27 | L'article 45 du règlement intérieur impose un inventaire contradictoire des effets personnels lorsque le patient est inconscient. |
| date_extraction | date | non_releve | HYP | sans_preuve_externe | Colonne technique de la zone d'atterrissage, absente du système observé. Elle porte la date de l'extraction dont la ligne provient et rend le rechargement d'une partition idempotent. Si une extraction réelle ne la fournissait pas, elle serait dérivée du nom du fichier partitionné, sans perte d'information. |

## source.encaissements

| colonne | type_metier | libelle_hosix | provenance | preuve | note |
|---|---|---|---|---|---|
| n_encaissement | code | non_releve | DOC | S-27 | L'article 79 du règlement intérieur range le règlement des frais parmi les formalités de sortie, ce qui identifie chaque encaissement. |
| n_facture | code | non_releve | DOC | S-27 | L'article 79 du règlement intérieur rattache le règlement des frais à la facture émise. |
| date_encaissement | horodatage | non_releve | DOC | S-27 | L'article 79 du règlement intérieur date le règlement des frais parmi les formalités de sortie. |
| mode_reglement | code | non_releve | HYP | sans_preuve_externe | Aucune source ouverte ne documente les moyens de paiement acceptés au guichet d'un hôpital public marocain ; la Cour des comptes décrit seulement un versement direct chez le régisseur. La colonne est posée parce que la page de recouvrement du tableau de bord distingue les canaux d'encaissement. Si la répartition retenue était fausse, aucun taux de recouvrement ni aucune ancienneté de créance n'en serait affecté, ces grandeurs ne dépendant que du montant et de la date. |
| montant | decimal | non_releve | DOC | S-18 | Le montant encaissé suit les taux de prise en charge de la tarification nationale de référence. |
| regisseur | texte | non_releve | DOC | S-20 | Le rapport de la Cour des comptes décrit un paiement direct chez le régisseur. |
| billet_sortie_delivre | booleen | non_releve | DOC | S-27 | L'article 79 du règlement intérieur conditionne la délivrance du billet de sortie au règlement des frais ou à la signature des documents de prise en charge. |
| date_extraction | date | non_releve | HYP | sans_preuve_externe | Colonne technique de la zone d'atterrissage, absente du système observé. Elle porte la date de l'extraction dont la ligne provient et rend le rechargement d'une partition idempotent. Si une extraction réelle ne la fournissait pas, elle serait dérivée du nom du fichier partitionné, sans perte d'information. |

## source.creances

| colonne | type_metier | libelle_hosix | provenance | preuve | note |
|---|---|---|---|---|---|
| n_creance | code | non_releve | DOC | S-27 | L'article 9, paragraphe b, du règlement intérieur charge le pôle des affaires administratives du recouvrement des créances de l'établissement, ce qui identifie chaque créance. |
| n_facture | code | non_releve | DOC | S-27 | L'article 9, paragraphe b, du règlement intérieur rattache la créance recouvrée à la facture qui l'a fait naître. |
| date_naissance_creance | date | non_releve | DOC | S-27 | L'article 79 du règlement intérieur fait naître la créance aux formalités de sortie, lorsque la facturation n'est pas soldée. |
| montant_du | decimal | non_releve | DOC | S-20 | Le rapport de la Cour des comptes établit l'existence d'un état des prestations non recouvrées, dont le montant dû. |
| montant_recouvre | decimal | non_releve | DOC | S-20 | Le rapport de la Cour des comptes établit l'existence d'un état des prestations non recouvrées, dont le montant recouvré. |
| montant_restant | decimal | non_releve | DOC | S-20 | Le rapport de la Cour des comptes établit l'existence d'un état des prestations non recouvrées, dont le montant restant dû. Cette colonne est conservée bien qu'elle se déduise des deux colonnes voisines : sa redondance interne à la ligne ne dépend pas de la date de lecture, et l'écart éventuel entre les trois montants est un contrôle de cohérence exploitable. |
| type_debiteur | code | non_releve | DOC | S-09 | Le module Facturación distingue les débiteurs publics, privés, mutualistes et particuliers. |
| motif_non_recouvrement | code | non_releve | DOC | S-20 | Le rapport de la Cour des comptes relève des sorties sans règlement, des patients non identifiés et des évasions comme motifs de non-recouvrement. |
| date_extraction | date | non_releve | HYP | sans_preuve_externe | Colonne technique de la zone d'atterrissage, absente du système observé. Elle porte la date de l'extraction dont la ligne provient et rend le rechargement d'une partition idempotent. Si une extraction réelle ne la fournissait pas, elle serait dérivée du nom du fichier partitionné, sans perte d'information. |

## source.relances

| colonne | type_metier | libelle_hosix | provenance | preuve | note |
|---|---|---|---|---|---|
| n_relance | code | non_releve | HYP | sans_preuve_externe | Aucune source ouverte ne documente une procédure de relance formalisée dans cet établissement ; le rapport de la Cour des comptes constate au contraire l'absence de diligences de recouvrement. La colonne identifie chaque relance parce que la page de recouvrement du tableau de bord la mobilise ; ce que la chaîne démontre ici est la calculabilité de l'indicateur, non une mesure. |
| n_creance | code | non_releve | HYP | sans_preuve_externe | Aucune source ouverte ne documente une procédure de relance formalisée ; la seule source disponible sur le recouvrement décrit au contraire son absence. La colonne rattache la relance à la créance parce que le tableau de bord en a besoin pour sa page recouvrement ; elle démontre une calculabilité, non une pratique observée. |
| date_relance | date | non_releve | HYP | sans_preuve_externe | Aucune source ouverte ne documente de procédure de relance formalisée dans cet établissement, et le rapport de la Cour des comptes constate précisément l'absence de diligences de recouvrement. La date de relance est posée parce que la page de recouvrement du tableau de bord en a besoin ; elle atteste une calculabilité, non un fait mesuré. |
| canal | code | non_releve | HYP | sans_preuve_externe | Aucune source ouverte ne documente les canaux de relance employés dans cet établissement ; la source disponible sur le recouvrement décrit au contraire une carence de diligences. La colonne existe parce que le tableau de bord distingue les canaux à sa page recouvrement ; elle démontre une capacité de calcul, pas une observation. |
| resultat | code | non_releve | HYP | sans_preuve_externe | Aucune source ouverte ne documente le résultat d'une procédure de relance dans cet établissement, dont la seule source disponible sur le recouvrement décrit l'absence de diligences. La colonne est posée parce que la page de recouvrement du tableau de bord en a besoin ; ce qu'elle démontre est une calculabilité, non une mesure. |
| date_extraction | date | non_releve | HYP | sans_preuve_externe | Colonne technique de la zone d'atterrissage, absente du système observé. Elle porte la date de l'extraction dont la ligne provient et rend le rechargement d'une partition idempotent. Si une extraction réelle ne la fournissait pas, elle serait dérivée du nom du fichier partitionné, sans perte d'information. |
