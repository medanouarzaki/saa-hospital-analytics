# ADR 0100 — Figures et tableaux numérotés, titrés et appelés

**Statut.** Accepté. Il révise l'`0085` sur la numérotation des captures du tableau de bord, non sur
leur présence.

---

## Contexte

Le rapport composait ses figures et ses tableaux dans des blocs centrés, suivis d'une légende en
petits caractères : aucun numéro, aucun titre que la classe connaisse, aucune liste, et aucun objet
appelé par un renvoi. Le texte désignait les objets par leur position — « ci-dessous », « ci-dessus »
— et une telle désignation devient fausse dès qu'un objet change de page. Les trois captures du
tableau de bord portaient seules un numéro, composé à la main par un compteur propre, à part de toute
autre figure. Trois passages du texte affirmaient ce que la composition démentait : un chapitre
« ne port[ait] aucune capture d'écran » au-dessus de trois captures, le chapitre de cadrage annonçait
deux schémas d'écran redessinés qui n'existent pas, et la conclusion rangeait parmi les pistes
écartées l'illustration du tableau de bord par des captures.

Deux localisations dans une source externe étaient tapées dans la prose (« le tableau~32 de la
page~46 » du recueil statistique), et le contrôle des nombres tapés les tolérait sous une exemption
de « renvoi interne » qui couvrait aussi les chapitres, sections, figures, tableaux et pages.

Enfin, une composition qui laissait un renvoi ou une citation indéfinis réussissait : `latexmk` rend
0 sur un « ?? », mesuré sur une copie du rapport portant un `\ref{inexistant}` et un
`\cite{inexistant}`, et le travail de composition restait vert.

## Décision

### La règle

Une figure est un environnement `figure` ; un tableau est un environnement `table`, ou `longtable`
quand il doit pouvoir se couper. Chacun porte un `\caption` et un `\label` de préfixe `fig:` ou
`tab:`. Le titre est court, factuel, sans nombre tapé, et ne commence ni par « Figure » ni par
« Tableau » ; un titre long reçoit un titre court pour la liste. Une liste des figures et une liste
des tableaux suivent la table des matières.

Chaque objet est appelé dans la prose, avant lui ou sur sa page, sous la forme « (voir
figure~`\ref{…}`) » ou « (cf. tableau~`\ref{…}`) », et commenté par au moins une phrase qui dit ce
qu'il montre. Ce que l'ancienne légende disait au-delà du titre est devenu ce commentaire. Le rapport
porte ainsi vingt figures et vingt-cinq tableaux.

### Les captures suivent la règle commune

`\captureTdb` ne compose plus que l'image, dans sa boîte réservée. Le titre et l'étiquette sont ceux de
l'environnement `figure` du chapitre ; le compteur `capturetdb` et `\legendeCapture` sont retirés de
`report/images.tex`. Les étiquettes `fig:tdb-activite`, `fig:tdb-donnees` et `fig:tdb-sejours` sont
conservées.

### Ce qui n'est ni une figure ni un tableau

- **Les deux logotypes de la page de garde** : ce sont des marques d'identification des
  institutions, à leur place d'usage ; ils ne portent ni numéro, ni titre, ni crédit.
- **Le bloc d'identité de la page de garde**, composé dans un tabulaire de pure mise en page.
- **Les tableaux des annexes produites** (dictionnaire, relevé des écrans, correspondance des
  relations) : l'annexe est l'unité titrée, et une phrase qui les appelle désigne l'annexe par
  `\ref`. Aucun générateur n'est modifié.

### Les localisations externes et les numéros tapés

Une localisation dans une source citée s'écrit dans l'argument optionnel de la citation :
`\cite[tableau~32, p.~46]{s30}`. Les messages numérotés d'un diagramme du rapport sont désignés par
ce qu'ils font. L'exemption « renvoi interne » de `tests/test_aucun_nombre_tape.py` est retirée
entièrement : le contrôle retire déjà l'argument d'un `\ref` et l'argument optionnel d'un `\cite`,
et un numéro tapé hors d'eux est un nombre tapé.

### Les passages d'image

L'interdiction d'image vise le seul système d'information observé ; son motif est dit une fois, au
chapitre de cadrage. Le tableau de bord est le travail de ce projet, sur des données engendrées, et
il se montre. Les trois affirmations contredites par la composition sont réécrites pour dire ce que
la page compose.

### Les contrôles

- `tests/test_structure_du_rapport.py` : tout flottant des chapitres porte exactement un `\caption`
  et une étiquette `fig:` ou `tab:` ; toute étiquette est appelée hors de son propre flottant ; tout
  appel désigne une étiquette existante ; aucune désignation par position dans la prose des sources
  écrites à la main sous `report/` ; aucune macro ne compose « Figure » ou « Tableau » devant un
  compteur tenu hors de la classe.
- `tests/test_annonce_du_plan.py` : l'interdiction des renvois tapés s'étend aux figures, tableaux et
  pages, hors argument optionnel de citation ; la propriété des tableaux d'outils ne garde que
  « exactement une citation par ligne », l'existence des clés étant tenue par
  `tests/test_provenance_des_chapitres.py`.
- Le travail « document » de l'intégration continue lit le journal de chaque composition et échoue
  sur un renvoi ou une citation indéfinis, ou sur une demande de nouvelle passe restée sans suite,
  aux formes exactes relevées sur des journaux réels.

### Les branches distantes

Trente-huit branches distantes, toutes fusionnées dans `main`, ont été supprimées une à une, la tête
de chacune consignée avant suppression. La branche d'une demande est désormais supprimée, en local
et à distance, juste après sa fusion.

## Conséquences

Un objet ajouté sans titre, sans étiquette ou sans appel fait échouer un contrôle ; un renvoi vers
un objet retiré fait échouer la composition en intégration continue. Le chiffre et le titre d'un
objet suivent le document, et non la mémoire de qui l'a écrit.
