# ADR 0082 — La réécriture des six derniers chapitres, et deux portées qui suivent la matière

**Statut.** Accepté.

---

## Contexte

Six chapitres et la conclusion n'avaient jamais été réécrits. Les travaux précédents les avaient
rognés au mot ; leur registre restait celui d'un dossier écrit contre une relecture adverse, avec
des exposés de méthode que le lecteur n'a pas à connaître et des termes techniques jamais définis.

## Décision

### 1. Le fichier de licence garde le nom de l'auteur, et l'exclusion est étroite

`LICENSE` porte le nom de l'auteur dans sa ligne de droit d'auteur. **C'est la fonction d'une
licence : elle nomme le titulaire des droits**, et le retirer viderait le fichier de son sens.

`tests/test_aucun_nom_de_personne.py` écarte donc `LICENSE` **pour le seul nom de l'auteur**. Le nom
de l'encadrant y est cherché comme partout ailleurs, et l'y déposer est rouge — éprouvé par
mutation. Une exclusion générale du fichier aurait ouvert une porte pour les deux noms au lieu d'un.

Le balayage est désormais fait **variable par variable** et non sur l'union des fragments : c'est ce
qui permet d'écarter un fichier pour un nom sans l'écarter pour l'autre.

### 2. Le tableau de correspondance descend en annexe, et deux contrôles suivent

Le tableau qui met en regard les relations injectées et les conclusions du chapitre d'analyse
occupait plus de deux pages du corps pour une matière qu'on consulte au cas par cas. Il descend en
annexe ; le chapitre garde à sa place un paragraphe qui dit ce que la correspondance établit.

**Deux contrôles voient leur portée suivre la matière**, comme aux trois travaux précédents :

- `tests/test_correspondance_relations_conclusions.py` lit désormais **deux fichiers** — les marques
  de conclusion restent dans la prose du chapitre, les lignes de correspondance sont en annexe. Les
  deux chemins sont écrits en clair. Sans le second, toute relation serait déclarée non reprise et
  le contrôle rougirait à tort.
- `tests/test_registre_des_chiffres.py` porte une liste d'annexes, parce que le tableau emporte
  trente appels de chiffre avec lui.

**Le décompte des identifiants couverts est identique des deux côtés du déplacement : 262 avant,
262 après.** Aucun n'était exclusif au tableau, et aucun ne l'est devenu.

### 3. Dix termes techniques reçoivent leur unique phrase d'explication

Quarantaine, schéma en étoile, idempotence, rattrapage, blocage, poids de correspondance,
instantané, orchestration. Chacun à sa première apparition, et une seule fois dans tout le rapport.

**L'idempotence et le rattrapage s'expliquent par un cas concret** plutôt que par leur définition :
le fichier du 12 mars rechargé après correction, les journées du 12, 13 et 14 mars rattrapées dans
n'importe quel ordre.

### 4. Trois emplacements de capture sont posés

Le chapitre du tableau de bord porte trois appels de la commande d'emplacement réservé, à leur place
et à leur largeur définitives. Ils composent leur cadre vide en attendant les captures, et la
pagination ne bougera presque pas à l'insertion — la commande réserve la hauteur.

### 5. Trois renvois consignés au travail précédent sont honorés

L'observation du numéro de téléphone rempli d'un numéro inventé est reprise **par renvoi** au
chapitre de conception, au chapitre du rapprochement et au chapitre des recommandations. Jamais
réécrite : chaque reprise pointe vers l'observation et en tire ce que sa section en fait.

C'est la troisième qui compte le plus. Une recommandation d'envoyer des rappels suppose un numéro
juste ; la première mesure à prendre n'est donc pas l'envoi, mais le taux d'aboutissement des
envois.

## Ce que le budget de pages est devenu

La cible était trente-neuf pages pour les sept pièces. **La mesure en donne cinquante, comme au
départ**, et l'écart s'explique entièrement :

| | pages |
|---|---|
| départ | 50 |
| coupes de registre et de paragraphe | −5 |
| trois emplacements de capture, réservés | +3 |
| dix définitions de termes techniques | +1 |
| trois renvois consignés | +1 |
| **mesuré** | **50** |

Les additions étaient toutes demandées. **Ce qui a été coupé l'a été sur la couche défensive**, et
ce qui reste est ce que la consigne protège : des chiffres avec leur source, des limites dans des
sections de limites, des observations de terrain, et vingt-deux conclusions chiffrées.

Atteindre trente-neuf aurait demandé d'y toucher, et la consigne l'interdit dans les mêmes termes
qu'elle fixe la cible.

## Ce qui a été écarté

**Descendre l'exposé du modèle probabiliste en annexe.** Écarté : allégé plutôt que déplacé. Le
lecteur a besoin de savoir qu'on compare des champs, qu'on en tire un poids et qu'un seuil décide ;
c'est désormais ce que le chapitre dit, et pas davantage.

**Compter les emplacements de capture comme du contenu.** Écarté : ils réservent une place, ils ne
la remplissent pas. Le rapport de ce travail les compte séparément.

## Ce que cette décision ne peut pas voir

**Rien ne vérifie qu'un renvoi consigné a été honoré.** Aucun contrôle ne lie une observation à ses
emplois, et les trois reprises auraient pu ne jamais être écrites sans qu'aucun rouge n'apparaisse.

**Rien ne vérifie qu'une capture sera prise au bon format.** La commande réserve une hauteur déduite
d'un rapport écrit dans son code ; une capture d'un autre rapport se composera correctement et
déplacera ce qui la suit.

**Le contrôle des noms restera rouge sur onze fichiers le jour où le secret de l'auteur sera posé**,
pour une raison qui n'est pas une fuite : les trois mots de ce nom sont des prénoms et noms courants,
et le générateur les tire dans ses réserves de noms. C'est mesuré et consigné au rapport de ce
travail ; l'exclusion décidée ici ne couvre que `LICENSE`.
