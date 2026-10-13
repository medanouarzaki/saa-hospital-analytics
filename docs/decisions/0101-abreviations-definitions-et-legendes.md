# ADR 0101 — Abréviations, définitions et réglages de légende

**Statut.** Accepté.

---

## Contexte

Le rapport employait quatre sigles — IPP, MPI, SMS, SQL — sans liste des abréviations, et aucun
n'était développé à sa première occurrence : les deux premiers l'étaient un paragraphe après le
tableau qui les portait, les deux autres jamais. Trois grandeurs de l'évaluation du rapprochement —
précision, rappel, F-mesure — n'étaient définies nulle part, et la table de faits ne l'était que
vingt et une pages après son premier emploi. Les titres de tableau se composaient « Table », la liste
des figures s'intitulait « Table des figures », les titres de longtable n'avaient ni la largeur ni le
séparateur des autres, et un titre posé au-dessus d'un tableau touchait son filet. Ni la liste des
figures ni celle des tableaux n'entraient à la table des matières.

Le motif de citation du contrôle de provenance et de l'entrée `sources-non-citees` du registre des
chiffres lisait `\cite{…}` et ne voyait pas `\cite[…]{…}` : depuis que les localisations dans une
source s'écrivent en argument optionnel de la citation, une source citée seulement avec sa page aurait
été tenue pour non citée.

## Décision

### Le registre des abréviations

`docs/abreviations/abreviations.yml` porte une entrée par sigle — le sigle, son développé, et le motif
de non-emploi s'il n'est employé nulle part — et une section d'exceptions : les jetons capitaux qui ne
sont pas des abréviations, chacun avec son motif (NET, fragment du nom du progiciel Hosix.NET ; SIVSA,
raison sociale de l'éditeur). `docs/abreviations/to_tex.py`, qui porte un analyseur d'arguments, en
écrit `report/liminaires/abreviations.tex` ; ce fichier ne s'écrit jamais à la main.

L'ordre de la liste est celui d'une clé de tri écrite dans le générateur : le sigle sans ses accents
(décomposition puis retrait des diacritiques), sans égard à la casse, puis, à égalité, la chaîne brute,
pour que l'ordre soit total.

### Ce qu'est un sigle

Un jeton de la prose composée qui commence par une capitale et en porte au moins deux, chiffres et
tirets admis. Ne sont pas cherchés : les arguments des commandes que le contrôle des nombres tapés
retire déjà, ceux de `\texttt`, `\cite`, `\ref`, `\label`, `\chiffre`, `\serie`, `\releve`,
`\convention`, des annonces du plan, de `\pageref`, `\url` et `\href` ; les environnements de tracé ;
les commentaires ; les fichiers produits.

### La première occurrence

Dans l'ordre d'inclusion du document, à partir de l'introduction, la première occurrence de chaque
sigle est dans la prose — jamais dans une cellule de tableau, un titre d'objet ou un libellé d'écran
reproduit, où le développé n'entre pas — et dans la même phrase que son développé. IPP et MPI sont
développés dans la phrase qui appelle le tableau de la recherche d'identifiant, SMS dans celle qui
appelle l'extrait de la fiche patient, SQL dans la phrase qui ouvre les briques de la chaîne ; le
paragraphe qui définissait IPP et MPI emploie désormais le sigle seul. Le résumé et l'abstract
précèdent la liste et doivent rester courts : ils sont exemptés.

### Les définitions

- **Rappel**, à son premier emploi, au blocage : la part des paires de doublons de la vérité terrain
  que les paires candidates retiennent.
- **Précision**, au seuil retenu : la part des paires que le modèle déclare doublons et qui le sont
  dans la vérité terrain. **F-mesure** : la moyenne harmonique de la précision et du rappel, qui ne
  s'élève que si les deux s'élèvent ensemble.
- **Table de faits**, à son premier emploi au chapitre de cadrage : une table dont chaque ligne
  enregistre un événement de l'activité, un passage ou une facture, avec ses mesures. La définition
  tardive du chapitre de l'architecture devient un emploi du terme.

Provenance : les trois grandeurs de l'évaluation, la page « Edge Metrics » de la documentation de
Splink (S-51), qui les rapporte à une vérité terrain ; la table de faits, la page « Fact Table
Structure » du Kimball Group (S-52). Les deux contenus ont été lus ; aucune formule n'est recopiée,
la citation y renvoie.

### Les noms et les légendes

`\tablename` vaut « Tableau », `\listfigurename` « Liste des figures », `\listtablename` « Liste des
tableaux », par `\addto\captionsfrench`, moyen que la documentation de babel-french donne pour ses
traductions. Le paquet `caption`, de `collection-latexrecommended`, uniformise le séparateur (tiret
demi-cadratin), le corps et la largeur de tous les titres, et pose un espace sous un titre placé
au-dessus d'un tableau. La largeur d'un titre de longtable se règle par `caption`, au moment de
composer : `\setlength{\LTcapwidth}{\linewidth}` dans le préambule prenait la largeur d'avant
`geometry` — 390 pt sur un document témoin.

### Les trois listes à la table des matières

La liste des figures, la liste des tableaux et la liste des abréviations entrent à la table des
matières, comme les remerciements, le résumé et l'abstract, chacune avec la page où elle commence.

### Les motifs de citation

Le contrôle de provenance et l'entrée `sources-non-citees` lisent `\cite{…}`, `\cite[…]{…}` et
`\cite[…][…]{…}` ; une commande dont le nom commence par `cite` n'est pas prise pour elle.

## Conséquences

Un sigle ajouté au texte sans entrée au registre, une entrée sans emploi, une liste retouchée à la
main ou mal ordonnée, un sigle employé avant d'être développé font échouer
`tests/test_abreviations.py`, sans base et sur un clone frais.
