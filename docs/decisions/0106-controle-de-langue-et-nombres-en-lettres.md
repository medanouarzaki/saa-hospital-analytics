# ADR 0106 — Un contrôle de langue, et les nombres écrits en lettres passés par le registre

**Statut.** Accepté.

---

## Contexte

La charte de style du rapport n'était tenue que par des mesures faites à la main, chapitre par
chapitre, au moment de chaque réécriture : rien ne l'empêchait de se défaire ensuite. Le contrôle des
nombres tapés ne voyait que les chiffres ; un nombre écrit en lettres échappait au registre, et deux
décomptes du projet ont vieilli ainsi sans bruit. Une relecture des sources rédigées a compté cent
seize nombres en lettres à partir de « trois », dont soixante-sept décomptes de données.

## Décision

### Le contrôle de langue

`tests/test_langue.py`, sans base, lit la prose des sources rédigées du rapport avec la liste de
fichiers et le dépouillement du contrôle des nombres tapés, importés et non réécrits. Il tient cinq
propriétés :

1. aucune forme de « engendrer » ;
2. aucun mot ni aucune locution de la liste des mots bannis de la charte, mot entier ou locution
   entière, au singulier comme au pluriel ; un emploi légitime est déclaré avec son motif, et la liste
   des emplois déclarés casse dans les deux sens — elle en porte un, « mutation » au sens du mouvement
   de séjour, dans une cellule de tableau ;
3. aucun « on », « l'on », « qu'on », « nous », « notre », « nos » ;
4. la première personne réservée aux remerciements et à la sous-section « Le volet professionnel » de
   la conclusion ;
5. chaque chapitre numéroté, sauf le dernier, finit sur un paragraphe qui renvoie au chapitre suivant
   par son étiquette.

L'abstract est retiré des propriétés 1 à 4, qui portent sur le français : « on » y est une
préposition anglaise. Le contrôle est inscrit au travail de l'intégration continue qui porte les
autres contrôles du rapport sans base.

### Les nombres écrits en lettres

Le contrôle des nombres tapés examine aussi les nombres écrits en lettres, de « trois » à « mille »,
composés et pluriels compris. Le seuil tient à ce que « un » et « deux » relèvent de la langue
courante plus que de la mesure ; à partir de « trois », un nombre en lettres peut être une donnée qui
vieillit. Seul ce qui peut vieillir passe par le registre : un nombre qui vient des données générées,
du dépôt ou d'une mesure du projet est une donnée, et passe par `\chiffre`. Les autres sont déclarés
dans `EXEMPTIONS_LETTRES`, occurrence par occurrence, avec une classe et un motif :

- énumération — les éléments comptés sont nommés un à un dans la phrase, la suivante, ou l'objet
  qu'elle introduit ;
- source — le nombre est repris d'une source citée dans la phrase, tel qu'elle le donne ;
- structure — structure du document ou d'une méthode fixe ;
- locution — locution figée, ou rapport arithmétique sans donnée ;
- personnel — passage d'écriture personnelle, gardé dans la forme de l'auteur.

La liste casse dans les deux sens, et le doute entre une donnée et une autre classe se tranche pour
la donnée. Quarante-neuf occurrences y sont déclarées. La liste des restes connus ne reçoit rien.

### Les entrées ajoutées

Trente et une entrées sont ajoutées au registre des chiffres, chacune avec sa commande : les mois de
la période ; les états du fait de rendez-vous et ceux qui portent un drapeau ; les niveaux de tri,
rétablie ; les dimensions qui ne portent que leur code ; les contrôles des versions de la dimension
patient ; la durée de disparition des vues pendant une reconstruction ; les profils applicatifs
relevés et ceux qui n'ont pas été observés ; les indicateurs qui ne sont pas recalculés depuis les
faits et ceux qui lisent la couche intermédiaire ; les indicateurs réglementaires de séjour ; les
écrans relevés ; les bornes du facteur d'erreur de la dérivation initiale ; l'écart d'années entre
deux sources ; les vérifications de la lecture du recueil ; les tableaux du recueil qui descendent à
l'établissement ; les missions du service, celles qui reçoivent un profil et celles qui n'en
reçoivent pas ; les onglets de la recherche d'identifiant ; les règles de blocage, celles que le
périmètre initial annonçait, la taille de l'union réduite et le rapport de substitution ; les lignes
de téléphone de la fiche patient ; le quantième de la date observée ; les filtres de la page des
données ; les couches de la pile technique ; les types d'épisode. Quand la valeur n'existe qu'écrite
en lettres dans un enregistrement de décision, la commande la lit telle que l'enregistrement la
donne.

### Les corrections du texte

Soixante-sept occurrences sont passées par le registre, au plus près : le nombre est remplacé par
son appel, et une phrase qui commencerait par un chiffre reçoit les quelques mots qui l'en
détournent (« Sur les … dimensions, … », « En tout, … indicateurs », « Parmi eux, … »). Elles portent
sur onze chapitres et l'annexe des compléments techniques. Le passage d'écriture personnelle ne
change pas.

### Les correctifs

Les pages des listes préliminaires composent la marque en vigueur en haut de la page, par un réglage
local au groupe des listes : une page qui finit une liste et en commence une autre porte le titre de
la première. La page où commence une liste reste sans en-tête, par la classe. Le commentaire
au-dessus de la liste des annexes du contrôle des chiffres nommait déjà les deux annexes, et le
fichier ne porte aucun avertissement de syntaxe : ni l'un ni l'autre n'a changé.

## Conséquences

La charte ne repose plus sur une mesure faite au moment d'écrire : une forme écartée qui revient
rougit. Un décompte écrit en lettres qui vieillirait avec les données ou le dépôt rougit aussi, tant
qu'il n'est pas passé par le registre ou déclaré avec un motif qui dit pourquoi il ne vieillit pas.
