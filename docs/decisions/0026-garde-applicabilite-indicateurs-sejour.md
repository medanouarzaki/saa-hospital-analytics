# ADR 0026 — Garde d'applicabilité des indicateurs de séjour : abstention plutôt que tolérance élargie

**Statut.** Accepté.

---

## Contexte

`tests/test_indicateurs_sejour.py` recalcule TOM, DMS, TROT et IROT depuis `marts.fct_sejour` et
les confronte aux valeurs publiées (`generator/config/volumetrie.yml`). Les quatre grandeurs sont
annualisées et définies sur la période complète de génération (`date_debut`/`date_fin`,
`generator/config/periode.yml`). Sur une fenêtre partielle (le sous-ensemble CI, trois mois), un
séjour non clos est prolongé jusqu'à la borne de fin de période pour le calcul de sa durée — un
mécanisme qui domine le calcul quand la fenêtre est courte.

## Décision

1. **Le test s'abstient (`pytest.skip`), avec un motif explicite, plutôt que d'élargir sa
   tolérance.** Une tolérance élargie jusqu'à couvrir l'écart d'une fenêtre partielle cesserait
   de détecter une vraie dérive sur une fenêtre complète — un contrôle qui ne détecte plus rien
   n'est pas un contrôle.
2. **Condition retenue : une égalité mesurée, pas une marge arbitraire.** `max(jour_admission)`
   de `marts.fct_sejour` comparé à `date_fin` de la configuration. Coïncidence exacte sur la base
   principale : `2026-06-30` des deux côtés — le test s'y exécute, ne s'abstient pas.

Ampleur de la domination sur fenêtre partielle, mesurée en forçant la condition (mutation du lot
6j, K4) : en excluant la seule ligne à date d'admission maximale de `fct_sejour`, le test passe
de vert (exécuté) à une abstention avec le motif attendu — la condition réagit à un écart d'un
seul jour entre la base et la configuration, la plus petite divergence possible, confirmant
qu'elle ne tolère aucune marge.

## Justification des points non triviaux

### Pourquoi cette égalité et pas une comparaison sur `date_debut`

Seule la borne de FIN gouverne la prolongation des séjours non clos (`fin_pour_calcul` vaut
`date_heure_sortie` si connue, sinon la borne de fin de période) ; une fenêtre dont la date de
début diffère mais dont la fin coïncide avec la configuration ne fausserait pas ce mécanisme —
seule `date_fin` est donc pertinente pour la garde.

## Conséquences

Sur le sous-ensemble CI (généré avec `--date-fin 2024-03-31`, `.github/workflows/ci.yml`), ce
test s'abstient systématiquement — c'est le comportement attendu, pas une lacune de couverture :
la CI ne peut pas prouver la conformité annualisée sur une fenêtre qui n'a jamais prétendu couvrir
une période complète. La preuve sur période complète reste portée par l'exécution locale contre
la base principale, rejouée et documentée à chaque exécution du contrôle.

## Ce qui aurait invalidé cette décision

Un changement de la date de fin par défaut du générateur ou de la configuration
(`generator/config/periode.yml::date_fin`) sans régénération de la base principale ferait
diverger la condition et abstiendrait le test même sur la base qui devrait normalement l'exécuter
— à re-mesurer après toute régénération.

## Sources

`tests/test_indicateurs_sejour.py` ; `marts.fct_sejour` ;
`generator/config/periode.yml::date_debut`, `date_fin` ; `generator/config/volumetrie.yml::
tom_publie`, `dms_publie`, `trot_publie`, `irot_publie` ; `tests/test_coherence_inter_tables.py::
test_regle_13_indicateurs_sejour_recalcules_depuis_les_donnees` (formules reprises) ; mutation de
la condition d'applicabilité (abstention forcée et motif vérifié).
