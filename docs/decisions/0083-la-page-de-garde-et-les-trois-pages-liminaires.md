# ADR 0083 — La page de garde reçoit une hiérarchie, et les trois pages liminaires sont écrites

**Statut.** Accepté.

---

## Contexte

La page de garde composait sur **trois niveaux de corps seulement**. « Rapport de stage
d'application », qui dit la nature du document, et « Organisme d'accueil », qui dit le lieu du
travail, étaient au même corps que des mentions accessoires. L'œil ne trouvait aucune hiérarchie et
lisait tout à plat.

Les trois pages liminaires — remerciements, résumé, abstract — portaient leur titre et rien d'autre.

## Décision

### 1. Cinq niveaux de corps, et un intitulé plus petit que sa valeur

| niveau | commande | ce qu'il porte |
|---|---|---|
| 1 | `\Huge\bfseries` | le titre du travail |
| 2 | `\LARGE\scshape` espacé | « Rapport de stage d'application » |
| 3 | `\large` | les valeurs — organisme d'accueil, noms — et le sous-titre |
| 4 | `\normalsize` | établissement de formation, filière, année universitaire |
| 5 | `\footnotesize\scshape` gris | les intitulés |

**La règle qui gouverne les niveaux 3 et 5 est celle qui manquait : un intitulé est plus petit que
sa valeur.** Ils étaient auparavant au même corps, et c'est cette égalité qui donnait l'impression
d'un texte posé au hasard.

Le niveau 2 est **espacé et jamais en gras** : il annonce la nature du document, il ne crie pas.
L'espacement vient de `microtype`, déjà chargé — mesuré avant d'être employé sur un document
d'essai portant le seul `\usepackage{microtype}`.

### 2. Aucun ressort élastique

Pas un seul `\vfill`. Tous les espaces sont fixes, en millimètres, pour que la page ne se recompose
pas quand un champ change de longueur.

**C'est ce qui a permis de trouver un défaut que la source ne montre pas.** Composée avec un fichier
de noms témoin, la page débordait sur une seconde page : les deux lignes de noms suffisaient à faire
sauter le bloc. Les espaces fixes ont été resserrés de seize millimètres, et la page tient
désormais dans les quatre combinaisons de logotype et de noms.

### 3. La page se juge avec les noms, et sans le logotype

Une page de garde composée sans ses noms a le bloc central vide : elle ne se juge pas. Les quatre
combinaisons ont donc été composées et regardées, et le décompte de pages du document est identique
dans les quatre.

### 4. Les trois pages liminaires

**Les remerciements nomment l'encadrant par son marqueur**, jamais en clair — la règle qui maintient
les noms hors du dépôt vaut ici comme sur la page de garde. La ponctuation est portée par la
condition : sans le nom, la phrase se compose sans virgule orpheline.

Rien n'y est affirmé qui ne soit établi. Le seul fait dont le dossier porte la trace est que
l'encadrant a remis le cahier de charges et laissé toute liberté d'action dans son cadre.

**Le résumé n'écrit aucun nombre en clair.** Ses neuf valeurs passent par le registre des chiffres,
comme partout ailleurs. Il n'introduit aucun résultat neuf, et il dit en une phrase que les données
sont engendrées — un résumé qui l'omettrait laisserait un lecteur pressé croire à des mesures
réelles.

**L'abstract est une traduction fidèle et non une variante** : mêmes appels de registre, mêmes
mots-clés. Son vocabulaire suit l'usage anglophone du domaine — *data pipeline*, *record linkage*,
*synthetic data* — et non une traduction littérale.

## Ce qui a été écarté

**Séparer l'abstract dans son propre fichier.** La liste fermée l'autorisait, mais l'inclure aurait
demandé de toucher au fichier principal pour une raison que cette liste ne prévoyait pas. Les deux
textes restent dans un même fichier, où ils forment déjà deux chapitres distincts.

**Conserver la ligne « Soutenu le » sur la page de garde.** La disposition arrêtée ne la porte pas.
Son marqueur reste déclaré et employé par le support de présentation ; la ligne ne composait rien,
le marqueur étant vide.

## Ce que cette décision ne peut pas voir

**Aucun contrôle ne tient la hiérarchie de la page de garde.** Ni les cinq niveaux, ni le rapport
entre un intitulé et sa valeur, ni l'absence de ressort. Ces propriétés sont typographiques et ne
se vérifient qu'en regardant le document composé.

**Les appels de registre du résumé ne sont comptés par aucun contrôle.** Celui du registre ne lit
que les chapitres et les annexes. Les neuf identifiants employés ici sont tous employés ailleurs :
aucun ne dépend de cette page pour ne pas devenir orphelin, et un identifiant qui n'y serait
qu'ici serait signalé inemployé — donc rouge, ce qui échoue du bon côté.
