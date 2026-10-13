# ADR 0099 — Trois parties, et les outils nommés

**Statut.** Accepté. Il révise l'`0088` sur un point : la désignation fonctionnelle des briques.

---

## Contexte

Le rapport alignait ses chapitres sans regroupement : le lecteur ne voyait pas où finissait le
cadrage, où commençait la conception, où commençait la réalisation. Les outils de la chaîne étaient
présentés dans une section du chapitre de cadrage, par leur seule fonction, sans référence à leur
documentation et sans le motif de leur choix. Deux renvois étaient tapés à la main — un numéro de
section écrit en clair —, et le contrôle de structure portait un décompte de chapitres écrit en
littéral.

## Décision

### Le rapport compose trois parties

| Partie | Chapitres |
|---|---|
| Contexte et cadrage | L'organisme d'accueil ; Le système d'information hospitalier ; Cadrage et méthodologie |
| Analyse et conception | Conception du jeu de données ; Architecture de la chaîne de données ; Qualité des données et rapprochement d'identités |
| Réalisation | Environnement et outils ; Analyse de l'activité ; Le tableau de bord ; Recommandations |

L'introduction les annonce par `\annoncePartie{titre}`, sans numéro : le rang d'une partie est son
ordre d'apparition. Chaque chapitre est annoncé sous la partie qui le contient.

### Un chapitre nomme les outils

`report/chapitres/environnement-et-outils.tex` ouvre la réalisation. Pour chaque outil : ce qu'il
est, ce que le projet en fait, le motif de son choix, et une référence à sa documentation officielle,
consignée au registre des sources et rendue dans la bibliographie par `docs/sources/to_bibtex.py`.

Le motif d'un choix vient de deux origines, et l'étiquette de provenance les distingue :

- `decision-…` quand un enregistrement l'a consigné : serveur de base (`0001`), rapprochement
  probabiliste (`0005`), orchestrateur (`0012`), transformation déclarative (`0018`), moteur en
  mémoire (`0029`), schéma du tableau de bord (`0043`) ;
- `choix-…` pour les autres outils, qui sont des choix posés sans enregistrement : langage unique,
  environnement verrouillé, génération, conteneurs, contrôles, intégration continue, composition.

La section « Outils et justification » quitte le chapitre de cadrage, qui n'en garde qu'une phrase
de renvoi au nouveau chapitre.

### La désignation fonctionnelle de l'`0088` est remplacée

L'`0088` faisait porter à chaque brique de la figure de la pile technique la désignation
fonctionnelle que le chapitre de cadrage lui donnait. Cette désignation est remplacée, au motif
de la consigne K11–K12 : les outils sont désormais nommés, avec leur référence ; la légende de la
figure renvoie au chapitre qui les nomme. L'absence de logotype d'éditeur est maintenue.

### Les renvois passent par une étiquette

Les deux renvois tapés deviennent des `\ref` vers deux étiquettes nouvelles :
`sec:orchestration` et `sec:choix-serveur`. `tests/test_annonce_du_plan.py` interdit désormais
toute forme de renvoi tapé — chapitre, section ou annexe suivis d'un numéro ou d'une lettre, et le
signe de paragraphe suivi d'un chiffre — dans les chapitres et les liminaires, avec ses témoins
positifs et négatifs.

Le même fichier vérifie aussi :

- la correspondance des parties annoncées et des parties composées, dans les deux sens : même
  nombre, même ordre, titre exact, chapitres rattachés ;
- une citation exactement par ligne des tableaux d'outils, et la présence de chaque clé citée au
  registre des sources.

### Le contrôle de structure ne porte plus de littéral

`tests/test_structure_du_rapport.py` comparait les chapitres présents à un nombre écrit. Il compare
désormais deux mesures : les fichiers de chapitres numérotés présents, et les chapitres que
l'introduction annonce. Un chapitre ajouté ou retiré d'un seul côté fait échouer l'égalité.

### Les en-têtes

L'introduction et la conclusion composent leur en-tête en capitales, comme les chapitres
numérotés.

## Conséquences

Le décompte des chapitres et des sections, et les chiffres qui en dépendent, sont remesurés et
consignés au registre des chiffres. Un outil ajouté à la chaîne exige une ligne dans le chapitre des
outils, une entrée au registre des sources, et un motif déclaré.
