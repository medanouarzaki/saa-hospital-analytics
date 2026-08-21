# ADR 0085 — Les deux logotypes, les captures, et une réservation qui cesse de deviner

**Statut.** Accepté.

---

## Contexte

Trois choses manquaient au document, et une quatrième était fausse sans qu'on le sache.

La page de garde ne portait **qu'un logotype**, par une commande `\logoEcole{hauteur}` qui
cherchait un fichier `figures/logos/ecole.pdf` ou `ecole.png` n'ayant jamais existé : la page
composait donc un cadre d'attente. Deux fichiers ont depuis été déposés — l'établissement de
formation et l'organisme dont il relève —, et la commande n'en prenait qu'un.

Les **trois captures** du chapitre 8 étaient déposées mais jamais composées.

La page de garde, enfin, tenait sa hiérarchie de corps mais **flottait** : deux filets fins, aucun
contraste, rien qui tienne le titre.

Et le mécanisme de réservation portait une supposition écrite : `\captureTdb` réservait la hauteur
par un rapport UNIQUE de 16:10, en déclarant que c'était son point aveugle — « une capture d'un
autre rapport se compose correctement, mais déplace ce qui la suit ». Les trois fichiers déposés
ont démenti la supposition.

## Décision

### 1. Deux logotypes, égalisés sur la surface d'encre et non sur la hauteur

`\logoEcole{hauteur}` est **remplacée** — et non doublée — par `\logosInstitutionnels`, qui compose
les deux côte à côte. Une seule voie mène un logotype dans le document.

Imposer la même hauteur aux deux ne les équilibre pas : un logotype large et bas paraît plus grand
qu'un logotype compact et haut à hauteur égale. L'égalisation porte donc sur la surface.

| fichier | dimensions | rapport | boîte utile | marge | encre | hauteur |
|---|---|---|---|---|---|---|
| `INSEA-logo.png` | 1200×1304 | 0,9202 | 983×1110 | 30,3 % | 582 421 px | **20,0 mm** |
| `HCP-logo.png` | 3790×1088 | 3,4835 | 3781×1088 | 0,2 % | 547 086 px | **17,2 mm** |

**Deux surfaces étaient candidates et ne donnaient pas le même résultat.** La boîte utile — le
rectangle hors marge transparente — donne un rapport de hauteurs de 2,3267, donc 8,6 mm pour le
second logotype. L'encre — le nombre de pixels réellement opaques — donne 1,1616, donc 17,2 mm.
L'écart tient à la densité : la boîte utile de l'INSEA est couverte à 53,4 %, celle du HCP à
13,3 % seulement, parce que ce second logotype est un mot écrit en fin, largement étalé, quand le
premier est une marque pleine.

**La mesure à l'encre est retenue, et c'est le rendu qui a tranché.** La page composée à 8,6 mm a
été regardée en image : le second logotype y paraissait nettement plus faible que le premier, et sa
ligne « Haut-Commissariat au Plan » n'était plus lisible. À 17,2 mm les deux marques pèsent le même
poids et les deux textes se lisent.

**Centrer les boîtes ne centre pas l'encre.** Le fichier de l'INSEA porte 51 pixels de marge
transparente en haut et 143 en bas : son encre est plus haute que le centre de sa boîte de 0,706 mm
à la hauteur déclarée. Les deux boîtes alignées, les deux médianes d'encre l'étaient à 0,76 mm près,
relevé sur l'image du PDF. Chaque logotype porte donc une correction mesurée sur son fichier ; après
correction, les deux médianes tombent toutes deux à 42,83 mm du haut de la feuille.

### 2. La hauteur réservée par `\captureTdb` est déclarée par fichier

Les trois captures avaient alors un rapport de 2,456, 1,973 et 1,964 au lieu des 1,600 supposés — la
première a été reprise depuis, et les conséquences ci-dessous le disent. La
réservation unique retenait de 1,7 à 3,2 cm de trop pour chacune. Le rapport est désormais
**déclaré pour chaque fichier**, mesuré sur lui, dans le fichier qui tient les images — c'est une
propriété du fichier image, pas du texte qui l'appelle. La valeur unique de 0,625 ne subsiste que
comme défaut, pour une capture non encore déposée et donc non encore mesurable.

L'image est en outre **posée DANS la boîte réservée**, bornée en largeur et en hauteur à rapport
conservé. Un fichier dont le rapport dériverait de sa déclaration n'en déborderait donc pas : il y
laisserait un peu de blanc. La pagination cesse de dépendre d'une supposition.

### 3. Une couleur d'accent, un titre ancré, une bande de pied

Une seule couleur — `RGB(23,54,93)` —, déclarée dans la page de garde parce qu'elle ne sert qu'à
elle. Elle porte les filets, la bande de pied et la mention « Rapport de stage d'application », et
rien d'autre. **Le titre reste noir** : c'est le plus gros corps de la page, et le mettre en couleur
ferait deux accents concurrents là où il n'en faut qu'un.

Le titre occupe un aplat de la même couleur mélangée à 8 % de blanc, sur toute la largeur du bloc de
texte, au lieu de flotter entre deux filets fins. La bande de pied fait 2,2 mm, pleine largeur.

**Aucun ressort élastique**, la bande de pied comprise : sa position vient d'un espace fixe réglé
sur l'image du PDF. Elle finit à 268,6 mm du haut de la feuille, pour une marge basse à 272,0 mm.

## Conséquences

`\logoEcole` n'existe plus ; l'ADR 0076, qui la nommait, est dépassée sur ce point.

La pagination ne bouge pas : 95 pages et 22 boîtes débordantes, images en place, un logotype retiré,
une capture retirée, ou sans le fichier de noms. Retirer une capture déplace la légende qui la suit
de **0,398 pt**, la seule épaisseur des deux traits du cadre d'attente.

**Les trois captures sont acceptées telles quelles par l'auteur.** Leur finesse a été mesurée et
rapportée — placées à 0,92 de la largeur du bloc de texte, elles rendent à 582 ppp, si bien qu'un
texte de 12 pixels à l'écran compose à 0,124 pt par pixel, soit 1,49 pt ; seuls les titres et les
grands chiffres se lisent. Ce n'est plus une question ouverte : l'auteur les retient ainsi.

**La capture de la page « Activité » a été reprise après la mise en français des étiquettes de
date**, et la reprise est vérifiée : son axe de temps porte `janv.`, `mars`, `mai`, `juil.`,
`sept.`, `nov.` sur deux lignes, son titre d'axe est « Jour », et sa légende « Admissions,
Consultations, Passages ». Aucun nom de mois anglais n'y subsiste.

**La reprise a toutefois changé le rapport du fichier, et la déclaration ne l'a pas suivi.** La
capture mesure désormais 3386×1698 pixels, soit un rapport hauteur sur largeur de 0,50148, quand
`\declarerCapture{page-activite}` porte encore 0,40724, mesuré sur la capture précédente. L'image
étant bornée en hauteur autant qu'en largeur, elle compose à **119,6 mm au lieu de 147,2 mm** —
19 % plus étroite que les deux autres. Le mécanisme fonctionne comme il doit : il n'a pas laissé
l'image déborder de sa réservation. C'est la déclaration qui est périmée, et la corriger tient en un
nombre. `report/images.tex` n'étant pas dans la liste fermée du travail qui a constaté le défaut, il
n'a pas été touché : le défaut est signalé, non commis.

**Le fichier `HCP-logo.png` est lui-même rogné à droite** : la dernière lettre du mot « PLAN » est
coupée au bord de l'image, à 3781 pixels sur 3790. La composition n'y est pour rien — le défaut est
dans le fichier déposé, et il se reprend à la source.
