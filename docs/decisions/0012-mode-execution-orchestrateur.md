# ADR 0012 — Mode d'exécution de l'orchestrateur

**Statut.** Accepté.

---

## Contexte

Le service d'orchestration tourne en conteneur unique, en mode autonome (`command: standalone`,
`docker/docker-compose.yml`), exécuteur local. Sa base de métadonnées réside dans la même
instance PostgreSQL que la base du projet, sous le même rôle, dans une base distincte
(`airflow`, créée par `docker/initdb/01_airflow_database.sql`). Le répertoire de graphes du
conteneur est monté en lecture seule depuis `airflow/` du dépôt. Aucun outil de la chaîne de
données (dbt, le paquet de rapprochement, le code du dépôt) n'est présent dans l'image officielle
de l'orchestrateur.

## Décision

Deux parties. **Le mode autonome à conteneur unique est conservé.** Et **le conteneur ordonnance
sans exécuter** : les tâches du graphe sont des commandes shell qui s'exécutent dans
l'environnement du projet, l'orchestrateur étant ajouté au groupe de dépendances de développement
du projet plutôt qu'à une image dédiée.

## Justification des points non triviaux

### Pourquoi pas une image de projet pour l'orchestrateur

Installer les dépendances d'exécution du projet dans l'image officielle change la version de 18
paquets déjà présents, dont deux que l'outil d'installation signale lui-même en conflit avec des
fournisseurs déjà installés dans cette même image (`pandas` 2.1.4 → 3.0.5, contre
`apache-airflow-providers-snowflake` qui exige `<2.2` ; `websockets` 16.0 → 17.0.1, contre
`google-genai` qui exige `<17.0`), fait passer la taille de l'image de 650 Mo à 4,19 Go, et casse
l'import de `ingestion.chargeur` parce que l'exclusion de contexte de construction Docker retire
`docs/` — dont `ingestion/controles.py` dépend au moment même de l'import, pour lire
`docs/champs/registre_champs.yml`. À l'inverse, ajouter l'orchestrateur au groupe de dépendances
de développement du projet ne change AUCUNE version de paquet déjà présente et coûte 1,53 s et
119 Mo à une synchronisation à froid, contre une base de 20,11 s et 632 Mo sans lui.

## Conséquences

Un fichier de graphe n'importe rien du projet — seulement l'orchestrateur — pour rester
analysable dans le conteneur officiel tel quel : mesuré, un tel fichier déposé sous `airflow/`
apparaît dans l'ensemble de graphes du conteneur en 83 s, sans action supplémentaire. Ses tâches, en
revanche, ne s'y exécutent pas : c'est une limite assumée, pas un oubli. Le graphe s'exécute
ailleurs, là où dbt, le paquet de rapprochement et le code du dépôt sont réellement installés.

## Ce qui aurait invalidé cette décision

Un exécuteur qui lance chaque tâche dans son propre conteneur (`DockerOperator` ou équivalent)
supprimerait le mélange de versions de dépendances au lieu de le subir en le reportant hors du
conteneur de l'orchestrateur — c'est la voie propre pour ce problème, mais elle n'est pas retenue
ici.

## Sources

`docker/docker-compose.yml` ; `docker/initdb/01_airflow_database.sql` ; comparaison des listes de
paquets d'une image candidate avant/après construction (`pip list --format=freeze`) ; mesure de
synchronisation à froid avec et sans l'orchestrateur ajouté au groupe de développement ; mesure
d'apparition d'un graphe minimal déposé sous `airflow/` dans l'ensemble de graphes du conteneur.
