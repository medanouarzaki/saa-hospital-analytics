# ADR 0032 — Le DDL du schéma `linkage` est écrit à la main

**Statut.** Accepté.

---

## Contexte

Les schémas `source` et `quarantaine` sont générés mécaniquement depuis
`docs/champs/registre_champs.yml` et vérifiés contre lui par un test dédié — le registre décrit
des champs observés dans les sources, pas des tables produites par un traitement. Le schéma
`linkage`, lui, ne décrit rien de tel : ses tables (`paires_candidates`, `grappes_identite`,
`evaluation`) portent des résultats calculés par le rapprochement — probabilités, niveaux de
comparaison, appartenance à une grappe —, sans correspondant dans le registre des champs.

## Décision

Le DDL du schéma `linkage` (`linkage/ddl/00_schema_linkage.sql` et les trois fichiers de table
qui le suivent) est écrit à la main, pas généré depuis le registre. Mesure sur le catalogue :
3 tables, 34 colonnes (`paires_candidates` : 17, `grappes_identite` : 4, `evaluation` : 13).

## Justification des points non triviaux

### Pourquoi un DDL généré puis vérifié contre le registre ne prouverait rien ici

Pour les schémas `source` et `quarantaine`, générer le DDL depuis le registre puis le vérifier
contre ce même registre est un contrôle légitime : la vérification porte sur la synchronisation
mécanique entre deux artefacts produits l'un depuis l'autre. Pour `linkage`, il n'existe pas de
second artefact indépendant contre lequel vérifier — le registre ne décrit pas ces tables.
Un DDL généré depuis le registre puis vérifié contre ce même registre serait vrai par
construction : la vérification ne prouverait rien, elle constaterait sa propre prémisse.

## Conséquences

La vérification que le DDL du schéma `linkage` correspond à ce qu'attend le code applicatif
(`linkage/evaluation.py`, `linkage/regroupement.py`, ...) n'est plus mécanique : elle repose sur
un test qui exécute le code contre le schéma réellement appliqué et constate l'absence
d'erreur, pas sur une comparaison octet à octet entre deux générations indépendantes. Toute
évolution des colonnes lues ou écrites par le code applicatif doit être répercutée à la main
dans le DDL, sans filet mécanique de synchronisation.

## Ce qui aurait invalidé cette décision

L'apparition d'une source indépendante du registre susceptible de décrire les tables du schéma
`linkage` (par exemple une spécification distincte des résultats de rapprochement) rendrait de
nouveau une génération-puis-vérification informative, et cette décision serait à reconsidérer.

## Sources

`linkage/ddl/00_schema_linkage.sql`, `linkage/ddl/01_paires_candidates.sql`,
`linkage/ddl/02_grappes_identite.sql`, `linkage/ddl/03_evaluation.sql` ;
`docs/champs/registre_champs.yml`.
