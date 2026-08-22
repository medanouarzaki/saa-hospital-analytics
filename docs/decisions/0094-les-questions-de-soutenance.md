# ADR 0094 — Les questions de soutenance, et deux chiffres arrondis à la main

**Statut.** Accepté.

---

## Contexte

Le rapport et le support sont terminés. Ce qui manquait était le jeu de questions qu'un jury posera,
avec les réponses que le projet peut soutenir — et surtout avec celles qu'il ne peut pas.

## Décision

### 1. Trente questions, en neuf familles, sous `docs/`

`docs/questions_de_soutenance.md`, à côté du relevé des critères. Il n'entre ni au rapport ni au
support : **ce n'est pas un document destiné au jury, c'est une préparation.**

| famille | questions |
|---|---|
| la nature des données | 4 |
| la méthode | 4 |
| le rapprochement d'identités | 4 |
| l'analyse de l'activité | 3 |
| le périmètre et l'honnêteté | 3 |
| ce que le relevé des critères ouvre | 3 |
| les nombres tapés | 2 |
| les questions techniques d'un jury d'ingénierie | 5 |
| **celles auxquelles le projet répond mal** | **2** |

Chaque question porte sa formulation telle qu'elle serait posée, la réponse en trois à six phrases à
la première personne, et **ce sur quoi elle s'appuie** — une mesure, une source ou un enregistrement
de décision.

### 2. Le principe : dire la limite avant que le jury la trouve

Un jury qui découvre seul la faiblesse d'un résultat cesse de croire les autres. Aucune réponse n'est
une manœuvre. Les trois qui portent le plus :

**« Vos données sont inventées, qu'est-ce que votre analyse démontre ? »** — la distinction entre ce
qu'un résultat *démontre* (une capacité) et ce qu'il *établit* (un fait), la seconde moitié étant
fausse sur un jeu construit.

**« Vous avez des centaines de contrôles, qu'est-ce que cela prouve ? »** — rien en soi. Ce qui vaut,
ce sont les mutations, et une mutation restée verte révèle presque toujours un contrôle défectueux.

**« Qu'est-ce qui, dans votre travail, ne marche pas ? »** — quatre défauts nommés : deux tables qui
décrivent le même épisode avec des durées tirées indépendamment, un indicateur affiché faux d'un
facteur 2,4986 sous un contrôle vert, les nombres tapés qui subsistent, et un aplat de page de garde
retiré parce qu'il n'ancrait pas.

### 3. Deux questions que le projet assume de mal traiter

Elles sont écrites pour ne pas être découvertes devant le jury. **Le tableau de bord n'a été utilisé
par personne du service** — aucun retour d'usage, ni sur l'ergonomie ni sur la pertinence des
indicateurs. Et **la durée d'un traitement quotidien de bout en bout n'a jamais été mesurée** : une
seule durée de la chaîne l'a été, celle du rafraîchissement de l'instantané, parce qu'elle
conditionnait une propriété à démontrer.

## Conséquences

**Vingt-cinq chiffres cités dans les réponses ont été confrontés au rendu du registre, et deux ont
dû être corrigés.** J'avais écrit « 66,74 % » là où le registre rend `66,7414`, et « 3,99 % » là où
il rend `3,9878` : deux **arrondis faits à la main**, c'est-à-dire exactement la faute que le
registre existe pour empêcher, commise dans le document qui explique pourquoi elle est grave. Les
deux portent la valeur du registre.

**Un chiffre de la consigne était faux, et la mesure le corrige.** Elle annonçait « quarante et un
nombres tapés qui restent » ; le contrôle en déclare **quarante-deux**, et en trouve quarante-deux.
Le compte de quarante et un venait d'un rapport antérieur qui avait soustrait la correction d'une
occurrence de la liste finale, alors que cette occurrence n'y figurait déjà plus. Les réponses
portent quarante-deux.

**Les deux interdits sont tenus.** Aucune réponse n'affirme qu'une recherche rendant plusieurs
résultats proches a été observée — celle qui en traite l'énonce comme une **négation** explicite. Et
aucune ne décrit la composition du service : celle qui l'évoque dit qu'elle est **inconnue**, et que
le rapport refuse de la supposer.
