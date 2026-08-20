<!-- Fichier produit mécaniquement : ne pas modifier à la main. -->

# Relevé de champs — MSM - GESTION DE RDV

Observation du 2026-07-28.

## DEM — Écran de démarrage

### I — Identification du site

| id | libelle | type_apparent | saisie | valeurs_observees |
|---|---|---|---|---|
| REL-DEM.I01 | Identification du site | texte | sans_objet | `005 Fès-Meknès; Sidi Said` |
| REL-DEM.I02 | Ministère de tutelle | texte | sans_objet | `Ministère de la Santé` |

- `REL-DEM.I01` : La graphie exacte du séparateur entre le code de région et le nom de l'établissement est celle relevée à l'écran.

### P — Profils applicatifs

| id | libelle | type_apparent | saisie | valeurs_observees |
|---|---|---|---|---|
| REL-DEM.P01 | MSM - FACTURATION SAA | liste | sans_objet | aucune valeur observée |
| REL-DEM.P02 | MSM - GESTION DE RDV | liste | sans_objet | aucune valeur observée |
| REL-DEM.P03 | MSM - RECOUVREMENT | liste | sans_objet | aucune valeur observée |
| REL-DEM.P04 | MSM - URGENCE | liste | sans_objet | aucune valeur observée |
| REL-DEM.P05 | MSM RAPPORTS ET STATISTIQUES | liste | sans_objet | aucune valeur observée |

- `REL-DEM.P02` : Seul profil dont les habilitations ont été accordées au poste. Les quatre autres sont relevés à l'écran de démarrage sans avoir été ouverts.
- `REL-DEM.P05` : Libellé dépourvu du tiret séparateur que portent les quatre autres profils. Reproduit tel qu'affiché.

### M — Menus principaux

| id | libelle | type_apparent | saisie | valeurs_observees |
|---|---|---|---|---|
| REL-DEM.M01 | Hosix.NET | menu | sans_objet | aucune valeur observée |
| REL-DEM.M02 | Données Patient | menu | sans_objet | aucune valeur observée |
| REL-DEM.M03 | Centre de Consultation | menu | sans_objet | aucune valeur observée |
| REL-DEM.M04 | Factures | menu | sans_objet | aucune valeur observée |

## IPP — Recherche d'IPP

### O — Onglets

| id | libelle | type_apparent | saisie | valeurs_observees |
|---|---|---|---|---|
| REL-IPP.O01 | Chercher | onglet | sans_objet | aucune valeur observée |
| REL-IPP.O02 | Chercher MPI | onglet | sans_objet | aucune valeur observée |
| REL-IPP.O03 | Chercher MPI Pondéré | onglet | sans_objet | aucune valeur observée |
| REL-IPP.O04 | Nouvel IPP | onglet | sans_objet | aucune valeur observée |

- `REL-IPP.O03` : Onglet de recherche pondérée sur l'index maître des patients. Avec la colonne de résultat Probabilité, il atteste que le rapprochement probabiliste d'identités est une fonction du système en place.

### C — Critères de recherche

| id | libelle | type_apparent | saisie | valeurs_observees |
|---|---|---|---|---|
| REL-IPP.C01 | N° document | texte | non_determine | `C.I.N` |
| REL-IPP.C02 | Nom | texte | non_determine | aucune valeur observée |
| REL-IPP.C03 | Prénom | texte | non_determine | aucune valeur observée |
| REL-IPP.C04 | Date de naissance | date | non_determine | aucune valeur observée |
| REL-IPP.C05 | Mois | entier | non_determine | aucune valeur observée |
| REL-IPP.C06 | Année | entier | non_determine | aucune valeur observée |
| REL-IPP.C07 | Approximation en années | entier | non_determine | aucune valeur observée |
| REL-IPP.C08 | Âge | entier | non_determine | aucune valeur observée |
| REL-IPP.C09 | Téléphone | texte | non_determine | aucune valeur observée |
| REL-IPP.C10 | N° document de contact | texte | non_determine | aucune valeur observée |
| REL-IPP.C11 | Sexe | liste | non_determine | aucune valeur observée |
| REL-IPP.C12 | État civil | liste | non_determine | aucune valeur observée |
| REL-IPP.C13 | N° assuré | texte | non_determine | aucune valeur observée |

- `REL-IPP.C02` : Le relevé de l'observation porte un critère unique formulé « nom et prénom ». Il est restitué en deux lignes, l'écran présentant deux zones distinctes ; la scission reste à confirmer.
- `REL-IPP.C03` : Le relevé de l'observation porte un critère unique formulé « nom et prénom ». Il est restitué en deux lignes, l'écran présentant deux zones distinctes ; la scission reste à confirmer.

### F — Filtres de population

| id | libelle | type_apparent | saisie | valeurs_observees |
|---|---|---|---|---|
| REL-IPP.F01 | Patients Hospitalisés | option | sans_objet | aucune valeur observée |
| REL-IPP.F02 | Patients aux Urgences | option | sans_objet | aucune valeur observée |
| REL-IPP.F03 | Tous les patients | option | sans_objet | aucune valeur observée |
| REL-IPP.F04 | Exitus | case_a_cocher | sans_objet | aucune valeur observée |

- `REL-IPP.F04` : Filtre sur les patients décédés. Terme latin employé tel quel par l'interface.

### R — Colonnes de résultat

| id | libelle | type_apparent | saisie | valeurs_observees |
|---|---|---|---|---|
| REL-IPP.R01 | IPP | colonne | sans_objet | aucune valeur observée |
| REL-IPP.R02 | Nom | colonne | sans_objet | aucune valeur observée |
| REL-IPP.R03 | D. Naissance | colonne | sans_objet | aucune valeur observée |
| REL-IPP.R04 | N° pièce d'identité | colonne | sans_objet | aucune valeur observée |
| REL-IPP.R05 | N° Assu | colonne | sans_objet | aucune valeur observée |
| REL-IPP.R06 | E. Civil | colonne | sans_objet | aucune valeur observée |
| REL-IPP.R07 | Tél | colonne | sans_objet | aucune valeur observée |
| REL-IPP.R08 | Sexe | colonne | sans_objet | aucune valeur observée |
| REL-IPP.R09 | Province | colonne | sans_objet | aucune valeur observée |
| REL-IPP.R10 | Ville | colonne | sans_objet | aucune valeur observée |
| REL-IPP.R11 | Code postal | colonne | sans_objet | aucune valeur observée |
| REL-IPP.R12 | Probabilité | colonne | sans_objet | aucune valeur observée |

- `REL-IPP.R12` : Colonne de score de rapprochement. Aucune échelle ni aucun seuil n'est affiché à l'écran.

## PAT — Fiche patient

### B — Barre d'actions

| id | libelle | type_apparent | saisie | valeurs_observees |
|---|---|---|---|---|
| REL-PAT.B01 | Nouveau | bouton | sans_objet | aucune valeur observée |
| REL-PAT.B02 | Enregistrer | bouton | sans_objet | aucune valeur observée |
| REL-PAT.B03 | Supprimer | bouton | sans_objet | aucune valeur observée |
| REL-PAT.B04 | Chercher | bouton | sans_objet | aucune valeur observée |
| REL-PAT.B05 | Imprimer | bouton | sans_objet | aucune valeur observée |
| REL-PAT.B06 | Caractéristiques | bouton | sans_objet | aucune valeur observée |
| REL-PAT.B07 | Identificateurs | bouton | sans_objet | aucune valeur observée |
| REL-PAT.B08 | Remplacer l'historique | bouton | sans_objet | aucune valeur observée |
| REL-PAT.B09 | Données de l'assuré | bouton | sans_objet | aucune valeur observée |
| REL-PAT.B10 | Données de la CNSS | bouton | sans_objet | aucune valeur observée |

- `REL-PAT.B10` : Bouton d'accès aux données de l'organisme d'assurance maladie du secteur privé.

### T — Onglets

| id | libelle | type_apparent | saisie | valeurs_observees |
|---|---|---|---|---|
| REL-PAT.T01 | Général | onglet | sans_objet | aucune valeur observée |
| REL-PAT.T02 | Contacts | onglet | sans_objet | aucune valeur observée |
| REL-PAT.T03 | Quota soins primaires | onglet | sans_objet | aucune valeur observée |

### D — Données principales

| id | libelle | type_apparent | saisie | valeurs_observees |
|---|---|---|---|---|
| REL-PAT.D01 | N° IPP | texte | non_determine | aucune valeur observée |
| REL-PAT.D02 | Nom | texte | non_determine | aucune valeur observée |
| REL-PAT.D03 | Nom de famille 1 | texte | non_determine | aucune valeur observée |
| REL-PAT.D04 | Nom de famille 2 | texte | non_determine | aucune valeur observée |
| REL-PAT.D05 | Sexe | liste | non_determine | aucune valeur observée |
| REL-PAT.D06 | D. Nai | date | non_determine | aucune valeur observée |
| REL-PAT.D07 | Âge | entier | non_determine | aucune valeur observée |
| REL-PAT.D08 | Num | non_determine | non_determine | aucune valeur observée |
| REL-PAT.D09 | Type pièce d'identité | liste | non_determine | `C`, `C.I.N` |
| REL-PAT.D10 | N° pièce d'identité | texte | non_determine | aucune valeur observée |
| REL-PAT.D11 | E. Civil | liste | non_determine | `C`, `CÉLIBATAIRE` |
| REL-PAT.D12 | Type patient | liste | non_determine | aucune valeur observée |
| REL-PAT.D13 | Date photo | date | non_determine | aucune valeur observée |
| REL-PAT.D14 | Modifié par | texte | non_determine | aucune valeur observée |
| REL-PAT.D15 | Créé par | texte | non_determine | aucune valeur observée |
| REL-PAT.D16 | Date d'attribution | date | non_determine | aucune valeur observée |

- `REL-PAT.D08` : Libellé relevé tel qu'affiché. La nature de la donnée qu'il porte n'a pas été observée. Le même libellé apparaît au bloc d'identification de l'écran de rendez-vous.
- `REL-PAT.D09` : Liste à code et libellé. Le code et le libellé sont affichés côte à côte.
- `REL-PAT.D11` : Liste à code et libellé. Le code et le libellé sont affichés côte à côte.

### A — Compagnie d'assurance

| id | libelle | type_apparent | saisie | valeurs_observees |
|---|---|---|---|---|
| REL-PAT.A01 | Compagnie d'assur. | liste | non_determine | `00116`, `CNSS PIPC` |
| REL-PAT.A02 | Police | texte | non_determine | aucune valeur observée |
| REL-PAT.A03 | N° Assu | texte | non_determine | aucune valeur observée |
| REL-PAT.A04 | Profession | texte | non_determine | aucune valeur observée |
| REL-PAT.A05 | Num. inscription | texte | non_determine | aucune valeur observée |
| REL-PAT.A06 | Date inscription | date | non_determine | aucune valeur observée |

### H — Domicile

| id | libelle | type_apparent | saisie | valeurs_observees |
|---|---|---|---|---|
| REL-PAT.H01 | Type | liste | non_determine | aucune valeur observée |
| REL-PAT.H02 | Adresse | texte | non_determine | aucune valeur observée |
| REL-PAT.H03 | Code postal | texte | non_determine | aucune valeur observée |
| REL-PAT.H04 | État | liste | non_determine | aucune valeur observée |
| REL-PAT.H05 | Ville | liste | non_determine | aucune valeur observée |
| REL-PAT.H06 | Quartier | texte | non_determine | aucune valeur observée |
| REL-PAT.H07 | Nationalité | liste | non_determine | `504`, `MAROC` |
| REL-PAT.H08 | Téléphone 1 | texte | non_determine | aucune valeur observée |
| REL-PAT.H09 | Téléphone 2 | texte | non_determine | aucune valeur observée |
| REL-PAT.H10 | Téléphone 3 | texte | non_determine | aucune valeur observée |
| REL-PAT.H11 | Téléphone 4 | texte | non_determine | aucune valeur observée |
| REL-PAT.H12 | Avertissements SMS | case_a_cocher | non_determine | aucune valeur observée |
| REL-PAT.H13 | E-mail | texte | non_determine | aucune valeur observée |
| REL-PAT.H14 | Avertissements e-mail | case_a_cocher | non_determine | aucune valeur observée |
| REL-PAT.H15 | Environnement | liste | non_determine | aucune valeur observée |

- `REL-PAT.H12` : Case d'envoi d'avertissements par message court. Le champ existe et n'est pas exploité par le service.

### N — Né

| id | libelle | type_apparent | saisie | valeurs_observees |
|---|---|---|---|---|
| REL-PAT.N01 | Nom. Père | texte | non_determine | aucune valeur observée |
| REL-PAT.N02 | Nom. Mère | texte | non_determine | aucune valeur observée |
| REL-PAT.N03 | Lieu de naissance - État | liste | non_determine | aucune valeur observée |
| REL-PAT.N04 | Ville | liste | non_determine | aucune valeur observée |
| REL-PAT.N05 | Pays | liste | non_determine | `504`, `MAROC` |
| REL-PAT.N06 | Quartier | texte | non_determine | aucune valeur observée |

### K — Commentaire

| id | libelle | type_apparent | saisie | valeurs_observees |
|---|---|---|---|---|
| REL-PAT.K01 | Commentaire | zone_texte | non_determine | aucune valeur observée |

## RDV — Donner rendez-vous

### B — Barre d'actions

| id | libelle | type_apparent | saisie | valeurs_observees |
|---|---|---|---|---|
| REL-RDV.B01 | Nouveau | bouton | sans_objet | aucune valeur observée |
| REL-RDV.B02 | Enregistrer | bouton | sans_objet | aucune valeur observée |
| REL-RDV.B03 | Supprimer | bouton | sans_objet | aucune valeur observée |
| REL-RDV.B04 | Chercher | bouton | sans_objet | aucune valeur observée |
| REL-RDV.B05 | Imprimer | bouton | sans_objet | aucune valeur observée |
| REL-RDV.B06 | Autres | bouton | sans_objet | aucune valeur observée |
| REL-RDV.B07 | Couvertures | bouton | sans_objet | aucune valeur observée |

### I — Identification du patient

| id | libelle | type_apparent | saisie | valeurs_observees |
|---|---|---|---|---|
| REL-RDV.I01 | N° IPP | texte | non_determine | aucune valeur observée |
| REL-RDV.I02 | Téléphone | texte | non_determine | aucune valeur observée |
| REL-RDV.I03 | Compagnie | liste | non_determine | aucune valeur observée |
| REL-RDV.I04 | N° Assu | texte | non_determine | aucune valeur observée |
| REL-RDV.I05 | Âge | entier | non_determine | aucune valeur observée |
| REL-RDV.I06 | Date naissance | date | non_determine | aucune valeur observée |
| REL-RDV.I07 | C.I.N | texte | non_determine | aucune valeur observée |
| REL-RDV.I08 | Num | non_determine | non_determine | aucune valeur observée |
| REL-RDV.I09 | Adresse | texte | non_determine | aucune valeur observée |
| REL-RDV.I10 | Ville | liste | non_determine | aucune valeur observée |

- `REL-RDV.I08` : Même libellé qu'au bloc de données principales de la fiche patient. Nature non observée.

### R — Rendez-vous

| id | libelle | type_apparent | saisie | valeurs_observees |
|---|---|---|---|---|
| REL-RDV.R01 | Agenda | liste | non_determine | aucune valeur observée |
| REL-RDV.R02 | Activité | liste | non_determine | aucune valeur observée |
| REL-RDV.R03 | Origine | liste | non_determine | `AU`, `AUTRES HÔPITAUX` |
| REL-RDV.R04 | Hôpital/C.S. | liste | non_determine | aucune valeur observée |
| REL-RDV.R05 | Médecin ext. | texte | non_determine | aucune valeur observée |
| REL-RDV.R06 | Service ext. | texte | non_determine | aucune valeur observée |
| REL-RDV.R07 | Observations | zone_texte | non_determine | aucune valeur observée |
| REL-RDV.R08 | Date rendez-vous | horodatage | non_determine | `07/28/2026 10:57:07 AM` |
| REL-RDV.R09 | Rendez-vous supplémentaire | case_a_cocher | non_determine | aucune valeur observée |
| REL-RDV.R10 | Type d'attention | liste | non_determine | aucune valeur observée |
| REL-RDV.R11 | État | liste | non_determine | `En instance` |
| REL-RDV.R12 | Durée | entier | non_determine | `0` |
| REL-RDV.R13 | Date réception | horodatage | non_determine | aucune valeur observée |
| REL-RDV.R14 | Imprimer données | case_a_cocher | non_determine | aucune valeur observée |

- `REL-RDV.R08` : Format d'affichage mois/jour/année sur douze heures, dans une interface en français.
- `REL-RDV.R11` : État du rendez-vous à la création.
- `REL-RDV.R12` : Durée exprimée en minutes, valeur nulle à la création.

### C — Contrôle de modifications

| id | libelle | type_apparent | saisie | valeurs_observees |
|---|---|---|---|---|
| REL-RDV.C01 | Créé par | texte | non_determine | aucune valeur observée |
| REL-RDV.C02 | Date création | horodatage | non_determine | `07/28/2026 10:57:06 AM` |
| REL-RDV.C03 | Modifié par | texte | non_determine | aucune valeur observée |
| REL-RDV.C04 | Date mod. | horodatage | non_determine | aucune valeur observée |
| REL-RDV.C05 | Confirmé par | texte | non_determine | aucune valeur observée |
| REL-RDV.C06 | Date conf. | horodatage | non_determine | aucune valeur observée |
| REL-RDV.C07 | Annulé par | texte | non_determine | aucune valeur observée |
| REL-RDV.C08 | Date annul. | horodatage | non_determine | aucune valeur observée |

- `REL-RDV.C02` : Sur le rendez-vous observé, une seconde sépare la création du rendez-vous lui-même. L'écart entre ces deux horodatages est le délai d'obtention d'un rendez-vous, grandeur centrale de l'analyse.
- `REL-RDV.C05` : Le couple confirmé par / annulé par sépare une annulation déclarée d'une absence non prévenue. Sans ce couple, les deux se confondent dans un même état non honoré.
- `REL-RDV.C07` : Le couple confirmé par / annulé par sépare une annulation déclarée d'une absence non prévenue. Sans ce couple, les deux se confondent dans un même état non honoré.

### L — Liste d'attente des consultations

| id | libelle | type_apparent | saisie | valeurs_observees |
|---|---|---|---|---|
| REL-RDV.L01 | Service | colonne | sans_objet | aucune valeur observée |
| REL-RDV.L02 | Agenda | colonne | sans_objet | aucune valeur observée |
| REL-RDV.L03 | Activité | colonne | sans_objet | aucune valeur observée |

## Champs non employés

17 champ(s) qu'aucune entrée du registre des champs n'invoque et qu'aucun chapitre du rapport ne cite. Chacun porte le motif de son groupe.

**Motif.** Boutons de la barre d'outils de la fiche patient. Ils déclenchent une opération et ne portent aucune donnée de dossier : aucune colonne n'en dérive, et les tableaux du rapport ne les reprennent pas. Leur relevé est conservé parce qu'il atteste l'agencement de l'écran, restitué par un schéma structurel.

| id |
|---|
| REL-PAT.B01 |
| REL-PAT.B02 |
| REL-PAT.B03 |
| REL-PAT.B04 |
| REL-PAT.B05 |
| REL-PAT.B06 |
| REL-PAT.B07 |
| REL-PAT.B08 |
| REL-PAT.B09 |
| REL-PAT.B10 |

**Motif.** Boutons de la barre d'outils de l'écran de prise de rendez-vous. Même raison que pour la fiche patient : une action, aucune donnée.

| id |
|---|
| REL-RDV.B01 |
| REL-RDV.B02 |
| REL-RDV.B03 |
| REL-RDV.B04 |
| REL-RDV.B05 |
| REL-RDV.B06 |
| REL-RDV.B07 |
