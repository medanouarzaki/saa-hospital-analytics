# ADR 0016 — Les fiches patient réextraites portent un changement métier tiré, enregistré en vérité terrain

**Statut.** Accepté.

---

## Contexte

`generator/patients.py::generer_lignes` produit, pour une part des fiches (`taux_modification_fiche`,
0,15), une seconde ligne à une `date_extraction` postérieure — une réextraction. Avant cette
décision, cette seconde ligne recopiait intégralement les 43 colonnes métier de la ligne de
création : seules trois colonnes techniques (`date_modification`, `modifie_par`,
`date_extraction`) différaient jamais entre les deux versions d'un même `n_ipp`. Le
versionnage envisagé pour la couche dimensionnelle (`dim_patient` en SCD 2) n'aurait alors
aucun changement d'attribut métier à historiser, et rien à confronter à une vérité terrain.

## Décision

Quand une ligne de réextraction est émise, un type de changement métier est tiré parmi quatre
(`repartition_type_modification`, `generator/config/demographie.yml`) : `demenagement`
(adresse), `telephone` (téléphone principal), `etat_civil`, `couverture` (compagnie
d'assurance, et le type de patient en conséquence si nécessaire). La colonne concernée reçoit
une valeur nouvelle, tirée par le mécanisme de génération déjà utilisé à la création
(mêmes pools/distributions), retirée jusqu'à différer de l'ancienne (bornée, 20 essais).
Chaque changement effectivement constaté est enregistré dans une nouvelle catégorie
`fiches_modifiees` de `verite_terrain.yml` (`n_ipp`, `date_extraction`, `type_modification`,
et un mapping colonne → {avant, apres}).

## Justification des points non triviaux

### Pourquoi seules `adresse`, `telephone_1`, `etat_civil`, `compagnie_assurance` (et
`type_patient` en conséquence)

Mesure préalable (`generator/patients.py::_tirer_foyer`, `_generer_ligne_patient`) : `adresse`
et `telephone_1` viennent d'un même tirage de foyer, mais `quartier` est une fonction
déterministe du rang du patient (`QUARTIER {rang % 20}`, aucun tirage à rejouer) et
`code_postal` est une dérivation pure de `ville` (`codes_postaux_par_ville`), elle-même non
liée à `adresse`. Aucun mécanisme de génération existant ne permet de tirer une nouvelle
valeur cohérente pour `quartier` ou `code_postal` indépendamment de `ville`, qui n'est pas
touchée par `demenagement` — inclure ces colonnes aurait exigé d'inventer un format,
proscrit. `police` et `n_assure` sont des identifiants tirés indépendamment de
`compagnie_assurance` (jamais dérivés d'elle dans le code), donc exclus de `couverture`.
`type_patient`, en revanche, est explicitement lié : `generator/config/coherence.yml` déclare
une contrainte d'appartenance (`compagnie_assurance = SANS ⇒ type_patient ≠ AS`), vérifiée par
`tests/test_patients.py::test_ordres_vraisemblance`. Un changement de `compagnie_assurance`
vers `SANS` alors que `type_patient` vaut `AS` retire donc aussi `type_patient`, par le même
tirage que celui utilisé à la création (`distribution_type_patient["non_assure"]`, qui exclut
`AS` par construction).

### Pourquoi la vérité terrain est recalculée en relisant les fichiers écrits, pas transmise en métadonnée

`generator/defauts.py::injecter_defauts` s'exécute après la génération de toutes les tables,
mute `contexte.lignes` en place, et peut porter sur les mêmes colonnes qu'un changement
métier (mesuré : `_injecter_defauts_surface` porte sur `adresse`, `_injecter_champs_manquants`
peut porter sur `quartier`). Ces deux mécanismes appliquent leur valeur finale identiquement à
toutes les versions d'un même `n_ipp` (jamais seulement à l'une) : ils ne peuvent qu'effacer
une différence déjà posée par le changement métier, jamais en créer une nouvelle sur une
colonne qu'aucun des deux mécanismes ne modifie. Une collision mesurée sur une génération
d'essai (`IPP-000273`, catégorie `casse_accents`) a confirmé ce risque : l'adresse
« démenagée » a été réécrite identiquement sur les deux versions par le défaut de surface,
effaçant le changement. Le seul point de passage vers `verite_terrain.ecrire()` que cette décision est
autorisé à modifier est `generator/verite_terrain.py` lui-même — `generator/execution.py`, qui
orchestre l'appel et ne transmet aujourd'hui que les paires de doublons et les altérations de
`defauts.py`, est explicitement hors périmètre. `fiches_modifiees` est donc recalculée après
coup, en relisant les partitions CSV déjà écrites par `execution` (`execution.partitions`) :
la vérité rapportée est toujours celle qui a réellement atteint le disque, y compris dans le
cas où un défaut de surface masque un changement métier — ce cas se traduit alors par
l'absence de la fiche en question dans `fiches_modifiees`, correctement, plutôt que par une
entrée devenue fausse.

### Pourquoi `etat_civil` peut ne rien changer sur certaines fiches

`etat_civil` vaut `"C"` codé en dur (pas tiré d'une distribution) pour un patient mineur au
moment de la création. Le domaine n'a donc qu'une seule valeur possible pour ces fiches ; le
tirage de retirage y échoue par construction et aucun changement n'est appliqué. Mesuré sur
une génération d'essai : 5 des 6 fiches multi-versions sans entrée `fiches_modifiees`
correspondaient à ce cas (la sixième à la collision de défaut de surface ci-dessus).

### Pourquoi les tirages du changement métier utilisent un générateur dérivé (`spawn`), pas le générateur partagé de la table

`generator/patients.py::generer_lignes` partage un seul générateur aléatoire séquentiel
(`generateur`) entre tous les patients de la boucle : chaque tirage supplémentaire pour un
patient décale la position de flux consommée par tous les patients suivants. Mesuré : router
les tirages du changement métier à travers ce générateur partagé faisait dériver, à graine
fixe, une statistique sans rapport et sans dépendance directe aux colonnes touchées
(`tests/test_coherence_inter_tables.py::test_regle_13_indicateurs_sejour_recalcules_depuis_les_donnees`,
IROT mesuré à 5,7685 contre 5,6 ± 0,168 attendu — l'écart franchissait la tolérance de 3 %
de moins de 0,01 point). Lecture de `generator/mouvements.py::_unites_eligibles` : elle ne
lit que `sexe` et `date_naissance` du patient, deux colonnes que ce changement ne touche pas — la
dérive ne venait donc pas d'une dépendance de donnée, mais du décalage de position dans le
flux aléatoire partagé, qui change les tirages (âge, sexe, noms, ...) de tous les patients
traités après le premier patient réextrait. `np.random.Generator.spawn(n)` dérive des
générateurs enfants indépendants sans consommer le flux du parent (mécanisme de
`SeedSequence`, déjà utilisé par `generator/execution.py::_generateur_pour` pour dériver un
générateur par table) : les tirages du changement métier utilisent désormais
`generateur.spawn(1)[0]`, un générateur propre à la fiche en cours, laissant le flux principal
de la table `patients` strictement identique à ce qu'il aurait été sans ce changement. Vérifié : le
test ci-dessus, et l'ensemble de la suite (245 tests), passent avec ce générateur dérivé.

## Conséquences

`dim_patient` (SCD 2, bloc ultérieur) dispose désormais de changements d'attribut métier réels
à historiser, et d'une vérité terrain contre laquelle confronter le résultat — le même rôle que
`verite_terrain.yml` joue déjà pour la quarantaine et le rapprochement probabiliste.
`generator/__main__.py` (nouveau point d'entrée CLI) permet de générer une période réduite pour
exercer ce mécanisme sans regénérer `scenario_30` en entier.

## Ce qui aurait invalidé cette décision

Une contrainte de cohérence supplémentaire (dans `generator/config/coherence.yml`) reliant
`adresse`, `telephone_1`, `etat_civil` ou `compagnie_assurance` à une autre colonne non prise
en compte ici aurait exigé d'étendre `COLONNES_PAR_TYPE_MODIFICATION`
(`generator/patients.py`) en conséquence, sous peine de produire une fiche métier incohérente
en sortie.

## Sources

`generator/patients.py` (`generer_lignes`, `COLONNES_PAR_TYPE_MODIFICATION`,
`_appliquer_changement_metier` et les quatre applicateurs) ; `generator/verite_terrain.py`
(`_calculer_fiches_modifiees`) ; `generator/config/demographie.yml`
(`repartition_type_modification`) ; `generator/config/coherence.yml` (contrainte
`compagnie_assurance`/`type_patient`) ; `generator/mouvements.py` (`_unites_eligibles`,
colonnes lues) ; `generator/execution.py` (`_generateur_pour`, précédent d'usage de
`spawn`) ; `tests/test_patients.py::test_ordres_vraisemblance`,
`tests/test_defauts.py::test_fiches_modifiees_exactement_enregistrees`,
`tests/test_defauts.py::test_fiches_modifiees_colonnes_du_type`,
`tests/test_patients.py::test_repartition_type_modification_complete`,
`tests/test_coherence_inter_tables.py::test_regle_13_indicateurs_sejour_recalcules_depuis_les_donnees`,
`tests/test_generator_cli.py`.
