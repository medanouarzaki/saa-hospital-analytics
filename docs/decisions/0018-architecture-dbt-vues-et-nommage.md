# ADR 0018 — dbt matérialise en vues, `profiles.yml` vit hors dépôt, les macros de conversion s'appuient sur des formats mesurés

**Statut.** Accepté.

---

## Contexte

La couche `source` est intégralement en `text`, sans exception (`docs/decisions/0014-typage-couche-source.md`).
`test_provenance.py::test_couverture_bidirectionnelle` compare le registre des champs au
catalogue PostgreSQL (`information_schema.columns`/`.tables`), filtré sur `t.table_type =
'BASE TABLE'` : toute colonne de `intermediate`/`marts` qui matérialiserait en TABLE
apparaîtrait dans ce catalogue sans correspondant dans le registre (qui ne couvre que
`source`) et ferait rougir ce test — mesuré avant d'écrire, lors de la mesure qui a établi le
périmètre de ce test. `docs/champs/registre_champs.yml` et `dbt/models/sources/source.yml`
(généré mécaniquement depuis lui, comparé octet à octet par
`test_provenance.py::test_artefacts_synchrones`) ne gouvernent que la couche source ; aucun
des deux ne s'étend à une couche intermédiaire ou dimensionnelle.

## Décision

1. **Matérialisation par défaut `view`** dans `dbt/dbt_project.yml`, pour tous les modèles
   d'`intermediate` et de `marts`. Une vue n'apparaît jamais comme `BASE TABLE` dans
   `information_schema.tables` — confirmé après coup par l'exécution réelle de
   `test_provenance.py` contre la base Compose où `dbt run` venait de créer
   `intermediate.int_patients` : les quatre tests passent, `int_patients` n'apparaît dans
   aucun résultat de `test_couverture_bidirectionnelle`.
2. **`~/.dbt/profiles.yml` hors dépôt**, chaque paramètre de connexion surchargeable par une
   variable d'environnement `DBT_POSTGRES_*` avec la valeur de `.env` comme défaut — sert
   une CI ou une base éphémère future sans modification du fichier ni exposition d'identifiant
   dans un fichier suivi.
3. **Nommage des schémas sans préfixe**, via une surcharge du macro `generate_schema_name`
   (mécanisme documenté par dbt-core lui-même dans son propre fichier
   `macros/get_custom_name/get_custom_schema.sql` : « This macro can be overriden in projects
   to define different semantics »). Sans cette surcharge, un modèle configuré
   `schema: intermediate` sur une cible dont le schéma par défaut est `intermediate` atterrit
   dans `intermediate_intermediate` — mesuré avec un modèle d'essai minimal avant toute
   macro, confirmé par `information_schema.tables`, corrigé, re-mesuré.
4. **Macros de conversion (`dbt/macros/conversions.sql`) fondées sur des formats mesurés**,
   pas supposés : `NULL` n'est jamais utilisé dans la couche source (zéro occurrence sur cinq
   colonnes de trois types, dont deux avec une part significative de valeurs manquantes) — la
   valeur manquante est toujours la chaîne vide, chaque macro utilise donc `nullif(col, '')`
   plutôt que de tester `is null` seul. Le domaine booléen est exactement `{'0', '1', ''}`
   (inventaire exhaustif des neuf colonnes booléennes du registre) — jamais `'true'`/`'false'`
   ni aucune autre représentation.

## Justification des points non triviaux

### Pourquoi ne pas utiliser le templater `dbt` de sqlfluff

Le templater `jinja` générique déjà en place (utilisé par `ingestion/ddl/*.sql`, du SQL pur)
échoue sur un modèle dbt (`Undefined jinja template variable: 'convertir_date'`) — mesuré
avant toute décision. Le templater `sqlfluff-templater-dbt` exigerait une nouvelle dépendance,
une compilation dbt complète et une connexion active à chaque lint (fragile, plus lent, non
nécessaire). Retenu à la place : les mécanismes déjà intégrés au templater `jinja` de
sqlfluff, trouvés dans le code source du paquet installé (référence la plus fiable pour la
version exacte utilisée) — `apply_dbt_builtins` (stubbe `ref`/`source`/`config`) et
`load_macros_from_path` (charge les macros réelles du projet, pas des stubs). Portée limitée à
`dbt/` via une configuration `sqlfluff` nichée (`dbt/.sqlfluff`), sans toucher au comportement
de lint du reste du dépôt.

### Pourquoi une configuration nichée plutôt qu'une seule racine

`ignore_paths` déclaré à la racine avec des motifs préfixés `dbt/` (`dbt/target/`) ne
s'appliquait pas, mesuré empiriquement ; le même motif relatif (`target/`) déclaré dans
`dbt/.sqlfluff` fonctionnait. Retenu tel quel, sans chercher plus loin la cause exacte
(résolution de chemin interne à sqlfluff, hors périmètre de cette décision) — le comportement mesuré
suffit à la décision.

### Pourquoi deux générateurs de test génériques plutôt que dbt_utils

`dbt_utils` (paquet communautaire) aurait fourni `unique_combination_of_columns` et d'autres
utilitaires, mais aurait ajouté une dépendance externe pour un besoin que deux tests
génériques courts (`meme_decompte_que_la_source`, `conversion_sans_perte`) couvrent
entièrement, chacun écrit comme deux sous-requêtes indépendantes, sans littéral de
volumétrie — valent aussi bien sur un sous-ensemble de trois mois que sur le scénario complet.
L'unicité du grain réutilise le test `unique` natif de dbt-core avec une expression concaténée
comme `column_name` (le code source de `test_unique` interpole `{{ column_name }}` tel quel,
sans exiger un identifiant de colonne simple) — pas de nouveau test, pas de nouvelle
dépendance.

## Conséquences

`int_patients`, premier modèle intermédiaire, prouve l'architecture complète (macros, nommage,
tests génériques mutation-testés, cohabitation avec `test_provenance.py` et `sqlfluff`) sur
les 46 colonnes de `source.patients`. Aucune colonne `decimal`/`entier` n'y figure : la macro
`convertir_numerique` reste écrite et testable isolément (mutation-testable de la même façon)
mais n'est exercée par aucun test pour l'instant — un futur modèle sur une table à colonnes
numériques (`creances`, `lignes_facture`, ...) l'exercera. La CI actuelle ne lance encore
aucune commande dbt (`.github/workflows/ci.yml` non modifié ici) — plus tard.

## Ce qui aurait invalidé cette décision

Une version de dbt-core future qui matérialiserait les vues différemment dans
`information_schema.tables` (par exemple un type de relation reclassé) aurait invalidé la
prémisse « une vue n'est jamais un `BASE TABLE` » — à re-mesurer avant toute mise à jour de
version majeure de dbt-core ou de PostgreSQL.

## Sources

`dbt/dbt_project.yml`, `dbt/macros/generate_schema_name.sql`, `dbt/macros/conversions.sql`,
`dbt/models/intermediate/int_patients.sql`, `dbt/tests/generic/meme_decompte_que_la_source.sql`,
`dbt/tests/generic/conversion_sans_perte.sql` ; `tests/test_provenance.py::test_couverture_bidirectionnelle`,
`::test_artefacts_synchrones` ; `.venv/.../dbt/include/global_project/macros/get_custom_name/get_custom_schema.sql` ;
`.venv/.../dbt/include/global_project/macros/generic_test_sql/unique.sql` ;
`.venv/.../sqlfluff/core/templaters/jinja.py`, `.../sqlfluff/core/linter/discovery.py` ;
`docs/decisions/0014-typage-couche-source.md`.
