# ADR 0090 — La présentation de soutenance, et une portée de contrôle qui s'étend au support

**Statut.** Accepté.

---

## Contexte

Le support de soutenance était un squelette : huit planches vides portant chacune le titre d'une
section, plus une planche de titre et une table des matières. Le rapport, lui, est terminé.

## Décision

### 1. Vingt et une planches, une idée par planche

La trame est celle que l'auteur a arrêtée, et son ordre ne change pas. Le titre de chaque planche
**énonce l'idée**, jamais le thème : « Un profil du logiciel sert une mission que le règlement place
ailleurs », « Un champ renseigné n'est pas un champ juste », « Un modèle qui classe encore juste peut
avoir cessé de discriminer ».

Trois planches sont longues et assumées — l'architecture, la ventilation du rappel de la ligne de
base, l'ablation. Les autres portent une idée et ce qui l'établit.

**Les surimpressions ont été retirées.** Quatorze `\pause` composaient 35 pages pour 21 planches :
un jury qui lit le PDF y voyait la même planche plusieurs fois. Le support compte désormais autant
de pages que de planches.

### 2. Aucun nombre n'est tapé, et le contrôle le tient désormais

Chaque valeur vient du registre par son identifiant : le support charge `../report/chiffres.tex`,
le fichier que le registre produit, exactement comme le rapport. **Quarante-neuf identifiants** sont
appelés, tous préexistants — aucune entrée n'a été ajoutée au registre.

**Mais le contrôle du registre ne regardait pas ce répertoire.** Sa portée était
`report/chapitres/*.tex` plus une annexe nommée ; une planche pouvait donc écrire un nombre à la
main, ou appeler un identifiant inexistant, sans qu'aucun code ne le voie. Le support serait devenu
le seul document du projet où un chiffre échappe au registre — et c'est par cette voie exacte que
cinq valeurs du projet sont devenues fausses.

**La portée suit la matière.** `tests/test_registre_des_chiffres.py` reçoit une liste `PLANCHES`,
déclarative comme celle des annexes, et deux témoins :

- un **témoin positif**, qui vérifie que le support est bien au périmètre et qu'il y appelle au
  moins un chiffre — sans quoi retirer la liste laisserait tous les autres contrôles verts ;
- un **témoin négatif**, qui vérifie que la portée nomme des fichiers et ne ramasse pas un
  répertoire : ni le journal de composition, ni la table des matières, ni le fichier de styles n'y
  entrent.

Une troisième épreuve ferme la voie par laquelle un fichier renommé sortirait du périmètre en
silence : **un fichier déclaré et absent du disque est rouge.**

Le point aveugle est écrit plutôt que découvert : un second fichier de planches non ajouté à
`PLANCHES` échapperait au contrôle.

### 3. Les styles vivent sous le répertoire du support

`slides/styles.tex` porte la couleur d'accent — la même que la page de garde du rapport, à
l'identique — et les styles de tracé. Le support n'emprunte pas `report/images.tex` : ce fichier
porte l'apparat des figures du rapport, dont une planche n'a que faire, et il déclare ses couleurs
par des noms que le document principal du rapport définit.

## Conséquences

**Vingt et une planches, zéro boîte débordante.** Le rapport reste à 98 pages et 22 boîtes : aucun
de ses fichiers n'est touché.

**La couverture du répertoire, contrôle par contrôle.** Trois des quatre y passaient déjà, parce
qu'ils lisent `git ls-files`, donc l'arbre entier ; le quatrième ne le faisait pas.

| contrôle | ce qui établit sa portée | verdict |
|---|---|---|
| noms de personne | `git ls-files`, ligne 117 | couvrait déjà |
| absence d'image | `git ls-files`, ligne 66 | couvrait déjà |
| trace de processus génératif | `git ls-files`, ligne 141 | couvrait déjà |
| registre des chiffres | `CHAPITRES.glob("*.tex")` plus `ANNEXES` | **ne couvrait pas — étendu** |

**Une valeur du rapport n'a pas pu passer au support.** La capacité litière annoncée par voie de
presse n'a pas d'identifiant au registre ; lui en créer un aurait obligé à réécrire
`report/chiffres.tex`, que le registre produit et qui n'était pas dans la liste fermée. La planche
des volumes porte donc la seule capacité fonctionnelle, celle du recueil ministériel, et n'énonce
aucun rapport entre les deux — ce qu'aucune planche ne doit faire de toute façon.

**Les valeurs longues se composent en pleine précision, et c'est illisible de loin.** La F-mesure de
la ligne de base compose seize décimales, les écarts de poids douze. C'est le rendu du registre, et
le rapport les compose à l'identique ; les arrondir sur une planche reviendrait à taper un nombre.
Le défaut est signalé et non corrigé.
