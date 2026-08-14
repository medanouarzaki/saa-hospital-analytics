# ADR 0029 — Le rapprochement s'exécute sur un moteur en mémoire, pas sur PostgreSQL

**Statut.** Accepté.

---

## Contexte

`splink`, la bibliothèque de rapprochement probabiliste utilisée, propose plusieurs moteurs
d'exécution interchangeables pour les mêmes règles de blocage et le même modèle : un moteur
PostgreSQL, qui écrit ses tables intermédiaires dans la base cible, et un moteur en mémoire
(DuckDB), qui n'écrit rien dans une base relationnelle. La population soumise au rapprochement
est lue une fois depuis `marts.dim_patient` (`linkage/population.py::extraire_population`,
requête `SELECT ... FROM marts.dim_patient WHERE est_courante`) et tient en 25 842 lignes.

Chaque schéma du projet est aujourd'hui soit généré mécaniquement depuis
`docs/champs/registre_champs.yml` et vérifié contre lui, soit écrit à la main et vérifié par un
test dédié (`docs/decisions/0014-typage-couche-source.md`,
`docs/decisions/0032-ddl-schema-linkage-ecrit-a-la-main.md`). Un moteur PostgreSQL créerait,
pour son propre usage, des tables intermédiaires dans la base du projet — des objets qui
n'appartiendraient à aucune des deux catégories.

## Décision

Le rapprochement s'exécute sur le moteur en mémoire de `splink` (`DuckDBAPI`,
`linkage/estimation.py`, `linkage/prediction.py`), jamais sur son moteur PostgreSQL.

## Justification des points non triviaux

### Pourquoi le moteur PostgreSQL n'est pas seulement plus lent, mais hors contrôle

Le problème n'est pas la performance. C'est que le moteur PostgreSQL de `splink` écrirait ses
tables intermédiaires dans le schéma cible sans passer par un DDL écrit à la main ni par un
DDL généré depuis le registre — un troisième mode de production de schéma, non couvert par les
tests de correspondance existants (`test_provenance.py` côté source,
`docs/decisions/0032-ddl-schema-linkage-ecrit-a-la-main.md` côté linkage). Ces tables
échapperaient à tout contrôle, pas seulement à une convention de nommage.

## Conséquences

Le rapprochement dépend de la mémoire disponible sur la machine qui l'exécute, pas de
l'espace disque de la base. À 25 842 lignes, la population tient largement en mémoire sur un
poste de développement ordinaire. Ce choix se rediscuterait à l'ordre de grandeur où la
population ne tiendrait plus en mémoire sur la machine d'exécution cible — un seuil qui se
mesure au moment où il se rapproche, pas aujourd'hui à 25 842 lignes.

## Ce qui aurait invalidé cette décision

Une croissance de la population de rapprochement à un ordre de grandeur où DuckDB
échouerait à charger la population en mémoire sur la machine d'exécution — à re-mesurer avant
toute campagne de rapprochement sur un jeu substantiellement plus grand que celui mesuré ici.

## Sources

`linkage/population.py::extraire_population` ; `linkage/estimation.py`,
`linkage/prediction.py` (`from splink.backends.duckdb import DuckDBAPI`) ;
`docs/decisions/0014-typage-couche-source.md` ;
`docs/decisions/0032-ddl-schema-linkage-ecrit-a-la-main.md`.
