# ADR 0015 — La part des séjours issus des urgences est posée, le taux d'hospitalisation aux urgences en est dérivé

**Statut.** Accepté.

---

## Contexte

`orientation_urgences` (`generator/config/urgences.yml`) répartit chaque passage aux
urgences entre cinq issues, dont l'hospitalisation (code HO). Une première version posait
directement la part HO, 10,2 %, comme les quatre autres codes de la même répartition
(RD, TR, SC, DC).

Trois grandeurs sont liées par une égalité de cohérence que le générateur applique déjà
ailleurs (`generator/urgences.py`) : le nombre de passages annuels aux urgences (dérivé de
`passages_urgences_par_jour`, `generator/config/volumetrie.yml`), le taux d'hospitalisation
aux urgences (HO), et le nombre de séjours d'hospitalisation dont l'admission provient des
urgences (dérivé d'`admissions_annuelles`, 1 197 par an, `generator/config/volumetrie.yml`,
source S-30). Poser HO fige un côté de cette égalité indépendamment des deux autres, gelés
par ailleurs : `admissions_annuelles` est une mesure DOC, et `passages_urgences_par_jour`
porte une analyse de sensibilité à trois scénarios, 14, 30 et 54 passages par jour
(`scenarios_passages_urgences`, `generator/config/volumetrie.yml`).

`docs/decisions/0003-volumetrie.md` (section « Pourquoi la fourchette des urgences est
asymétrique ») documente déjà la tension sur la borne basse de ce scénario : avec HO posé à
10,2 % et une part de séjours issus des urgences de 45 %, la borne basse impliquée est de
5 284 passages par an, une valeur dérivée de deux ratios eux-mêmes non sourcés. Mesurée aux
trois scénarios retenus de l'analyse de sensibilité, la même valeur de HO posée aboutit à des
parts de séjours issus des urgences de 43 %, 93 % et 168 % : la troisième dépasse 100 %, ce
qu'aucune proportion ne peut atteindre. Le scénario haut de l'analyse de sensibilité devenait
arithmétiquement impossible à produire tant que HO restait posé.

## Décision

`part_sejours_provenant_urgences` (`generator/config/urgences.yml`), la part des séjours
d'hospitalisation dont l'admission provient des urgences, est posée à 0,57 — une valeur
indépendante du scénario de volumétrie retenu, positionnée au milieu arrondi de l'intervalle
de plausibilité [0,4940 ; 0,6525] calculé depuis les taux d'hospitalisation par niveau de tri
documentés (S-14) et pondérés par `repartition_niveaux_tri`. Le taux d'hospitalisation aux
urgences (HO) en est dérivé, scénario par scénario, par
`generator/urgences.py` : `HO = part_sejours_provenant_urgences × admissions_annuelles /
passages_annuels_du_scenario`. Les quatre autres codes d'orientation (RD, TR, SC, DC) sont
redistribués sur le complément (1 − HO), en conservant leurs proportions relatives d'origine.

## Justification des points non triviaux

### Pourquoi poser la part plutôt que le taux

La part des séjours issus des urgences est une propriété d'organisation de l'établissement,
relativement stable d'un scénario de volumétrie à l'autre. Le taux d'hospitalisation aux
urgences dépend, lui, directement du nombre de passages : à nombre d'admissions fixé, plus il
y a de passages, plus la part d'entre eux menant à une hospitalisation est nécessairement
faible. Poser la grandeur la plus stable et dériver la plus dépendante du volume rend
l'égalité de cohérence automatiquement satisfaite à chaque scénario, plutôt que de la
contraindre a posteriori.

### Pourquoi 0,57 et non le milieu exact de l'intervalle

L'intervalle [0,4940 ; 0,6525] est calculé, non posé : sa borne haute vient des taux
d'hospitalisation par niveau de tri (S-14) pondérés par la répartition des niveaux déjà
alignée sur le cadrage, sa borne basse est posée à 3 % en dessous de laquelle l'existence même
des niveaux de tri 1 et 2 (taux 80,9 % et 59,6 % selon S-14) serait contredite. 0,57 est le
milieu arrondi, une position choisie pour sa moindre sensibilité à l'incertitude relative de
l'une ou l'autre borne, plutôt que le milieu non arrondi de l'intervalle.

## Conséquences

Les trois scénarios de l'analyse de sensibilité (14, 30 et 54 passages par jour) deviennent
réalisables par construction : quel que soit le nombre de passages annuels retenu, HO se
recalcule pour que le nombre de séjours issus des urgences qu'il implique reste cohérent avec
`admissions_annuelles` et `part_sejours_provenant_urgences`, sans jamais dépasser 100 %.
`tests/test_sensibilite.py` exerce les trois scénarios sur ce mécanisme.

## Ce qui aurait invalidé cette décision

Une mesure sourcée directe du taux d'hospitalisation aux urgences (HO) à l'échelle de
l'établissement, qui aurait rendu la dérivation inutile et la part des séjours issus des
urgences elle-même calculable plutôt que posée.

## Sources

`generator/config/urgences.yml` (paramètres `part_sejours_provenant_urgences`,
`orientation_urgences`, `repartition_niveaux_tri`, calibration S-14 des taux
d'hospitalisation par niveau de tri) ; `generator/config/volumetrie.yml` (paramètres
`admissions_annuelles`, `passages_urgences_par_jour`, `scenarios_passages_urgences`) ;
`docs/decisions/0003-volumetrie.md` (tension documentée sur la borne basse du scénario de
passages aux urgences) ; `generator/urgences.py` (calcul de HO) ;
`tests/test_sensibilite.py` (exercice des trois scénarios).
