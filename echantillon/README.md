# Échantillon de données

## Ces données sont synthétiques

**Aucune ligne de ce répertoire ne provient d'un patient réel, d'un dossier réel ou d'un
établissement réel.** Le jeu est produit par simulation : des paramètres tirés de statistiques
publiques et de textes réglementaires marocains — volumétries hospitalières publiées, règlement
intérieur des hôpitaux, nomenclatures nationales — alimentent un simulateur qui engendre des
identités, des rendez-vous, des passages, des séjours et des factures cohérents entre eux.

Les identifiants, numéros de pièce d'identité et numéros de téléphone sont tirés dans des espaces
**disjoints** des séries réellement émises.

**Chaque fichier le redit dans ses propres octets** : sa première colonne, `donnees_synthetiques`,
porte la mention sur chacune de ses lignes. Un fichier téléchargé seul, sans ce document, reste
identifiable comme synthétique quel que soit l'outil avec lequel on l'ouvre.

## Ce que contient l'échantillon

Vingt-trois fichiers, un par table, au format à séparateur virgule et en encodage universel avec
marque d'ordre d'octets — les mêmes que ceux du livrable complet.

| Couche | Tables | Lignes par table |
|---|---|---|
| Source — les données telles qu'elles arrivent du système d'information | 11 | 200 |
| Analytique — le schéma en étoile qui les modélise | 12 | jusqu'à 50 |

Les lignes sont prélevées **systématiquement** : une ligne sur *N*, dans l'ordre d'une clé stable.
L'extrait parcourt donc toute l'étendue de chaque table plutôt qu'une seule période, et il est
**reproductible** — le réengendrer rend exactement le même contenu, sans tirage aléatoire ni graine.

Deux fiches sont ajoutées d'office à l'extrait des patients : **`IPP-002116` et `IPP-025034`**, qui
désignent la même personne. Elles ne diffèrent que par une variante graphique du prénom —
*Mohammed* et *Mohamed* — et permettent de voir, sur une ligne, ce que le rapprochement d'identités
a à rapprocher.

## Ce qu'il ne faut pas en conclure

**Cet échantillon illustre la forme des données ; il ne mesure aucune activité.** Un extrait d'une
table sur *N* ne porte aucun total, aucune moyenne et aucune proportion exploitables : les compter
donnerait des chiffres faux. Les grandeurs du projet se lisent sur le tableau de bord, qui les
recalcule sur le jeu entier.

Il ne dit rien non plus d'un établissement réel : les paramètres sont posés ou tirés de sources
publiques, et le document des sources dit, paramètre par paramètre, lesquels sont mesurés et
lesquels sont posés.

## D'où il est extrait

De la base construite par la chaîne du dépôt : la couche `source` pour les onze premières tables,
le schéma d'instantané que lit le tableau de bord pour les douze autres.

Il est produit par `extraction/echantillon.py`, versionné, dont l'exécution redonne le même contenu :

```
uv run python -m extraction.echantillon
```
