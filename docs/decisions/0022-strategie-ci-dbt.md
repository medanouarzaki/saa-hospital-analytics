# ADR 0022 — la CI exécute dbt sur un sous-ensemble de trois mois, avec confrontation comptable des retraits légitimes du chargement

**Statut.** Accepté.

---

## Contexte

104 tests dbt sur la base complète ne prouvaient rien en intégration continue : aucun job de
`.github/workflows/ci.yml` n'exécutait ni le générateur ni dbt avant ce travail. Rejouer le
scénario complet (30 mois, coût de génération/chargement mesuré à plusieurs minutes) à chaque
`push` était jugé disproportionné ; un sous-ensemble généré à la volée, borné dans le temps,
suffit si — et seulement si — chaque test dbt reste une propriété sans littéral de volumétrie
(vrai sur 3 mois comme sur 30) et si la matière SCD 2 (paires de versions patient) survit à la
réduction de fenêtre.

## Décision

1. **Le job `dbt`** (`.github/workflows/ci.yml`) génère un sous-ensemble de trois mois
   (`python -m generator ... --date-fin 2024-03-31`, graine par défaut — c'est-à-dire la graine
   fixe `42` de `generator/config/execution.yml`, jamais un tirage aléatoire par exécution,
   mesuré déterministe sur plusieurs régénérations indépendantes), le charge (DDL +
   `ingestion.chargeur`), exécute `dbt seed`/`dbt run`/`dbt test`, puis confronte `marts.dim_
   patient` à la vérité terrain du sous-ensemble (`pytest tests/test_dim_patient.py`). Coûts
   mesurés localement (estimation basse, pas la mesure CI elle-même) : génération ≈ 11-11,6 s,
   chargement ≈ 40 s, dbt (seed+run+test) ≈ 6-8 s, confrontation ≈ 2-16 s selon l'état du cache
   de connexion — somme de l'ordre de la minute.
2. **Le garde-fou de collecte des tests** (`tests/test_collecte_ci.py`) est généralisé : il
   balaye tous les jobs du workflow pour leurs commandes `pytest`, sans nom de job en dur — le
   job `dbt` (et tout job futur) est reconnu automatiquement. Un faux positif (un chemin `tests/
   *.py` capturé dans un argument `--ignore=`, pas une cible réelle) et une vraie duplication
   pré-existante (`tests/test_collecte_ci.py` exécuté deux fois, invisible à l'ancien garde-fou
   restreint à un seul nom de job) ont été détectés et corrigés au passage.
3. **`dim_date_debut` élargie à `2023-01-01`** (`dbt/dbt_project.yml`, amendement de `docs/
   decisions/0019-...md`). `generator/config/rendez_vous.yml::delai_rdv_par_specialite` /
   `ecart_type_log_delai_par_specialite` gouvernent, via une loi LOG-NORMALE
   (`generator/rendez_vous.py::_delai_lognormal`), le délai entre la prise d'un rendez-vous et
   sa date — une queue à droite non bornée par aucun plafond explicite relativement à la fenêtre
   demandée (le seul `min(delai, marge_disponible)` du code borne par la date de création du
   PATIENT, pas par `date_debut` de la génération ; un patient préexistant peut porter un délai
   arbitrairement long). Deux minima mesurés : `2023-08-08` (base complète), `2023-05-13`
   (sous-ensemble CI trois mois, reproductible sur trois régénérations indépendantes).
   `2023-01-01` couvre les deux avec 132 jours de marge sur le plus contraignant — **limite
   explicite** : cette borne couvre les deux générations CANONIQUES de ce projet, pas tous les
   tirages log-normaux concevables ; un futur changement de fenêtre CI ou de graine par défaut
   exige une re-mesure, pas une confiance aveugle en la marge actuelle.
4. **`tests/test_dim_patient.py` devient comptable des retraits légitimes du chargement.**
   Chaque entrée de `fiches_modifiees` est classée en exactement une catégorie : `conforme` (deux
   versions présentes, valeurs et bornes exactes), `exclue_quarantaine` (`n_ipp` présent dans
   `quarantaine.patients`), `exclue_partition` (la partition de la version manquante est
   ENTIÈREMENT absente de `source.patients` — zéro ligne pour cette `date_extraction` — alors que
   le CSV brut du scénario pour cette même partition n'est pas vide), ou `non_conforme` (aucune
   des trois preuves, un échec réel). L'équation `total = conformes + exclues_quarantaine +
   exclues_partition` est une assertion du test ; elle ne peut tenir que si `non_conformes` est
   vide. Motivée par `ingestion/chargeur.py::charger_table_partition` : une partition dont le
   taux de rejet dépasse `seuil_quarantaine` (5 %, `ingestion/controles.yml`, gelé) ET dont le
   nombre absolu de rejets atteint `plancher_rejets_bloquants` (2) est bloquée EN BLOC — ni
   `source` ni `quarantaine` n'en gardent trace. Une fenêtre CI réduite (trois mois) produit des
   partitions journalières plus petites (≈ 30 lignes contre ≈ 90 sur le scénario complet) ; le
   même nombre absolu de défauts injectés (indépendant de la taille de la fenêtre) y représente
   une proportion plus grande, franchissant plus facilement le seuil — mesuré sur `IPP-000651`
   (changement de `telephone_1` daté `02/28/2024`), seule occurrence sur 178 entrées du
   sous-ensemble CI, zéro occurrence sur 3 070 entrées de la base complète.

## Justification des points non triviaux

### Pourquoi ne pas modifier `ingestion/controles.yml`

Le seuil de blocage (`seuil_quarantaine`, `plancher_rejets_bloquants`) est une décision de
qualité de données valable sur TOUT scénario, complet ou réduit — un taux de rejet élevé signale
un problème d'extraction, indépendamment de la taille de l'échantillon. Rendre le seuil sensible
à la taille de la fenêtre de génération ferait dépendre une règle métier d'un détail
d'infrastructure CI ; le test de confrontation s'adapte à la réalité du chargeur, pas l'inverse.

### Pourquoi la preuve d'exclusion exige les DEUX conditions (partition absente ET CSV brut non vide)

Une partition absente de `source.patients` sans vérifier le CSV brut ne prouverait rien : un jour
sans aucune activité (par construction, hors période, férié...) produirait aussi zéro ligne, sans
qu'aucun blocage n'ait eu lieu. Exiger que le CSV généré porte au moins une ligne pour cette même
partition élimine cette confusion — seul un jour RÉELLEMENT généré avec des lignes, puis disparu
au chargement, prouve un blocage.

## Conséquences

Le job `dbt` est complet, vérifié par répétition locale intégrale (deux fois : une fois révélant
le bug de racine du chargeur et la borne de `dim_date`, une fois confirmant la levée des deux et
révélant la comptabilité des retraits, une troisième fois confirmant tout vert). 104 tests dbt et
2 tests de confrontation verts sur les deux générations canoniques (base complète, sous-ensemble
CI). Le premier run CI réel de la branche, à la publication, reste le juge final — la
répétition locale n'a jamais prétendu reproduire l'environnement du runner.

## Ce qui aurait invalidé cette décision

Un changement de fenêtre CI (plus courte que trois mois) ou de graine par défaut referait
diverger les deux minima mesurés au point 3 et le nombre de partitions bloquées au point 4 — à
re-mesurer avant tout changement de ce type. Une évolution de `seuil_quarantaine`/`plancher_
rejets_bloquants` changerait la fréquence des blocages en bloc, sans invalider le mécanisme de
preuve du point 4 (qui reste correct quel que soit le seuil).

## Sources

`.github/workflows/ci.yml` (job `dbt`) ; `tests/test_collecte_ci.py` ; `tests/test_dim_patient.py`
; `dbt/dbt_project.yml` ; `generator/config/rendez_vous.yml`, `generator/rendez_vous.py` ;
`ingestion/chargeur.py::charger_table_partition`, `ingestion/controles.yml` ; `docs/decisions/
0019-seed-calendrier-marocain-et-dim-date.md`, `0021-dim-patient-scd2.md`.
