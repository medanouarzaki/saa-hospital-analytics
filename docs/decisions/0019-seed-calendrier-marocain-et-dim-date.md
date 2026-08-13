# ADR 0019 — le seed du calendrier marocain est dérivé mécaniquement, testé en équivalence et en synchronisation, `dim_date` couvre à partir d'août 2023

**Statut.** Accepté. **Amendée** : la borne `dim_date_debut` retenue au point 4 (`2023-08-01`,
calibrée sur la base complète) s'est révélée trop étroite pour la fenêtre de génération réduite
utilisée en intégration continue — élargie à `2023-01-01`, justification mesurée dans
`docs/decisions/0022-...md`.

---

## Contexte

`generator/config/calendrier.yml` est la vérité du calendrier marocain depuis le générateur
lui-même (`generator/calendrier.py::jours_feries`/`est_ramadan`) : une liste plate de paramètres
nommés, fériés fixes (préfixe `ferie_fixe_`, un couple mois-jour récurrent), observances mobiles
(`ramadan_debut`/`ramadan_fin`/`aid_al_fitr`/`aid_al_adha`, suffixées par année), et deux
paramètres transverses (`aid_al_wahda_premiere_annee`, `duree_aid_jours`). Les observances mobiles
ne couvrent que 2024 à 2026 : aucune entrée `_2023` n'existe dans le fichier. `dim_date` doit
couvrir `2023-08-01 → 2026-12-31` (variables `dim_date_debut`/`dim_date_fin` de `dbt/dbt_project.
yml`) pour englober la totalité des 34 colonnes d'événement mesurées dans les vues `intermediate`
(38 colonnes `date`/`horodatage` du registre, moins les quatre attributs d'état civil de
`patients` — `date_naissance`, `date_photo`, `date_attribution`, `date_inscription` — dont le
minimum mesuré est antérieur à `2023-08-01`).

`tests/test_provenance.py::test_couverture_bidirectionnelle` filtre son catalogue sur
`c.table_schema in ('source', 'intermediate', 'marts')` : un schéma absent de cette liste échappe
au filtre par construction, avant même la distinction `BASE TABLE`/vue déjà exploitée pour
`intermediate`/`marts` (`docs/decisions/0018-...md`).

## Décision

1. **Un seed dbt (`referentiels.calendrier_marocain`), dérivé mécaniquement, jamais édité à la
   main.** `docs/calendrier/generer_seed_calendrier.py::generer()` relit `generator/config/
   calendrier.yml` (jamais modifié par les lots dbt) et les variables `dim_date_debut`/
   `dim_date_fin`, reproduit exactement la logique de `generator/calendrier.py` (même filtre
   `premiere_annee`, même durée d'Aïd, même plage de Ramadan), et écrit `dbt/seeds/calendrier_
   marocain.csv` (grain `jour, categorie, libelle` ; catégories mesurées : `ferie_fixe`,
   `ferie_mobile`, `ramadan`). Placé dans un nouveau dossier `docs/calendrier/`, miroir de
   `docs/champs/` pour ce domaine — `generator/` étant fermé à l'écriture pour les lots dbt, le
   script ne pouvait pas vivre à côté de sa source.
2. **Schéma `referentiels`, distinct de `source`/`intermediate`/`marts`.** Confirmé par lecture du
   filtre de `test_couverture_bidirectionnelle` avant écriture, puis par la preuve en conditions
   réelles (le test reste vert une fois la table créée en base).
3. **Deux tests indépendants pour la même dérivation, chacun couvrant une propriété que l'autre ne
   couvre pas.** Un test pytest (`tests/test_calendrier.py::test_seed_calendrier_synchronise_avec_
   la_source`) régénère le CSV et le compare octet à octet au fichier committé, sur le patron de
   `test_provenance.py::test_artefacts_synchrones` — il détecte une divergence entre le fichier
   committé et sa régénération, y compris si les DEUX implémentations (script et générateur)
   dérivaient d'un même défaut. Un second test pytest (`test_equivalence_derivation_feries_avec_
   le_generateur`) compare, année par année, l'ensemble des fériés produits par le script à
   `generator/calendrier.py::jours_feries(annee)` — deux implémentations indépendantes du même
   calcul, sans lien de dérivation entre elles ; il détecte une divergence que la seule
   comparaison octet à octet ne peut pas voir puisqu'elle compare la sortie du script à
   elle-même. Signature réelle de `jours_feries` vérifiée avant l'écriture du test
   (`jours_feries(annee: int) -> set[date]`, un seul paramètre — le module recharge sa
   configuration en interne).
4. **`dim_date` (vue, `marts`) sans aucun littéral de date**, `generate_series` sur les deux
   variables du projet, attributs calculables (`annee`, `trimestre`, `mois`, `jour`,
   `jour_semaine_iso`, `est_weekend`) et jointure sur le seed pré-agrégé (`est_ferie`/
   `libelle_ferie` sur `ferie_fixe`+`ferie_mobile`, `est_ramadan` sur `ramadan` — jamais la même
   ligne du seed, le Ramadan n'étant pas un jour férié dans la source).
5. **Quatre tests dbt sur `dim_date`, chacun mutation-testé** : `unique` (natif) sur `date_jour` ;
   trois tests singuliers sous `dbt/tests/` (continuité par arithmétique de dates, synchronisation
   bidirectionnelle des fériés contre le seed restreint à l'étendue de `dim_date`, couverture des
   34 colonnes d'événement par une liste statique générée par script puis collée). Le contrôle
   `premiere_annee` n'est PAS un cinquième test dbt : la dérivation applique déjà la règle, un
   test sur `dim_date` serait vrai par construction (aucune mutation possible qui ne mute pas
   d'abord le script lui-même) — porté par le test d'équivalence pytest à la place (point 3).

## Justification des points non triviaux

### Pourquoi la synchronisation des fériés compare contre le seed restreint, pas contre le seed entier

Mesuré avant correction : le test de synchronisation, écrit sans restriction, rougissait dès la
première exécution (5 anomalies, pas une mutation). Cause : le seed explose les fériés fixes sur
des années CALENDAIRES complètes (2023 à 2026, `_etendue_annees()` retourne des années entières),
alors que `dim_date` ne commence que le 1ᵉʳ août 2023 — cinq fériés fixes de janvier/mai/juillet
2023 existent légitimement dans le seed sans avoir de contrepartie dans `dim_date`. Ce n'est pas
un défaut du seed (il a raison de porter l'année 2023 complète, une future dimension pourrait
vouloir la même donnée sur une étendue plus large) ni de `dim_date` (son étendue est fixée par
mesure des événements, `docs/decisions` du lot de mesure). Le test compare donc le seed restreint
aux mêmes variables que `dim_date` (`jour >= var("dim_date_debut") and jour <= var("dim_date_
fin")`), pas le seed modifié.

### Pourquoi la couverture des événements est une liste statique, pas une boucle Jinja sur le registre

Le SQL du test dbt ne lit pas `docs/champs/registre_champs.yml` à la compilation : générer la
liste par script puis la coller garde le test lisible et diffable comme n'importe quel autre
fichier SQL du projet, et évite une dépendance Jinja-vers-YAML supplémentaire pour un besoin qui
ne change qu'au rythme des lots qui ajoutent des tables (rare). Le script n'est que l'outil de
génération une fois, pas une dépendance du test à l'exécution.

## Conséquences

`referentiels.calendrier_marocain` (142 lignes) et `marts.dim_date` sont les deux premiers objets
de la couche dimensionnelle du projet. 87 tests dbt verts (84 de la couche `intermediate` + 3
nouveaux singuliers), 10 tests pytest verts dans `tests/test_calendrier.py` (8 préexistants + le
test de synchronisation + le test d'équivalence). Le seed est la seule source du calendrier pour
tout modèle `marts` futur qui en aurait besoin (agrégats par jour férié, saisonnalité).

## Ce qui aurait invalidé cette décision

Un changement de `generator/config/calendrier.yml` qui ajouterait une nouvelle catégorie
d'observance (au-delà de `ferie_fixe`/`ferie_mobile`/`ramadan`) exigerait une mise à jour
symétrique du script de dérivation ET des tests de `dim_date` qui énumèrent ces catégories en dur
(`categorie in ('ferie_fixe', 'ferie_mobile')`) — les deux tests de synchronisation/équivalence le
détecteraient (la nouvelle catégorie apparaîtrait comme un écart), mais ne le corrigeraient pas
automatiquement.

## Sources

`docs/calendrier/generer_seed_calendrier.py`, `dbt/seeds/calendrier_marocain.csv`, `dbt/dbt_
project.yml`, `dbt/models/marts/dim_date.sql`/`.yml`, `dbt/tests/dim_date_continuite_sans_trou.
sql`, `dbt/tests/dim_date_synchronisation_feries.sql`, `dbt/tests/dim_date_couverture_evenements.
sql` ; `generator/config/calendrier.yml`, `generator/calendrier.py` ; `tests/test_calendrier.py`
(`test_seed_calendrier_synchronise_avec_la_source`, `test_equivalence_derivation_feries_avec_le_
generateur`) ; `tests/test_provenance.py::test_couverture_bidirectionnelle`,
`::test_artefacts_synchrones` ; `docs/decisions/0018-architecture-dbt-vues-et-nommage.md`.
