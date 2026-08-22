# Relevé daté des critères de terminaison

**Relevé du 2026-08-22, mis à jour après fermeture du critère A12.** Dépôt à `939d466` puis à la
branche de correction, sur la branche principale.

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
| A13 | **Aucun chiffre littéral n'est composé hors d'un appel au registre**, hors les quarante-deux occurrences nommées | `pytest -q tests/test_aucun_nombre_tape.py` | `13 passed` | **vrai pour toute occurrence nouvelle** — voir B4 |
| A12 | **Les valeurs du registre sont celles que leurs commandes rendent aujourd'hui** | `python docs/chiffres/mesurer.py --verifier` | `266 entrée(s) et 13 série(s) confrontée(s), 0 écart(s)` | **vrai** |

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

### A12 — le critère était FAUX, il est fermé, et sa cause est une propriété du dispositif

**Neuf écarts au relevé du 2026-08-21. Zéro aujourd'hui.** Sortie brute :

```
266 entrée(s) et 13 série(s) confrontée(s), 0 écart(s)
```

**Ce que la cause mesurée a montré, et qui n'était pas ce qu'on croyait.** Six des neuf écarts ne
venaient pas d'une valeur devenue fausse : ils venaient d'une **commande devenue aveugle**. Le
tableau de correspondance et le relevé des écrans étaient descendus en annexe, et quatre commandes
cherchaient encore leur matière sous `report/chapitres/` ; cinq tracés du tableau de bord étaient
passés par une fonction commune, et deux commandes ne comptaient plus que les formes intégrées. Les
valeurs consignées — 5, 16, 6, 17, 23 — étaient **justes**. Corriger la commande les a rendues
vraies de nouveau, sans qu'aucune valeur du rapport ne bouge.

Deux écarts seulement étaient une vraie dérive de valeur : le décompte des fichiers de contrôle et
celui des sections du rapport. Un troisième — le volume de l'instantané — n'était pas une dérive du
tout : il varie d'un rafraîchissement à l'autre, et il a concordé de lui-même à la mesure suivante.

### CE QUI DOIT ÊTRE FAIT AVANT TOUTE REMISE

**`docs/chiffres/mesurer.py --verifier` est dû avant toute remise, et il est périmé par tout travail
qui déplace de la matière.**

Ce n'est pas une consigne d'hygiène, c'est une **propriété du dispositif** : cette vérification
ouvre la base et compare des valeurs mesurées sur la période entière, quand l'exécuteur de
l'intégration continue n'engendre que trois mois. Elle ne peut pas être un travail de la chaîne, et
elle ne tourne donc qu'à la main.

Les neuf écarts n'étaient pas nés d'une négligence : ils étaient nés de ce que personne ne l'avait
lancée depuis plusieurs campagnes de rédaction, et que **déplacer une section, descendre un tableau en
annexe ou changer la forme d'un appel périme une commande sans rien casser de visible**. Toute campagne de
rédaction périme donc cette vérification, par construction.

---

## Partie B — les critères qu'aucun contrôle ne peut établir

Chacun est nommé avec ce qui le vérifierait à la main.

| # | Critère | Pourquoi aucun contrôle ne l'établit | Ce qui le vérifie |
|---|---|---|---|
| B1 | Le document composé ne porte pas plus de boîtes débordantes qu'avant | **Aucun contrôle ne lit le PDF ni le journal de composition.** La composition n'échoue que sur une erreur, jamais sur un débordement | composer, compter `Overfull` au journal — 22 au rapport, 0 au support ce jour |
| B2 | Aucune planche ne déborde, aucune valeur n'y est illisible de loin | idem : rien ne lit le PDF | rendre chaque planche en image et la lire réduite au quart |
| B3 | Aucune page ne porte de ligne veuve, de titre orphelin ni de coupure malheureuse | idem | relecture en image, page par page |
| B4 | **Aucun nombre n'est tapé en clair dans une source du rapport** | Le contrôle du registre vérifie la **correspondance** entre appels et entrées ; il ne cherche pas les chiffres littéraux. `tests/test_aucun_nombre_tape.py` le fait désormais, mais **quarante-deux occurrences existantes y sont nommées une par une** : elles restent des nombres tapés | corriger chacune demande une entrée au registre avec la commande qui la produit, ces valeurs venant de sources publiées dont la valeur vit dans la prose d'un fichier de sources. Une seule a été corrigée, celle du tableau d'ablation |
| B5 | Un fait cité d'une source est cité fidèlement | Aucun contrôle ne lit la source citée | relecture contre le texte source. Un cas a été trouvé et corrigé : le tableau du chapitre premier rangeait le recouvrement parmi les missions de l'article 35, que le texte ne lui donne pas |
| B6 | Une capture d'écran est à jour et lisible à sa largeur composée | Aucun contrôle ne lit une image ni ne la date | comparer la capture à l'application, et mesurer sa résolution composée. Un cas a été trouvé : une capture antérieure à la mise en français des dates |
| B7 | La phase exclusive du rafraîchissement reste une opération de catalogue **sur une machine chargée** | Le contrôle A8 mesure des durées et dérive son seuil sur la machine du moment : il a rendu rouge une fois sur un exécuteur lent, vert à la reprise, sans qu'aucun code ne change | relancer, et ne conclure à une régression qu'après plusieurs mesures concordantes |
| B8 | Les deux noms de personne n'entrent jamais au dépôt | Le contrôle s'abstient sans ses deux variables, et l'intégration continue ne les pose pas pour les tests (voir A3) | poser les variables et relancer, en connaissant la limite des fragments |
| B9 | Le support tient dans le temps de soutenance et se dit à voix haute | Rien de tout cela n'est mesurable par un contrôle | répétition chronométrée |
| B10 | Le jeu de données engendré ressemble à ce qu'un fichier réel porterait | Le rapport le dit lui-même : la ressemblance est **posée**, non mesurée, et aucune donnée réelle n'existe pour la confronter | rien, tant que la contrainte de confidentialité tient. C'est la limite centrale du travail, et elle est écrite au rapport |

---

## Ce que ce relevé établit

**Treize critères qu'un contrôle établit : onze vrais, deux non encore applicables.** Le seul qui
était faux — A12, la concordance du registre avec ses commandes — **est fermé** : la remesure rend
zéro écart, et sa sortie brute est ci-dessus.

**Dix critères qu'aucun contrôle ne peut établir**, nommés un par un. L'un d'eux — B4 — a reçu son
contrôle dans l'intervalle, mais il porte une dette explicite : **quarante-deux chiffres littéraux
subsistent dans les sources du rapport**, nommés ligne par ligne dans le contrôle lui-même. Toute
occurrence nouvelle est rouge ; celles-là sont comptées comme la dette qu'elles sont.

**La réponse à la question du jury.** Un critère avait bien été déclaré atteint sans l'être. Il y en
avait **un**, et sa cause n'était pas une négligence : la vérification qui l'établit n'est pas
exécutable en intégration continue, et tout travail de rédaction qui déplace de la matière la
périme. Elle est désormais écrite comme due avant toute remise.
