# ADR 0025 — Méthode de conformité du délai de rendez-vous : population, tolérance à deux termes

**Statut.** Accepté.

---

## Contexte

`agg_delai_rendez_vous` expose une médiane de délai par activité, censée refléter le paramètre
`delai_rdv_par_specialite` du générateur (loi log-normale, `generator/config/rendez_vous.yml`).
Trois populations candidates existaient pour la comparaison, et une tolérance devait être choisie
sans littéral de volumétrie, pour rester valide aussi bien sur la génération complète que sur un
sous-ensemble réduit (le job CI, trois mois).

## Décision

1. **Population retenue : délai strictement positif.** Le générateur court-circuite le tirage de
   la loi log-normale pour les rendez-vous pris le jour même (`delai_obtention_jours = 0`,
   `est_jour_meme`) — une décision de construction, pas un tirage de la loi. Deux populations
   écartées, chacune avec sa mesure : la population complète (jour même inclus) biaise la
   médiane vers le bas sans rapport avec le paramètre, mesurée jusqu'à 4,6 de rapport
   écart/erreur-type pour l'activité 14 quand le mode « jour même » contamine l'échantillon ; la
   population des seuls rendez-vous honorés NON plafonnés (délai différent de la marge
   disponible du patient) est biaisée par sélection — retirer les cas où le délai plafonne à la
   marge disponible retire aussi, de façon corrélée, une partie de la queue log-normale
   naturellement longue, mesurée avec des rapports écart/erreur-type de 6,6 à 11,9 sur les huit
   activités, largement au-delà de ce qu'une fluctuation d'échantillonnage expliquerait.
2. **Tolérance à deux termes, le plus grand des deux retenu.** Plancher d'un jour : résolution
   de la comparaison, le délai observé étant un entier de jours et le paramètre un réel. Terme
   statistique : `3 × erreur_type`, où `erreur_type = médiane × écart-type du log × √(π/2) /
   √effectif` — l'erreur type asymptotique de la médiane d'un échantillon fini d'une loi
   log-normale, qui rend la propriété vraie sur un grand échantillon comme sur un petit, sans
   qu'aucun littéral de volumétrie n'y figure.
3. **Aucun des deux termes seuls ne suffirait, démontré par l'activité qui l'illustre dans
   chaque sens.** Activité 20 (médecine générale, 4 232 rendez-vous à délai positif) : écart
   mesuré de 1 jour, terme statistique de seulement 0,11 jour (`3 × erreur_type = 0,32`) — sans
   le plancher, un écart d'un jour sur un grand échantillon ferait échouer le contrôle pour une
   différence sans substance. Activité 14 (gynéco-obstétrique, 1 598 rendez-vous) : écart mesuré
   de 1 jour, terme statistique de 2,17 jours (`3 × erreur_type`) — sans ce terme, un plancher
   fixe à 1 jour serait déjà à sa limite sur cette activité alors qu'un échantillon plus réduit
   (sous-ensemble CI) y aurait une incertitude d'échantillonnage bien plus grande, que le
   plancher seul ne représenterait pas.
4. **Facteur retenu : 3.** Le rapport écart/erreur-type maximal mesuré sur la population retenue
   (délai strictement positif) est 9,31 (activité 20) — un rapport supérieur au facteur retenu,
   mais qui ne rend pas le facteur insuffisant : c'est le plancher d'un jour, pas le terme
   statistique, qui couvre cette activité précise (l'écart mesuré, 1 jour, égale exactement le
   plancher). Le facteur 3 reste la borne décisive pour les activités où l'erreur type dépasse
   le plancher (par exemple l'activité 14, ci-dessus) — c'est sur celles-là, pas sur l'activité
   20, que sa valeur importe.

## Justification des points non triviaux

### Pourquoi le rapport maximal mesuré (9,31) n'invalide pas le facteur 3

Le facteur 3 ne prétend pas majorer le rapport écart/erreur-type observé sur chaque activité — il
majore la marge statistique elle-même, l'un des deux termes du maximum. Sur l'activité 20, ce
terme statistique (0,32 jour) reste bien inférieur à l'écart mesuré (1 jour), mais c'est le
plancher d'un jour, l'autre terme du maximum, qui rend le contrôle vert — le facteur 3 n'a
simplement pas de rôle à jouer sur cette activité précise. La conformité du contrôle repose sur le
maximum des deux termes, jamais sur le terme statistique isolé.

## Conséquences

`tests/test_delai_rendez_vous.py` s'exécute identiquement sur la base complète et sur le
sous-ensemble CI, sans distinction de fenêtre — aucune garde d'applicabilité n'y est nécessaire,
à la différence des indicateurs de séjour (`docs/decisions/0026-...md`).

## Ce qui aurait invalidé cette décision

Un changement du mécanisme de plafonnement du générateur (`generator/rendez_vous.py`), ou de la
distribution log-normale elle-même, changerait les rapports mesurés au point 4 et pourrait
rendre le facteur 3 insuffisant sur une activité aujourd'hui couverte par le seul plancher — à
re-mesurer avant toute évolution de ce mécanisme.

## Sources

`dbt/models/marts/agg_delai_rendez_vous.sql` ; `tests/test_delai_rendez_vous.py` ;
`generator/config/rendez_vous.yml::delai_rdv_par_specialite`,
`ecart_type_log_delai_par_specialite` ; `generator/rendez_vous.py` ; mesures antérieures sur
l'identité de plafonnement du délai et sur les rapports écart/erreur-type par population de
comparaison.
