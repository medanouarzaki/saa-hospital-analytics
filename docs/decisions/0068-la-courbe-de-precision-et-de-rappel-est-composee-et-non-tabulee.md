# ADR 0068 — La courbe de précision et de rappel est composée par un paquet de tracé, et le choix a été tranché par mesure

**Statut.** Accepté, et appliqué au chapitre sur le rapprochement d'identités.

---

## Contexte

Le rapport n'employait jusqu'ici **aucun paquet graphique**. Les schémas des chapitres précédents —
architecture de la chaîne, étoile dimensionnelle, graphe des tâches, agencement de deux écrans — sont
composés à partir de boîtes encadrées et de flèches, sans paquet de tracé. Ce n'était pas une
contrainte mais une commodité : un agencement de blocs se compose très bien ainsi.

Une courbe ne se compose pas ainsi. Le chapitre sur le rapprochement présente un balayage de
**74 points de seuil**, dont 61 donnent une F-mesure de 1, et le lecteur doit voir la forme du
compromis entre précision et rappel — un tableau de 74 lignes ne la montre pas.

**Deux issues étaient possibles** : composer la courbe si un paquet de tracé vectoriel est disponible
partout où le document se compile, ou la remplacer par un tableau du balayage à des seuils nommés en
disant pourquoi.

## La mesure

**Ici.** Un document d'essai chargeant le paquet compile sans erreur, et le journal nomme le fichier
trouvé sous `/usr/local/texlive/2025/texmf-dist/tex/latex/pgfplots/pgfplots.sty`.

**Chez l'exécuteur.** La chaîne typographique n'y est pas installée paquet par paquet : l'action de
composition exécute une image préconstruite. Son script de sélection montre que, sans image
explicitement demandée et sans version de distribution fixée, l'image retenue est
`ghcr.io/xu-cheng/texlive-alpine:latest` ; et le dépôt qui produit cette image déclare, dans son
tableau des images publiées, que sa distribution suit le schéma **Full**. Un schéma complet porte le
paquet.

**La mesure décisive reste le travail de composition lui-même**, qui échoue à la première erreur :
si le paquet manquait, ce travail rougirait avant toute fusion.

## Décision

**La courbe est composée.** Le paquet est chargé une fois dans le document principal, avec un
commentaire disant que le choix est mesuré et non supposé.

**Le tableau reste, à côté, pour ce que la courbe ne montre pas** : la ventilation du rappel de la
référence par collision exacte, variation injectée par variation injectée. Ce n'est pas une
redondance — la courbe montre un compromis, le tableau montre *où* une méthode défaille.

## Justification des points non triviaux

**Pourquoi un paquet de tracé et pas une image.** Deux dispositifs indépendants interdisent toute
image dans ce rapport, et l'interdiction porte sur les captures du système observé. Un tracé
vectoriel composé à partir de coordonnées écrites dans la source n'est pas une image : il se relit
dans un diff, il se corrige à la main, et le contrôle d'absence d'image reste vert parce qu'aucun
fichier d'image n'existe.

**Pourquoi les coordonnées sont écrites et non lues.** Le paquet sait lire un fichier de valeurs
séparées ; la courbe pourrait donc être tracée directement depuis l'artefact d'évaluation versé au
dépôt. Elle ne l'est pas, et c'est un écart assumé : **les dix points portés sont écrits dans la
source du chapitre**, ce qui les soustrait au registre des chiffres. Le choix tient à ce que le
balayage porte 74 points dont 61 identiques, et qu'une courbe les portant tous serait illisible.
La conséquence est nommée ci-dessous.

## Conséquences

- Le document principal charge un paquet de plus, et le travail de composition de l'intégration
  continue devient le témoin que ce paquet existe là-bas.
- Les autres schémas du rapport **ne sont pas convertis** : ils fonctionnent, et les réécrire
  n'apporterait rien.

## Ce que cette décision laisse ouvert

**Les coordonnées de la courbe ne sont pas couvertes par le registre des chiffres.** Elles sont
écrites dans la source du chapitre, extraites à la main de l'artefact d'évaluation. Si cet artefact
changeait, la courbe ne suivrait pas, et **aucun contrôle ne le dirait** — à la différence de tous
les autres nombres du rapport. Les grandeurs qui portent l'argument du chapitre — précision, rappel,
F-mesure au seuil retenu, marges d'ablation — sont, elles, au registre et remesurées.

C'est une exception, elle est unique, et elle est écrite ici pour qu'on la retrouve.

## Sources

- `report/rapport.tex` — le chargement du paquet et son commentaire.
- `linkage/courbe_precision_rappel.csv` — l'artefact d'évaluation dont les points sont extraits.
- `docs/decisions/0010-aucune-image-du-systeme.md` — l'interdiction que cette décision ne franchit
  pas.
