# ADR 0081 — La forme du document et du dépôt, et ce qu'un silence de commande cachait

**Statut.** Accepté.

---

## Contexte

Le rapport était dense, et son lecteur le disait. Composé en interligne simple, sans blanc entre
paragraphes, il portait en outre un quart de son volume en un tableau que personne ne lit d'un bout
à l'autre, et une bibliographie qui imprimait des entrées qu'aucun chapitre ne cite.

Le dépôt, lui, n'était pas présentable : du texte qui court, aucun titre intermédiaire, des
commandes noyées dans des listes, et des décomptes devenus faux.

## Décision

### 1. La bibliographie liste ce que le document emploie

`\nocite{*}` imprimait les vingt-huit entrées du fichier bibliographique, dont huit qu'aucun
chapitre ne cite. Le motif d'origine était réel — il rendait la chaîne bibliographique vérifiable
dès le squelette, avant qu'aucune citation n'existe — et il a servi. Il ne sert plus : vingt clés
sont citées, et toute rupture se voit à la première compilation.

Les entrées non citées restent au registre des sources avec leur motif de non-emploi. Elles n'ont
pas disparu ; elles ne s'impriment plus.

### 2. Le dictionnaire des données descend à une synthèse

Vingt-trois folios sur cent deux. L'annexe porte désormais **une ligne par table** — nom, nombre de
colonnes, répartition de provenance — et renvoie au dictionnaire complet, qui reste un artefact du
dépôt.

**La synthèse est produite, jamais écrite**, par le même module que le dictionnaire complet et
depuis le même registre. Deux fichiers écrits séparément peuvent diverger ; deux sorties d'une même
lecture ne le peuvent pas.

**C'est la répartition PAR TABLE qui apprend quelque chose.** Une table entièrement observée et une
table entièrement hypothétique ne se distinguent pas dans une proportion d'ensemble : la table des
relances porte six colonnes, dont zéro observée et zéro documentée.

**Une exclusion de contrôle a perdu son objet et a été retirée.**
`tests/test_provenance_des_chapitres.py` écartait explicitement le dictionnaire complet de son
examen, parce qu'il était composé sans porter de déclaration de provenance. Il n'est plus composé :
l'exclusion ne protégeait plus rien, et une exception dont personne ne sait plus dire ce qu'elle
protège est pire qu'une exception absente. Elle vise désormais la synthèse, qui est dans le même
cas.

### 3. Le texte est aéré et allégé, par deux leviers opposés

Interligne à 1,15 et espacement de paragraphe visible : même contenu, plus de pages, lecture plus
facile.

Et une coupe, dont la règle est écrite : garder ce qui dit ce qui a été fait et pourquoi, en une
phrase ; couper ce qui défend ce choix contre une objection non formulée, ce qui le compare aux
choix non retenus, et ce qui précise au second ordre.

### 4. La page de garde a une hiérarchie, et aucun ressort

Cinq corps de caractère, deux filets, des intitulés en petites capitales grises. **Aucun `\vfill`** :
la page était bâtie sur des ressorts élastiques et se recomposait entièrement dès qu'un champ
changeait de longueur. Tous les espaces sont fixes, en millimètres.

## Une mesure qui était fausse, et ce qu'elle cachait

Le rapport de l'avant-dernier travail annonçait « zéro boîte débordante », sur la foi d'un
`grep -c` qui ne rendait rien. Le travail suivant a recompté : **183**.

Ce travail est allé plus loin, et le silence cachait davantage :

| défaut | avant | après |
|---|---|---|
| boîtes débordantes | 183 | **23** |
| avertissements `fancyhdr` sur la hauteur d'en-tête | 54 | **0** |

Les cent vingt-cinq débordements du dictionnaire sont partis avec lui. Les autres tenaient à des
colonnes trop étroites, à une hauteur d'en-tête que `fancyhdr` réclamait depuis l'origine, et à des
adresses en ligne que rien n'autorisait à se couper.

**Un motif textuel qui ne rend rien peut être muet parce qu'il n'a rien trouvé, ou muet parce qu'il
ne cherche pas.** La distinction n'avait pas été faite, et elle a coûté deux travaux.

## Ce qui a été écarté

**Rembourrer ou tronquer pour atteindre un nombre de pages.** Écarté dans les deux sens : la cible
est un indicateur, pas une contrainte, et un contenu vérifié ne se coupe pas pour tenir dedans.

**Corriger les débordements restants.** Ils sont dans la bibliographie, produite depuis le registre
des sources, et dans deux chapitres — les uns portent des empreintes de soixante-quatre caractères
qu'aucune césure ne peut couper.

## Ce que cette décision ne peut pas voir

**Aucun contrôle ne tient la forme.** Ni l'interligne, ni la hiérarchie de la page de garde, ni la
densité du texte, ni le nombre de pages. Toutes ces propriétés sont typographiques, et elles ne se
vérifient qu'en regardant le document composé.

**Le nombre de boîtes débordantes n'est pas contrôlé non plus.** Il est mesuré à chaque composition
et rapporté ; rien n'empêche qu'il remonte.
