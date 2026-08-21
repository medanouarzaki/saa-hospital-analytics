# Relevé daté des critères de terminaison

**Relevé du 2026-08-21, 23:07 UTC.** Dépôt à `9c02c7a`, sur la branche principale.

Ce document n'entre pas dans le rapport. Il sert deux choses : la vérification avant remise, et la
réponse à deux questions de soutenance — *quels critères sont atteints, et comment le sait-on ?* et
*un critère a été déclaré atteint alors qu'il ne l'était pas ; combien d'autres ?*

Chaque ligne porte **la commande qui l'établit et sa sortie brute**, et un verdict en trois
valeurs : **vrai**, **faux**, **non encore applicable**.

---

## La limite de ce relevé, et elle est essentielle

**La liste des critères n'existe pas dans le dépôt.** Elle est reconstituée depuis les contrôles :
chaque contrôle porte une propriété, et cette propriété est un critère.

Une liste reconstituée ainsi ne peut nommer **que ce qu'un contrôle porte**. Un critère qu'aucun
contrôle ne surveille y est invisible — non parce qu'il serait faux, mais parce que rien ne le
regarde. La seconde partie de ce relevé nomme ceux-là un par un, avec ce qui les vérifierait à la
main.

Le dépôt en donne un exemple immédiat : **aucun contrôle ne lit le PDF.**

---

## Partie A — les critères qu'un contrôle établit

| # | Critère | Commande | Sortie brute | Verdict |
|---|---|---|---|---|
| A1 | Aucun fichier suivi ne porte une image du système d'information observé | `pytest -q tests/test_aucune_image.py` | `16 passed in 0.05s` | **vrai** |
| A2 | Aucun fichier suivi ne porte de trace de vocabulaire d'outil génératif | `pytest -q tests/test_aucune_trace_processus.py` | `4 passed in 0.56s` | **vrai** |
| A3 | Aucun fichier suivi ne porte l'un des deux noms de personne | `pytest -q tests/test_aucun_nom_de_personne.py` | `17 passed, 1 skipped in 0.03s` | **non encore applicable** — voir ci-dessous |
| A4 | Tout chiffre appelé existe au registre, toute entrée est employée ou déclarée non employée, chaque fichier déclare ce qu'il appelle | `pytest -q tests/test_registre_des_chiffres.py` | `19 passed in 0.97s` | **vrai** |
| A5 | Chaque chapitre déclare sa provenance, dans les deux sens ; plus aucun emplacement de rédaction personnelle | `pytest -q tests/test_provenance_des_chapitres.py` | `20 passed in 0.25s` | **vrai** |
| A6 | L'index des décisions coïncide avec les enregistrements | `pytest -q tests/test_index_des_decisions.py` | `4 passed in 0.04s` | **vrai** |
| A7 | L'intégration continue collecte tous les fichiers de contrôle | `pytest -q tests/test_collecte_ci.py` | `2 passed in 0.09s` | **vrai** |
| A8 | Le rafraîchissement de l'instantané reste une opération de catalogue | `pytest -q tests/test_instantane_transparence.py` | `7 passed in 33.11s` | **vrai** — mais voir B7 |
| A9 | Le rapport compose sans erreur | `latexmk -pdf -halt-on-error -interaction=nonstopmode rapport.tex` | sortie 0, 98 pages | **vrai** |
| A10 | Le support de soutenance compose sans erreur | `latexmk -pdf -halt-on-error -interaction=nonstopmode presentation.tex` | sortie 0, 21 planches | **vrai** |
| A11 | Le chargement est idempotent et le rattrapage indifférent à l'ordre | `pytest -q tests/test_idempotence.py` | `SAA_INSTRUMENT_JETABLE doit valoir '1'` | **non encore applicable** — voir ci-dessous |
| A12 | **Les valeurs du registre sont celles que leurs commandes rendent aujourd'hui** | `python docs/chiffres/mesurer.py --verifier` | `265 entrée(s) et 13 série(s) confrontée(s), 9 écart(s)` | **FAUX** |

### A3 — pourquoi « non encore applicable » et non « vrai »

Le contrôle lit les deux noms dans deux variables d'environnement, et **s'abstient explicitement**
quand elles sont absentes plutôt que de passer en silence. C'est son état ordinaire : l'intégration
continue ne les pose pas pour les travaux de test — elle ne les pose que pour composer le document.
Le `1 skipped` de la sortie est exactement cette abstention.

Le critère n'est donc **pas établi** par ce contrôle en l'état. Ce qui l'établirait : poser les deux
variables et relancer. Fait à la main lors du travail sur la présentation, avec un nom témoin absent
du dépôt : le contrôle est vert, et il rougit dès qu'on dépose ce nom dans une planche.

Sur les noms réels, il rougit sur des **fragments** — trois mots que le dépôt porte ailleurs, dans
des noms d'établissement et des titres de source. C'est une limite connue et consignée.

### A11 — pourquoi « non encore applicable »

Ces contrôles détruisent et rechargent des partitions. Ils exigent que
`SAA_INSTRUMENT_JETABLE=1` atteste explicitement que la cible est jetable, et **refusent de
s'exécuter sans**. Ce n'est jamais un saut silencieux : l'échec nomme la variable. L'intégration
continue la pose ; la machine de rédaction ne la pose pas.

### A12 — le critère faux, et c'est la réponse à la question du jury

**Neuf écarts.** Sortie brute :

```
fichiers-de-controle : consigné 74, mesuré 75
tdb-graphiques : consigné 23, mesuré 18
instantane-volume : consigné 32710656, mesuré 34799616
sections-du-rapport : consigné 54, mesuré 51
releve-champs-non-employes : consigné 17, mesuré 101
relations-non-reprises : consigné 5, mesuré 0
conclusions-avec-relation : consigné 16, mesuré 0
conclusions-sans-relation : consigné 6, mesuré 0
tableau-de-bord-par-page : le fichier que la commande produit a pour empreinte 00255f5d…, le
registre consigne 0ba7b302… — la commande et le registre divergent
265 entrée(s) et 13 série(s) confrontée(s), 9 écart(s)
```

**Ce que ces écarts sont, et ce qu'ils ne sont pas.** Aucun ne dit qu'une valeur du rapport est
fausse au sens où elle aurait été inventée : chacune a bien été mesurée par sa commande, un jour.
Ils disent que **le dépôt a bougé depuis, et que le registre n'a pas suivi**. Quatre d'entre eux
sont directement imputables aux travaux de rédaction récents :

- `sections-du-rapport` — trois sections ont été fondues en une au chapitre du système
  d'information ;
- `releve-champs-non-employes` — la même coupe a retiré les tableaux d'agencement, et les
  identifiants de relevé qu'ils citaient ne sont plus cités ;
- `tdb-graphiques` et l'empreinte de `tableau-de-bord-par-page` — cinq tracés du tableau de bord
  sont passés par une fonction commune pour porter des étiquettes françaises, et la commande qui
  les compte ne les voit plus sous la forme qu'elle cherche ;
- `fichiers-de-controle` — un fichier de contrôle de plus.

Les trois écarts à zéro — `relations-non-reprises`, `conclusions-avec-relation`,
`conclusions-sans-relation` — sont d'une autre nature : mesurer **zéro** là où le registre consigne
cinq, seize et six suggère que la commande cherche sa matière à un endroit où elle n'est plus, le
tableau de correspondance étant descendu en annexe. Il n'est pas établi ici que le rapport soit
faux ; il est établi que **la commande et le registre ne parlent plus de la même chose**.

**Pourquoi rien ne l'a vu.** `mesurer.py --verifier` n'est pas un travail de l'intégration
continue, et ne peut pas l'être : il ouvre la base et compare des valeurs mesurées sur la période
entière, quand l'exécuteur n'engendre que trois mois. C'est écrit en tête du registre. Le critère
n'est donc vérifiable **qu'à la main**, sur une machine portant la période complète — ce qui est
exactement ce que ce relevé vient de faire.

**Il n'est pas corrigé ici.** Corriger un écart demande de remesurer la valeur et de la reporter au
registre, ce qui change une valeur composée par le rapport ; ni les chapitres ni les valeurs du
registre n'étaient ouverts à ce travail. Le défaut est relevé, daté et nommé.

---

## Partie B — les critères qu'aucun contrôle ne peut établir

Chacun est nommé avec ce qui le vérifierait à la main.

| # | Critère | Pourquoi aucun contrôle ne l'établit | Ce qui le vérifie |
|---|---|---|---|
| B1 | Le document composé ne porte pas plus de boîtes débordantes qu'avant | **Aucun contrôle ne lit le PDF ni le journal de composition.** La composition n'échoue que sur une erreur, jamais sur un débordement | composer, compter `Overfull` au journal — 22 au rapport, 0 au support ce jour |
| B2 | Aucune planche ne déborde, aucune valeur n'y est illisible de loin | idem : rien ne lit le PDF | rendre chaque planche en image et la lire réduite au quart |
| B3 | Aucune page ne porte de ligne veuve, de titre orphelin ni de coupure malheureuse | idem | relecture en image, page par page |
| B4 | **Aucun nombre n'est tapé en clair dans une source du rapport** | Le contrôle du registre vérifie la **correspondance** entre appels et entrées ; il ne cherche pas les chiffres littéraux. Un nombre tapé n'appelle rien, donc rien ne le voit | relecture, ou un contrôle à écrire. **Un cas existe aujourd'hui** : `report/chapitres/qualite-et-rapprochement.tex:340` compose `0,9995` à la main, dans le tableau même où les trois autres valeurs viennent du registre |
| B5 | Un fait cité d'une source est cité fidèlement | Aucun contrôle ne lit la source citée | relecture contre le texte source. Un cas a été trouvé et corrigé : le tableau du chapitre premier rangeait le recouvrement parmi les missions de l'article 35, que le texte ne lui donne pas |
| B6 | Une capture d'écran est à jour et lisible à sa largeur composée | Aucun contrôle ne lit une image ni ne la date | comparer la capture à l'application, et mesurer sa résolution composée. Un cas a été trouvé : une capture antérieure à la mise en français des dates |
| B7 | La phase exclusive du rafraîchissement reste une opération de catalogue **sur une machine chargée** | Le contrôle A8 mesure des durées et dérive son seuil sur la machine du moment : il a rendu rouge une fois sur un exécuteur lent, vert à la reprise, sans qu'aucun code ne change | relancer, et ne conclure à une régression qu'après plusieurs mesures concordantes |
| B8 | Les deux noms de personne n'entrent jamais au dépôt | Le contrôle s'abstient sans ses deux variables, et l'intégration continue ne les pose pas pour les tests (voir A3) | poser les variables et relancer, en connaissant la limite des fragments |
| B9 | Le support tient dans le temps de soutenance et se dit à voix haute | Rien de tout cela n'est mesurable par un contrôle | répétition chronométrée |
| B10 | Le jeu de données engendré ressemble à ce qu'un fichier réel porterait | Le rapport le dit lui-même : la ressemblance est **posée**, non mesurée, et aucune donnée réelle n'existe pour la confronter | rien, tant que la contrainte de confidentialité tient. C'est la limite centrale du travail, et elle est écrite au rapport |

---

## Ce que ce relevé établit

**Onze critères vrais, un faux, deux non encore applicables** en partie A ; **dix critères qu'aucun
contrôle ne peut établir** en partie B.

La réponse à la question du jury est donc chiffrée et documentée : le seul critère de la partie A
qui soit **faux** est A12 — la concordance du registre avec ses commandes —, avec neuf écarts
nommés ; et la partie B dit que dix autres critères ne sont pas tenus par un contrôle du tout, dont
un — B4 — dont un manquement existe aujourd'hui et est nommé.
