# ADR 0021 — dim_patient en SCD type 2, bornes semi-ouvertes alignées sur la sémantique du générateur

**Statut.** Accepté.

---

## Contexte

`int_patients` porte 25 842 `n_ipp` distincts, 22 577 à une version et 3 265 à deux (matière déjà
mesurée et confrontée aux lots précédents). Le générateur porte sa propre sémantique de sélection
de version : `generator/patients.py::version_en_vigueur(versions, jour)` retient la dernière
version dont `date_extraction <= jour` — c'est la version « en vigueur » à une date donnée, déjà
utilisée par `generator/prises_en_charge.py` et `generator/defauts.py` pour ancrer leurs décisions
sur la couverture réellement en vigueur au moment de l'événement (`docs/decisions/0017-...md`).
Aucune dimension patient n'existait auparavant.

## Décision

1. **Bornes semi-ouvertes, borne haute exclusive.** `valide_de` = `date_extraction` de la version ;
   `valide_jusqu_a` = `date_extraction` de la version suivante du même `n_ipp` (`lead(...) over
   (partition by n_ipp order by valide_de)`), `NULL` pour la version la plus récente ;
   `est_courante` = absence de version suivante. C'est exactement la sémantique de `version_en_
   vigueur` : un lecteur qui filtre `dim_patient` sur `valide_de <= jour and (valide_jusqu_a is
   null or jour < valide_jusqu_a)` retrouve la même version que le générateur aurait choisie pour
   ce jour — le générateur et l'entrepôt racontent la même histoire, sans code dupliqué entre les
   deux (l'entrepôt ne réimplémente pas la logique Python, il reproduit la même propriété en SQL
   sur les mêmes données).
2. **Trois invariants testés, chacun mutation-testé indépendamment**, en plus des deux tests
   génériques (conservation, unicité du grain `n_ipp || '|' || valide_de`) : non-chevauchement des
   intervalles (borne NULL traitée comme infini ouvert via une sentinelle `9999-12-31`),
   continuité (`valide_jusqu_a` d'une version non courante égale exactement `valide_de` de la
   suivante — aucun trou, aucun recouvrement), exactement une version courante par `n_ipp`. Les
   deux derniers ne sont pas redondants avec le premier : un trou n'est pas un recouvrement,
   démontré par mutation (le test de continuité rougit sur un trou d'un jour sans que le test de
   non-chevauchement ne bouge).
3. **Versionnage de fiches, pas de fusion de personnes.** `dim_patient` porte une ligne par
   version de fiche, exactement comme `int_patients` ; les doublons de personnes (fiches
   distinctes pour le même individu réel, hors du périmètre SCD 2) restent intacts et ne sont ni
   détectés ni fusionnés ici — c'est le travail d'une future couche de rapprochement, hors
   périmètre de cette dimension.
4. **Confrontation à la vérité terrain démontrée par script, pas committée en test pytest.** La confrontation exige une base chargée avec `dbt run` déjà exécuté, ce dont aucun
   groupe de la CI actuelle ne dispose (`.github/workflows/ci.yml`, lu, non modifié). Un test
   pytest committé maintenant échouerait en CI ou casserait le garde-fou de collecte
   (`test_collecte_ci.py`) faute d'emplacement pour l'héberger. Démontrée ici par script éphémère
   (`/tmp/lot_5l/`, deux comparateurs, chacun validé sur un cas positif connu avant tout verdict) ;
   son institutionnalisation en test committé attend l'intégration continue qui créera le job
   capable de l'héberger.

## Justification des points non triviaux

### Pourquoi la confrontation n'est pas un test dbt

Les deux comparateurs lisent `generator/output/scenario_30/verite_terrain.yml`, un
artefact hors du dépôt de données que dbt interroge (dbt ne lit que la base). Une confrontation
à la vérité terrain du générateur ne peut être qu'un script (Python, comme pour la confrontation
de `int_patients` aux lots de rechargement) ou un test pytest — jamais un test dbt.

## Conséquences

Dix-sept vues dans `marts` désormais (`dim_date`, quatre dimensions simples, `dim_patient`,
`agg_provenance_champs`), 104 tests dbt verts (99 précédents + 2 génériques + 3 singuliers). La
confrontation à la vérité terrain (égalité d'ensembles A == B à 3 064, exactitude des 3 064
versions, critère de bloc sur trois cas réels de déménagement) est démontrée mais pas encore
committée comme garde-fou automatique — dette explicite, portée par ce même ADR jusqu'à l'écriture
d'intégration CI.

## Ce qui aurait invalidé cette décision

Une future colonne mutable dont la valeur ne serait PAS capturée par `generator/patients.py::
COLONNES_PAR_TYPE_MODIFICATION` invaliderait l'hypothèse implicite que toute divergence entre deux
versions d'un même `n_ipp` provient d'un des cinq types de changement métier déjà connus — à
re-mesurer avant d'étendre le générateur avec un nouveau type de modification.

## Sources

`dbt/models/marts/dim_patient.sql`/`.yml` ; `dbt/tests/dim_patient_non_chevauchement.sql`,
`dim_patient_une_version_courante.sql`, `dim_patient_continuite.sql` ; `generator/patients.py::
version_en_vigueur`, `versions_par_ipp` ; `generator/output/scenario_30/verite_terrain.yml`
(`fiches_modifiees`) ; `docs/decisions/0016-changements-metier-sur-les-fiches-reextraites.md`,
`0017-version-en-vigueur-a-la-date-de-levenement.md`.
