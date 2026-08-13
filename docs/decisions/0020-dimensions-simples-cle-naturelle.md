# ADR 0020 — quatre dimensions simples à clé naturelle, aucun libellé inventé, sans clé de substitution

**Statut.** Accepté.

---

## Contexte

`dim_date` (`docs/decisions/0019-...md`) est la seule dimension existante. Quatre familles de
codes reviennent à travers plusieurs tables `intermediate` sans dimension dédiée : service, code
d'activité, organisme/couverture, compte agent — chacune mesurée depuis `docs/champs/registre_
champs.yml` par script, avec contrôle positif avant acceptation (`service_accueil` retrouvé dans
la famille service, `cree_par` dans la famille agent). Aucune de ces quatre familles n'est
accompagnée, dans le registre ou ailleurs dans le dépôt, d'une table de libellés documentée avec
provenance.

## Décision

1. **Clé naturelle, jamais de clé de substitution.** Chaque dimension (`dim_service`,
   `dim_activite`, `dim_organisme`, `dim_agent`) porte une seule colonne, le code lui-même
   (`code_service`, `code_activite`, `code_organisme`, `code_agent`), `select distinct` en
   `union` sur les colonnes mesurées de sa famille. Aucune clé auto-générée : la vue reste
   déterministe d'une exécution `dbt run` à l'autre, propriété déjà exploitée par les tests de
   complétude (point 3).
2. **Aucun libellé inventé.** Les quatre dimensions ne portent que le code. Un libellé (« HGO »
   → « Gynéco-Obstétrique ») serait utile mais n'est documenté nulle part dans le dépôt avec une
   provenance vérifiable — l'inventer violerait la discipline de provenance déjà appliquée à
   toutes les autres décisions de ce projet (chaque valeur du domaine métier remonte à une preuve
   citée). Ce choix attend une source documentée, pas une paresse : la structure de la dimension
   (une seule colonne aujourd'hui) n'empêche pas d'ajouter des colonnes de libellé plus tard, sans
   migration de clé puisqu'il n'y en a pas.
3. **Complétude bidirectionnelle testée, écrite indépendamment du modèle.** Chaque dimension a un
   test singulier qui réécrit l'union des colonnes source (pas un appel à `ref('dim_X')` pour
   construire son propre attendu) et la compare par `except` dans les deux sens à ce que produit
   le modèle. Mutation-testé dans les quatre directions (voir les mutations du rapport de ce
   lot) : filtrage d'un code, ajout d'un code fantôme, duplication, injection d'un `null` —
   chacune isole le test visé, un seul collatéral réel rencontré (une valeur `null` injectée fait
   aussi rougir la complétude, puisque chaque branche du recalcul exclut déjà les valeurs vides/
   nulles par construction — expliqué, pas un défaut).

## Justification des points non triviaux

### Pourquoi `dim_organisme` réunit deux registres de codes disjoints

`patients.compagnie_assurance` (`00042`, `00089`, `00116`, `SANS`) et `prises_en_charge.organisme`
(`CNSS`, `TNS`, `ACHAMIL`) ne partagent aucun code — mesuré, pas supposé (`except` croisé, zéro
recoupement). Réunis dans une même dimension malgré cela : les deux représentent un organisme de
couverture au sens large (l'un l'identifiant de la compagnie/du régime déclaré à l'inscription,
l'autre l'organisme gestionnaire de la prise en charge), catégorie conceptuelle unique même si les
deux espaces de codes ne se recoupent jamais dans les données observées. Chaque code reste
rattaché à ce qu'il est : la dimension ne prétend pas qu'un `00116` et un `CNSS` seraient le même
référentiel, elle catalogue simplement l'ensemble des codes de couverture rencontrés.

### Pourquoi `rendez_vous.service_ext` n'entre pas dans `dim_service`

Seule colonne de la famille service en `texte` (les huit autres sont en `code`) ; ses cinq valeurs
mesurées sont des libellés complets (« Urgences », « Medecine interne »...), pas les codes courts
des huit autres colonnes (`UR`, `HM`...). Un domaine de valeurs disjoint et de nature différente :
l'inclure aurait mélangé codes et libellés dans une même colonne `code_service`, contradictoire
avec la décision du point 2 (aucun libellé).

### Pourquoi `encaissements.regisseur` entre dans la famille agent malgré un critère textuel négatif

Le critère de recherche (`_par` en suffixe) ne le capture pas ; sa note de registre ne dit pas
littéralement « compte utilisateur ». Retenu après mesure des valeurs elles-mêmes (`REG-GUI01`,
`REG-CAI01`, `REG-GUI02` — motif `PREFIXE-POSTE##` identique à `ADM-ACC01`, `AGT-GUI01`,
`INF-BUR01`...), pas sur la base du texte de la note — illustration directe de la règle 6 : un
contrôle par motif textuel peut se tromper par omission, la mesure des valeurs tranche.
`medecin_ext`/`medecin` (noms de praticiens en texte libre, aucun motif de compte) ont été mesurés
et exclus par le même raisonnement, en sens inverse.

## Conséquences

Seize vues dans `marts` (`dim_date`, quatre nouvelles dimensions, `agg_provenance_champs`), 99
tests dbt verts (87 précédents + 8 génériques + 4 de complétude). La dette obstétricale (aucune
colonne mesurée ne distingue un accouchement d'un autre séjour du service `HGO`) est mesurée et
consignée dans ce lot, sans décision — reportée à la couche des faits qui devra soit s'en passer,
soit documenter une source qui comble ce manque.

## Ce qui aurait invalidé cette décision

L'apparition, dans une future extraction, d'un code partagé entre `compagnie_assurance` et
`organisme` (aujourd'hui disjoints) n'invaliderait pas la décision de les réunir mais changerait
l'interprétation du recoupement — à re-mesurer avant toute jointure de `dim_organisme` sur les
deux colonnes source dans un modèle de faits. Une source documentée de libellés (traduction
officielle des codes de service, par exemple) inverserait le point 2 pour `dim_service`
spécifiquement, sans toucher aux trois autres dimensions.

## Sources

`dbt/models/marts/dim_service.sql`/`.yml`, `dim_activite.sql`/`.yml`, `dim_organisme.sql`/`.yml`,
`dim_agent.sql`/`.yml` ; `dbt/tests/dim_service_completude.sql`, `dim_activite_completude.sql`,
`dim_organisme_completude.sql`, `dim_agent_completude.sql` ; `docs/champs/registre_champs.yml` ;
`docs/decisions/0019-seed-calendrier-marocain-et-dim-date.md`.
