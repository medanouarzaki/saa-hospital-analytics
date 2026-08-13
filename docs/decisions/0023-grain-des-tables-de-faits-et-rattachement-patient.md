# ADR 0023 — Grain des six tables de faits et rattachement à la version du patient

**Statut.** Accepté.

---

## Contexte

Six événements distincts existent dans la couche source (rendez-vous, passage de consultation,
passage d'hospitalisation, passage aux urgences, séjour, facturation, encaissement — sept en
réalité, réparties en six tables de faits, la facturation et l'encaissement restant deux tables
distinctes malgré leur proximité) sans qu'aucun grain commun n'ait été fixé jusqu'ici. Chacun
porte un `n_ipp`, rattaché à `dim_patient` (SCD 2, `docs/decisions/0021-dim-patient-scd2.md`) —
un même patient réel pouvant avoir plusieurs versions de fiche, un fait ne peut pointer sur une
version qu'en résolvant celle en vigueur au jour de l'événement, jamais sur `n_ipp` seul.

## Décision

1. **Grain, une phrase par fait.** `fct_rendez_vous` : une ligne par rendez-vous (`n_rdv`).
   `fct_passage` : une ligne par passage de consultation ou d'hospitalisation ou d'urgence
   (`n_passage`), les trois types réunis. `fct_passage_urgence` : une ligne par passage aux
   urgences (`n_passage`), satellite de `fct_passage` portant les colonnes propres aux urgences
   (niveau de tri, orientation de sortie). `fct_sejour` : une ligne par séjour (`n_sejour`),
   agrégée depuis les 1 à 3 lignes de mouvement qui le composent. `fct_facturation` : une ligne
   par facture (`n_facture`). `fct_encaissement` : une ligne par ligne d'encaissement (grain le
   plus fin des six, plusieurs encaissements pouvant régler une même facture).
2. **`fct_passage` couvre les trois types de passage, pas seulement la consultation.** Motif
   mesuré : `fct_facturation.n_episode` pointe vers `n_passage` quel que soit `type_episode`
   (`CE`, `HOS`, `UR`) — 8 221/8 221 factures `CE`, 2 561/2 561 `HOS`, 10 284/10 284 `UR`
   résolvent toutes vers `fct_passage`, sans exception ni table intermédiaire différente selon
   le type. Restreindre `fct_passage` à la seule consultation aurait exigé trois jointures
   distinctes côté facturation selon le type d'épisode, pour une distinction que la source ne
   porte pas au niveau de la clé.
3. **`fct_passage` et `fct_passage_urgence` partagent le même espace de clés `n_passage`,
   exposé par une relation, jamais masqué par un préfixe.** Les 27 360 `n_passage` de
   `fct_passage_urgence` sont un sous-ensemble EXACT des `n_passage` de type `U` de
   `fct_passage` (27 360 lignes `U` dans `fct_passage`, correspondance à 100 %) : préfixer les
   identifiants de `fct_passage_urgence` (par exemple `URG-...`) masquerait cette identité et
   empêcherait un test `relationships` natif de la vérifier — la clé partagée rend la relation
   entre les deux tables déclarative, pas recalculée à chaque requête.
4. **Résolution de la version du patient au moment de la construction du fait.** Chaque fait
   porte `patient_valide_de`, résolu par jointure sur `dim_patient` avec la convention déjà
   fixée par `docs/decisions/0021-...md` : borne basse incluse, borne haute exclue
   (`jour >= valide_de and (jour < valide_jusqu_a or valide_jusqu_a is null)`) — la même
   sémantique que `generator/patients.py::version_en_vigueur`, jamais réinventée par fait.
5. **Comptabilité des versions non résolues : deux causes admissibles, tout le reste est un
   échec.** Un fait dont `patient_valide_de` reste `NULL` après la jointure n'est excusé que
   si (i) son `n_ipp` est absent de `dim_patient` dans son ensemble, ou (ii) le jour de
   l'événement précède la première version connue de ce `n_ipp`. Les deux causes sont
   prouvables depuis la seule dimension, sans artefact externe. Mesuré sur les six faits :
   `fct_rendez_vous` 41 non résolues (37 + 4), `fct_passage` 114 (104 + 10),
   `fct_passage_urgence` 84 (77 + 7), `fct_sejour` 3 (3 + 0), `fct_facturation` 55 (50 + 5),
   `fct_encaissement` 49 (42 + 7) — dans chaque cas l'égalité `non_résolues = cause_1 + cause_2`
   tient exactement, aucun troisième cas mesuré.

## Justification des points non triviaux

### Pourquoi ne pas séparer `fct_passage` par type au lieu d'un discriminant `type_passage`

Une table par type (consultation, hospitalisation, urgence) aurait dupliqué les colonnes communes
(`n_ipp`, `date_entree`, `code_service`) trois fois et exigé que tout lecteur en amont
(`fct_facturation`, les agrégats d'activité) sache lequel des trois joindre selon le type
d'épisode — un branchement que la source elle-même ne demande pas, `n_episode` étant un seul
espace de clés indépendamment du type.

### Pourquoi une relation plutôt qu'un préfixe pour `fct_passage_urgence`

Un préfixe est un contrôle textuel, faux jusqu'à preuve du contraire ; une relation déclarée (`relationships` dbt) est vérifiée par la base à chaque exécution, sur la
totalité des lignes, sans hypothèse sur le format de l'identifiant.

## Conséquences

Les six faits partagent une même discipline de rattachement patient, testée par le test
générique `version_patient_comptable` (un test par fait, six au total). Un lecteur de
`fct_facturation` n'a besoin que d'un `n_episode` et d'un `type_episode` pour retrouver le
passage correspondant dans une table unique, sans branchement.

## Ce qui aurait invalidé cette décision

Une évolution de la source introduisant un type d'épisode dont `n_episode` ne pointerait plus
vers l'espace de clés de `fct_passage` (par exemple un type d'épisode entièrement nouveau, hors
consultation/hospitalisation/urgence) invaliderait le point 2 — à re-mesurer avant d'étendre
`type_episode`. Une future colonne mutable de `dim_patient` non couverte par
`generator/patients.py::COLONNES_PAR_TYPE_MODIFICATION` invaliderait la comptabilité du point 5,
comme déjà noté par `docs/decisions/0021-...md`.

## Sources

`dbt/models/marts/fct_rendez_vous.sql`, `fct_passage.sql`, `fct_passage_urgence.sql`,
`fct_sejour.sql`, `fct_facturation.sql`, `fct_encaissement.sql` ; `dbt/tests/generic/
version_patient_comptable.sql` ; `docs/decisions/0021-dim-patient-scd2.md` ;
`generator/patients.py::version_en_vigueur`.
