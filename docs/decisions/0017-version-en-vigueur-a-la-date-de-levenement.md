# ADR 0017 — Les lecteurs aval d'une colonne patient modifiable utilisent la version en vigueur à la date de l'événement

**Statut.** Accepté.

---

## Contexte

Depuis que `generator/patients.py` porte de vrais changements métier sur les fiches
réextraites (`adresse`, `telephone_1`, `etat_civil`, `compagnie_assurance`, `type_patient`),
toute table calculée à partir des lignes patients doit choisir laquelle des deux versions lire
quand elles diffèrent. Une régénération complète de `scenario_30`, comparée à l'ancien
manifeste à graine égale (42), a fait apparaître un écart sur quatre tables sur onze
(`creances` -94, `encaissements` +119, `prises_en_charge` -25, `relances` -24 lignes), alors
que la reproductibilité octet à octet était attendue partout ailleurs. Cause mesurée par
citation de code : `generator/prises_en_charge.py` construisait
`patients_par_ipp = {p["n_ipp"]: p for p in lignes_patients}` — une compréhension de dict où la
dernière occurrence gagne — puis décidait de l'éligibilité à une prise en charge sur cette
version-là, y compris pour des factures antérieures au changement de couverture. C'est un
anachronisme : une information connue seulement plus tard (la réextraction) gouvernait la
décision prise pour un événement passé (la facture).

## Décision

Toute lecture d'une colonne patient modifiable, en aval de `patients.generer_lignes`, utilise
la **version en vigueur à la date de l'événement traité** : la dernière version dont
`date_extraction <= jour`, ou la première version si aucune ne satisfait cette condition
(l'événement précède toute extraction connue). Fonctions partagées, ajoutées à
`generator/patients.py` — l'emplacement naturel, module qui définit déjà `TABLE` et
`COLONNES_PAR_TYPE_MODIFICATION` :

```python
def versions_par_ipp(lignes_patients: list[dict]) -> dict[str, list[dict]]:
    par_ipp: dict[str, list[dict]] = {}
    for ligne in lignes_patients:
        par_ipp.setdefault(ligne["n_ipp"], []).append(ligne)
    return par_ipp


def version_en_vigueur(versions: list[dict], jour: date) -> dict:
    versions_triees = sorted(versions, key=lambda v: v["date_extraction"])
    candidates = [v for v in versions_triees if v["date_extraction"] <= jour]
    if candidates:
        return candidates[-1]
    return versions_triees[0]
```

Deux lecteurs corrigés, un par module, chacun avec `facture["date_facture"]` comme date
d'ancrage :

- `generator/prises_en_charge.py::generer_lignes` — l'éligibilité à une prise en charge
  (`compagnie_assurance != "SANS"`).
- `generator/defauts.py::_injecter_factures_sans_pec` — la part structurelle de factures
  couvertes (`n_couvertes`), qui doit s'accorder avec la même notion de « couvert » que
  `prises_en_charge.py` (le premier mécanisme resserre le taux de demande avant que le second
  n'injecte le complément nécessaire — les deux doivent compter les mêmes factures comme
  éligibles).

## Justification des points non triviaux

### Pourquoi `date_facture`, pas `date_verification`

`prises_en_charge.py` ne porte qu'une seule colonne de date propre, `date_verification`, qui
porte la date de *décision* — un événement postérieur et dérivé (`date_facture + délai tiré`).
Le docstring du module l'énonce déjà : « la date de facture sert de point de départ implicite
de la démarche ». La couverture pertinente est celle en vigueur quand la demande de prise en
charge a été *initiée*, pas quand elle a été *décidée*.

### Pourquoi l'inventaire ne s'est pas arrêté à `prises_en_charge.py`

L'énoncé du besoin ne citait que `generator/prises_en_charge.py` comme lecteur connu. Le
même motif de recherche (`lignes_patients`, paramètre reçu d'un générateur amont), validé sur
ce cas positif avant d'être appliqué ailleurs, a fait ressortir un second lecteur non anticipé
avec la même sémantique erronée : `generator/defauts.py::_injecter_factures_sans_pec`, qui
construisait son propre `compagnie_par_ipp` dernière-occurrence. Corrigé de la même façon,
avec la même date d'ancrage — les deux mécanismes doivent nécessairement s'accorder, l'un
resserrant le taux que l'autre complète.

### Pourquoi `generator/mouvements.py` n'a pas été touché

Reçoit aussi des lignes patients (`patients_par_ipp`, dernière occurrence), mais ne lit que
`sexe` et `date_naissance` — deux colonnes qui ne font pas partie de
`COLONNES_PAR_TYPE_MODIFICATION` et ne varient donc jamais entre les versions d'une même
fiche. La sémantique de version n'a aucun effet observable sur ces deux colonnes ; rien à
corriger.

### Pourquoi `generator/doublons.py` n'a pas été touché

Mesuré, pas supposé : `injecter_doublons` sélectionne explicitement
`ligne_source = next(ligne for ligne in lignes_source_meme_ipp if ligne["date_modification"]
is None)` — la version de *création*, jamais la dernière ni une version en vigueur à une
date. Un choix délibéré (un `next(... if ...)` explicite, pas une compréhension de dict qui
écraserait silencieusement) : un doublon reste une fiche plausible quelle que soit la version
qui le fonde, et la vérité terrain des paires ne porte que sur l'identité des deux fiches
dupliquées, jamais sur le contenu métier d'une version précise. Aucune notion de « version en
vigueur à une date d'événement » ne s'applique à la fabrication d'un doublon.

### Pourquoi `generator/facturation.py` n'était pas concerné

Mesuré : ne reçoit pas `lignes_patients` en paramètre, et `type_facture` est un tirage
indépendant (`repartition_types_facture`, configuration), sans lecture de `type_patient` ni
`compagnie_assurance`.

## Conséquences

Les tests existants qui utilisaient eux-mêmes la sémantique dernière-version pour vérifier une
propriété liée à la couverture (`tests/test_prises_en_charge.py::test_eligibilite`,
`tests/test_defauts.py::test_exactitude_verite_terrain_biunivoque`) ont dû être corrigés en
même temps que le code — ils faisaient la même hypothèse anachronique, révélée en échec réel
par la correction avant toute modification du test. Deux nouveaux tests couvrent directement
la propriété : `test_pec_utilise_version_en_vigueur_a_la_date_facture` (avec anti-vacuité
mesurée sur la génération partagée : 223 fiches traversent la frontière `SANS`, 133 factures
encadrent un tel changement) et `test_version_en_vigueur_cas_aux_bornes` (la fonction de
sélection isolément). Un effet mesurable et non nul est confirmé sur une génération d'essai de
deux mois (11 factures sur 76 changent de décision d'éligibilité).

Cette même règle — la valeur en vigueur à la date de l'événement traité, jamais la valeur la
plus récente connue — est la sémantique SCD 2 (« Slowly Changing Dimension » de type 2)
attendue de `dim_patient` dans la couche dimensionnelle à venir : un fait daté doit se
raccorder à la version de la dimension valide à sa date d'effet, pas à la version courante.
Le générateur applique désormais, en amont, la même règle de validité temporelle que
l'entrepôt appliquera en aval.

## Ce qui aurait invalidé cette décision

Une preuve que `date_facture` n'est pas l'ancre correcte de la demande de prise en charge
(par exemple si une source documentait que la couverture applicable est celle du jour de la
*décision*, pas du jour de la *facture*) aurait exigé une date d'ancrage différente, changeant
l'implémentation sans changer le principe (version en vigueur à une date d'événement, quelle
que soit la date retenue).

## Sources

`generator/patients.py` (`versions_par_ipp`, `version_en_vigueur`) ; `generator/prises_en_charge.py`
(`generer_lignes`, docstring sur `date_facture`) ; `generator/defauts.py`
(`_injecter_factures_sans_pec`) ; `generator/mouvements.py` (`_unites_eligibles`, colonnes
lues) ; `generator/doublons.py` (`injecter_doublons`, sélection de la version de création) ;
`generator/facturation.py` (absence de dépendance à `lignes_patients`) ;
`tests/test_prises_en_charge.py::test_eligibilite`,
`::test_pec_utilise_version_en_vigueur_a_la_date_facture` ;
`tests/test_defauts.py::test_exactitude_verite_terrain_biunivoque` ;
`tests/test_patients.py::test_version_en_vigueur_cas_aux_bornes`.
