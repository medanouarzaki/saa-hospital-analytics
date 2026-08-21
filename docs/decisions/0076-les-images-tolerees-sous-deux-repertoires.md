# ADR 0076 — Les images sont tolérées sous deux répertoires, et l'emplacement est réservé avant d'être rempli

**Statut.** Accepté. Il révise l'`0010` et l'`0070` sur la tolérance, non sur l'interdiction.

---

## Contexte

L'`0010` interdit toute image du système d'information observé. L'`0070` a étendu le refus aux
captures du tableau de bord produit par le projet, et le chapitre correspondant a été écrit sans
aucune. L'interdiction du premier reste entière ; la seconde n'a plus de motif : une capture d'un
écran que ce projet a lui-même produit ne divulgue rien du système observé.

Deux images manquent au document : le logotype de l'établissement de formation, et les captures du
tableau de bord.

**L'état de départ, mesuré.** `tests/test_aucune_image.py` ne regardait que la racine et `report/` :
un fichier image suivi sous `dashboard/`, `docs/` ou `slides/` ne faisait rougir aucun contrôle. Sa
liste d'extensions ignorait `.svg`, `.gif`, `.webp` et `.tif`/`.tiff`. Et `.gitignore` ignorait cinq
motifs d'image sur tout le dépôt, sans aucune négation : un fichier déposé sous un répertoire toléré
n'aurait pas pu être ajouté.

## Décision

### 1. Deux répertoires, et deux seulement

`report/figures/logos/` et `report/figures/tableau-de-bord/`. **La barre oblique finale fait partie
du préfixe** : sans elle, `report/figures/logos-anciens/x.png` passerait, et un témoin négatif
l'établit.

### 2. Le périmètre du contrôle devient le dépôt entier

C'est une **extension de portée**, pas seulement un ajout de tolérance, et elle est éprouvée par
mutation : la même image suivie sous `dashboard/` est rouge avec le contrôle actuel et **verte
avec celui d'avant**, sur le même index.

### 3. La liste des extensions s'étend, sauf à `.pdf`

`.svg`, `.gif`, `.webp`, `.tif` et `.tiff` sont ajoutés — un logotype arrive typiquement en `.svg`.

**`.pdf` en est délibérément absent, et le motif est écrit dans le fichier** : `.gitignore` ignore
déjà `report/*.pdf` et `slides/*.pdf`, et la composition PRODUIT des PDF. Interdire l'extension
ferait rougir le contrôle sur un artefact légitime au lieu de le laisser au dispositif qui s'en
occupe. **La conséquence est assumée : un logotype livré en `.pdf` sous un répertoire toléré passe
sans être vu.**

### 4. Les négations de `.gitignore`, et pourquoi elles mordent

Chaque extension ignorée reçoit sa négation sous les deux répertoires. **La négation ne mord que
parce que les motifs visent des FICHIERS et non un répertoire parent** : si `report/figures/` était
un jour ignoré en tant que répertoire, git cesserait d'y descendre et aucune négation d'un fichier à
l'intérieur ne mordrait. La phrase est dans `.gitignore`.

Vérifié sur des fichiers réels, non sur une lecture du motif : deux images déposées sous les
répertoires tolérés apparaissent à `git status` comme ajoutables, les deux mêmes déposées ailleurs
apparaissent comme ignorées.

### 5. La place est réservée maintenant et remplie plus tard

`report/images.tex` porte `\logoEcole{hauteur}` et `\captureTdb{fichier}{largeur}{légende}{label}`.
Chacune teste l'existence du fichier attendu ; s'il manque, elle compose **un cadre de la taille
déclarée** portant la légende et la mention « à insérer ». Le document compose donc à tous les
stades.

**L'ÉCART RÉSIDUEL EST MESURÉ, ET LA MESURE A CORRIGÉ LE CODE.** Un premier essai alignait le cadre
sur son centre : un document témoin composé avec puis sans l'image montrait la ligne suivante
déplacée de **3,304 pt**. Avec l'alignement par le bas — `\parbox[b]`, comme `\includegraphics`,
dont la ligne de base est le bas de l'image — la même mesure donne **0,395 pt**, la seule épaisseur
du trait inférieur du cadre. Un emplacement rempli déplace donc le texte qui le suit d'un vingtième
de ligne.

`graphicx` est chargé, et le choix est mesuré de deux façons : `kpsewhich` le trouve dans l'ensemble
`graphics`, et surtout `pgfcore.sty` porte à sa ligne 10 `\RequirePackage{graphicx}` — `pgfplots`,
déjà chargé, le tire à lui. **L'image de composition de l'intégration continue le compose donc déjà
à chaque exécution verte**, sans que rien ne l'ait demandé.

## Ce qui a été écarté

**Un seul répertoire pour les deux familles d'image.** Écarté : le logotype et les captures ne
relèvent pas de la même autorisation, et les séparer permet de retirer l'une sans l'autre.

**Un cadre d'attente de taille libre.** Écarté : il annulerait tout l'intérêt du mécanisme, la
pagination bougeant à l'insertion.

## Ce que cette décision ne peut pas voir

**Le contrôle voit un chemin, jamais le contenu d'une image.** Une capture du système
d'information observé déposée sous `report/figures/tableau-de-bord/` passerait, et c'est la
frontière que l'`0010` trace, qu'aucun dispositif automatique ne tient. Elle reste tenue par la
relecture.

**La hauteur réservée par `\captureTdb` vient de la largeur, par un rapport de 16:10 écrit dans le
fichier.** Une capture prise à un autre rapport se compose correctement, mais déplace ce qui la
suit. Aucun contrôle ne vérifie le rapport d'une image déposée.

**Aucune image n'est encore appelée dans le corps du rapport.** `\captureTdb` est éprouvée sur un
document témoin hors du dépôt, jamais sur une page du rapport — rien ici ne touche à aucune prose de
chapitre.
