# ADR 0061 — Une grandeur décimale est convertie en nombre à virgule pour être tracée, et là seulement

**Statut.** Accepté, et appliqué depuis l'écriture des graphiques du tableau de bord.

> **Enregistrement rétrospectif.** La décision a été prise et appliquée avant que sa consignation ne
> le soit ; elle est reprise de la fonction qui la porte et de sa documentation, non de mémoire.

---

## Contexte

Le serveur rend les montants et les taux en **décimal exact** : un montant en dirhams et un taux
d'occupation reviennent avec toutes leurs décimales et sans erreur de représentation. C'est ce qui
permet à un contrôle de comparer deux calculs à 10⁻⁹ près, et le projet en dépend en plusieurs
endroits.

La bibliothèque d'affichage, elle, ne sait pas déduire un type d'axe d'une colonne décimale : elle
retombe sur un **axe catégoriel**, où les valeurs sont traitées comme des étiquettes sans ordre
numérique. Un graphique ainsi tracé range ses barres dans l'ordre lexicographique et n'a plus
d'échelle. Un avertissement le signale, mais l'affichage ne s'interrompt pas.

## Décision

**Les colonnes destinées à un graphique sont converties en nombres à virgule juste avant le tracé,
par une fonction unique, et nulle part ailleurs.** La conversion est nommée dans l'appel — chaque
page dit quelles colonnes elle convertit — et n'a lieu qu'à l'affichage : **les valeurs qui entrent
dans un contrôle restent exactes.**

La fonction ne convertit que les colonnes qu'on lui nomme et qui existent, et rend un tableau neuf
sans modifier celui qu'elle reçoit.

## Justification des points non triviaux

### Pourquoi ne pas convertir plus tôt, à la lecture

Convertir au point de lecture ferait perdre l'exactitude à tout le monde, y compris aux contrôles
qui comparent deux calculs et aux valeurs affichées en chiffres — un montant arrondi par le type
flottant, puis mis en forme, peut différer d'un centime du montant exact. La conversion est donc
placée au plus près du tracé, sur les seules colonnes qui en ont besoin.

### Pourquoi une fonction plutôt qu'une conversion écrite dans chaque page

Une conversion répétée dans neuf pages diverge : l'une convertit, l'autre oublie, et l'axe redevient
catégoriel sur un seul graphique sans que rien ne le dise. La fonction unique rend le geste visible
et repérable ; l'oublier sur une colonne se voit à l'écran, sur un axe qui cesse d'être numérique.

## Conséquences

- Les axes de position des graphiques portant une grandeur décimale sont numériques.
- Les valeurs comparées par un contrôle ne sont jamais celles qui ont été converties : les deux
  chemins sont séparés.
- Une colonne décimale tracée sans passer par la fonction retombe sur un axe catégoriel ; c'est
  visible à l'écran, et cela reste le mode de détection.

## Ce qui aurait invalidé cette décision

Une version de la bibliothèque d'affichage qui déduirait le type d'axe d'une colonne décimale
rendrait la conversion inutile ; elle deviendrait alors une transformation sans motif, à retirer
plutôt qu'à conserver.

## Sources

`dashboard/rendu.py::en_nombres` et sa documentation ; les appels des pages qui la nomment
colonne par colonne.
