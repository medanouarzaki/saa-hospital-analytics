# ADR 0109 — La remise : état composé, mise en page, conformité au référentiel et version figée

**Statut.** Accepté.

---

## Contexte

Le rapport est rédigé, contrôlé et composé à chaque intégration. Restaient quatre choses avant de le
remettre : établir que le document remis compose bien l'état de remise ; corriger sa mise en page sans
toucher au texte ; dire, consigne par consigne, ce qu'il respecte du référentiel de la filière ; et
figer une version que les liens du rapport désignent sans ambiguïté.

## Décision

### L'état de remise

Ce que l'auteur remet est l'artefact « rapport » de l'intégration continue sur la fusion finale.
L'étape qui précède sa composition écrit `report/noms.tex` depuis un secret du dépôt : le nom de
l'auteur et l'état `remise`. Le fichier suivi, `report/marqueurs.tex`, garde l'état `brouillon` et un
marqueur nominatif vide, comme son contrôle l'exige : le dépôt public ne porte aucun nom, l'artefact le
porte. La page de garde de l'artefact a été lue : le nom y figure, et aucune mention de version de
travail. Le mécanisme n'a pas changé.

La propriété qui exige, en état de remise, que toute source citable soit citée ou déclarée non
employée lit l'état dans le fichier suivi : elle s'abstient donc toujours, intégration continue
comprise. C'est consigné, non corrigé.

### La mise en page

Le texte n'a pas changé. Trois moyens, dans cet ordre :

1. **Réglage global.** La pénalité de ligne veuve passe à 10000 : une fin de paragraphe ne reste plus
   seule en haut d'une page. La pénalité de ligne orpheline reste celle du noyau : portée à 10000,
   elle repoussait la fin d'une synthèse de chapitre sur une page sinon vide. Le bas de page reste
   irrégulier (`\raggedbottom`, la règle de la classe en recto seul) : une page plus courte d'une
   ligne vaut mieux que des blancs étirés entre paragraphes.
2. **Réglage local d'un tableau.** Le tableau des étiquettes de provenance compose ses deux colonnes
   de texte en fer à gauche, et sa première colonne s'élargit : ses cellules n'ont plus d'espaces
   béants, et la seule boîte trop pleine du document disparaît.
3. **Dernier recours, écarté.** Deux synthèses de chapitre débordent de deux et de trois lignes sur
   une page sinon vide. Agrandir la page qui les commence (`\enlargethispage`) les y faisait tenir,
   mais leur dernière ligne recouvrait alors le numéro de page : le réglage est retiré, et les deux
   courtes pages restent.

Ce qui reste, et pourquoi : la dernière entrée de la liste des figures et celle de la liste des
tableaux passent chacune en tête de la page suivante, parce que les listes s'enchaînent sur les mêmes
pages ; agrandir la page les rattrape, mais fait alors passer le titre de la liste suivante sous le
pied de page. Les annexes produites (dictionnaire, relevé des écrans) gardent quelques cellules
étirées et une fin d'annexe courte : elles sont rendues par leur générateur, et ne s'écrivent pas à la
main.

### La conformité au référentiel

`docs/releve_des_criteres.md` reçoit une section datée, « Conformité au référentiel de la filière » :
chaque consigne citée par son texte, la commande qui l'établit, sa sortie et un verdict. Vingt-sept
consignes sur vingt-neuf sont respectées ; deux le sont partiellement — le temps des verbes du bilan
et l'équilibre des chapitres en pages. Les consignes de jugement sont établies par une mesure qui les
approche, nommée dans le relevé.

### La version figée

Les liens du rapport vers le dépôt désignent l'étiquette `rapport-de-stage-v1`, et non la branche
principale : un lecteur du rapport remis lit les fichiers tels qu'ils étaient à la remise. L'étiquette
est posée sur la fusion finale, et une publication du dépôt sur cette étiquette porte le rapport
composé en pièce jointe.

## Conséquences

Une modification ultérieure du dépôt ne change ni le rapport remis ni ce que ses liens désignent. Une
nouvelle remise demanderait une nouvelle étiquette, et des liens qui la désignent.
