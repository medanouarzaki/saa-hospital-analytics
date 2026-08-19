# Exigences statistiques — ce que la nomenclature nationale demande, et ce que la chaîne produit

Ce document confronte la liste des indicateurs qu'un hôpital nommé remonte à la statistique
nationale à ce que la chaîne de données du projet permet de calculer. Chaque indicateur reçoit un
classement en trois valeurs, et chaque classement s'appuie sur une mesure.

---

## 1. Ce que la nomenclature nationale demande

La liste des indicateurs remontés n'est pas définie par le règlement intérieur des hôpitaux. Elle
se lit dans la nomenclature de *Santé en chiffres* [`S-30`], document de restitution nationale de
ces remontées. Un inventaire exhaustif de ses quatre-vingt-quatre tableaux établit que **quatre
seulement descendent à l'établissement nommé**, et ces quatre donnent la liste exacte des
indicateurs attendus.

| tableau | indicateurs par établissement |
|---|---|
| 76, page 102 | capacité litière fonctionnelle, journées d'hospitalisation, admissions, taux d'occupation moyen, durée moyenne de séjour, intervalle de rotation, taux de rotation |
| 77, page 105 | nombre total des médecins, interventions chirurgicales, interventions par médecin |
| 78, page 109 | nombre total des médecins, consultations spécialisées externes, consultations par médecin |
| 79, page 113 | examens de bactériologie, parasitologie, immuno-sérologie, hématologie et transfusion, hygiène alimentaire, chimie-biologie ; total ; nombre de prélèvements |

Les quatre formules d'indicateurs de séjour sont retrouvées et vérifiées sur les données publiées,
bien que le document ne comporte aucune note méthodologique les énonçant :

    taux d'occupation moyen  = journées ÷ (capacité litière fonctionnelle × 365)
    durée moyenne de séjour  = journées ÷ admissions
    taux de rotation         = admissions ÷ capacité litière fonctionnelle
    intervalle de rotation   = (capacité × 365 − journées) ÷ admissions

L'entrée `S-10` du registre des sources porte l'intitulé de la nomenclature ; son contenu n'est pas
vérifiable par outil. `S-30` porte les valeurs et son contenu a été lu ; c'est donc lui qui fait
foi, et son empreinte est consignée au registre des sources.

### Indicateurs dont la définition est reconstruite faute de source citable

**Cinq des quinze indicateurs traités ne correspondent à aucun tableau descendant à
l'établissement.** Leur définition est donc reconstruite, et cela est signalé partout où ils
apparaissent :

| indicateur | ce que la source publie |
|---|---|
| capacité litière **existante** | rien — aucun tableau ne la donne par établissement ; seule une capacité annoncée de 140 lits, datée de 2020, existe par voie de presse [`S-29`], à ne pas confondre avec la capacité fonctionnelle |
| passages aux urgences | rien — aucun volume de passages n'est publié à aucun niveau géographique, seulement un dénombrement de structures |
| accouchements | rien |
| taux de césarienne | rien |
| activité d'imagerie | rien — contrairement au laboratoire, aucun volume d'imagerie n'est mesuré par la source |

---

## 2. Le tableau de correspondance

Trois valeurs de classement, et trois seulement :

| valeur | signification | ce qu'elle implique |
|---|---|---|
| **calculable** | la chaîne produit la valeur | rien ; l'indicateur peut être affiché |
| **non calculable faute de champ** | un champ manque au **système d'information** | une recommandation : ajouter le champ |
| **sans objet pour ce site** | l'**établissement** n'exerce pas l'activité | un constat, jamais un reproche au logiciel |

Toutes les grandeurs annuelles ci-dessous sont obtenues en divisant par le nombre de jours de la
période — **912 jours, mesuré par requête** sur l'union des dates d'extraction des onze tables de
la couche source — puis en multipliant par 365 jours, durée de l'année de référence. Le facteur
appliqué est donc 365 ÷ 912 = 0,4002192982.

| indicateur | définition en une ligne | classement | tables mobilisées | champ manquant | valeur calculée | valeur relevée | écart |
|---|---|---|---|---|---|---|---|
| **Capacité litière existante** | lits installés, en service ou non | **non calculable faute de champ** | *aucune* | table de structure de l'établissement | — | 140 lits [`S-29`, 2020] | — |
| **Capacité litière fonctionnelle** | lits en service | **calculable** | `source.mouvements` | — | **40** | **40** | **0,00 %** |
| **Admissions** | nombre de séjours | **calculable** | `marts.fct_sejour` | — | **1 192,65 / an** | 1 197 / an | **0,3631 %** |
| **Journées d'hospitalisation** | somme de `duree_jours`, colonne nulle pour un séjour non clos | **calculable** | `marts.fct_sejour` | — | **7 751,88 / an** | 7 851 / an | **1,2625 %** |
| **Taux d'occupation moyen** | journées ÷ (capacité × 365) | **calculable** | `marts.fct_sejour` + capacité | — | **53,0951 %** | 53,8 % | **1,3103 %** |
| **Durée moyenne de séjour** | journées ÷ admissions | **calculable** | `marts.fct_sejour` | — | **6,4997 j** | 6,6 j | **1,5198 %** |
| **Taux de rotation** | admissions ÷ capacité | **calculable** | `marts.fct_sejour` + capacité | — | **29,8163** | 29,9 | **0,2798 %** |
| **Intervalle de rotation** | (capacité × 365 − journées) ÷ admissions | **calculable** | `marts.fct_sejour` + capacité | — | **5,7419 j** | 5,6 j | **2,5343 %** |
| **Consultations spécialisées externes** | passages de consultation | **calculable** | `marts.fct_passage` | — | **4 126,26 / an** | 4 142 / an | **0,3800 %** |
| **Consultations par médecin** | consultations ÷ médecins | **non calculable faute de champ** | `marts.fct_passage` (numérateur seul) | référentiel des médecins | 206,31 | 518 | **60,1718 %** |
| **Passages aux urgences** | admissions au service des urgences | **calculable** | `marts.fct_passage_urgence` | — | **10 950 / an**, 30,00 / jour | *aucune* | — |
| **Accouchements** | séjours avec accouchement | **non calculable faute de champ** | *aucune ne convient* | marqueur d'accouchement | — | *aucune* | — |
| **Taux de césarienne** | césariennes ÷ accouchements | **sans objet pour ce site** | *aucune* | — | — | — | — |
| **Interventions chirurgicales** | actes chirurgicaux | **sans objet pour ce site** | *aucune* | — | — | 0, absence de ligne | — |
| **Activité des laboratoires** | prélèvements, examens, six catégories | **calculable** pour trois catégories, le total et les prélèvements ; **sans objet** pour trois catégories | `source.lignes_facture` | — | *voir le détail ci-dessous* | | |
| **Activité d'imagerie** | actes d'imagerie réalisés | **calculable** | `source.lignes_facture` | — | **876,08 actes / an** | *aucune* | — |

### Détail de l'activité des laboratoires

| grandeur | classement | valeur calculée | valeur relevée | écart |
|---|---|---|---|---|
| chimie-biologie | calculable | **29 413,32 / an** | 29 525 / an | **0,3783 %** |
| hématologie et transfusion | calculable | **13 156,01 / an** | 13 206 / an | **0,3785 %** |
| immuno-sérologie | calculable | **6 840,15 / an** | 6 866 / an | **0,3765 %** |
| **total des examens** | calculable | **49 409,47 / an** | 49 597 / an | **0,3781 %** |
| **nombre de prélèvements** | calculable, **reconstruit** | **9 575,25 / an** | 9 625 / an | **0,5169 %** |
| bactériologie | **sans objet pour ce site** | — | 0, zéro imprimé | — |
| parasitologie | **sans objet pour ce site** | — | 0, zéro imprimé | — |
| hygiène alimentaire | **sans objet pour ce site** | — | 0, zéro imprimé | — |

Le nombre de prélèvements est **reconstruit** et cela est signalé : aucune colonne ne porte
d'identifiant de prélèvement. Le regroupement retenu — un prélèvement par couple (facture, date
d'acte) sur les lignes de laboratoire — retrouve la valeur publiée à 0,52 % près et le rapport
d'examens par prélèvement à 0,20 % près, ce qui le valide sans le démontrer.

---

## 3. Le décompte par classement

Le décompte porte sur les **quinze rubriques traitées**, l'indicateur des accouchements et le taux
de césarienne étant deux grandeurs distinctes traitées séparément.

| classement | nombre |
|---|---|
| **calculable** | **10** |
| **non calculable faute de champ** | **3** |
| **sans objet pour ce site** | **2** |
| **total** | **15** |

**Vérification de l'égalité : 10 + 3 + 2 = 15**, égal au nombre d'indicateurs traités. Aucune
rubrique n'échappe au classement, aucune n'en reçoit deux.

Un décompte alternatif, donné pour être complet : compter les **grandeurs** plutôt que les
rubriques — l'activité des laboratoires en portant huit — donnerait 15 calculables, 3 non
calculables et 5 sans objet, soit 23 grandeurs. Le décompte par rubriques est celui retenu au
tableau, parce que c'est l'unité que la nomenclature énumère.

---

## 4. Les champs manquants

Trois champs distincts, dédoublonnés. **C'est cette liste qui fonde la recommandation.**

L'absence de chacun est vérifiée par **deux chemins indépendants** : le registre des champs de la
couche source d'une part, le catalogue de la base d'autre part. Les deux chemins ont été éprouvés
au préalable contre des noms de colonnes dont l'existence est certaine — le motif `lit` rend bien
la colonne d'identifiant de lit, le motif `medecin` rend bien les deux colonnes de médecin — de
sorte que leur silence sur les motifs cherchés ne soit pas l'artefact d'une recherche trop étroite.

| # | champ manquant | indicateur débloqué | vérification d'absence |
|---|---|---|---|
| 1 | **une table de structure de l'établissement**, portant au minimum la capacité litière existante et son horodatage | capacité litière existante | motifs `capacit` et `nombre de lits` : **0** au registre des champs, **0** au catalogue sur les 175 colonnes de la couche source |
| 2 | **un référentiel des médecins**, dont découlerait l'effectif médical | consultations par médecin | motif `effectif` : **0** par les deux chemins ; et la colonne de médecin existante est mesurée **orpheline à 100 %** de la dimension des agents — 40 650 valeurs, 40 650 orphelines, 20 valeurs distinctes formant un espace de codes disjoint |
| 3 | **un marqueur d'accouchement** rattaché au séjour | accouchements ; et, si l'activité chirurgicale existait, le taux de césarienne | motifs `accouchement` et `césarienne` : **0** par les deux chemins |

**La correspondance est de un à un** : aucun de ces trois champs n'en débloquerait plusieurs à lui
seul. C'est **l'ampleur de l'écart produit** qui les départage, et sur ce critère le référentiel
des médecins vient nettement en tête — son absence produit un écart de 60,17 % sur un indicateur
par ailleurs entièrement calculable au numérateur, là où les deux autres rendent leur indicateur
simplement absent.

Un quatrième champ est **utile mais non bloquant**, et il est nommé sans entrer dans la
recommandation : un **identifiant de prélèvement** sur les lignes de facture. Son absence
n'empêche pas le calcul, mais elle fait reposer un indicateur de la nomenclature sur une convention
de regroupement plutôt que sur une donnée enregistrée.

---

## 5. Ce que la chaîne produit et que la nomenclature ne demande pas

Vingt grandeurs, toutes produites par la chaîne, **dont aucune ne figure dans les quatre tableaux
descendant à l'établissement**.

| # | grandeur | table qui la porte | décision qu'elle sert |
|---|---|---|---|
| 1 | délai d'obtention d'un rendez-vous, médiane et centile 90 par activité | `marts.agg_delai_rendez_vous` | ouvrir ou fermer des créneaux sur les spécialités dont le délai s'écarte des autres |
| 2 | part des rendez-vous pris le jour même | `marts.agg_delai_rendez_vous` | dimensionner la part d'activité non programmée absorbée par la consultation |
| 3 | taux d'absentéisme par activité | `marts.agg_absenteisme` | décider d'un rappel de rendez-vous, et sur quelles spécialités le cibler |
| 4 | taux d'annulation par activité | `marts.agg_absenteisme` | distinguer l'annulation, réaffectable, de l'absence, qui perd le créneau |
| 5 | délai de prise en charge médicale aux urgences, par niveau de tri | `marts.agg_urgences_journalier` | vérifier que le tri produit une priorisation, et où la file se forme |
| 6 | durée de passage aux urgences | `marts.agg_urgences_journalier` | dimensionner les places d'observation |
| 7 | orientation de sortie des urgences | `marts.agg_urgences_journalier` | mesurer le taux de transfert, mode de fonctionnement de cet établissement |
| 8 | taux de recouvrement | `marts.agg_recouvrement` | décider d'une action de relance, et sur quel type de débiteur |
| 9 | aboutissement des relances | `marts.agg_recouvrement` | mesurer le rendement de la relance avant d'en augmenter le volume |
| 10 | ancienneté des créances par tranche | `intermediate.int_creances` | prioriser le recouvrement |
| 11 | complétude par table et par colonne | `marts.agg_qualite_donnees` | cibler la saisie sur les champs les moins renseignés plutôt que sur tous |
| 12 | taux de mise en quarantaine par table | `marts.agg_qualite_donnees` | détecter une dégradation d'extraction avant qu'elle ne contamine l'entrepôt |
| 13 | doublons d'identité par collision exacte | `marts.agg_doublons_identite` | lancer une campagne de fusion d'identités, et sur quel critère la prioriser |
| 14 | grappes d'identité du rapprochement probabiliste | `linkage.grappes_identite` | mesurer ce que le rapprochement trouve en plus de la collision exacte |
| 15 | courbe de précision et de rappel du rapprochement | `linkage.evaluation` | déplacer le seuil de décision en connaissance du compromis |
| 16 | provenance des champs du système d'information | `marts.agg_provenance_champs` | savoir quelle part du modèle repose sur l'observation et laquelle sur l'hypothèse |
| 17 | réconciliation du montant facturé et de la somme de ses lignes | `marts.fct_facturation` | détecter les factures dont le total ne s'accorde pas à ses lignes |
| 18 | part organisme et part patient | `marts.fct_facturation` | mesurer le reste à charge effectif |
| 19 | épisodes non facturés | `marts.fct_passage` et `marts.fct_facturation` | mesurer ce qui échappe à la facturation, et sur quelle famille d'épisode |
| 20 | activité par jour, croisée au calendrier | `marts.agg_activite_journaliere` et `marts.dim_date` | lire la saisonnalité et l'effet des jours fériés et du Ramadan |

Trois observations, sans développement :

- la nomenclature ne demande **aucun délai**, alors que la chaîne en produit trois ;
- elle ne demande **aucune mesure de qualité de la donnée**, alors que la chaîne en produit quatre ;
- elle ne demande **que des volumes annuels agrégés**, là où la chaîne porte le grain de la ligne
  et permettrait une distribution.

---

## 6. Réserves de méthode

**Les valeurs calculées proviennent d'un jeu de données généré.** Elles établissent ce que la
chaîne permet de mesurer, non l'activité réelle du service. Là où une valeur relevée de
l'établissement existe, les deux sont données côte à côte et leur écart est commenté sans être
corrigé.

**Deux indicateurs n'ont aucune valeur relevée à confronter** : les passages aux urgences et
l'activité d'imagerie. Pour le premier, la valeur de référence n'est pas relevée mais posée en
hypothèse, à trente passages par jour, entre des bornes de quatorze et cinquante-quatre dont
l'asymétrie reflète l'asymétrie de la confiance accordée à chacune. La mesure retrouve exactement
30,0000 passages par jour — **ce zéro d'écart vérifie la chaîne de génération, il ne mesure pas
l'activité de l'établissement**, et il faut le lire ainsi.

**Un écart mesuré tient à une différence de dénominateur et non à une erreur.** Les consultations
par médecin valent 206,31 en divisant par les vingt identifiants de médecin observés dans les
données, et 518 en divisant par les huit médecins que la source dénombre pour ce tableau. Le
rapport des deux dénominateurs, 2,5, reproduit presque exactement le rapport des deux résultats,
2,51. Aucun des deux calculs n'est faux ; ils ne comptent pas la même chose.

Les onze autres confrontations donnent des écarts compris **entre 0,00 % et 1,95 %**, tous
inférieurs à la tolérance de 3 % que le dépôt applique à ces grandeurs.

**La distinction structurante de tout ce document est celle entre un champ absent du système
d'information et une activité absente de l'établissement.** Un indicateur non calculable est un
défaut du système d'information et appelle une recommandation ; un indicateur sans objet est une
propriété de l'établissement et appelle un constat. Les confondre ferait reprocher au logiciel une
absence de champ là où c'est l'hôpital qui n'a pas l'activité, et la recommandation qui en
découlerait serait fausse.

Cette distinction n'est jamais tranchée par un décompte nul. **Un zéro mesuré en base est
compatible avec les trois classements** : l'activité peut ne pas exister, le champ peut manquer de
sorte que rien n'ait pu être enregistré, ou l'activité peut exister sans avoir eu lieu sur la
période. Seule une source indépendante des données peut trancher, et elle est citée à chaque fois.

Deux exemples opposés le montrent. Les examens de bactériologie et de parasitologie sont classés
sans objet sur un **zéro imprimé** dans la source : la ligne existe et porte cette valeur, ce qui
atteste que l'établissement a été interrogé et a répondu zéro. Les interventions chirurgicales le
sont sur une **absence de ligne**, argument plus fragile qu'un zéro imprimé, et qui a donc exigé
quatre contrôles indépendants avant d'être retenu — recherche exhaustive de dénomination avec son
contrôle positif, contrôle de somme provinciale, cohérence de la structure du document, et
corroboration par un rapport de la Cour des comptes portant sur un exercice antérieur de huit ans.

Une dernière réserve, de nature différente : **le contenu d'une colonne ne se déduit jamais de son
nom.** Le cas le plus net est le code diagnostique international dont l'une des valeurs désigne un
accouchement unique spontané. Il apparaît 731 fois, mais **324 de ces occurrences portent sur des
patients de sexe masculin**, et sa fréquence est la même dans les trois types d'épisode et les cinq
services émetteurs. Il ne porte aucun signal obstétrical, et l'utiliser pour dénombrer des
accouchements aurait produit un chiffre faux en lui donnant l'apparence d'une mesure.

---

## Sources

`S-10` Ministère de la Santé et de la Protection Sociale, *Santé en chiffres 2023* — intitulé de la
nomenclature des indicateurs remontés.
`S-29` Dépêche d'agence, février 2020 — capacité litière annoncée de 140 lits.
`S-30` Ministère de la Santé et de la Protection Sociale, *Santé en chiffres 2024* — valeurs
relevées par établissement, tableaux 76, 77, 78 et 79.
`docs/decisions/0003-volumetrie.md` — volumétrie relevée, absence d'activité chirurgicale établie
par quatre contrôles, et grille de calculabilité à trois valeurs.
`docs/decisions/0045-composition-des-sept-pages.md` — indicateurs retirés et leur motif.
`docs/decisions/0047-ecarts-assumes-au-cadrage.md` — écarts assumés, dont la capacité litière et
les codes sans libellé.
`docs/modules_non_observes.md` — liste des indicateurs remontés et formules des indicateurs de
séjour.
`docs/champs/registre_champs.yml` — premier chemin de vérification d'absence d'un champ.
