# ADR 0088 — La correction de l'article 35, et une passe de conversion qui n'atteint pas sa cible

**Statut.** Accepté.

---

## Contexte

Le tableau du chapitre premier rangeait « Recouvrer les sommes dues à l'hôpital » parmi les missions
que l'article 35 du règlement intérieur prescrit au service. Le texte de l'article, lu intégralement
pour composer le diagramme des cas d'utilisation, ne la porte pas.

Par ailleurs le rapport comptait 98 pages, et une cible de 85 a été posée : réduire le volume de
texte sans perdre d'information, en convertissant ce qui se lit mieux en figure.

## Décision

### 1. Le tableau du chapitre premier porte les neuf missions, dans les termes du texte

Il en portait cinq, dont trois paraphrasées et une qui n'en est pas une. Il porte désormais les
**neuf**, reproduites mot pour mot, les deux qui gouvernent ce travail en gras.

**Le recouvrement n'y figure pas, et cette absence est écrite plutôt que tue.** Il relève de
l'article 9, paragraphe b, qui charge le pôle des affaires administratives de veiller au recouvrement
des créances de l'établissement. Le profil applicatif `MSM - RECOUVREMENT` reste l'un des cinq
profils observés — ce fait est observé et ne change pas ; ce qui change est le rattachement
réglementaire de la mission qu'il porte. **Un profil du logiciel sert une mission que le règlement
place ailleurs** : le découpage de l'outil ne recopie pas le découpage réglementaire.

**Le balayage du rapport entier ne trouve aucune autre occurrence.** Les quatre autres mentions de
l'article 35 — toutes dans le dictionnaire de données, sur la facturation — sont exactes.

### 2. Le chapitre du système d'information décrit ce que le service saisit, non une interface

Partent : les décomptes d'éléments par bloc, les barres d'actions, les onglets comptés, et les deux
reconstitutions d'agencement de blocs. Elles décrivaient un logiciel d'éditeur.

Restent intacts : **les quatre tables de champs avec leurs identifiants de relevé** — ce sont elles
qui font que les colonnes du modèle sont observées et non supposées —, **les quatre observations
exploitables**, les deux définitions de vocabulaire, la lecture des critères de recherche, la forme
des nomenclatures et la contrainte de format de date.

Le chapitre passe de huit sections à cinq, de 2 929 à 2 673 mots, et de neuf à huit pages.

### 3. Deux figures nouvelles

**Le parcours du patient**, au chapitre premier : de l'arrivée à la relance, à travers les cinq
processus. Le rapport décrivait le service par ses missions et par son logiciel, jamais par le chemin
d'un patient.

**La pile technique**, au chapitre de l'architecture : cinq couches, sept briques, chacune portant la
désignation fonctionnelle que le chapitre de cadrage lui donne et son rôle en trois verbes. **Aucun
logotype d'éditeur** : ce sont des marques déposées.

### 4. Deux conversions ont été défaites, et leur échec est consigné

**Les neuf pages du tableau de bord, mises en tableau** : les deux paragraphes qui les décrivent
tenaient en vingt lignes, le tableau en a pris davantage. Le document passait de 97 à 98 pages. Défaite.

**Les cinq recommandations, mises en deux colonnes** — rubrique et contenu. Le document passait de 97
à 100 pages et gagnait une boîte débordante : une colonne étroite casse les longs paragraphes en
lignes courtes. Défaite.

Une conversion qui allonge est une mauvaise conversion.

## Conséquences

**La cible de 85 pages n'est pas atteinte, et elle ne l'est pas parce qu'il faudrait couper un
contenu vérifié.** Le document passe de **98 à 97 pages**. Le détail par chapitre est au rapport de
ce travail.

Le motif tient en une mesure : ce qui reste après la coupe du chapitre du système d'information est
de la matière protégée — un chiffre et sa source, une limite énoncée, une observation de terrain, un
résultat, les vingt-deux conclusions chiffrées, les cinq recommandations. Les deux figures nouvelles,
exigées par ailleurs, coûtent à elles seules deux pages.

**Une piste a été sondée et mesurée : elle ne vaut qu'une page.** Réduire la profondeur de la table
des matières aux seuls chapitres — `\setcounter{tocdepth}{0}` — fait passer le document de 97 à 96
pages, et non de 97 à 92 comme la taille de la table le laissait croire : une table plus courte
décale le corps, elle ne le raccourcit pas. La sonde a été retirée ; `report/rapport.tex` n'était de
toute façon pas dans la liste fermée de ce travail.
