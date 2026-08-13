# ADR 0028 — Les agrégats : grain de chacun, choix guidés par mesure, et le huitième maintenu hors dbt

**Statut.** Accepté.

---

## Contexte

Sept agrégats ont été écrits comme modèles dbt, chacun résumant un ou plusieurs faits à un grain
plus large. Un huitième agrégat, `agg_provenance_champs`, existait déjà auparavant sous forme
d'une vue créée par DDL statique (`ingestion/ddl/20_marts_agg_provenance.sql`), hors du projet
dbt — cette décision documente pourquoi il le reste.

## Décision

1. **Grain de chacun des sept agrégats dbt.** `agg_delai_rendez_vous` : une ligne par
   `code_activite` (8 lignes). `agg_absenteisme` : une ligne par `code_activite` (8 lignes).
   `agg_activite_journaliere` : une ligne par jour, type d'événement, service et activité
   (13 855 lignes). `agg_urgences_journalier` : une ligne par jour d'arrivée et niveau de tri
   (3 972 lignes). `agg_recouvrement` : une ligne par jour de naissance de créance et type de
   débiteur (1 394 lignes). `agg_qualite_donnees` : une ligne par table intermediate et par
   colonne (175 lignes, grain colonne — voir point 2). `agg_doublons_identite` : une ligne par
   critère de collision exacte (2 lignes, deux critères retenus — voir point 3).
2. **Grain de `agg_qualite_donnees` décidé sur une mesure de coût, pas par convenance.** Le coût
   de convertir chaque ligne des onze vues intermediate en document puis de l'exploser en paires
   clé-valeur a été mesuré vue par vue avant d'écrire le modèle : ≈ 1,78 seconde au total pour
   les onze vues, loin sous le seuil de 10 secondes qui aurait justifié un repli sur
   le grain table seule. Le grain colonne a donc été retenu, chaque ligne portant le nombre de
   lignes examinées, de valeurs renseignées, et — dénormalisés depuis le niveau table — le
   nombre de lignes en quarantaine et le taux de quarantaine correspondants.
3. **Règle du dernier instantané pour les créances.** `agg_recouvrement` ne retient, par
   créance, que son instantané le plus récent (`row_number() over (partition by n_creance order
   by date_extraction desc)`, `rang = 1`). Une créance porte plusieurs lignes-instantané
   (5 876 lignes pour 5 486 créances distinctes, jusqu'à 5 instantanés pour une même créance,
   mesuré) où `montant_du` est constant mais `montant_recouvre`/`montant_restant`
   évoluent : sommer toutes les lignes surcompterait `montant_du` autant de fois qu'il existe
   d'instantanés pour la créance.
4. **Deux critères de collision d'identité retenus, un écarté, sur mesure de
   non-dégénérescence.** Retenus : nom (en réalité le prénom, `generator/patients.py`) +
   `nom_famille_1` + date de naissance (723 patients concernés, 361 groupes, plus grand groupe
   de taille 3, sur 25 842 patients courants) ; type et numéro de pièce d'identité (1 534
   patients concernés, 767 groupes, plus grand groupe de taille 2). Écarté : le numéro de
   téléphone (`telephone_1`) — mesuré dégénéré, 24 594 patients sur 25 842 (95 %) appartenant à
   un groupe de deux ou plus, jusqu'à 10 patients partageant une même valeur, cohérent avec le
   mécanisme de foyer partagé du générateur (`generator/patients.py::_tirer_foyer`) : la colonne
   ne distingue plus rien à cette échelle, elle ne figure dans aucun agrégat. `agg_doublons_
   identite` énonce explicitement, dans sa description de modèle, qu'il COMPTE et EXPOSE des
   collisions exactes uniquement — un rapprochement probabiliste d'identités est un traitement
   distinct, hors du périmètre de cette couche.
5. **Le huitième agrégat, `agg_provenance_champs`, reste hors du projet dbt.** Il lit
   directement `pg_catalog` (commentaires de colonnes de la couche source) plutôt qu'une table
   ou une vue de données — le réécrire en modèle dbt (`ref()`/`source()`) n'apporterait rien à
   une vue déjà recalculée à chaque lecture sur le catalogue système, et l'exposerait sans motif
   au mécanisme de remplacement de vue concurrent propre à dbt
   (`docs/decisions/0027-materialisation-dbt-un-seul-fil.md`) pour un objet qui n'a jamais
   dépendu de ce mécanisme.

## Justification des points non triviaux

### Pourquoi la règle du dernier instantané (point 3) plutôt qu'une fenêtre sur la date d'extraction la plus récente globale

Une date d'extraction maximale UNIQUE, commune à toutes les créances, exclurait les créances dont
le dernier instantané est antérieur à cette date (une créance soldée tôt, sans nouvel instantané
depuis) — `row_number()` partitionné par créance retient le dernier instantané DE CHAQUE créance,
quelle que soit sa date, jamais une date arbitraire commune à toutes.

## Conséquences

Sept agrégats dbt, testés (`dbt/tests/agg_*_coherence.sql`, une propriété par égalité ou
inégalité bornante de deux quantités calculées indépendamment) et un agrégat de provenance
maintenu hors du projet, sans que cette différence de statut nuise à sa fraîcheur (une vue sur
catalogue reste toujours à jour, par construction).

## Ce qui aurait invalidé cette décision

Une évolution qui matérialiserait `agg_provenance_champs` en table alimentée par script (plutôt
qu'en vue sur catalogue) romprait la garantie de fraîcheur qui justifie aujourd'hui son maintien
hors dbt — à réévaluer alors son rattachement au projet. Une mesure future du coût de conversion
de `agg_qualite_donnees` dépassant significativement le seuil de 10 secondes (croissance du
volume des vues intermediate) invaliderait le grain colonne retenu au point 2.

## Sources

`dbt/models/marts/agg_delai_rendez_vous.sql`, `agg_absenteisme.sql`,
`agg_activite_journaliere.sql`, `agg_urgences_journalier.sql`, `agg_recouvrement.sql`,
`agg_qualite_donnees.sql`, `agg_doublons_identite.sql` ; `ingestion/ddl/
20_marts_agg_provenance.sql` ; `generator/patients.py::_tirer_foyer` ; mesures antérieures de
coût de conversion et de dégénérescence des critères de collision ; `docs/decisions/
0027-materialisation-dbt-un-seul-fil.md`.
