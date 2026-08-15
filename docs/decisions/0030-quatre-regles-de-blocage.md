# ADR 0030 — Quatre règles de blocage, pas les trois annoncées au périmètre

**Statut.** Accepté.

---

## Contexte

Le périmètre initial du rapprochement annonçait trois règles de blocage. Mesure
(`linkage/blocage.py`) : l'union des quatre règles retenues atteint le rappel maximal mesuré à
5 014 paires candidates ; la meilleure union possible à trois règles pour atteindre ce même
rappel coûtait 399 733 paires — un rapport d'environ quatre-vingts.

## Décision

Une quatrième règle de blocage est ajoutée : nom du père et nom de la mère et date de
naissance, en plus des trois règles du périmètre initial (pièce d'identité ; nom de famille et
téléphone ; nom de famille et adresse).

## Justification des points non triviaux

### Pourquoi une règle supplémentaire réduit l'ensemble candidat au lieu de l'agrandir

Ajouter une règle de blocage à une union agrandit toujours ou laisse égal l'ensemble des
paires qu'elle capture, à rappel fixé pour cette règle seule. Ce n'est pas ce qui se passe ici :
ce qui est comparé n'est pas « ensemble à trois règles » contre « ensemble à trois règles plus
une quatrième », mais la meilleure union possible à trois règles capable d'atteindre le même
rappel maximal que l'union à quatre règles. Sans la quatrième règle (ciblée, sélective : nom du
père, nom de la mère et date de naissance simultanément), atteindre ce rappel avec seulement
trois règles impose de recourir à des règles plus larges, chacune capturant beaucoup plus de
paires non pertinentes. La quatrième règle est plus sélective que ce qu'il faudrait lui
substituer à trois règles pour conserver le même rappel : elle referme l'ensemble candidat au
lieu de l'élargir. Le rapport de quatre-vingts mesure exactement ce coût de substitution.

## Conséquences

Le périmètre initial (trois règles) est dépassé, formellement documenté ici plutôt que corrigé
silencieusement. Le coût d'exécution du rapprochement reste borné par 5 014 paires candidates
plutôt que par 399 733 : c'est la règle supplémentaire qui rend le passage sur le moteur en
mémoire praticable (`docs/decisions/0029-moteur-execution-en-memoire.md`) à cette échelle de
population.

## Ce qui aurait invalidé cette décision

Une mesure future où le rapport entre l'ensemble à trois règles et l'ensemble à quatre règles
se réduirait fortement (une évolution du générateur qui rendrait les champs père/mère/date de
naissance moins discriminants) affaiblirait la justification de la quatrième règle — à
re-mesurer avant toute évolution substantielle du générateur de patients.

## Sources

`linkage/blocage.py` (docstring du module et fonction `regles_blocage`) ;
`linkage/ablation.csv` (ligne `complet`, `nb_paires_candidates=5014`) ;
`docs/decisions/0029-moteur-execution-en-memoire.md`.
