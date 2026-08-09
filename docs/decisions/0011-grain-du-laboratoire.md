# ADR 0011 — Grain de l'activité de laboratoire

**Statut.** Accepté.

---

## Contexte

L'activité de laboratoire est publiée par établissement nommé, en deux grandeurs
distinctes : le nombre de prélèvements et le nombre d'examens. Modéliser l'une sans
l'autre revient à choisir un grain sans le dire.

## Décision

Le prélèvement est l'en-tête, l'examen est la ligne. Un passage de type laboratoire
correspond à un prélèvement ; les examens qui en découlent sont des lignes d'acte
rattachées à ce passage.

## Justification des points non triviaux

### La mesure qui fonde le choix

Sur la ligne de l'établissement, exercice 2024 : 9 625 prélèvements et 49 597 examens,
soit **5,15 examens par prélèvement** [`S-30`, tableau 79, page 113].

### Pourquoi ce ratio tranche la question du grain

Un ratio de 5,15 exclut la confusion des deux grains : à un ratio proche de l'unité,
prélèvement et examen auraient été indiscernables et le choix aurait été arbitraire. Ce
ratio commande en outre la volumétrie des lignes d'acte de laboratoire, qui n'est donc
pas posée mais dérivée de deux grandeurs relevées.

## Conséquences

Les volumes de lignes de facture de laboratoire se dérivent du nombre de prélèvements
par ce ratio. Aucun examen de bactériologie ni de parasitologie n'est produit : la
source imprime une valeur nulle pour ces deux familles sur l'établissement.

## Ce qui aurait invalidé cette décision

Un ratio proche de 1, ou une publication ne donnant qu'une seule des deux grandeurs.

## Sources

`S-30` Ministère de la Santé et de la Protection Sociale, *Santé en chiffres 2024*,
tableau 79, page 113 : prélèvements et examens de laboratoire de l'établissement,
exercice 2024.
