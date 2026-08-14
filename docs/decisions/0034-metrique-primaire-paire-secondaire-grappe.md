# ADR 0034 — Métrique primaire au niveau de la paire, secondaire au niveau de la grappe

**Statut.** Accepté.

---

## Contexte

L'évaluation du rapprochement peut se lire à trois portées possibles : la paire (deux
enregistrements comparés), la grappe (le groupe de composantes connexes que le regroupement
produit à un seuil donné) en portée restreinte, et la grappe en portée globale. Mesure de
référence : 991 paires de vérité terrain sont présentes dans la population courante
(`linkage/courbe_precision_rappel.csv`, colonne `nb_paires_verite_terrain`, constante sur tout
le balayage de seuils).

## Décision

La métrique primaire est la paire. La grappe est secondaire, et déclinée en deux portées :
restreinte (limitée aux enregistrements présents dans au moins une paire de vérité terrain) et
globale (l'ensemble de la population).

## Justification des points non triviaux

### Motifs mesurés du choix

La paire est la seule des trois grandeurs directement comparable à la ligne de base de
détection de doublons par collision exacte (`agg_doublons_identite`,
`docs/decisions/0028-agregats-grain-perimetre-et-limites.md`), elle-même mesurée au niveau de
la paire. La grappe voit l'amplification par transitivité qu'une métrique de paire ne montre
pas : deux fiches jamais comparées directement peuvent se retrouver dans la même grappe par
enchaînement de paires intermédiaires, un effet que seule une lecture au niveau de la grappe
révèle. La portée restreinte évite le gonflement que produirait la portée globale : au seuil
retenu (`docs/decisions/0035-seuil-choisi-sans-etiquettes.md`), le nombre de grappes exactement
retrouvées en portée globale (24 851) dépasse d'un facteur d'environ vingt-cinq celui de la
portée restreinte (991) — écart entièrement imputable aux singletons triviaux (un
enregistrement seul dans sa propre grappe, sans aucune paire de vérité terrain qui le concerne)
que la portée globale compte comme des grappes « exactement retrouvées » sans que cela
signifie quoi que ce soit sur la qualité du rapprochement.

## Conséquences

Toute communication sur la performance du rapprochement cite en premier lieu précision, rappel
et f-mesure au niveau de la paire. Les deux lectures de grappe restent disponibles dans
`linkage.evaluation` pour qui veut observer l'effet de transitivité, mais aucune des deux ne
remplace la métrique de paire dans un résumé à un seul chiffre.

## Ce qui aurait invalidé cette décision

Un usage aval du rapprochement qui exploiterait directement les grappes produites (et non les
paires) comme unité de décision opérationnelle referait de la métrique de grappe la grandeur
primaire pertinente pour cet usage — sans invalider la métrique de paire pour la comparaison à
la ligne de base, qui resterait nécessaire par ailleurs.

## Sources

`linkage/courbe_precision_rappel.csv` ; `linkage/ddl/03_evaluation.sql` (colonnes à portée
restreinte et globale) ; `docs/decisions/0028-agregats-grain-perimetre-et-limites.md` ;
`docs/decisions/0035-seuil-choisi-sans-etiquettes.md`.
