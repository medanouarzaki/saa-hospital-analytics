# ADR 0003 — Volumétrie du jeu de données

**Statut.** Accepté. Remplace intégralement la dérivation du cadrage initial.

---

## Contexte

Le cadrage initial dérivait la volumétrie par le calcul suivant, faute de données propres à l'établissement :

    séjours annuels = capacité litière × 365 × taux d'occupation ÷ durée moyenne de séjour
                    = 140 × 365 × 0,546 ÷ 3,2
                    = 8 720

et, pour l'ambulatoire :

    consultations annuelles = consultations par médecin × effectif médical
                            = 438 × 60
                            = 26 300

Trois des quatre entrées de la première formule et les deux entrées de la seconde étaient des grandeurs nationales ou des hypothèses. L'effectif de 60 médecins n'avait aucune source et était identifié au cadrage comme l'hypothèse la plus fragile du modèle.

Deux constats ont été établis lors de la recherche documentaire.

Le premier est que *Santé en chiffres 2024* [`S-30`] publie les indicateurs hospitaliers **par établissement nommé**, au tableau 76 page 102. HP Sidi Said y figure, ainsi que dans les tableaux 78 (consultations spécialisées externes) et 79 (activités des laboratoires). Un inventaire exhaustif des quatre-vingt-quatre tableaux du document a établi que quatre d'entre eux, et seulement quatre, descendent à l'établissement : les tableaux 76, 77, 78 et 79. Les quatre ont été extraits.

Le second est que la dérivation initiale était fausse d'un facteur cinq à sept sur ses deux branches :

| Grandeur | Cadrage initial | Mesuré 2024 | Rapport |
|---|---|---|---|
| Capacité litière fonctionnelle | 140 | 40 | 3,5 |
| Séjours annuels | 8 720 | 1 197 | 7,3 |
| Consultations externes annuelles | 26 300 | 4 142 | 6,4 |
| Durée moyenne de séjour | 3,2 j | 6,6 j | 0,5 |
| Taux d'occupation moyen | 54,6 % | 53,8 % | 1,0 |

La seule entrée correcte était le taux d'occupation. L'écart de capacité tient à une confusion entre capacité litière **existante** — les 140 lits annoncés par la dépêche d'agence de 2020 [`S-29`] — et capacité litière **fonctionnelle**, seule grandeur publiée par établissement. L'écart de durée moyenne de séjour tient à l'application d'une moyenne nationale à un établissement dont le profil d'activité s'en écarte.

## Décision

**La volumétrie n'est plus dérivée. Elle est relevée au tableau 76 et aux tableaux 78 et 79 de *Santé en chiffres 2024*, ligne HP Sidi Said, et mise à l'échelle de la période.**

Période : 1er janvier 2024 – 30 juin 2026, soit **912 jours**. L'exercice 2024 comptant 366 jours, le facteur d'échelle appliqué à une grandeur annuelle 2024 est **912 ÷ 366 = 2,4918**.

### Grandeurs relevées

| Grandeur | 2024 | Sur 912 jours | Preuve |
|---|---|---|---|
| Journées d'hospitalisation | 7 851 | 19 560 | `S-30` T76 p.102 |
| Séjours | 1 197 | 2 983 | `S-30` T76 p.102 |
| Consultations spécialisées externes | 4 142 | 10 321 | `S-30` T78 p.109 |
| Prélèvements de laboratoire | 9 625 | 23 984 | `S-30` T79 p.113 |
| Examens de laboratoire | 49 597 | 123 586 | `S-30` T79 p.113 |

### Grandeurs relevées à zéro

Trois activités sont mesurées comme absentes, et l'absence est établie sur les deux exercices publiés.

| Grandeur | Valeur | Preuve |
|---|---|---|
| Interventions chirurgicales | 0 | `S-30` T77 p.105 — absence de ligne, 2023 et 2024 |
| Césariennes | 0 | conséquence de la précédente |
| Examens de bactériologie | 0 | `S-30` T79 p.113 — valeur nulle imprimée |
| Examens de parasitologie | 0 | `S-30` T79 p.113 — valeur nulle imprimée |

Les deux dernières sont des **zéros imprimés**. Les deux premières sont une **absence de ligne**, ce qui n'est pas la même chose et exige une justification distincte, donnée ci-dessous.

### Grandeurs restées hypothétiques

| Grandeur | Traitement | Étiquette |
|---|---|---|
| Passages aux urgences | fourchette 14 / **30** / 54 par jour | `HYP` |
| Actes d'imagerie | dérivés de coefficients par séjour et par consultation | `HYP` |
| Accouchements par voie basse | part des séjours, bornée par la durée moyenne de séjour | `HYP` |
| Extrapolation 2025 et premier semestre 2026 | exercice 2024 tenu constant | `HYP` |

## Justification des points non triviaux

### Pourquoi l'absence de ligne au tableau 77 vaut mesure

Un argument fondé sur une absence est fragile à une variation de dénomination. Trois contrôles ont été conduits avant de retenir cette conclusion.

**Recherche exhaustive de la dénomination.** Recherche de `sidi` sans distinction de casse sur le texte intégral des deux éditions — 305 occurrences en 2024, 302 en 2023, toutes relevées sans filtrage. La recherche retrouve les trois occurrences connues de HP Sidi Said aux tableaux 76, 78 et 79 : le contrôle positif porte donc sur la propriété exploitée et non sur la seule présence d'un enregistrement. Aucune occurrence dans l'emprise du tableau 77, balayée page par page. Les variantes `HSS` et `said` seul ont été testées séparément.

**Contrôle de somme.** La somme des lignes visibles de la section Meknès égale exactement le total provincial imprimé, sur les deux exercices et sur les deux colonnes : 34 médecins et 5 071 interventions en 2023, 33 et 4 016 en 2024. Aucun établissement non listé ne contribue au total. L'absence n'est donc pas un artefact d'agrégation.

**Cohérence de la structure du document.** La composition des quatre tableaux nominatifs varie d'un tableau à l'autre : HP Moulay Ismail est absent du tableau des laboratoires comme HP Sidi Said l'est de celui de la chirurgie, et le CRO de Meknès n'apparaît qu'au tableau des consultations. Ces tableaux recensent une activité et non un parc d'établissements. Y être absent signifie ne pas l'exercer.

**Corroboration externe.** Le rapport de la Cour des comptes sur le centre hospitalier préfectoral de Meknès [`S-20`] écrit que la gynéco-obstétrique de l'hôpital Sidi Saïd fonctionne comme une maison d'accouchement, sans médecins gynéco-obstétriciens et en l'absence de toute activité chirurgicale, malgré l'existence d'un bloc opératoire équipé. Ce constat porte sur 2016, la mesure sur 2023 et 2024 : deux sources indépendantes, huit ans d'écart, même conclusion.

### Pourquoi l'exercice 2024 est tenu constant sur 2025 et 2026

Les variations de 2023 à 2024 sont importantes : +26,7 % sur les admissions, +18,7 % sur les journées, +40,5 % sur les consultations spécialisées externes. Les extrapoler ferait de la période un régime de croissance forte reposant sur deux points.

Un motif supplémentaire s'y ajoute. La capacité litière fonctionnelle imprimée pour 2023, cinquante lits, est contredite par les indicateurs de sa propre ligne : le taux d'occupation de 46,4 % implique 39,1 lits et l'intervalle de rotation de 8,1 implique 39,1 lits également ; seul le taux de rotation utilise 50. Deux colonnes dérivées sur trois désignent une capacité voisine de celle de 2024. La variation apparente entre les deux exercices reflète donc pour partie une correction de la capacité déclarée, et non une croissance d'activité réelle.

Tenir 2024 constant est le choix conservateur, il est déclaré `HYP`, et il n'affecte aucune grandeur exprimée en taux ou en délai.

### Pourquoi la fourchette des urgences est asymétrique

*Santé en chiffres* ne publie aucun volume de passages aux urgences, à aucun niveau géographique — seulement un dénombrement de structures. Les bornes sont donc construites, et elles ne sont pas de même nature.

**Borne haute, 54 passages par jour.** Le rapport de la Cour des comptes donne 160 659 passages aux urgences à l'hôpital Mohamed V en 2016, pour 324 lits, soit 496 passages par lit et par an ; appliqué à 40 lits, 19 800 par an. Cette transposition suppose une fonction d'urgence comparable entre les deux établissements. **Le même rapport la contredit** : le service des urgences de l'hôpital Sidi Saïd n'assurait pas la garde, faute de généralistes affectés. S'y ajoute que le chiffre de référence est antérieur à la généralisation de l'assurance maladie obligatoire, qui a modifié le recours aux urgences publiques dans un sens que le projet ne peut pas déterminer.

**Borne basse, 14 passages par jour.** Si 45 % des séjours proviennent des urgences, soit 539 hospitalisations, et si le taux d'hospitalisation aux urgences est de 10,2 %, alors les passages s'élèvent à 5 284 par an. Les deux ratios employés ne sont pas sourcés : c'est une hypothèse construite sur deux hypothèses.

**Scénario retenu, 30 passages par jour.** Le milieu de la fourchette serait 34. La valeur retenue est délibérément placée en dessous, parce que la borne haute repose sur une transposition que la seule description disponible du service contredit, tandis que la borne basse ne souffre que d'un défaut de sourçage de ses ratios. L'asymétrie de la fourchette reflète l'asymétrie de la confiance accordée à ses bornes.

C'est la dernière hypothèse du modèle qui porte un volume absolu, et la seule sur laquelle une analyse de sensibilité subsiste.

### Pourquoi les volumes secondaires sont dérivés et non posés

Les actes d'imagerie et les accouchements ne sont pas fixés par un total annuel choisi, mais produits par des coefficients appliqués à des grandeurs mesurées — actes d'imagerie par séjour et par consultation, part des séjours donnant lieu à un accouchement. Les coefficients sont `HYP`, les grandeurs auxquelles ils s'appliquent sont `DOC`.

Ce choix rend les volumes secondaires solidaires des volumes mesurés au lieu d'en être indépendants, et il déplace l'hypothèse d'un total invérifiable vers un ratio dont l'ordre de grandeur se discute.

La part d'accouchements est en outre bornée par une contrainte interne vérifiable : la durée moyenne de séjour mesurée est de 6,6 jours, or un accouchement par voie basse sans complication produit un séjour d'un à deux jours. Toute part d'accouchements élevée impose aux autres séjours une durée que le profil d'activité de l'établissement rendrait invraisemblable. Cette contrainte est vérifiée par un test.

## Conséquences

**L'analyse de sensibilité à l'effectif médical disparaît.** On ne conduit pas une analyse de sensibilité sur une grandeur mesurée. Les trois exécutions à 40, 60 et 80 médecins prévues pour la génération du jeu de données sont supprimées, et la section correspondante du rapport est remplacée par l'analyse de sensibilité aux passages aux urgences.

**L'effectif médical sort du chemin critique.** Il n'est plus un paramètre du générateur. Il subsiste comme contrôle de cohérence : le tableau 78 donne 8 médecins assurant des consultations spécialisées externes à Sidi Saïd, pour 4 142 consultations, soit 518 par médecin.

Cette colonne doit être nommée par son intitulé exact partout où elle est citée. Elle ne compte pas l'effectif médical de l'établissement, qui reste inconnu : le tableau 77 porte une colonne homonyme dont les valeurs diffèrent pour les mêmes hôpitaux — 40 contre 20 à Mohamed V, 10 contre 5 à Pagnon.

**`dim_service` ne comporte ni service de chirurgie ni bloc opératoire.** La taxonomie des services reflète l'établissement mesuré, non un hôpital générique. L'article 27 du règlement intérieur des hôpitaux [`S-27`] prescrit pourtant un département de chirurgie pour la tranche 120 à 240 lits. L'écart entre organisation prescrite et organisation effective est réel et doit être décrit ; il n'est pas imputé à l'établissement, la Cour des comptes l'ayant déjà qualifié d'éparpillement du plateau technique entre les cinq structures du centre hospitalier, et la direction régionale ayant proposé en réponse un hôpital régional unifié.

**`dim_acte` ne contient aucun acte chirurgical**, ni aucun acte de bactériologie ou de parasitologie. `source.lignes_facture` n'en produit donc aucun.

**Les forfaits de la tarification nationale de référence se réduisent.** Le forfait de chirurgie disparaît. Le forfait de réanimation aussi, selon toute vraisemblance : la Cour des comptes situe le seul service de réanimation du centre hospitalier à l'hôpital Mohamed V, sept lits. Subsistent l'hospitalisation médicale, l'accouchement et l'hôpital de jour ; la dialyse reste à vérifier.

**Le taux de transfert depuis les urgences est relevé.** Le cadrage le fixait à 3 %. Un établissement sans chirurgie ni réanimation transfère tout ce qui relève de l'une ou de l'autre, et la Cour chiffre les seules grossesses à risque référées de Sidi Saïd vers l'hôpital Pagnon à 1 253 femmes en 2015 et 932 en 2016. Le transfert est ici un mode de fonctionnement et non un flux résiduel. La valeur reste `HYP`.

**La durée moyenne de séjour de 6,6 jours n'est plus interprétée d'une seule façon.** Elle est plus du double de la moyenne nationale de 3,2 jours. Deux explications coexistent et les sources disponibles ne permettent pas de les départager : un établissement de proximité en sous-capacité peut garder ses patients plus longtemps, et une durée moyenne calculée sur une activité exclusivement médicale et obstétricale n'est pas comparable à une moyenne nationale qui agrège des séjours chirurgicaux généralement courts. Le rapport pose les deux.

**`docs/exigences_statistiques.md` passe à trois valeurs** pour la colonne de calculabilité : calculable, non calculable faute de champ, **sans objet pour ce site**. Les interventions chirurgicales et le taux de césarienne relèvent de la troisième. La distinction est nécessaire : un indicateur non calculable est un défaut du système d'information, un indicateur sans objet est une propriété de l'établissement, et les confondre ferait reprocher à Hosix une absence de champ là où c'est l'hôpital qui n'a pas l'activité.

**Le rapport ne met la volumétrie en avant à aucun titre de performance.** Les volumes sont donnés parce qu'ils sont mesurés et référencés, non parce qu'ils sont grands. Le projet démontre la modélisation dimensionnelle, le rapprochement probabiliste et la traçabilité de provenance ; il ne démontre pas l'ingénierie de volume et ne le prétend pas.

## Ce qui aurait invalidé cette décision

Une ligne HP Sidi Said au tableau 77, sous une graphie non testée. Un écart entre la somme des lignes de la section Meknès et son total provincial imprimé, qui aurait signalé une ligne agrégée sans être détaillée. Un tableau de capacité litière existante par établissement, qui aurait permis de vérifier que les 140 lits de 2020 valent encore — il n'en existe aucun dans le document, l'inventaire des quatre-vingt-quatre tableaux l'établit.

## Sources

`S-20` Cour des comptes, *Centre hospitalier préfectoral de Meknès*.
`S-27` Arrêté n° 456-11 portant règlement intérieur des hôpitaux, texte intégral, article 27.
`S-29` Dépêche MAP, février 2020, capacité litière annoncée de 140 lits.
`S-30` Ministère de la Santé et de la Protection Sociale, *Santé en chiffres 2024*, tableaux 76 p.102, 77 p.105, 78 p.109, 79 p.113. Empreinte SHA-256 du fichier consulté : `f9cebbb62fe1b3cfff3f8e1dd0890f827e786e9cc91809b5b464b9c46addfa05`.
