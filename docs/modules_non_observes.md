# Modules non observés — reconstruction documentaire

Quatre des cinq profils applicatifs du SAA n'ont pas pu être observés au poste : les habilitations Hosix cloisonnent l'accès par profil et le service n'accorde à un stagiaire que le profil `MSM - GESTION DE RDV`. Le cahier de charges portant sur l'activité du service entier, ces quatre processus sont reconstruits par voie documentaire.

Ce fichier est la condition d'existence de toute étiquette `DOC` du modèle. Aucun champ ne porte cette étiquette s'il n'apparaît pas ici avec un `source_id` présent dans `docs/sources/sources.yml`.

## Méthode

Chaque profil est traité en trois temps.

**Ce que la documentation de l'éditeur décrit.** SIVSA publie une fiche par module de Hosix.NET. Ces fiches sont commerciales : elles énoncent des fonctions, pas des schémas de données. Elles établissent qu'une fonction existe et ce qu'elle recouvre, jamais quels champs la portent.

**Ce que la réglementation marocaine impose.** L'arrêté n° 456-11 du 6 juillet 2010 portant règlement intérieur des hôpitaux prescrit les missions du service d'accueil et d'admission et les formalités qui s'y attachent. C'est la source la plus contraignante du dossier : elle dit ce que le service *doit* faire, indépendamment du logiciel qui le lui permet.

**Les champs qui en découlent.** Une fonction prescrite par la réglementation et documentée par l'éditeur implique des champs. Ceux-ci sont proposés ici avec leur source, et repris tels quels dans `docs/champs/registre_champs.yml`.

## Deux avertissements sur la nature des preuves

**Un champ `DOC` n'est pas un champ observé.** Il est déduit d'une obligation ou d'une fonction documentée. Sa dénomination exacte dans Hosix est inconnue ; seule sa nécessité fonctionnelle est établie. Les noms retenus ci-dessous sont donc des noms de modèle, non des libellés relevés — à la différence des champs `OBS` du profil observé, dont le nom est reproduit à l'identique.

**Une source qui ne dit rien ne dit pas toujours la même chose.** Trois silences se distinguent dans ce dossier et sont signalés à chaque fois qu'ils se présentent : *absent d'un recensement qui existe* (information sur l'établissement), *non recensé à aucun niveau* (silence sur la grandeur), *non descendu assez bas* (silence sur la maille).

---

# 1. Profil `MSM - FACTURATION SAA`

## 1.1 Ce que la documentation de l'éditeur décrit

Le module *Facturación* de Hosix Core [`S-09`] capte les mouvements manuellement ou automatiquement, en récupérant dans chacun des autres modules l'information nécessaire à la facturation. Il recueille toute activité de l'hôpital susceptible d'être facturée et générée par les autres modules du fait de la prise en charge des patients.

Il contrôle l'état des activités réalisées : facturées, en attente de facturation, et autres états. Il est paramétrable par l'utilisateur, par définition de groupes, de types de contrats et de types de prestations. Il admet la facturation aux entités publiques, aux entités privées et particuliers, et aux mutuelles d'accidents.

Un point de datation [`S-07`] : la migration de Hosix de WebForms vers MVC est achevée sur quatre modules, dont `facturación` et `admisión`. Le module de facturation a par ailleurs été adapté au format de facturation exigé par un ministère de la santé étranger, ce qui atteste sa paramétrabilité par pays.

## 1.2 Ce que la réglementation marocaine impose

**L'article 35 du règlement intérieur des hôpitaux** [`S-27`] range la facturation parmi les neuf missions du service d'accueil et d'admission, dans ces termes : établir la facturation des prestations et services rendus par l'hôpital **sur la base de la classification des maladies, des nomenclatures des actes et des tarifs en vigueur**.

Cette formulation impose trois référentiels distincts, et c'est la contrainte structurante de tout le module :

| Référentiel | Nature | Effet sur le modèle |
|---|---|---|
| Classification des maladies | CIM-10 | un diagnostic codé rattaché à l'épisode |
| Nomenclatures des actes | lettres clés et coefficients | une ligne de facture porte un code d'acte, pas un libellé libre |
| Tarifs en vigueur | TNR pour le remboursement, arrêté n° 221-98 pour la facturation hospitalière | deux barèmes, deux usages, à ne pas confondre |

**L'article 42** pose une règle d'ordre que le générateur doit respecter : aux urgences, la procédure de facturation n'est entamée qu'après l'engagement de la prise en charge médicale. Aucune facture ne peut donc précéder le premier acte de soin sur un passage aux urgences.

**L'article 40** décrit les formalités d'admission ordinaire : présentation d'une pièce d'identité et des documents exigés selon le statut de couverture médicale. En l'absence de régime de couverture et d'affection exonérante, le patient ou sa famille est informé de l'obligation de paiement direct de l'intégralité des frais.

**L'article 43** impose au patient admis aux urgences et non hospitalisé de s'acquitter des frais auprès du service d'accueil et d'admission préalablement à sa sortie.

**L'article 57** soumet les ressortissants étrangers aux mêmes modalités de facturation, sauf convention de soins entre le Maroc et leur pays.

**L'article 79** énumère les formalités administratives de sortie, dont la deuxième est *facturation et règlement des frais d'hospitalisation **ou** signature des documents de prise en charge*. Cette alternative est la justification directe du grain retenu pour `source.prises_en_charge` (ADR `0007`).

## 1.3 Barèmes applicables

**Tarification nationale de référence, grille des lettres clés du secteur public** [`S-17`] :

| Désignation | Lettre clé | Tarif (DH) |
|---|---|---|
| Consultation de généraliste | `C` | 50,00 |
| Consultation de spécialiste | `Cs` | 75,00 |
| Consultation psychiatre et neuropsychiatre | `CNPSY` | 100,00 |
| Consultation de professeur | `Cp` | 120,00 |
| Actes de biologie médicale | `B` | 0,90 |
| Actes d'anatomopathologie | `P` | 0,90 |
| Actes de radiologie | `Z` | 9,00 |
| Actes d'échographie | `KE` | 10,00 |
| Actes de chirurgie ou de spécialité | `K` | 13,00 |
| Actes de chirurgie dentaire | `D` | 10,00 |
| Actes de kinésithérapie, par séance | `AMM` | 40,00 |

La convention du secteur public ne comporte que deux grilles : les lettres clés et les forfaits d'actes de chirurgie. **L'établissement ne pratiquant aucune chirurgie, seule la grille des lettres clés s'applique.** Le générateur ne produit donc aucun forfait.

**Taux de prise en charge** [`S-18`, `S-19`] :

- hospitalisation et hôpital de jour dans le secteur public : **100 % de la TNR** ;
- actes d'exploration, de radiologie et d'imagerie en ambulatoire : **80 % de la TNR** ;
- ambulatoire dans le secteur public : ticket modérateur de **20 % de la TNR** au-delà de 200 DH ;
- **en dessous de 200 DH, aucun tiers payant en ambulatoire public** — la part organisme est nulle et le patient acquitte l'intégralité. Ce n'est pas un taux, c'est une règle en dur ;
- aucune demande de prise en charge préalable n'est exigée dans le secteur public.

**Un cas particulier qui touche un tiers de la file active** [`S-15`] : pour les bénéficiaires du régime AMO-Tadamon, l'État prend en charge le ticket modérateur des prestations dispensées dans les structures publiques de soins. La part patient est donc **nulle** pour ce régime, en ambulatoire comme en hospitalisation.

**Un avertissement à porter au rapport.** La TNR fixe ce que l'organisme rembourse ; l'arrêté n° 221-98 du 28 janvier 1998 fixe les tarifs des actes et prestations rendus par les centres hospitaliers, c'est-à-dire ce que l'hôpital facture [`S-32`]. Ce sont deux barèmes distincts. Le texte de l'arrêté n'a pas pu être retrouvé pendant les recherches ; le générateur assimile donc le montant facturé au tarif TNR, et cette assimilation est déclarée `HYP`.

## 1.4 Ce que la Cour des comptes ajoute

Le rapport sur le centre hospitalier préfectoral de Meknès [`S-20`] documente le fonctionnement réel de la facturation dans cet établissement, à une date antérieure au déploiement de Hosix :

- le code de la nomenclature générale des actes professionnels est à la base de la facturation de l'acte, et n'est pas toujours renseigné sur les fiches de prestations ;
- 4 370 dossiers d'hospitalisation sur 7 653 n'étaient pas facturés au titre de 2015, soit **57 % des admis** ;
- les assurés AMO versaient 20 % de la tarification au caissier **sans facture préalablement établie** ;
- aux urgences de l'hôpital Mohamed V en 2016, 3 477 patients sur 160 659 ont payé leur consultation, soit une sur quarante-six ;
- la date de sortie n'était renseignée que pour les patients ayant réglé les frais, ce qui empêchait le calcul de la durée d'hospitalisation.

Ces constats portent sur 2012-2016, **avant la généralisation de l'assurance maladie obligatoire**, qui couvre 88 % de la population depuis 2025 contre 42 % auparavant [`S-15`]. Ils fournissent une borne basse documentée pour les taux de facturation, non une valeur applicable à la période 2024-2026.

## 1.5 Champs qui en découlent

**`source.factures`**

| Champ | Provenance | Source | Justification |
|---|---|---|---|
| `n_facture` | `DOC` | `S-09` | l'éditeur documente l'émission de factures et de listings |
| `n_ipp` | `OBS` | — | relevé sur la fiche patient |
| `n_episode` | `DOC` | `S-09` | le module capte les mouvements générés par les autres modules |
| `type_episode` | `DOC` | `S-27` art. 36 | taxonomie réglementaire des modes d'utilisation |
| `code_diagnostic_cim10` | `DOC` | `S-27` art. 35 | facturation sur la base de la classification des maladies |
| `date_facture` | `DOC` | `S-09` | — |
| `type_facture` | `DOC` | `S-09` | publique, privée et particuliers, mutuelles |
| `service_emetteur` | `DOC` | `S-27` art. 35 | la facturation est établie par le SAA |
| `etat` | `DOC` | `S-09` | l'éditeur documente explicitement le contrôle de l'état : facturée, en attente |
| `montant_total` | `DOC` | `S-17` | grille des lettres clés du secteur public |
| `part_organisme` | `DOC` | `S-18` | 100 % en hospitalisation, 80 % en ambulatoire au-delà de 200 DH |
| `part_patient` | `DOC` | `S-18`, `S-15` | complément ; nulle pour AMO-Tadamon en structure publique |
| `cree_par`, `date_creation` | `OBS` | — | le bloc de contrôle des modifications est relevé sur l'écran de rendez-vous |

**`source.lignes_facture`**

| Champ | Provenance | Source |
|---|---|---|
| `n_facture`, `n_ligne` | `DOC` | `S-09` |
| `code_acte`, `libelle_acte` | `DOC` | `S-27` art. 35, `S-17` |
| `lettre_cle` | `DOC` | `S-17` |
| `coefficient` | `DOC` | `S-17` |
| `quantite` | `HYP` | structure usuelle d'une ligne de facturation, non documentée |
| `tarif_unitaire`, `montant` | `DOC` | `S-17` |
| `service_executant` | `DOC` | `S-09` |
| `date_acte` | `DOC` | `S-27` art. 42 |

**Contrainte de génération.** `dim_acte` ne contient aucun acte chirurgical, aucun acte de bactériologie et aucun acte de parasitologie : ces trois activités sont mesurées comme absentes de l'établissement [`S-30`, tableaux 77 et 79]. Aucune ligne de facture ne peut en porter.

---

# 2. Profil `MSM - RECOUVREMENT`

## 2.1 Ce que la documentation de l'éditeur décrit

SIVSA ne publie pas de fiche distincte pour le recouvrement : la fonction est intégrée au module *Facturación*, qui contrôle la situation des activités réalisées et distingue celles déjà facturées de celles restant en attente [`S-09`].

**C'est un silence à qualifier** : la documentation ne dit pas que la fonction est absente, elle ne la traite pas séparément. Le recouvrement est donc le moins documenté des quatre modules du côté de l'éditeur, et le mieux documenté du côté marocain.

## 2.2 Ce que la réglementation marocaine impose

Le recouvrement ne figure pas à l'article 35 parmi les missions du service d'accueil et d'admission. Il relève de **l'article 9, paragraphe b** [`S-27`], qui charge le pôle des affaires administratives de veiller au recouvrement des créances de l'établissement conformément à la législation et à la réglementation en vigueur.

Le processus traverse donc deux structures : la créance naît au SAA, où la facture est établie et où le règlement est encaissé à la sortie (article 79), et son recouvrement relève du pôle administratif. Cette césure organisationnelle est un fait de modélisation : `source.factures` et `source.encaissements` n'ont pas le même service responsable.

**L'article 79** énumère les quatre étapes des formalités de sortie, dans cet ordre : enregistrement des nom et prénom sur le registre des sortants ; facturation et règlement des frais, ou signature des documents de prise en charge ; restitution des effets personnels et valeurs déposés ; délivrance du billet de sortie.

**Le billet de sortie est donc conditionné au règlement ou à la signature de la prise en charge.** C'est la clé du modèle de recouvrement : un patient qui quitte l'hôpital sans billet de sortie est un patient dont la créance n'est pas soldée.

**L'article 80** traite du cas du patient quittant l'hôpital à l'insu du personnel : procès-verbal établi, transmission au directeur, information des autorités et de la famille, inscription au registre comme sortant.

## 2.3 Les quatre ancrages mesurés

Le rapport de la Cour des comptes [`S-20`] fournit, pour ce centre hospitalier :

| Grandeur | Valeur | Période |
|---|---|---|
| Ratio recettes réalisées sur recettes prévues | ≤ **42 %** | 2012–2015 |
| Dossiers d'hospitalisation non facturés | **4 370 sur 7 653**, soit 57 % | 2015 |
| Créances non recouvrées cumulées | **50 876 365 DH** | au 31/12/2016 |
| Patients quittant l'hôpital sans billet de sortie | 4 370 puis 2 789 | 2015, 2016 |
| Consultations d'urgence payées, hôpital Mohamed V | **3 477 sur 160 659** | 2016 |

La Cour relève également que le service d'admission n'effectue pas les diligences nécessaires au recouvrement des frais des malades venant des urgences, et que les patients dits « évadés » ne sont pas déclarés par les services hospitaliers, de sorte qu'aucune statistique n'en existe.

Ces cinq constats sont antérieurs à la généralisation de l'AMO. Ils bornent le modèle par le bas ; ils ne le calibrent pas.

## 2.4 Champs qui en découlent

**`source.encaissements`**

| Champ | Provenance | Source |
|---|---|---|
| `n_encaissement` | `DOC` | `S-27` art. 79 |
| `n_facture` | `DOC` | `S-27` art. 79 |
| `date_encaissement` | `DOC` | `S-27` art. 79 |
| `mode_reglement` | `HYP` | non documenté |
| `montant` | `DOC` | `S-18` |
| `regisseur` | `DOC` | `S-20` — la Cour décrit un paiement direct chez le régisseur |
| `billet_sortie_delivre` | `DOC` | `S-27` art. 79 |

**`source.creances`**

| Champ | Provenance | Source |
|---|---|---|
| `n_creance`, `n_facture` | `DOC` | `S-27` art. 9(b) |
| `date_naissance_creance` | `DOC` | `S-27` art. 79 |
| `montant_du`, `montant_recouvre`, `montant_restant` | `DOC` | `S-20` — l'état des prestations non recouvrées existe |
| `type_debiteur` | `DOC` | `S-09` — publique, privée, mutuelle, particulier |
| `motif_non_recouvrement` | `DOC` | `S-20` — sortie sans règlement, patient non identifié, évasion |
| `anciennete_jours` | `DOC` | `S-20` — le cumul est produit par exercice |

**`source.relances`**

| Champ | Provenance | Source |
|---|---|---|
| `n_relance`, `n_creance` | `HYP` | aucune source ne documente une procédure de relance formalisée |
| `date_relance`, `canal`, `resultat` | `HYP` | idem |

**La table des relances est intégralement `HYP`, et il faut le dire.** La Cour reproche précisément l'absence de diligences de recouvrement ; modéliser une chaîne de relances structurée, c'est modéliser une pratique que la seule source disponible décrit comme défaillante. Le générateur produit cette table parce que le tableau de bord en a besoin pour sa page recouvrement, et le rapport signale qu'elle est la partie la plus hypothétique du jeu de données.

---

# 3. Profil `MSM - URGENCE`

## 3.1 Ce que la documentation de l'éditeur décrit

Le module *Urgencias* figure au catalogue de Hosix Core [`S-06`]. **Sa fiche descriptive n'a pas pu être ouverte pendant les recherches** ; elle n'est pas indexée par les moteurs et l'accès direct à son adresse a échoué. C'est une lacune de ce dossier et elle est consignée comme telle : ce que fait le module Urgencias de Hosix n'est pas documenté ici.

Un élément indirect est établi : la fiche du module *Médicos* [SIVSA, Hosix Clinic] décrit une liste de travail regroupant les patients **par type d'épisode — hospitalisés, consultation, urgences**. Le système type donc ses épisodes, et l'urgence en est un au même titre que l'hospitalisation et la consultation. C'est la seule affirmation de l'éditeur que ce dossier peut soutenir sur ce module.

Faute de documentation éditeur, la reconstruction du profil `URGENCE` repose **presque intégralement sur la réglementation et sur les sources marocaines**, ce qui est un état de fait à assumer plutôt qu'à masquer.

## 3.2 Ce que la réglementation marocaine impose

**L'article 42** — accueil aux urgences. Tout patient, blessé ou parturiente se présentant en situation d'urgence doit être reçu, examiné et, le cas échéant, admis en hospitalisation si son état l'exige, **même en cas d'indisponibilité de lits**. La procédure de facturation n'est entamée qu'après engagement de la prise en charge médicale. Si l'état n'est pas jugé médicalement urgent, le patient est référé vers la structure appropriée ou pris en charge sous réserve de s'acquitter préalablement des frais.

**L'article 43** — le patient admis aux urgences dont l'état n'exige pas l'hospitalisation doit s'acquitter des frais auprès du SAA préalablement à sa sortie.

**L'article 44** — l'hospitalisation d'urgence est ordonnée par le médecin des urgences ou par le spécialiste de garde ou d'astreinte. Pour les parturientes, elle peut être décidée par la sage-femme ou l'infirmière accoucheuse sous encadrement du médecin ou du gynécologue-obstétricien de garde.

**L'article 45** — les formalités d'admission en urgence suivent celles de l'admission ordinaire, à la suite de l'administration des premiers soins, soit au chevet du patient, soit au SAA par sa famille, et **dans tous les cas avant sa sortie de l'hôpital**. Si le patient est inconscient, l'infirmier de garde dresse un inventaire contradictoire de ses effets, signé avec un accompagnant ou deux témoins.

**L'article 46** — l'admission d'une personne décédée est interdite ; en l'absence de morgue municipale, un constat portant la mention « arrivé mort à l'hôpital » est établi.

**L'article 47** — transfert d'un patient admis en urgence lorsque les soins requis relèvent d'une discipline ou d'une technique n'existant pas à l'hôpital. Le médecin des urgences prodigue les premiers secours et ordonne le transfert ; le consentement écrit du patient est requis sauf extrême urgence ; la famille est informée.

**L'article 67** — pour un patient mineur, incapable ou inconscient hospitalisé en urgence, la famille est recherchée et, le cas échéant, la police judiciaire locale informée.

## 3.3 Ce que les sources marocaines établissent sur les volumes et le tri

**Ampleur nationale** [`S-12`] : les services d'urgence du secteur hospitalier public assurent **6 482 185 consultations et soins d'urgence par an**. Le réseau compte 148 services d'accueil des urgences, dont 94 services d'urgences médico-hospitalières de base au niveau des hôpitaux de proximité, provinciaux et préfectoraux — la catégorie dont relève Sidi Saïd.

**Poids dans l'activité hospitalière** [`S-12`] : 25 % des hospitalisations et 47 % des cas opérés en 2021 se sont faits à partir des services des urgences ; 66 % des cas opérés en 2020.

**Répartition de la gravité, chiffres du ministère** [`S-12`] : les urgences vitales représentent environ **10 %** de l'ensemble des passages, les consultations médicales non urgentes **64 %**. Le solde, 26 %, correspond aux urgences réelles non vitales.

**Taux d'hospitalisation aux urgences** [`S-12`] : les services d'urgence des polycliniques de la CNSS ont assuré 103 443 consultations sur neuf mois, donnant lieu à hospitalisation dans **13 %** des cas. Cette valeur ne s'applique pas directement à Sidi Saïd, qui ne pratique ni chirurgie ni réanimation et transfère au lieu d'admettre ; elle constitue une borne haute.

**Recours non approprié** [`S-13`] : sur 410 patients du service des urgences du centre hospitalier provincial de Nador en 2010, **30,7 %** des consultations ont été considérées non appropriées, selon une définition combinant le caractère urgent, le jour et le moment de la consultation et l'ancienneté des symptômes.

Cette valeur ne se confond pas avec les 64 % de consultations non urgentes du ministère : la définition de Nador est plus stricte et l'étude est antérieure à la généralisation de l'AMO. **Les deux figurent au modèle avec des rôles différents** — les 64 % calibrent la répartition des niveaux de tri, les 30,7 % servent d'indicateur de comparaison au tableau de bord.

**Délais d'attente déclarés** [`S-12`] : prise en charge immédiate pour 12 % des répondants, dans l'heure pour plus de la moitié, au-delà de quatre heures dans 12 % des cas.

**Un constat à retenir pour le chapitre 9** [`S-12`] : 6,35 % des répondants dont l'état nécessitait une hospitalisation n'ont pas été admis faute de pouvoir s'acquitter de la caution ou de fournir un chèque de garantie.

## 3.4 Ce que la Cour des comptes établit sur cet établissement

Le service des urgences de l'hôpital Sidi Saïd **n'assurait pas la garde** en 2016, faute de médecins généralistes affectés, alors que l'hôpital comptait neuf généralistes au total. Les patients des zones avoisinantes devaient se déplacer aux urgences de l'hôpital Mohamed V. [`S-20`]

Ce constat est antérieur de trois ans à la rénovation de 2019 et à la création du pôle Mère-Enfant. Aucune source ne décrit l'organisation actuelle de la garde : *Santé en chiffres* ne publie aucun volume de passages aux urgences, à aucun niveau géographique — seulement un dénombrement de structures. **C'est un silence de la source, pas une information sur l'établissement.** Le modèle retient le régime d'après rénovation et le déclare `HYP` (section 6.3 du document maître).

## 3.5 Champs qui en découlent

**`source.passages_urgences`**

| Champ | Provenance | Source | Justification |
|---|---|---|---|
| `n_passage` | `DOC` | `S-27` art. 45 | les formalités d'admission en urgence sont enregistrées |
| `n_ipp` | `OBS` | — | relevé sur la fiche patient |
| `date_heure_arrivee` | `DOC` | `S-27` art. 42 | l'accueil est l'acte fondateur du passage |
| `mode_arrivee` | `DOC` | `S-12` | protection civile, ambulance SMUR, moyens propres, transport privé |
| `motif_recours` | `DOC` | `S-13` | l'étude classe les motifs par chapitre CIM-10 |
| `niveau_tri` | `DOC` | `S-12` | vitales ≈ 10 %, non urgentes 64 %, solde 26 % |
| `date_heure_pec_medicale` | `DOC` | `S-27` art. 42 | la facturation n'est entamée qu'après cet engagement — la date est donc portée |
| `date_heure_sortie` | `DOC` | `S-27` art. 43 | le règlement précède la sortie |
| `orientation_sortie` | `DOC` | `S-27` art. 42, 44, 46, 47 | domicile, hospitalisation, transfert, sortie contre avis, décès |
| `service_orientation` | `DOC` | `S-27` art. 44 | l'hospitalisation est ordonnée vers un service |
| `motif_transfert` | `DOC` | `S-27` art. 47 | discipline ou technique n'existant pas à l'hôpital |
| `consentement_transfert` | `DOC` | `S-27` art. 47 | consentement écrit requis sauf extrême urgence |
| `famille_informee` | `DOC` | `S-27` art. 47, 67 | obligation d'information |
| `inventaire_effets` | `DOC` | `S-27` art. 45 | inventaire contradictoire si patient inconscient |

**Le nombre de niveaux de l'échelle de tri reste `HYP`.** La structure à cinq ou six niveaux est proposée par la littérature [`S-14`, source non encore vérifiée], tandis que les seuls chiffres marocains disponibles [`S-12`] ne distinguent que trois groupes : vitales, urgentes non vitales, non urgentes. Le modèle retient cinq niveaux avec une répartition contrainte par ces trois groupes, et le déclare.

**Le taux de transfert est relevé à 12 %.** Un établissement sans chirurgie ni réanimation transfère tout ce qui relève de l'une ou de l'autre. La Cour chiffre les seules grossesses à risque référées de Sidi Saïd vers l'hôpital Pagnon à 1 253 femmes en 2015 et 932 en 2016. [`S-20`] La valeur reste `HYP`, mais son ordre de grandeur est argumenté.

---

# 4. Profil `MSM RAPPORTS ET STATISTIQUES`

## 4.1 Ce que la documentation de l'éditeur décrit

Le catalogue de Hosix.NET comporte une offre décisionnelle distincte, **Hosix BI** [`S-06`], présentée hors des trois paquets contractables Core, Clinic et Extension Packs. La fiche descriptive n'a pas été ouverte ; le seul fait établi est l'existence d'une brique décisionnelle séparée du transactionnel.

Le module *Consultas* documente en revanche explicitement, parmi ses fonctions, la **gestion des notifications, des listings et des statistiques** [`S-08`], et le module *Facturación* la production de documentation et de listings personnalisés [`S-09`]. La production statistique est donc distribuée dans les modules, pas concentrée dans un module unique — ce qui est cohérent avec un profil applicatif dédié à sa restitution.

## 4.2 Ce que la réglementation marocaine impose

**L'article 35** [`S-27`] range parmi les missions du SAA : *établir les statistiques et gérer l'information hospitalière*. C'est une mission propre du service, pas une fonction déléguée.

**L'article 15** confie au comité de suivi et d'évaluation l'examen des données sur l'activité hospitalière et l'analyse de la performance de l'hôpital et de la qualité des soins, sur la base d'une **analyse mensuelle des indicateurs et résultats obtenus**. Le secrétariat de ce comité est assuré par le responsable du service d'accueil et d'admission.

**L'article 13** charge le comité d'établissement de se prononcer sur le rapport d'activité et l'analyse de la performance et de la qualité des prestations, eu égard aux objectifs préalablement fixés, à raison d'une réunion par trimestre.

**L'article 2** charge le directeur d'établir un rapport annuel des activités techniques, administratives et financières.

**Trois périodicités réglementaires en découlent** : mensuelle pour le comité de suivi et d'évaluation, trimestrielle pour le comité d'établissement, annuelle pour le rapport du directeur. Le tableau de bord doit pouvoir servir les trois.

## 4.3 La liste des indicateurs remontés

Elle n'est pas définie par le règlement intérieur. Elle se lit dans la nomenclature de *Santé en chiffres* [`S-30`], qui est le document de restitution nationale de ces remontées. Les quatre tableaux descendant à l'établissement donnent la liste exacte des indicateurs attendus d'un hôpital nommé :

| Tableau | Indicateurs par établissement |
|---|---|
| 76 | capacité litière fonctionnelle, journées d'hospitalisation, admissions, taux d'occupation moyen, durée moyenne de séjour, intervalle de rotation, taux de rotation |
| 77 | nombre total des médecins, interventions chirurgicales, interventions par médecin |
| 78 | nombre total des médecins, consultations spécialisées externes, consultations par médecin |
| 79 | examens de bactériologie, parasitologie, immuno-sérologie, hématologie et transfusion, hygiène alimentaire, chimie-biologie ; total ; nombre de prélèvements |

**Les quatre formules d'indicateurs de séjour sont retrouvées et vérifiées** sur les données publiées, bien que le document ne comporte aucune note méthodologique les énonçant :

    TOM   = journées ÷ (capacité litière fonctionnelle × 365)
    DMS   = journées ÷ admissions
    TROT  = admissions ÷ capacité litière fonctionnelle
    IROT  = (capacité × 365 − journées) ÷ admissions

Vérification sur la ligne HP Sidi Said, exercice 2024 : 53,77 contre 53,8 publié ; 6,559 contre 6,6 ; 29,93 contre 29,9 ; 5,638 contre 5,6.

## 4.4 Champs qui en découlent

Ce profil ne produit pas de table de la couche source : il consomme. Il détermine en revanche le contenu de la couche `marts` et le fichier `docs/exigences_statistiques.md`.

**La colonne de calculabilité de ce fichier prend trois valeurs, et non deux :**

| Valeur | Signification | Ce qu'elle implique |
|---|---|---|
| calculable | l'indicateur se dérive des tables de faits | rien |
| non calculable faute de champ | un champ manque au système d'information | **recommandation au chapitre 9** |
| sans objet pour ce site | l'établissement n'exerce pas l'activité | **constat au chapitre 1** |

Les interventions chirurgicales, les interventions par médecin et le taux de césarienne relèvent de la troisième valeur : l'établissement est absent du tableau 77 sur les deux exercices publiés, et la Cour des comptes décrit une gynéco-obstétrique sans activité chirurgicale [`S-20`, `S-30`]. Les examens de bactériologie et de parasitologie y relèvent également, la source imprimant un zéro.

**Confondre les deux dernières valeurs ferait reprocher à Hosix une absence de champ là où c'est l'hôpital qui n'a pas l'activité**, et le chapitre 9 en tirerait une recommandation fausse.

## 4.5 Un constat qui justifie le principe de la chaîne de données

Dans la section Meknès du tableau 77, la colonne dérivée « interventions chirurgicales par médecin » se reconstitue exactement à partir des deux colonnes voisines sur les quatre lignes de l'exercice 2023. En 2024 elle échoue sur l'hôpital Pagnon : 1 047 ÷ 5 = 209, la source imprime 228.

Une colonne calculée d'une publication officielle ne se reconstitue donc pas toujours. C'est l'argument le plus court en faveur du principe retenu : **les indicateurs du tableau de bord sont recalculés depuis les tables de faits, jamais repris d'une colonne calculée en amont.**

---

# 5. Ce que cette reconstruction ne couvre pas

Quatre lacunes sont assumées et signalées au rapport.

**La fiche du module Urgencias n'a pas pu être ouverte.** Le profil `URGENCE` est donc reconstruit sur la réglementation seule, sans contrepartie éditeur. C'est le module le moins solidement adossé des quatre.

**La fiche Hosix BI n'a pas été ouverte.** Ce que fait la brique décisionnelle de l'éditeur reste inconnu, et le rapport ne peut donc pas comparer le tableau de bord produit à celui qu'offrirait le produit.

**L'arrêté n° 221-98 fixant les tarifs des centres hospitaliers n'a pas été retrouvé** [`S-32`]. Le montant facturé est assimilé au tarif TNR, ce qui est une hypothèse déclarée.

**Aucune source ne donne les libellés de champs réels de ces quatre modules.** Les noms retenus ici sont des noms de modèle. Cette distinction entre un champ `OBS`, dont le libellé est reproduit à l'identique, et un champ `DOC`, dont seule la nécessité fonctionnelle est établie, est la limite principale de tout le dispositif et elle est écrite au chapitre 3.
