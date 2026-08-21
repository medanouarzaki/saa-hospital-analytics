# ADR 0086 — La page de garde reprise : l'aplat retiré, le nom développé

**Statut.** Accepté.

---

## Contexte

L'ADR 0085 avait ancré le titre de la page de garde dans **un aplat très clair de la couleur
d'accent**, sur toute la largeur du bloc de texte, pour qu'il cesse de flotter entre deux filets
fins.

Regardé sur l'image du PDF, cet aplat **alourdissait au lieu d'ancrer**. Un rectangle gris de 52,1 mm
de haut pesait plus que le titre qu'il devait porter, et le fond blanc du reste de la page s'y
arrêtait net.

Par ailleurs, le nom de l'établissement composait avec son sigle et sa ville — « Institut National de
Statistique et d'Économie Appliquée (INSEA), Rabat » —, au même corps que la filière.

## Décision

### 1. L'aplat est retiré ; deux filets épais le remplacent

**Une correction qui ne corrige pas se défait.** L'aplat est retiré et son échec est consigné ici.

L'ancrage tient désormais à deux filets, l'un au-dessus du titre et l'autre en dessous, **à 1,5 pt
contre 0,4 pt** pour les filets fins du document — presque quatre fois plus épais, et l'écart est
voulu : deux filets de même épaisseur que les autres ne tiendraient rien. Ils font **0,62 de la
largeur du texte**, soit 99,1 mm, et sont centrés. Le titre respire entre eux sur fond blanc.

### 2. Le nom de l'établissement, développé, monte d'un cran

Le sigle et la ville disparaissent de la page de garde. Le nom monte du niveau 4 au **niveau 3**,
celui des valeurs — le même que le bloc des noms —, la filière restant au niveau 4, un cran en
dessous.

**La valeur n'est pas réécrite pour autant, et c'est le point.** Le marqueur continue de porter le
nom entier : la page des remerciements et la présentation l'emploient tel quel, et il ne leur
appartient pas moins qu'à cette page. La page de garde en **dérive** la partie qui la concerne, par
une macro à argument délimité qui coupe à la première parenthèse ouvrante :

```latex
\def\nomSansSigle#1(#2\FINSIGLE{#1}
\newcommand{\etablissementDeveloppe}{%
  \expandafter\nomSansSigle\marqueurEtablissementFormation(\FINSIGLE%
}
```

La parenthèse ajoutée par l'appel sert de garde : un marqueur qui n'en porterait aucune rendrait le
marqueur entier au lieu de faire déborder l'analyse. Aucune valeur n'est écrite dans le fichier, et
la règle que la page se donne — « aucune valeur ici, chaque champ vient d'un marqueur » — tient.

### 3. Les espaces fixes sont repris, et restent fixes

Le nom passé au niveau 3 et l'aplat remplacé par deux filets, la page débordait sur une seconde
feuille : 96 pages au lieu de 95. Trois espaces fixes sont réduits — 18 mm → 13 mm deux fois,
14 mm → 11 mm — et un quatrième porté de 20 à 24 mm pour ramener la bande de pied au bas du bloc.
**Aucun ressort élastique n'a été introduit** ; la mesure a réglé chaque valeur sur l'image du PDF.

## Conséquences

Relevé sur l'image du PDF, dans l'état complet — avec les deux noms et les deux logotypes :

| ce qui compose | y (mm) | x (mm) | épaisseur |
|---|---|---|---|
| les deux logotypes | 34,2 – 51,4 | 58,8 – 152,1 | |
| l'établissement, niveau 3 | 63,8 – 69,2 | 29,3 – 180,7 | |
| la filière, niveau 4 | 72,6 – 76,5 | 78,6 – 131,4 | |
| filet fin d'accent | 85,5 – 85,7 | 25,0 – 184,9 | 0,8 pt |
| « Rapport de stage d'application » | 102,4 – 107,6 | 26,8 – 183,0 | |
| **filet épais supérieur** | 119,1 – 119,5 | 55,4 – 154,5 | **1,5 pt** |
| le titre et son sous-titre | 131,9 – 164,0 | 65,1 – 144,9 | |
| **filet épais inférieur** | 175,6 – 176,1 | 55,4 – 154,5 | **1,5 pt** |
| les deux noms | 189,4 – 203,1 | 63,8 – 146,0 | |
| organisme d'accueil | 214,9 – 226,2 | 77,0 – 132,8 | |
| année universitaire | 237,3 – 240,4 | 77,9 – 131,9 | |
| **la bande de pied** | 267,3 – 269,4 | 25,0 – 184,9 | 2,2 mm |

**Aucun aplat ne subsiste sur la page** : hors les logotypes, la seule encre est celle du texte et
des quatre filets.

La page tient sur une feuille dans les quatre états — avec et sans noms, avec et sans logotypes —,
et le document fait **95 pages et 22 boîtes débordantes** dans chacun.

**Les noms ne sont jamais commis.** Le témoin qui a servi à juger la page a été supprimé en fin de
travail, et le contrôle qui cherche les deux noms dans l'ensemble des fichiers suivis est vert.
