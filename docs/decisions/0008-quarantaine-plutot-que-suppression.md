# ADR 0008 — Une ligne rejetée est mise en quarantaine avec son motif, jamais supprimée

**Statut.** Accepté, et appliqué depuis l'écriture du chargeur.

> **Enregistrement rétrospectif.** Cette décision a été prise et appliquée avant que sa consignation
> ne soit écrite ; le présent enregistrement est rédigé le 18 août 2026, à partir de l'état du dépôt
> et des documents de suivi du projet. Le cadrage prescrit qu'un enregistrement soit écrit au moment
> de la décision et jamais rétrospectivement : il y est ici dérogé sciemment, pour qu'un numéro
> réservé et cité depuis l'origine cesse de renvoyer à un fichier absent.

---

## Contexte

Le chargement applique des contrôles ligne à ligne à chaque partition journalière. Certaines lignes
les échouent : une date de naissance postérieure à la date d'extraction du fichier, un horodatage de
rendez-vous hors de la plage admissible.

La question posée était de savoir ce qu'il advient d'une ligne rejetée. Trois issues se
présentaient : la supprimer sans trace, la supprimer en la journalisant, ou la conserver en base.

Les deux premières partagent la même propriété, et c'est elle qui les disqualifie : **une fois la
ligne partie, on ne peut plus rien mesurer sur elle**. Un journal dit combien de lignes sont tombées
et pourquoi ; il ne permet pas de vérifier que ce sont bien celles-là, ni de les confronter à autre
chose, ni de les recompter autrement plus tard.

## Décision

**Un schéma `quarantaine` réplique la couche source, table pour table, colonne pour colonne. Une
ligne rejetée y est écrite intégralement, avec trois colonnes techniques en sus :**

- `rejet_motifs` — le motif, la colonne en cause et la valeur fautive ;
- `rejet_date_chargement` — l'horodatage du chargement qui l'a écartée ;
- `rejet_partition` — la date de partition d'où elle vient.

**Le rejet est de grain ligne, jamais de grain entité.** Une ligne rejetée n'entraîne pas le rejet
des autres lignes de la même entité.

**Le chargement d'une partition est une transaction unique** : suppression du contenu de cette
partition dans les **deux** schémas, puis insertion des lignes acceptées dans `source` et des lignes
rejetées dans `quarantaine`. Recharger un fichier corrigé remplace exactement la partition
précédente, dans les deux schémas à la fois, plutôt que de l'accumuler.

**Un taux de rejet excessif bloque le fichier plutôt que de le charger partiellement** :
au-delà de **5 %** de lignes rejetées **et** d'un plancher de **2** rejets, la partition n'est pas
chargée du tout. Le plancher évite qu'une petite partition journalière soit bloquée par un rejet
isolé — sur moins de vingt lignes, une seule dépasse mécaniquement tout seuil en pourcentage.

## Justification des points non triviaux

### Ce que la conservation permet, et que la suppression aurait rendu impossible

Trois usages, tous mesurés sur l'état actuel de la base.

**1. La confrontation à la vérité terrain.** Le schéma porte aujourd'hui **106 lignes** : 64 fiches
patient et 42 rendez-vous. Confrontées aux défauts que le générateur déclare avoir injectés :

| Table de quarantaine | Lignes | Motif unique | Retrouvées dans la vérité terrain |
|---|---|---|---|
| `quarantaine.patients` | 64 | `naissance_future` | **64 / 64** dans `ages_incoherents` |
| `quarantaine.rendez_vous` | 42 | `plage_basse` | **42 / 42** dans `dates_aberrantes` |

Le recouvrement est **total dans les deux sens** : rien en quarantaine qui ne soit un défaut injecté,
et l'identifiant de chaque ligne le confirme un à un. Cette vérification exige les lignes elles-mêmes
et pas seulement leur décompte — un journal donnant « 64 rejets pour naissance future » serait
compatible avec 64 lignes entièrement fausses.

**2. La mesure du taux de rejet par la couche analytique.** `marts.agg_qualite_donnees` lit
directement les onze tables de quarantaine et publie un taux par table :

| Table | Lignes examinées | En quarantaine | Taux |
|---|---|---|---|
| `int_patients` | 29 107 | 64 | 0,00219 |
| `int_rendez_vous` | 14 169 | 42 | 0,00296 |

Ce taux est un **indicateur de qualité affiché**, non un compteur d'exécution. Il se recalcule à tout
moment, sur toute période, sans dépendre d'un fichier de journal conservé quelque part.

**3. La ré-instruction d'un rejet.** Le motif porte la valeur fautive et la partition d'origine. Un
lecteur qui conteste un contrôle a devant lui la ligne entière et peut juger — ce qui, pour un
contrôle posé par hypothèse plutôt que relevé, est la seule façon de le remettre en cause.

### Pourquoi le grain ligne, et ce que le grain entité aurait détruit

Sur les 64 fiches patient rejetées, **6 patients ont une autre version acceptée** dans `source`, et
**aucune** des 64 versions rejetées n'y figure. Le grain ligne écarte donc exactement la version
fautive, en laissant vivre les autres versions du même patient.

Un rejet de grain entité aurait retiré ces 6 patients entièrement, sur la foi d'une seule de leurs
versions — et l'aurait fait silencieusement, puisque les versions saines n'auraient eu, elles, aucun
motif à porter.

### Pourquoi la quarantaine n'est pas déclarée comme source dbt

Aucune de ses onze tables n'est déclarée au fichier de sources du projet de transformation.
L'agrégat de qualité les référence en clair, et le dit dans son propre en-tête.

C'est délibéré : **une déclaration de source signifierait que la couche de transformation est en
droit de bâtir sur ces lignes**. Elle ne l'est pas. La quarantaine est un objet de **mesure**, pas un
objet de **construction** ; ce qui est mesuré, c'est son volume, jamais son contenu.

### Pourquoi un seuil bloque quand même le chargement

Conserver ne veut pas dire tout accepter. Un taux de rejet élevé sur une partition ne ressemble pas à
une accumulation de fautes de saisie ligne à ligne : il ressemble à un problème d'extraction en amont
— export tronqué, colonne décalée, encodage corrompu. Charger malgré tout noierait ce signal dans la
masse des lignes acceptées, et remplirait la quarantaine de lignes dont le motif serait faux, la vraie
cause étant ailleurs.

**La quarantaine est faite pour des rejets individuels justes, pas pour absorber un fichier cassé.**

## Conséquences

Le schéma `quarantaine` double la surface de la couche source : onze tables de plus, entretenues avec
elle. Elles sont engendrées mécaniquement depuis le registre des champs, comme les tables source, ce
qui rend le doublement automatique plutôt que manuel.

Une donnée écartée reste en base. Elle est écartée de la couche analytique, **pas du dépôt de
données** — un lecteur qui compterait les lignes sans regarder le schéma les compterait deux fois.

L'idempotence porte sur les deux schémas conjointement. Un rechargement corrigé qui viderait `source`
sans vider `quarantaine`, ou l'inverse, laisserait deux versions incohérentes d'une même partition :
c'est pourquoi les deux suppressions sont dans la même transaction que les deux insertions.

## Ce qui aurait invalidé cette décision

**Qu'aucun usage aval ne lise la quarantaine.** Le schéma n'aurait alors été qu'un journal coûteux,
écrit en base pour rien, et un fichier de journal aurait suffi. La mesure a été faite : la couche
analytique le lit — les onze tables sont référencées par l'agrégat de qualité — et publie un taux par
table.

**Que les lignes retenues ne se confrontent à rien.** La conservation ne vaut que si les lignes
servent à vérifier quelque chose. Elles le servent : **106 sur 106** se retrouvent une à une dans la
vérité terrain, ce qui vérifie du même coup le contrôle et l'injection.

**Qu'un rejet doive entraîner l'entité entière** — si une version fautive rendait les autres versions
du même patient inexploitables. Elle ne les rend pas inexploitables, et **6 patients** en font la
démonstration : leurs autres versions sont chargées et servies normalement.

## Sources

`ingestion/chargeur.py` — la transaction unique, le grain ligne, l'idempotence sur les deux schémas.
`ingestion/controles.yml` — le seuil de 5 % et le plancher de deux rejets, avec la justification de
chacun.
`ingestion/controle_qualite.py` — le taux de rejet cumulé sur la journée et son échec au-delà du
seuil.
`dbt/models/marts/agg_qualite_donnees.sql` — la lecture des onze tables de quarantaine et le taux
publié, avec la raison de leur non-déclaration en source.
`docs/confrontation_quarantaine.md` — la confrontation des lignes retenues aux défauts injectés.
`docs/decisions/0014-typage-couche-source.md` — le typage textuel qui permet à une ligne fautive
d'être écrite telle quelle plutôt que refusée par la base.
`docs/decisions/0037-idempotence-portee-par-le-chargement.md` — l'idempotence dont cette décision
étend la portée au second schéma.
`docs/decisions/0040-controle-qualite-taux-rejet-cumule.md` — le contrôle qui exploite ces décomptes.
