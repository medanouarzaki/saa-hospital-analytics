# Relevé daté des critères de terminaison

**Relevé du 2026-08-22, dans l'état de remise, après fermeture des trois points bloquants.** Les deux
secrets de dépôt sont posés, le fichier de noms non suivi redéfinit les deux marqueurs et l'état du
document, et les deux documents sont composés avec ces trois valeurs.

Ce document n'entre pas dans le rapport. Il sert deux choses : la vérification avant remise, et la
réponse à deux questions de soutenance — *quels critères sont atteints, et comment le sait-on ?* et
*un critère a été déclaré atteint alors qu'il ne l'était pas ; combien d'autres ?*

Chaque ligne porte **la commande qui l'établit et sa sortie brute**, et un verdict en trois
valeurs : **vrai**, **faux**, **non encore applicable**.

**Ce relevé remplace celui écrit plus tôt le même jour.** Le critère qui y était faux — A3 — est
désormais vrai, et la section A3 dit par quoi. Aucun critère de la partie A n'est faux.

---

## La limite de ce relevé, et elle est essentielle

**La liste des critères n'existe pas dans le dépôt.** Elle est reconstituée depuis les contrôles :
chaque contrôle porte une propriété, et cette propriété est un critère.

Une liste reconstituée ainsi ne peut nommer **que ce qu'un contrôle porte**. Un critère qu'aucun
contrôle ne surveille y est invisible — non parce qu'il serait faux, mais parce que rien ne le
regarde. La seconde partie de ce relevé nomme ceux-là un par un, avec ce qui les vérifie à la main.

Le dépôt en donne deux exemples immédiats, et ce sont les deux découvertes de la remise :

- **aucun contrôle ne lit le PDF.** La relecture page par page a trouvé, par cette seule voie,
  **treize défauts** qu'aucun contrôle ne voyait, dont un en-tête faux sur huit pages ;
- **aucun contrôle ne lit la prose autour d'un appel au registre.** Un appel peut donc désigner une
  grandeur voisine de celle que la phrase annonce : **la valeur est juste, la phrase est fausse**, et
  tout reste vert. C'est le défaut trouvé à la planche 22, et le balayage écrit pour le chercher
  ailleurs est décrit en B11.

---

## Partie A — les critères qu'un contrôle établit

| # | Critère | Commande | Sortie brute | Verdict |
|---|---|---|---|---|
| A1 | Aucun fichier suivi ne porte une image du système d'information observé | `pytest -q tests/test_aucune_image.py` | `16 passed in 0.05s` | **vrai** |
| A2 | Aucun fichier suivi ne porte de trace de vocabulaire d'outil génératif | `pytest -q tests/test_aucune_trace_processus.py` | `4 passed in 0.47s` | **vrai** |
| A3 | **Aucun fichier suivi ne porte l'un des deux noms de personne** | `RAPPORT_AUTEUR=… RAPPORT_ENCADRANT=… pytest -q tests/test_aucun_nom_de_personne.py` | `25 passed in 0.40s` | **VRAI** — voir ci-dessous |
| A4 | Tout chiffre appelé existe au registre, toute entrée est employée ou déclarée non employée, chaque fichier déclare ce qu'il appelle | `pytest -q tests/test_registre_des_chiffres.py` | `19 passed in 0.97s` | **vrai** |
| A5 | Chaque chapitre déclare sa provenance, dans les deux sens | `pytest -q tests/test_provenance_des_chapitres.py` | `20 passed in 0.27s` | **vrai** |
| A6 | L'index des décisions coïncide avec les enregistrements | `pytest -q tests/test_index_des_decisions.py` | `4 passed in 0.04s` | **vrai** |
| A7 | L'intégration continue collecte tous les fichiers de contrôle | `pytest -q tests/test_collecte_ci.py` | `2 passed in 0.07s` | **vrai** |
| A8 | Le rafraîchissement de l'instantané reste une opération de catalogue | `pytest -q tests/test_instantane_transparence.py` | vert au travail `instantane` de la chaîne | **vrai** — mais voir B7 |
| A9 | Le rapport compose sans erreur | `latexmk -g -pdf -halt-on-error -interaction=nonstopmode rapport.tex` | sortie 0, **98 pages** | **vrai** |
| A10 | Le support de soutenance compose sans erreur | `latexmk -g -pdf -halt-on-error -interaction=nonstopmode presentation.tex` | sortie 0, **30 planches** | **vrai** |
| A11 | Le chargement est idempotent et le rattrapage indifférent à l'ordre | `pytest -v tests/test_idempotence.py` puis `tests/test_rattrapage.py`, au travail `dbt` | `1 passed in 98.43s` et `1 passed in 244.07s` | **vrai** — voir ci-dessous |
| A12 | Les valeurs du registre sont celles que leurs commandes rendent aujourd'hui | `python docs/chiffres/mesurer.py --verifier` | `267 entrée(s) et 13 série(s) confrontée(s), 0 écart(s)` | **vrai** |
| A13 | Aucun chiffre littéral n'est composé hors d'un appel au registre, hors les quarante-deux occurrences nommées | `pytest -q tests/test_aucun_nombre_tape.py` | `13 passed in 0.10s` | **vrai pour toute occurrence nouvelle** — voir B4 |
| A14 | Le fichier des marqueurs déclare `brouillon` et ses deux marqueurs nominatifs vides | `pytest -q tests/test_marqueurs_nominatifs.py` | `24 passed in 0.03s` | **vrai** |

### A3 — le critère était FAUX, il est VRAI, et ce n'est pas la portée du contrôle qui a changé

Le critère avait été établi pour la première fois quelques heures plus tôt, les secrets une fois
posés, et il était **faux** : douze fichiers rougissaient, et **aucun ne portait de nom**.

**La propriété écrite était fausse, et pas seulement bruyante.** Le contrôle cherchait chaque mot du
nom **pris isolément**, dès quatre caractères. Un mot isolé n'identifie personne : le fragment de
sept caractères était un prénom très répandu que le dépôt porte **dix fois comme nom d'un autre
hôpital** du centre hospitalier et comme prénom de fiches engendrées, et les deux autres étaient des
morceaux du nom de compte contenus dans **l'adresse du dépôt** elle-même.

**La propriété corrigée cherche des noms, et non des mots** : toute suite d'au moins **deux mots
consécutifs** du nom, normalisée sur la casse et les diacritiques. Pour un nom de trois mots, trois
suites — les deux paires et le nom entier. Un mot isolé n'est cherché que dans un seul cas : celui
d'un nom qui n'en compte qu'un, et il est alors le nom complet.

**Aucun mécanisme neuf n'a été écrit.** Le contrôle en portait déjà un, `EXCLUSIONS_PAR_VARIABLE`,
qui écarte un fichier nommément et pour un seul des deux noms — il sert au fichier de licence. Il
continue de servir : mesuré, `LICENSE` porte bien le nom complet de l'auteur, et l'exclusion y est
donc encore nécessaire. **Aucun autre fichier n'a eu besoin d'y être ajouté** : la propriété corrigée
rend zéro fautif sur l'arbre.

**CINQ MUTATIONS SUR L'ARBRE RÉEL, et les trois dernières sont les seules qui prouvent quelque
chose.** Sans elles, on n'aurait changé que la portée du contrôle, pas la nature de sa propriété.

| mutation | attendu | mesuré |
|---|---|---|
| le nom complet de l'**encadrant** déposé dans un fichier suivi | rouge | `1 failed in 0.48s` |
| le nom complet de l'**auteur** déposé hors du fichier de licence | rouge | `1 failed in 0.43s` |
| **un seul mot du nom, isolé**, dans un fichier de réserve | **vert** | `1 passed in 0.47s` |
| **les mots du nom collés**, comme dans une adresse | **vert** | `1 passed in 0.42s` |
| un autre mot du nom, isolé | **vert** | `1 passed in 0.40s` |

Chaque mutation a été défaite par restauration depuis une copie hors du dépôt, et l'arbre vérifié
propre après chacune.

**Les témoins du fichier ont changé avec la propriété**, et c'est la partie la plus révélatrice :
quatre témoins qui étaient déclarés VUS sont devenus NON VUS, parce qu'aucun ne nommait personne. Le
fichier compte vingt-cinq contrôles, dont dix formes du nom qui doivent être vues et neuf qui ne
doivent pas l'être.

**Par quelle voie un nom complet passerait-il malgré tout ?** Neuf ont été cherchées, quatre sont
fermées, **cinq restent ouvertes et sont écrites dans le fichier** — les mots écrits sans séparateur,
un séparateur autre qu'une espace, l'ordre des mots inversé, une césure à l'intérieur d'un mot, et un
nom présent dans l'historique mais plus dans l'arbre. Les trois premières sont le prix exact de la
propriété corrigée : les fermer ramènerait la recherche par mot isolé, donc les douze faux positifs.

**Ce que le contrôle ne peut pas voir, et qui n'est pas une voie de contournement** : il ne voit
qu'un nom **écrit**. Une personne désignée sans être nommée — une adresse électronique, une
photographie, une signature dans une image, un nom porté par les métadonnées d'un fichier binaire —
lui échappe entièrement. Il ne dit donc pas « personne n'est identifiable » : il dit « aucun des deux
noms déclarés n'est écrit en toutes lettres dans un fichier suivi ».

### A11 — établi par la chaîne, et non sur la machine de rédaction

Il reste inétablissable **sur cette machine**, et pour une raison qui n'est pas une commodité : ces
contrôles détruisent et rechargent des partitions, et la base locale porte la période entière —
celle-là même sur laquelle A12 se mesure. Les lancer ici rendrait A12 inétablissable. Ils sont donc
établis là où une base jetable existe, au travail `dbt` de la chaîne.

### A12 — la remesure, et pourquoi elle est due avant toute remise

Lancée trois fois pour cette remise : avant la relecture, après les corrections de composition, et
après la création de l'entrée de registre neuve. Zéro écart les trois fois ; la dernière porte sur
**267 entrées**, l'entrée neuve comprise.

**`docs/chiffres/mesurer.py --verifier` est dû avant toute remise, et il est périmé par tout travail
qui déplace de la matière.** Ce n'est pas une consigne d'hygiène, c'est une propriété du dispositif :
cette vérification ouvre la base et compare des valeurs mesurées sur la période entière, quand
l'exécuteur de l'intégration continue n'engendre que trois mois. Elle ne peut pas être un travail de
la chaîne, et elle ne tourne donc qu'à la main.

**ET ELLE EXIGE UNE CHOSE DE PLUS QUE LA BASE : LE JEU ENGENDRÉ.** Une entrée sur les 267 —
`vt-paires-injectees`, les paires de doublons injectées avant tout chargement — lit
`generator/output/scenario_30/verite_terrain.yml`, et cette grandeur n'existe dans aucune couche de
la base : la quarantaine en écarte cinq au chargement, si bien que la base ne porte que les 991
présentes, jamais les 996 injectées.

**La régénération du jeu engendré est donc due avant toute remesure, au même titre que la remesure
est due avant toute remise** :

```bash
uv run python -m generator generator/output      # mesuré : 1 min 12
```

Elle ne coûte rien d'autre que ce temps, et son identité se vérifie : le manifeste porte une empreinte
SHA-256 par fichier et aucun horodatage. Confrontation faite — **18 956 fichiers, tous identiques**.

Ce point n'a pas été deviné : un nettoyage a supprimé ce répertoire comme un artefact jetable, et la
remesure a échoué. `generator/output/` est **régénérable sans être jetable**, et l'enregistrement de
décision 0097 en tire la règle générale.

---

## Partie B — les critères qu'aucun contrôle ne peut établir

Chacun est nommé avec ce qui le vérifie à la main, et avec **ce qui a été fait**.

| # | Critère | Pourquoi aucun contrôle ne l'établit | Vérification à la main | Verdict |
|---|---|---|---|---|
| B1 | Le document composé ne porte aucune boîte débordante | **Aucun contrôle ne lit le PDF ni le journal de composition.** La composition n'échoue que sur une erreur, jamais sur un débordement | `grep -c Overfull` : **0** au rapport, **0** au support. Et, mesuré sur l'image des 98 pages, **zéro page** porte de l'encre au-delà du bloc de texte | **vrai** |
| B2 | Aucune planche ne déborde, aucune valeur n'y est illisible de loin | idem : rien ne lit le PDF | les 30 planches relues en image ; **zéro planche** touche le bord. L'écart de valeur trouvé à la planche 22 est corrigé | **vrai** |
| B3 | Aucune page ne porte de ligne veuve, de titre orphelin, d'en-tête faux ni de coupure malheureuse | idem | les 98 pages relues en image, puis **comparées image à image** à chaque recomposition. Treize défauts trouvés, onze corrigés, deux laissés avec leur motif | **vrai après corrections, sous les réserves nommées** |
| B4 | Aucun nombre n'est tapé en clair dans une source du rapport | Le contrôle du registre vérifie la correspondance entre appels et entrées ; il ne cherche pas les chiffres littéraux. `tests/test_aucun_nombre_tape.py` le fait, mais **quarante-deux occurrences existantes y sont nommées une par une** | la dette reste de quarante-deux, déclarée ligne par ligne. Le contrôle a d'ailleurs attrapé une occurrence NEUVE pendant cette remise — un numéro d'enregistrement de décision cité dans une phrase corrigée —, et la phrase a été reformulée plutôt que l'occurrence déclarée | **faux, et chiffré** |
| B5 | Un fait cité d'une source est cité fidèlement | Aucun contrôle ne lit la source citée | relecture contre le texte source : un cas trouvé et corrigé, le tableau de l'article 35 | **vrai à la connaissance acquise** |
| B6 | Une capture d'écran est à jour et lisible à sa largeur composée | Aucun contrôle ne lit une image ni ne la date | les trois captures relues à 400 points par pouce. **Une réserve, non corrigée** : la capture de la page *Activité* porte un filtre de période allant au 2026-11-11, quand la période s'arrête au 2026-06-30 | **vrai pour la lisibilité, réserve nommée** |
| B7 | La phase exclusive du rafraîchissement reste une opération de catalogue sur une machine chargée | Le contrôle A8 dérive son seuil sur la machine du moment : il a rendu rouge deux fois sur un exécuteur lent, vert à la reprise, sans qu'aucun code ne change | relancer, et ne conclure à une régression qu'après plusieurs mesures concordantes | **vrai, avec sa réserve** |
| B8 | Les deux noms de personne n'entrent jamais au dépôt | — | **repris en A3**, où un contrôle l'établit désormais, et où il est vrai | **repris en A3** |
| B9 | Le support tient dans le temps de soutenance et se dit à voix haute | Rien de tout cela n'est mesurable par un contrôle | **non fait.** Trente planches, aucune répétition chronométrée | **non établi** |
| B10 | Le jeu de données engendré ressemble à ce qu'un fichier réel porterait | Le rapport le dit lui-même : la ressemblance est **posée**, non mesurée, et aucune donnée réelle n'existe pour la confronter | rien, tant que la contrainte de confidentialité tient. C'est la limite centrale du travail, et elle est écrite au rapport | **inétablissable, et écrit comme tel** |
| B11 | **Aucune phrase n'annonce une grandeur pendant qu'un appel en désigne une autre** | **Aucun contrôle ne lit la prose autour d'un appel.** Le registre vérifie que l'identifiant existe et que sa valeur est juste — jamais qu'il est le bon identifiant à cet endroit-là | **trois balayages écrits pour cette remise**, décrits ci-dessous | **vrai à la portée des trois balayages** |

### B11 — le critère neuf, et pourquoi il manquait

Le défaut de la planche 22 avait cette forme exacte : la ligne disait « Variante C », l'appel disait
« modèle complet ». Les deux identifiants existaient, les deux valeurs étaient justes au registre, et
la remesure rendait zéro écart. **Rien ne pouvait le voir.**

Trois balayages ont été écrits pour chercher la même forme ailleurs.

1. **Les égalités affirmées entre des nombres qui ne s'additionnent pas.** Toute phrase portant au
   moins trois appels et un signe d'énumération, dont la valeur de tête diffère de la somme des
   suivantes. Seize phrases relevées, **toutes examinées à la main, aucune fautive** : ce sont des
   énumérations qui n'affirment aucune somme. Le défaut de la page 39 était le seul de cette forme,
   et il est corrigé.
2. **Les totaux de tableau.** Chaque ligne « Total » confrontée à la somme de sa colonne, appels
   résolus contre le registre. **Neuf colonnes vérifiées, zéro écart.**
3. **Les appels dont la prose voisine porte le qualificatif d'un identifiant frère.** C'est le
   discriminant de la forme exacte du défaut. **Il a été mis en défaut avant d'être cru** : le défaut
   de la planche 22 a été réintroduit, et le balayage l'a nommé, avec l'identifiant qui aurait dû
   être appelé. Restauré, il ne trouve plus que six lignes portant l'intitulé générique « Total »,
   toutes vérifiées justes à la main.

**Ce que ces balayages ne voient pas.** Ils cherchent un désaccord entre un identifiant et les mots
qui l'entourent. Une phrase dont la prose et l'identifiant s'accordent tous deux sur une grandeur qui
n'est pas celle qu'il fallait citer leur échappe entièrement. Ils ne remplacent pas la relecture.

---

## Ce que ce relevé établit

**Quatorze critères qu'un contrôle établit : quatorze vrais.** Le seul qui était faux — A3, l'absence
des deux noms — est fermé, et il ne l'a pas été en élargissant la portée du contrôle mais en
**corrigeant la propriété qu'il portait**. La troisième mutation le prouve : un mot du nom, isolé,
laisse le contrôle vert, là où il le faisait rougir avant.

**Onze critères qu'aucun contrôle ne peut établir**, vérifiés un par un à la main. Un est neuf —
B11, découvert en corrigeant le défaut de la planche 22. Un est faux et chiffré : B4, quarante-deux
nombres tapés. Un n'a pas été fait : B9, la répétition chronométrée. Un est inétablissable par
construction : B10.

**La réponse à la question du jury.** Un critère avait été déclaré atteint sans l'être, et un autre
n'était pas mesurable du tout. Les deux sont désormais établis. Ce qui reste : quarante-deux nombres
tapés, une répétition non faite, une réserve sur une capture, et une limite qui ne se lèvera pas tant
qu'aucune donnée réelle n'existera pour la confronter.
