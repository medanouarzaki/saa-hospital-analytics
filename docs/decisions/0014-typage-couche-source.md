# ADR 0014 — Typage et absence de contraintes dans la couche source

**Statut.** Accepté.

---

## Contexte

La couche source reproduit une extraction du système hospitalier, avec ses défauts. Le
jeu de données produit comporte délibérément des valeurs mal formées, des dates au
format d'affichage du système observé — mois, jour, année, douze heures — et des
doublons de fiches patients.

## Décision

Les cent soixante-quinze colonnes du schéma source sont typées en texte. Aucune
contrainte n'est posée : ni clé primaire, ni non-nullité, ni clé étrangère, ni index.

## Justification des points non triviaux

### Pourquoi une ligne mal formée doit se charger

Une ligne mal formée doit se charger pour pouvoir être mise en quarantaine avec son
motif ; si la base la rejetait à l'insertion, le dispositif de quarantaine n'aurait plus
d'objet et le taux de rejet ne serait plus mesurable.

### Pourquoi aucune clé primaire

Une clé primaire rejetterait les doublons, qui sont à la fois une famille de défauts
injectés et la matière même du rapprochement d'identités. Le typage strict, la
standardisation des dates et le contrôle d'unicité appartiennent à la couche
intermédiaire.

## Conséquences

Le registre des champs porte deux clés de type : le type effectif dans la couche
source, uniformément textuel, et le type métier attendu, qui alimente le dictionnaire
des données et la déclaration des sources de l'outil de transformation. Le dictionnaire
publie le second, non le premier.

## Ce qui aurait invalidé cette décision

L'abandon du mécanisme de quarantaine au profit d'un rejet au chargement, ou un jeu de
données sans défaut injecté.

## Sources

Aucune source externe : décision de conception de la chaîne de données, non un fait
mesuré dans une source tierce.
