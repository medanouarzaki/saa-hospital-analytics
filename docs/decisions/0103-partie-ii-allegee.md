# ADR 0103 — Une deuxième partie allégée, et une annexe pour son détail technique

**Statut.** Accepté.

---

## Contexte

Les trois chapitres de la deuxième partie occupaient vingt-six pages composées : dix pour la
conception du jeu de données, huit pour l'architecture de la chaîne, huit pour la qualité et le
rapprochement. Le corps y portait des inventaires complets (correspondance champ par champ, liste des
distributions, identifiants des tâches du graphe), des concepts de cours exposés en général (schéma en
étoile, dimension historisée, modèle probabiliste et ses deux probabilités, blocage), et quatre idées
dites plusieurs fois : la quarantaine des lignes rejetées, le numéro de téléphone inventé, la limite
des données générées, la performance du rapprochement et son ablation. Le rappel y était défini à
l'étape du blocage, puis redéfini à l'évaluation. Dix-neuf lignes de nombres tapés, déclarées dans
`RESTES_CONNUS` de `tests/test_aucun_nombre_tape.py`, y vivaient sans commande au registre. Aucune
annexe couverte par le contrôle de provenance ne pouvait recevoir un déplacement.

## Décision

### Le budget et l'annexe des compléments techniques

Le budget, en pages composées, est de six pages pour la conception du jeu de données, cinq pour
l'architecture et six pour la qualité et le rapprochement, à une demi-page près. Pour le tenir, les
coupes motivées passent en premier, puis la charte, puis le déplacement. Un contenu vérifié — une
affirmation étiquetée, un tableau, une formule, un inventaire — ne se supprime pas : il descend dans
l'annexe « Compléments techniques », `report/complements_techniques.tex`, avec ses étiquettes, et le
corps y renvoie par `\ref`. Le corps garde le raisonnement et les résultats, l'annexe le détail ; ses
sections suivent l'ordre des chapitres d'où vient leur matière. Le chemin suit celui des autres
annexes rédigées, à la racine de `report/`, parce que la liste `ANNEXES` du contrôle de provenance
nomme des fichiers relatifs à ce répertoire.

L'annexe porte les mêmes déclarations de tête que les chapitres et entre dans `ANNEXES` de
`tests/test_provenance_des_chapitres.py` ; rien d'autre de ce contrôle ne change. Le contrôle des
nombres tapés l'examine déjà, comme toute source rédigée de `report/`. Le contrôle des appels de
chiffres, `tests/test_registre_des_chiffres.py`, ne la parcourt pas : sa portée nomme les chapitres,
l'annexe de correspondance et le support de soutenance. Une entrée appelée par cette seule annexe
porte donc un motif de non-emploi qui le dit, et non un appel que ce contrôle verrait.

### La charte resserrée

Mots courants, le simple avant le savant ; vingt-cinq mots et tournures bannis de la prose réécrite
(afférent, idoine, subséquent, corpus, nonobstant, à l'aune de, prégnant, exhiber, asymétrie,
disjoint, instance, dispositif, appareil, artefact, témoin, mutation, il convient de, il est important
de, crucial, robuste, en somme, en définitive, force est de constater, dès lors, en l'espèce) ;
phrases de douze à vingt mots en moyenne, aucune au-delà de trente sauf énumération ; un paragraphe
par idée, de trois à cinq phrases ; chaque section ouvre sur ce qu'elle montre ; sujet concret, voix
active ; ni formule-choc, ni symétrie rhétorique, ni phrase de chute ; la limite des données
générées dite une fois par chapitre au plus ; aucun discours sur le document hors des transitions ;
un identifiant de code dans la prose seulement s'il est l'objet de la phrase ; ponctuation sobre ;
passé composé pour ce qui a été fait, présent pour ce que montre une figure ; impersonnel. Le mot
« mutation » reste dans les cellules de tableau reprises à l'identique, où il nomme le mouvement de
séjour du logiciel.

### Le motif COURS

Aux cinq motifs de coupe s'ajoute COURS : un concept exposé en général est remplacé par une phrase
qui dit ce qu'il fait dans le projet. Le schéma en étoile, la dimension historisée, le modèle de
rapprochement et le blocage reçoivent chacun cette phrase ; la clé des versions, les deux
probabilités du poids et l'hypothèse d'indépendance descendent en annexe.

### Le rappel

Le rappel est défini une fois, sans référence à une étape : la part des doublons de la vérité
terrain qu'une étape retrouve. Chaque emploi nomme ensuite son étape — le rappel du blocage, le
rappel du modèle, le rappel de la collision exacte.

### Les redites

La quarantaine est dite en entier au chapitre de l'architecture, à la couche intermédiaire où elle
vit ; le numéro de téléphone inventé au chapitre de la conception, parmi les défauts que le
générateur reproduit ; la performance du rapprochement et son ablation au chapitre de la qualité.
Ailleurs, une demi-phrase y renvoie.

### Le vocabulaire et la table des matières

« Engendrer » et ses formes deviennent les formes de « générer » dans les sources rédigées du
rapport et du support de soutenance. Les noms de fichiers, les identifiants et les commandes ne
changent pas. La table des matières s'arrête aux sections (`\setcounter{tocdepth}{1}`) ; les entrées
des pages préliminaires et des trois listes y restent.

### Les registres

Trente-quatre entrées sont ajoutées au registre des chiffres, chacune avec sa commande : les parts
de colonnes et de paramètres par étiquette, les cinq réductions du blocage, les trois rapports
d'accord des colonnes écartées, lus dans les motifs de `linkage/champs.py`, les dix-huit cellules du
tableau du rappel de la collision exacte par variation, recalculées depuis la couche analytique et la
vérité terrain, le milieu de la fourchette des passages aux urgences et le nombre de colonnes typées
de la couche intermédiaire, deux valeurs que la prose écrivait en toutes lettres. Deux valeurs tapées étaient fausses et le registre les corrige : la réduction de la
règle nom de famille et téléphone vaut 99,99945 % et non 99,99948 %, celle de la pièce d'identité
99,99977 % et non 99,99770 %. Les dix-neuf lignes de `RESTES_CONNUS` des trois chapitres sont
retirées. Vingt-huit entrées appelées par la seule annexe portent le motif de non-emploi décrit
ci-dessus. Aucune entrée n'est retirée ; aucune source et aucun élément du relevé ne cessent d'être
cités. Le décompte des sections passe de cinquante à quarante-six.

### Le clone de sécurité du disque virtuel

Le clone de sécurité du disque virtuel de Docker Desktop, conservé sur le disque externe à côté du
disque en service, est supprimé après une remesure du registre à zéro écart. Docker Desktop n'en
dépend pas, et la base vit dans un volume que cette suppression ne touche pas.

## Conséquences

Chaque chapitre de la partie s'ouvre sur la question qu'il traite et se ferme sur une synthèse qui
nomme le chapitre suivant. Le détail technique reste vérifiable au même titre que le corps, dans une
annexe que le contrôle de provenance examine. Les nombres de la partie passent tous par le registre.
Les rapports d'accord se rendent avec les décimales que la valeur porte (1,1 et non 1,10), le
registre n'arrondissant qu'une valeur qui porte plus de décimales que son format.
