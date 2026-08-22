# Relevé daté des critères de terminaison

**Relevé du 2026-08-22, dans l'état de remise.** Les deux secrets de dépôt sont posés, le fichier de
noms non suivi redéfinit les deux marqueurs et l'état du document, et les deux documents sont
composés avec ces trois valeurs.

Ce document n'entre pas dans le rapport. Il sert deux choses : la vérification avant remise, et la
réponse à deux questions de soutenance — *quels critères sont atteints, et comment le sait-on ?* et
*un critère a été déclaré atteint alors qu'il ne l'était pas ; combien d'autres ?*

Chaque ligne porte **la commande qui l'établit et sa sortie brute**, et un verdict en trois
valeurs : **vrai**, **faux**, **non encore applicable**.

**Ce relevé remplace celui du 2026-08-21.** Deux critères qui s'y abstenaient sont désormais
établis, et l'un des deux est **faux**.

---

## La limite de ce relevé, et elle est essentielle

**La liste des critères n'existe pas dans le dépôt.** Elle est reconstituée depuis les contrôles :
chaque contrôle porte une propriété, et cette propriété est un critère.

Une liste reconstituée ainsi ne peut nommer **que ce qu'un contrôle porte**. Un critère qu'aucun
contrôle ne surveille y est invisible — non parce qu'il serait faux, mais parce que rien ne le
regarde. La seconde partie de ce relevé nomme ceux-là un par un, avec ce qui les vérifie à la main.

Le dépôt en donne un exemple immédiat : **aucun contrôle ne lit le PDF.** La relecture page par page
conduite pour cette remise a trouvé, par cette seule voie, **treize défauts qu'aucun contrôle ne
voyait**, dont un en-tête faux sur huit pages et une surimpression rendant quatre valeurs
illisibles.

---

## Partie A — les critères qu'un contrôle établit

| # | Critère | Commande | Sortie brute | Verdict |
|---|---|---|---|---|
| A1 | Aucun fichier suivi ne porte une image du système d'information observé | `pytest -q tests/test_aucune_image.py` | `16 passed in 0.09s` | **vrai** |
| A2 | Aucun fichier suivi ne porte de trace de vocabulaire d'outil génératif | `pytest -q tests/test_aucune_trace_processus.py` | `4 passed in 0.88s` | **vrai** |
| A3 | Aucun fichier suivi ne porte l'un des deux noms de personne | `RAPPORT_AUTEUR=… RAPPORT_ENCADRANT=… pytest -q tests/test_aucun_nom_de_personne.py` | `1 failed, 17 passed in 0.70s` | **FAUX** — voir ci-dessous |
| A4 | Tout chiffre appelé existe au registre, toute entrée est employée ou déclarée non employée, chaque fichier déclare ce qu'il appelle | `pytest -q tests/test_registre_des_chiffres.py` | `19 passed in 1.30s` | **vrai** |
| A5 | Chaque chapitre déclare sa provenance, dans les deux sens | `pytest -q tests/test_provenance_des_chapitres.py` | `20 passed in 0.37s` | **vrai** |
| A6 | L'index des décisions coïncide avec les enregistrements | `pytest -q tests/test_index_des_decisions.py` | `4 passed in 0.06s` | **vrai** |
| A7 | L'intégration continue collecte tous les fichiers de contrôle | `pytest -q tests/test_collecte_ci.py` | `2 passed in 0.11s` | **vrai** |
| A8 | Le rafraîchissement de l'instantané reste une opération de catalogue | `pytest -q tests/test_instantane_transparence.py` | vert au travail `instantane` de l'exécution `32543510389` | **vrai** — mais voir B7 |
| A9 | Le rapport compose sans erreur | `latexmk -g -pdf -halt-on-error -interaction=nonstopmode rapport.tex` | sortie 0, **98 pages** | **vrai** |
| A10 | Le support de soutenance compose sans erreur | `latexmk -g -pdf -halt-on-error -interaction=nonstopmode presentation.tex` | sortie 0, **30 planches** | **vrai** |
| A11 | Le chargement est idempotent et le rattrapage indifférent à l'ordre | `pytest -v tests/test_idempotence.py` puis `tests/test_rattrapage.py`, au travail `dbt` | `1 passed in 98.43s` et `1 passed in 244.07s` | **vrai** — voir ci-dessous |
| A12 | Les valeurs du registre sont celles que leurs commandes rendent aujourd'hui | `python docs/chiffres/mesurer.py --verifier` | `266 entrée(s) et 13 série(s) confrontée(s), 0 écart(s)` | **vrai** |
| A13 | Aucun chiffre littéral n'est composé hors d'un appel au registre, hors les quarante-deux occurrences nommées | `pytest -q tests/test_aucun_nombre_tape.py` | `13 passed in 0.13s` | **vrai pour toute occurrence nouvelle** — voir B4 |
| A14 | Le fichier des marqueurs déclare `brouillon` et ses deux marqueurs nominatifs vides | `pytest -q tests/test_marqueurs_nominatifs.py` | `24 passed in 0.05s` | **vrai** |

### A3 — le critère est établi pour la première fois, et il est FAUX

Il s'abstenait jusqu'ici : le contrôle lit les deux noms dans deux variables d'environnement et se
déclare abstenu quand elles manquent. Les secrets posés, l'abstention cesse — **en intégration
continue aussi**, `.github/workflows/ci.yml` les passant à ce contrôle par `env:` (lignes 95 à 98).

Sortie brute, les deux variables posées :

```
AssertionError: Nom de personne trouvé dans des fichiers suivis :
  README.md : porte un fragment de 4 caractères de RAPPORT_AUTEUR
  README.md : porte un fragment de 6 caractères de RAPPORT_AUTEUR
  docs/decisions/0003-volumetrie.md : porte un fragment de 7 caractères de RAPPORT_AUTEUR
  docs/decisions/0052-echantillon-de-donnees-au-depot.md : porte un fragment de 7 caractères de RAPPORT_AUTEUR
  docs/modules_non_observes.md : porte un fragment de 7 caractères de RAPPORT_AUTEUR
  docs/sources/sources.yml : porte un fragment de 7 caractères de RAPPORT_AUTEUR
  echantillon/README.md : porte un fragment de 7 caractères de RAPPORT_AUTEUR
  echantillon/patients.csv : porte un fragment de 7 caractères de RAPPORT_AUTEUR
  generator/config/defauts.yml : porte un fragment de 7 caractères de RAPPORT_AUTEUR
  generator/config/volumetrie.yml : porte un fragment de 7 caractères de RAPPORT_AUTEUR
  report/biblio.bib : porte un fragment de 7 caractères de RAPPORT_AUTEUR
  tests/test_linkage_normalisation.py : porte un fragment de 7 caractères de RAPPORT_AUTEUR
```

**Ce que la mesure dit exactement, et il faut le dire avec précision.** Aucun des deux noms complets
ne figure dans l'arbre suivi ; la confrontation a été faite séparément et rend `aucun` pour les
deux. Le nom de l'encadrant n'y paraît sous aucune forme, entière ou fragmentaire. Les douze
occurrences portent toutes sur **trois mots du nom de l'auteur pris isolément** :

- le fragment de sept caractères est un **prénom très répandu**, que le dépôt porte dix fois comme
  nom d'un autre hôpital du centre hospitalier et comme prénom de fiches du jeu engendré ;
- les deux fragments de quatre et six caractères sont dans `README.md`, à l'intérieur de **l'adresse
  du dépôt lui-même**, où le nom de compte les contient.

**C'est donc un point aveugle du contrôle, pas une fuite — et le contrôle l'avait annoncé.** Sa
documentation nomme le seuil de quatre caractères comme une voie ouverte et assumée, et prévoit un
mécanisme d'exclusion étroite par variable, déjà employé pour `LICENSE`.

**Ce qui n'est pas fait, et pourquoi.** Deux remèdes existent, et aucun n'appartient à la liste
fermée des fichiers ouverts à l'écriture pour cette remise :

1. étendre `EXCLUSIONS_PAR_VARIABLE` aux douze porteurs légitimes, nommément et pour le seul nom de
   l'auteur — c'est une écriture dans `tests/test_aucun_nom_de_personne.py` ;
2. retirer les mots du dépôt — impossible sans effacer le nom d'un hôpital que des sources citées
   nomment, et sans renommer le dépôt.

Le premier est le bon. Il n'a pas été fait ici parce qu'élargir un contrôle pour le faire verdir est
précisément le geste que ce projet s'interdit sans décision explicite. **Le critère reste faux, et
l'intégration continue est rouge sur la branche principale tant qu'il l'est.**

### A11 — le critère est établi, et il est vrai

Il s'abstenait faute d'attestation `SAA_INSTRUMENT_JETABLE`. Il reste inétablissable **sur cette
machine**, et pour une raison qui n'est pas une commodité : ces contrôles détruisent et rechargent
des partitions, et la base locale porte la période entière — celle-là même sur laquelle A12 se
mesure. Les lancer ici rendrait A12 inétablissable.

Ils sont donc établis là où une base jetable existe, au travail `dbt` de l'exécution
`32543510389` :

```
tests/test_idempotence.py::test_chargement_idempotent PASSED
1 passed in 98.43s
tests/test_rattrapage.py::test_rattrapage_ordre_indifferent PASSED
1 passed in 244.07s
```

### A12 — la remesure, et pourquoi elle est due avant toute remise

Elle a été lancée deux fois pour cette remise : avant la relecture, et après les corrections. Zéro écart
les deux fois.

**`docs/chiffres/mesurer.py --verifier` est dû avant toute remise, et il est périmé par tout travail
qui déplace de la matière.** Ce n'est pas une consigne d'hygiène, c'est une propriété du dispositif :
cette vérification ouvre la base et compare des valeurs mesurées sur la période entière, quand
l'exécuteur de l'intégration continue n'engendre que trois mois. Elle ne peut pas être un travail de
la chaîne, et elle ne tourne donc qu'à la main.

Les neuf écarts du relevé précédent n'étaient pas nés d'une négligence : ils étaient nés de ce que
personne ne l'avait lancée depuis plusieurs campagnes de rédaction, et que déplacer une section,
descendre un tableau en annexe ou changer la forme d'un appel périme une commande sans rien casser
de visible.

---

## Partie B — les critères qu'aucun contrôle ne peut établir

Chacun est nommé avec ce qui le vérifie à la main, et avec **ce qui a été fait ce jour**.

| # | Critère | Pourquoi aucun contrôle ne l'établit | Vérification à la main, 2026-08-22 |
|---|---|---|---|
| B1 | Le document composé ne porte aucune boîte débordante | **Aucun contrôle ne lit le PDF ni le journal de composition.** La composition n'échoue que sur une erreur, jamais sur un débordement | `grep -c Overfull report/rapport.log` → `0` ; idem au support. Et, mesuré sur l'image des 98 pages, **zéro page porte de l'encre au-delà du bloc de texte**. Trois débordements existaient encore ce matin, dont deux qui sortaient de la feuille | **vrai** |
| B2 | Aucune planche ne déborde, aucune valeur n'y est illisible de loin | idem : rien ne lit le PDF | **les 30 planches relues en image**, une par une. Aucun débordement ; un écart de fond trouvé, voir plus bas | **faux sur un point** |
| B3 | Aucune page ne porte de ligne veuve, de titre orphelin, d'en-tête faux ni de coupure malheureuse | idem | **les 98 pages relues en image**, une par une, deux fois : avant corrections, puis après, par comparaison image à image des deux jeux. Treize défauts trouvés, onze corrigés | **vrai après corrections, sous les réserves nommées** |
| B4 | Aucun nombre n'est tapé en clair dans une source du rapport | Le contrôle du registre vérifie la correspondance entre appels et entrées ; il ne cherche pas les chiffres littéraux. `tests/test_aucun_nombre_tape.py` le fait, mais **quarante-deux occurrences existantes y sont nommées une par une** | inchangé depuis le relevé précédent : la dette est de quarante-deux, déclarée ligne par ligne | **faux, et chiffré** |
| B5 | Un fait cité d'une source est cité fidèlement | Aucun contrôle ne lit la source citée | relecture contre le texte source, faite lors d'un travail antérieur : un cas trouvé et corrigé, le tableau de l'article 35 | **vrai à la connaissance acquise** |
| B6 | Une capture d'écran est à jour et lisible à sa largeur composée | Aucun contrôle ne lit une image ni ne la date | les trois captures relues à 400 points par pouce. **Une observation, non corrigée** : la capture de la page *Activité* porte un filtre de période allant jusqu'au 2026-11-11, quand la période couverte s'arrête au 2026-06-30 | **vrai pour la lisibilité, réserve nommée** |
| B7 | La phase exclusive du rafraîchissement reste une opération de catalogue sur une machine chargée | Le contrôle A8 dérive son seuil sur la machine du moment : il a rendu rouge deux fois sur un exécuteur lent, vert à la reprise, sans qu'aucun code ne change | relancer, et ne conclure à une régression qu'après plusieurs mesures concordantes | **vrai, avec sa réserve** |
| B8 | Les deux noms de personne n'entrent jamais au dépôt | remplacé : le critère est désormais établi par un contrôle, et il est **faux** (voir A3) | — | **repris en A3** |
| B9 | Le support tient dans le temps de soutenance et se dit à voix haute | Rien de tout cela n'est mesurable par un contrôle | **non fait.** Trente planches, aucune répétition chronométrée | **non établi** |
| B10 | Le jeu de données engendré ressemble à ce qu'un fichier réel porterait | Le rapport le dit lui-même : la ressemblance est **posée**, non mesurée, et aucune donnée réelle n'existe pour la confronter | rien, tant que la contrainte de confidentialité tient. C'est la limite centrale du travail, et elle est écrite au rapport | **inétablissable, et écrit comme tel** |

---

## Ce que ce relevé établit

**Quatorze critères qu'un contrôle établit : treize vrais, un faux.** Le faux est A3, l'absence des
deux noms dans l'arbre suivi, et il n'était faux ni hier ni avant-hier — il était **inétablissable**,
et le poser l'a rendu mesurable. Sa cause est mesurée et n'est pas une fuite : douze collisions de
fragments, dont dix sur un prénom que le dépôt porte comme nom d'hôpital.

**Dix critères qu'aucun contrôle ne peut établir**, vérifiés un par un à la main ce jour. Deux sont
faux et chiffrés (B4, quarante-deux nombres tapés ; B2, un écart de valeur au support), un n'a pas
été fait (B9, la répétition chronométrée), un est inétablissable par construction (B10).

**La relecture du document composé est le seul instrument qui ait vu treize de ces défauts**, et
aucun contrôle n'en voyait un seul. C'est la justification empirique de la partie B tout entière.
