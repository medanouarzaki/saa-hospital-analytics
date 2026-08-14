# ADR 0037 — L'idempotence est portée par le chargement, pas par la couche dimensionnelle

**Statut.** Accepté.

---

## Contexte

Le cadrage du projet prescrivait un mécanisme de suppression de partition suivie d'une
réinsertion en aval de la chaîne, et une fusion d'historisation par clé de hachage dans la couche
dimensionnelle.

## Décision

L'idempotence de la chaîne se prouve au chargement, pas dans les couches en aval. Les couches
`intermediate` et `marts` sont idempotentes par construction et cette propriété se vérifie
plutôt qu'elle ne s'implémente. L'historisation qu'elles portent est recalculée à chaque lecture,
jamais fusionnée.

## Justification des points non triviaux

### Pourquoi la suppression-réinsertion en aval n'a pas de sens ici

Mesure sur le catalogue de la base : la totalité des 11 objets d'`intermediate` et des 20 objets
de `marts` sont des vues (`table_type = 'VIEW'`), aucun n'est une table — donc aucun contenu
stocké en aval du chargement à supprimer ni à fusionner. Le mécanisme de suppression puis
réinsertion existe réellement dans la chaîne, mais dans `ingestion/chargeur.py`, par partition de
date et en transaction unique (`DELETE` des deux schémas pour la date, puis `INSERT`) — c'est là,
et seulement là, qu'une notion de partition rejouable existe.

### Preuve mesurée de l'idempotence et de ses deux exceptions

Empreintes de contenu (somme de contrôle sur les lignes triées) identiques au rejeu, sur les
tables `source.*`, sur la graine dbt (`referentiels.calendrier_marocain`), sur la dimension
patient reconstruite (`marts.dim_patient`) et sur les tables de rapprochement
(`linkage.paires_candidates`, `linkage.evaluation`). Indépendance à l'ordre du chargement prouvée
par empreintes identiques sur trois partitions de dates chargées dans un ordre puis dans l'ordre
inverse. Deux exceptions mesurées, toutes deux à cardinalité inchangée mais contenu divergent :
`quarantaine.*` porte une colonne `rejet_date_chargement` (horodatage réel du chargement), qui
diffère à chaque rejeu même quand les lignes rejetées et leurs motifs sont identiques ; et
`linkage/ablation.csv` diffère au seizième chiffre significatif d'une réestimation du modèle à
l'autre, sur sa seule variante qui réestime (bruit de calcul en virgule flottante, pas une
divergence de logique).

## Conséquences

Une tâche de graphe qui recharge une partition déjà chargée ne modifie ni le contenu de
`source.*` ni celui des vues qui en dépendent — l'idempotence de la chaîne entière découle de
celle du seul chargement. L'égalité de contenu au rejeu s'entend hors la colonne
`rejet_date_chargement` de la quarantaine, qui reste, par nature, un horodatage et non une
donnée métier.

## Ce qui aurait invalidé cette décision

Une matérialisation en table d'un modèle de la couche `marts` (passage de `+materialized: view`
à `table` dans `dbt/dbt_project.yml`) créerait un contenu stocké en aval du chargement, à propos
duquel la question de la suppression-réinsertion ou de la fusion d'historisation redeviendrait
pertinente — à réexaminer alors.

## Sources

`information_schema.tables` (catalogue de la base du projet, `table_schema in ('intermediate',
'marts')`) ; `dbt/dbt_project.yml` (`+materialized: view`) ; `ingestion/chargeur.py` (docstring
de module, mécanisme `DELETE`/`INSERT` par partition) ; empreintes SHA-256/MD5 mesurées sur
instrument éphémère avant/après rejeu, et dans deux ordres de chargement opposés ;
`linkage/ablation.py` (variante `C_les_deux_retraits`, seule à réestimer le modèle).
