# ADR 0040 — Le contrôle de qualité bloque sur le taux de rejet cumulé de la journée

**Statut.** Accepté.

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
