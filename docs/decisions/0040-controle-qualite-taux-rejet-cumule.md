# ADR 0040 — Le contrôle de qualité bloque sur le taux de rejet cumulé de la journée

**Statut.** Accepté. **Amendée** : le contrôle se place immédiatement après le chargement et
fusionne avec la tâche de vérification des contrôles d'entrée qui s'y trouvait déjà — pas après
les agrégats, sa position d'origine dans ce graphe. Trois motifs mesurés : (1) ses entrées
(`source`/`quarantaine` d'une seule date) sont disponibles dès le chargement et ne dépendent
d'aucune couche aval — vérifié par lecture de `ingestion/controle_qualite.py`, qui ne référence
ni `marts`, ni `intermediate`, ni `linkage` ; (2) à sa position d'origine il est inatteignable
dès qu'une dégradation suffisante déclenche `dbt_tests`, dont deux vérifications de portée
globale (`dbt/tests/fct_facturation_reconciliation.sql`,
`dbt/tests/fct_passage_rendez_vous_resolus.sql`, sans clause de date dans l'une ni l'autre)
tombent en amont — le taux journalier maximal atteignable en évitant les tables qu'elles
couvrent, mesuré sur les 91 dates d'un sous-ensemble généré de trois mois, vaut 3,64 %, sous le
seuil de 5 % de ce contrôle ; (3) un défaut d'extraction doit arrêter la chaîne avant que
l'entrepôt (couche dbt, rapprochement) ne soit reconstruit sur des données déjà connues
défectueuses. Alternative rejetée : exclure ces deux vérifications du sélecteur `dbt_tests` du
graphe aurait rendu la position d'origine de nouveau atteignable, au prix d'affaiblir une
vérification réelle pour la rendre aveugle à la dégradation qui la révèle — ajuster le contrôle
sur la réponse, écarté. Conséquence assumée : quand le contrôle bloque, la journée reste chargée
en base sans que l'entrepôt soit reconstruit ; l'idempotence du chargement (`docs/decisions/
0037-idempotence-portee-par-le-chargement.md`) rend le rejeu sûr après correction de
l'extraction. Écart au cadrage assumé : le document maître place le contrôle bloquant après les
agrégats — second écart de cet ordre dans ce travail, après celui déjà consigné par l'ADR 0037
sur la portée de l'idempotence. Ce qui invaliderait cette décision : des vérifications de
réconciliation restreintes à la date traitée plutôt que globales, qui rendraient la position
d'origine de nouveau atteignable.

---

## Contexte

Le chargeur garde déjà chaque fichier individuellement : une partition n'est chargée que si son
taux de rejet reste sous un seuil ET que son nombre de rejets reste sous un plancher
(`ingestion/controles.yml`, `seuil_quarantaine.valeur = 0.05`,
`plancher_rejets_bloquants.valeur = 2`).

## Décision

Le graphe porte un contrôle qui cumule les rejets de la journée sur les onze tables et compare ce
cumul au même seuil que celui du chargeur — 0,05, lu dans `ingestion/controles.yml`, jamais
recopié en littéral dans le graphe.

## Justification des points non triviaux

### Pourquoi le seuil du chargeur ne suffit pas déjà

Mesuré, en fabriquant une dégradation sans toucher au générateur ni au chargeur : une partition
de 42 lignes dont une seule est corrompue (2,4 % de rejet, sous le seuil de 5 % ET sous le
plancher de 2) n'est PAS bloquée par le chargeur — le fichier se charge normalement, avec 1 ligne
en quarantaine, un décompte qui passe de 0 à 1. Par construction, un défaut systémique déposant
peu de lignes mauvaises dans chacune des onze tables, chaque fichier restant individuellement
sous le seuil, échappe intégralement à une garde qui raisonne fichier par fichier. Un contrôle
qui cumule sur la journée entière observe ce que le chargeur, structurellement, ne peut pas voir.

### Marge mesurée avant déclenchement

Sur les 912 partitions du jeu complet et les 91 du sous-ensemble de trois mois, le taux de rejet
journalier cumulé (toutes tables confondues) a une médiane nulle sur les deux jeux — 808/912
jours (88,6 %) et 77/91 jours (84,6 %) sans aucun rejet — et un maximum observé de 0,4843 % (jeu
complet) et 0,4435 % (sous-ensemble), contre un seuil de 5 % : une marge d'un facteur environ dix
entre le pire jour mesuré et le seuil de blocage.

## Conséquences

Le chargeur garde le fichier, le graphe garde le jour : deux granularités distinctes du même
mécanisme de quarantaine, pas un contrôle redondant avec l'autre. Une dégradation qui déclenche
l'un ne déclenche pas nécessairement l'autre — un jour sans aucune partition individuellement
bloquée peut malgré tout dépasser le seuil cumulé si la dégradation est disséminée sur plusieurs
tables.

## Ce qui aurait invalidé cette décision

Un jour normal, dans les données déjà mesurées, dont le taux cumulé approcherait le seuil de
5 % — ce que la distribution mesurée exclut sur les deux jeux (maximum observé sous 0,5 %).

## Sources

`ingestion/controles.yml` (`seuil_quarantaine`, `plancher_rejets_bloquants`) ;
`ingestion/chargeur.py:148` (condition de blocage) ; distribution du taux de rejet journalier
cumulé calculée sur instrument éphémère, jeu complet (912 partitions) et sous-ensemble de trois
mois (91 partitions) ; dégradation fabriquée par corruption d'une copie de fichier CSV hors
dépôt, rejouée via `ingestion.chargeur --table --date-debut --date-fin`.
