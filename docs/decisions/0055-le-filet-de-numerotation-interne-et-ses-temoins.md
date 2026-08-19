# ADR 0055 — Un filet par motif textuel n'est éprouvé que si chaque forme a son témoin, dans les deux sens

**Statut.** Accepté.

---

## Contexte

### Le fait mesuré

Le dépôt interdit toute trace du découpage interne du travail dans ses fichiers suivis, et un
contrôle permanent, `tests/test_aucune_trace_processus.py`, est censé la tenir. **Il était vert.**

Une revue manuelle a mesuré ce qu'il laissait passer : **135 occurrences sur 44 fichiers suivis**.

| Forme | Occurrences | Le filet la voyait-il ? |
|---|---|---|
| unité de travail désignée — « ce lot », « au lot », « du lot » | 108 | **non** : son motif exigeait un chiffre après le mot |
| unité de travail nommée — « lot de correction », « lot de vraisemblance » | 16 | **non** : même raison |
| étape numérotée — « à l'etape 3 », « voir Etape 5 » | 8 | **non** pour la graphie sans accent ; son motif exigeait « étape » accentué |
| renvoi décimal interne — « relevé au 1.2 », « mesure du 1.3 » | 3 | **non** : son motif de sous-étape attendait chiffre-point-**lettre** |
| unité de travail numérotée — « lot 12 », « bloc 3 » | 0 | oui, et c'est la seule forme qu'il cherchait |

Une cinquième cécité, découverte en corrigeant : **le filet lisait ligne à ligne**. Six occurrences
coupées par un retour à la ligne — « touchées par ce ⏎ lot » — échappaient à la fois au motif et au
découpage.

**Le filet cherchait donc une forme sur cinq, et a été cru sur son silence depuis l'origine.** La
règle qu'il devait tenir est en vigueur depuis le début du projet.

### Ce que cela apprend, et c'est le point qui vaut d'être écrit

> **Un contrôle par motif textuel ne prouve rien tant que chaque forme qu'il doit voir n'a pas son
> témoin positif, et chaque forme qu'il ne doit pas voir son témoin négatif.**

La première moitié était connue et écrite dans ce dépôt — « un contrôle par motif textuel se trompe,
le tester d'abord contre un cas positif connu ». Elle a été appliquée **une fois, sur une forme**, et
le contrôle a ensuite été cru sur son silence. Un témoin unique n'éprouve que la branche qu'il
traverse.

La seconde moitié est apparue en armant le filet, et elle a immédiatement mordu. Le motif élargi
attrapait le mot **bloc** dans son sens d'hôpital et d'écriture : `bloc opératoire`, `bloc de code`,
`bloc SQL`. **Quarante emplois légitimes**, tous vrais, que la correction aurait effacés. Le motif a
été resserré au seul mot « lot » — comme unité de travail, « bloc » n'apparaît jamais qu'avec un
nombre, ce qu'une autre forme couvre déjà — et le cas est devenu un témoin négatif permanent.

**Un filet qui efface des références vraies est pire qu'un filet aveugle** : le premier produit des
erreurs, le second en laisse passer.

## Décision

**1. Le filet cherche les cinq formes, sur le contenu entier de chaque fichier.** La lecture ligne à
ligne est abandonnée ; le numéro de ligne est reconstitué depuis la position de la correspondance,
pour que le message reste actionnable.

**2. Les témoins vivent dans le contrôle, pas dans un rapport.** Deux propriétés neuves les
exercent : l'une vérifie que chaque forme reconnaît son témoin positif, l'autre qu'aucune des sept
catégories de référence légitime n'est reconnue — numéro de version, article de règlement, référence
de source, identifiant d'enregistrement de décision, renvoi de chapitre, emploi métier du mot,
bloc de code. Sans elles, l'épreuve disparaîtrait avec le travail qui l'a faite.

**3. Les 135 occurrences sont corrigées, une ligne à la fois.** La référence de travail est
remplacée par ce qu'elle désigne réellement — le nom de la chose, jamais son rang. « L'étape de
chargement » est acceptable ; « la phase deux » ne l'est pas.

**4. Aucune tolérance n'est posée**, parce qu'aucune occurrence indécidable n'a été trouvée. Le
classement a été fait par lecture de chaque ligne et de son contexte : les 135 désignent toutes une
unité, une étape ou un renvoi du travail. Aucune n'est un numéro de version, un article de norme, un
identifiant d'enregistrement ou un renvoi de chapitre — et ce n'est pas un hasard, c'est le motif qui
les exclut par construction, ce que les sept témoins négatifs établissent.

Une mesure a permis de trancher les huit « étape N », qui étaient les plus discutables : **aucun
document de cadrage n'est suivi par le dépôt** — l'ADR `0002` l'écrit — et `report/` ne porte aucune
étape numérotée. Ces renvois ne pouvaient donc désigner qu'une étape du travail.

## Ce qui a été écarté

**Corriger sans classer.** Le motif trouve 135 correspondances ; les remplacer en masse aurait
effacé toute référence légitime qu'il aurait attrapée — et il en attrapait quarante avant d'être
resserré. Le classement est ce qui rend la correction sûre, et il précède l'écriture.

**Armer le filet avant de corriger.** Il serait devenu rouge sur 135 occurrences sans qu'aucune
écriture ne puisse le verdir, et aurait bloqué toute publication. L'ordre — classer, corriger,
armer — n'est pas une commodité.

## Ce qui aurait invalidé cette décision

**Que le motif ne puisse pas distinguer une référence de travail d'une référence légitime.** Le filet
aurait alors été inutilisable, et la relecture manuelle serait restée le seul recours — ce qu'il
aurait fallu écrire plutôt que de livrer un contrôle dangereux.

Il le peut, et les sept témoins négatifs l'établissent, à une distinction près qui a demandé une
mesure : le mot « bloc » ne peut pas être cherché sans nombre, ses quarante emplois du dépôt étant
tous légitimes. Cette restriction est écrite dans le contrôle, avec son motif.
