# ADR 0013 — Registre des relations injectées

**Statut.** Accepté.

---

## Contexte

Le jeu de données est produit par un générateur dont les paramètres encodent des
relations entre grandeurs. Toute relation ainsi injectée sera nécessairement retrouvée
par l'analyse qui exploite ce jeu. Sans dispositif, le rapport présenterait comme un
résultat ce qui est un paramètre.

## Décision

Toute relation injectée est enregistrée dans un registre versionné, avec son intitulé,
le paramètre qui la porte, son statut de provenance, sa source le cas échéant, la
conséquence pour l'interprétation, et l'endroit du tableau de bord ou du rapport où elle
apparaît. Le registre compte vingt entrées et un contrôle bloquant vérifie que toute
source qu'il cite existe au registre des sources.

## Justification des points non triviaux

### La règle bloquante

Toute conclusion du chapitre d'analyse et toute recommandation qui repose sur une
relation figurant au registre est marquée comme circulaire et présentée comme un
paramètre affiché, non comme une découverte.

### Ce que la chaîne démontre malgré tout

Que l'indicateur est calculable. Le service ne peut pas le produire aujourd'hui ; la
chaîne le produit ; sur une extraction réelle, la forme véritable de la relation
apparaîtrait. C'est une capacité démontrée, pas une valeur mesurée, et le rapport le dit
à chaque occurrence.

## Conséquences

Deux correspondances restent à établir et sont portées en dette : celle du registre vers
les paramètres du générateur, et celle du registre vers les conclusions du rapport. Sans
elles, le registre décrit une intention sans garantir qu'elle est tenue.

## Ce qui aurait invalidé cette décision

Un jeu de données réel, où aucune relation ne serait injectée et où la question ne se
poserait pas.

## Sources

Aucune source externe : le registre des relations injectées, interne au projet, en tient
lieu et se suffit à lui-même pour cette décision.
