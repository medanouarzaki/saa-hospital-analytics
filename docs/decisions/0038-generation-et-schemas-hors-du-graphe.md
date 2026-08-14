# ADR 0038 — La génération et l'application des schémas restent hors du graphe

**Statut.** Accepté.

---

## Contexte

La chaîne de données compte huit étapes, toutes enchaînées en dur aujourd'hui dans l'intégration
continue : génération, DDL source/quarantaine, DDL du rapprochement, chargement, dbt, prédiction,
évaluation, ablation.

## Décision

La génération et l'application des schémas (DDL source/quarantaine et DDL du rapprochement)
restent des préalables d'initialisation, hors du graphe quotidien. Le graphe suppose les schémas
déjà en place et les fichiers d'une date d'extraction déjà déposés ; sa première tâche vérifie
cette disponibilité plutôt que de la produire.

## Justification des points non triviaux

### Pourquoi la génération n'est pas une tâche candidate

Mesuré par exécution effective : le générateur échoue sur une période d'un seul jour
(`ValueError: effectif de personnes eligibles insuffisant pour le taux de doublons configure`),
le mécanisme d'injection de doublons (`generator/doublons.py`) ayant besoin d'un effectif de
personnes éligibles qu'une seule journée ne fournit pas. Ce n'est pas une limite de son
interface en ligne de commande, qui accepte pourtant des dates de début et de fin identiques :
c'est une limite structurelle de son mécanisme, qui ne se contourne pas en modifiant
l'invocation.

### Pourquoi l'application des schémas n'est pas une tâche candidate

Le fichier `ingestion/ddl/20_marts_agg_provenance.sql` crée `marts.agg_provenance_champs` par
`create view`, sans `drop view if exists` ni `create or replace view` en amont — confirmé par
lecture directe du fichier. Rejouer l'application des schémas sans réinitialisation préalable
échoue systématiquement sur ce fichier (`DuplicateTable`), un comportement observé en conditions
réelles, pas seulement supposé. Une tâche de graphe qui échouerait de façon prévisible à son
second passage n'a pas sa place dans une chaîne planifiée à répétition.

## Conséquences

Le graphe ne recrée ni ne réinitialise aucun schéma : il part d'un état où `source`,
`quarantaine` et `linkage` existent déjà, peuplés ou non pour la date traitée. Sa première tâche
constate cette disponibilité (par exemple un contrôle de présence des schémas et des fichiers
d'extraction attendus) plutôt que de la garantir elle-même.

## Ce qui aurait invalidé cette décision

Une garde de ré-exécution ajoutée à `ingestion/ddl/20_marts_agg_provenance.sql` (`drop view if
exists` avant `create view`, sur le modèle des 24 autres fichiers du même répertoire) rendrait
l'application des schémas rejouable sans échec prévisible, et la rendrait candidate à devenir une
tâche du graphe — une modification qui n'est pas apportée ici.

## Sources

`.github/workflows/ci.yml` (job `dbt`, huit étapes enchaînées) ; `generator/doublons.py`
(`injecter_doublons`) ; exécution effective du générateur sur une période d'un jour, hors
`generator/output/` ; `ingestion/ddl/20_marts_agg_provenance.sql` ; rejeu du DDL sur instrument
éphémère, `DuplicateTable` reproduit.
