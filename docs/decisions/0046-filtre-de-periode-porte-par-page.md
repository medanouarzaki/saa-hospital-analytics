# ADR 0046 — Le filtre de période est porté par page, et son absence est affichée plutôt que tue

**Statut.** Accepté.

---

## Contexte

Un tableau de bord d'activité hospitalière appelle naturellement un filtre de période, et l'endroit
qui vient à l'esprit pour le placer est une barre latérale commune à toutes les pages.

Une mesure exhaustive a confronté cette intention à ce que les objets permettent réellement. Les
trente-sept indicateurs des sept pages ont été examinés un par un sur deux critères qu'il ne faut
pas confondre : **porter une colonne de date** permettant la restriction, et **avoir un sens sur une
sous-période**. Un indicateur peut satisfaire le premier et pas le second.

## Décision

**Le filtre de période est porté par page, et non globalement.**

- Les pages dont **tous** les indicateurs se filtrent le portent **sans réserve**.
- Les pages dont **une partie** ne se filtre pas le portent **avec marquage explicite** des
  indicateurs concernés.
- Les pages dont **aucun** indicateur ne se filtre **ne le portent pas**, et affichent le motif.

## Justification des points non triviaux

### Pourquoi pas une barre latérale commune

Le décompte mesuré l'interdit : **vingt-quatre indicateurs sur trente-sept se filtrent, treize ne
se filtrent pas**, et la somme des deux catégories égale bien le nombre d'indicateurs.

Les non filtrables ne sont pas dispersés : **deux pages entières sur sept — qualité des données et
rapprochement d'identités — sont totalement insensibles à un filtre de période.** Une barre
latérale commune afficherait donc, sur deux pages sur sept, des chiffres rigoureusement identiques
quelle que soit la période choisie, sans que rien ne le signale.

### Pourquoi ces deux pages sont insensibles, mesuré au catalogue

Les six objets qui portent leurs indicateurs — trois agrégats et les trois tables de rapprochement
— ont été interrogés au catalogue sur le type de leurs colonnes, et non sur leur nom :

**zéro colonne de type date ou horodatage sur les cinquante et une colonnes des six objets.**

Ce n'est pas un oubli de conception mais la nature des grandeurs. La complétude d'une colonne, la
provenance d'un champ, une grappe d'identité, une courbe de précision et de rappel sont des
**états**, non des flux : ils décrivent l'entrepôt dans son ensemble, à la date de son dernier
chargement. Les filtrer n'aurait pas de sens même si une colonne le permettait.

### Pourquoi trois motifs de non-filtrabilité et non un seul

Les confondre conduirait à traiter de la même façon des situations qui appellent des affichages
différents.

**Premier motif — l'objet ne porte aucune colonne de date.** Huit indicateurs, sur les deux pages
ci-dessus. Rien n'est possible, et le motif affiché doit dire que la grandeur décrit un état et non
une période.

**Deuxième motif — la grandeur est annualisée et n'a pas de sens sur une sous-période.** Les quatre
indicateurs réglementaires de séjour divisent par un nombre de jours puis multiplient par une année
de référence ; deux d'entre eux divisent en outre par la capacité multipliée par cette année. La
restriction est techniquement possible et méthodologiquement fausse. Le dépôt porte déjà une garde
d'applicabilité sur ce point, décidée par l'ADR `0026`, dont le motif est mesuré : sur une fenêtre
partielle, la prolongation des séjours non clos jusqu'à la borne de période domine le calcul et
l'écart sort de la tolérance.

Le décompte des séjours non clos relève du même motif par une autre voie : il est défini **par
rapport à la dernière extraction**, et restreindre à une période antérieure changerait la
définition plutôt que la population.

**Troisième motif — la date existe mais hors de la couche des faits.** L'ancienneté des créances se
date depuis la couche intermédiaire, aucune table de faits ne portant les créances. Un filtre
appliqué aux faits ne l'atteindrait pas ; il faudrait une seconde chaîne de filtrage.

### Pourquoi le marquage plutôt que le masquage

Une page partiellement filtrable pourrait masquer ses indicateurs non filtrables dès qu'un filtre
est posé. Ce serait pire : la page changerait de composition selon le filtre, et un lecteur ne
saurait pas si un indicateur a disparu parce qu'il ne se filtre pas ou parce qu'il n'a pas de
valeur sur la période. Le marquage laisse la page stable et déplace l'information là où elle est
utile — sur l'indicateur lui-même.

### Le risque évité, formulé simplement

**Un filtre présent à l'écran et sans effet ferait lire des chiffres comme s'ils portaient sur la
période choisie.** C'est une erreur silencieuse : rien n'échoue, rien ne s'affiche en rouge, et le
lecteur tire une conclusion datée d'un chiffre qui ne l'est pas. C'est le mode de défaillance que
cette décision écarte.

## Conséquences

Cinq pages portent un filtre de période, dont trois sans réserve — activité, rendez-vous, urgences,
dont tous les indicateurs se filtrent — et deux avec marquage : séjours, dont deux indicateurs sur
cinq ne se filtrent pas et un troisième se filtre avec un biais vers les séjours courts, et
facturation, dont l'ancienneté des créances relève du troisième motif.

Deux pages n'en portent pas et affichent leur motif.

La filtrabilité de chaque indicateur est portée par le registre décidé par l'ADR `0044`, ce qui
permet à l'affichage de la lire plutôt que de la redéclarer, et à un test de vérifier qu'aucun
indicateur non filtrable ne figure sans marquage sur une page filtrée.

Cinq indicateurs comptés filtrables le sont **sous réserve**, et la réserve est portée au registre :
le filtre y agit sur une date qui n'est pas celle qu'un lecteur attendrait — date de naissance de
créance plutôt que date de facture, ou deux dates différentes au numérateur et au dénominateur d'un
même ratio.

## Ce qui aurait invalidé cette décision

Que les trente-sept indicateurs soient tous filtrables, auquel cas la barre latérale commune serait
la forme juste et la plus simple.

Que les non filtrables soient dispersés un par page plutôt que concentrés sur deux pages entières :
le marquage aurait alors suffi partout, et aucune page n'aurait eu à se passer du filtre.

## Sources

`docs/decisions/0026-garde-applicabilite-indicateurs-sejour.md` — garde d'applicabilité des quatre
indicateurs de séjour sur une fenêtre partielle.
`docs/decisions/0044-registre-des-indicateurs-fichier-unique-teste.md` — le registre porte la
filtrabilité de chaque indicateur.
Catalogue de la base — types des colonnes des six objets sans colonne temporelle.
