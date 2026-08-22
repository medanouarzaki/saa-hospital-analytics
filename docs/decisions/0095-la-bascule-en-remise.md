# ADR 0095 — La bascule en remise, et ce que la relecture a vu

**Statut.** Accepté, avec un point bloquant nommé et non résolu.

---

## Contexte

Dernier travail du projet : produire le document final. Les trois valeurs qui font un document remis —
l'auteur, l'encadrant, l'état — voyagent ensemble et sortent du dépôt (ADR 0077). Il restait à poser
les deux secrets, à basculer l'état, à remesurer le registre, à relire les 98 pages et les 30
planches, et à refaire le relevé daté des critères.

## Décision

### 1. Les deux secrets sont posés, et rien ne les journalise

`gh secret set` depuis deux fichiers hors du dépôt, jamais par argument de ligne de commande. La
commande n'affiche aucune valeur. En intégration continue, elles passent par `env:` et non par une
interpolation dans le corps du script, si bien que le texte recopié au journal ne les porte pas ; et
la plateforme les masque partout ailleurs.

### 2. La bascule tient dans un fichier non suivi

`report/noms.tex`, porté par `.gitignore`, redéfinit les deux marqueurs et `\etatDuDocument`.
`report/marqueurs.tex` n'a pas bougé : il déclare `brouillon` et ses deux marqueurs vides, et il le
déclarera toujours. `git status` est resté propre à chaque instant.

### 3. La remesure du registre rend zéro écart

`266 entrée(s) et 13 série(s) confrontée(s), 0 écart(s)`, deux fois : avant la relecture et après
les corrections.

### 4. La relecture page par page a trouvé treize défauts, et onze sont corrigés

Aucun contrôle n'en voyait un seul. C'est la justification empirique de la partie B du relevé des
critères.

| # | Page | Défaut | Suite |
|---|---|---|---|
| 1 | 84 à 91 | **En-tête faux** : les huit pages des annexes B et C portaient « ANNEXE A. DICTIONNAIRE DE DONNÉES » | corrigé |
| 2 | 29 | **Surimpression** : quatre noms de colonne recouvraient la colonne « Type », quatre valeurs illisibles | corrigé |
| 3 | 27 | `passages_urgences` débordait sa colonne de 0,7 mm | corrigé |
| 4 | 59, 63, 81 | Noms d'objet en romain, où le souligné produit une barre démesurée : `int_patients` se lisait `int__patients` | corrigé |
| 5 | 59 | Le tableau de complétude débordait la marge de droite de 1,05 cm | corrigé |
| 6 | 78 à 80 | **Adresses de bibliographie sortant de la feuille** : le texte était perdu au bord de la page | corrigé |
| 7 | 24, 39 | Flèches de figure s'arrêtant dans le vide, sans rien relier | corrigé |
| 8 | iii | Typographie française appliquée à l'*Abstract* anglais | corrigé |
| 9 | 51, 52, 55, 58 | Clés de légende touchant leur libellé | corrigé |
| 10 | 64 et 65 | Légende « Figure 2 » séparée de la capture qu'elle nomme, par une coupure de page | corrigé |
| 11 | 28, puis 32 | Page aux trois quarts vide **en plein chapitre**, un tableau ne tenant pas sur la fin de page | corrigé |
| 12 | 90 | « du restant dû **a** un an », lecture ambiguë | **non touché** : « a » y est le verbe *avoir*, la tournure se tient. Une correction qui ne corrige rien se défait |
| 13 | 62 | La capture porte un filtre de période allant au 2026-11-11, quand la période s'arrête au 2026-06-30 | **non touché** : c'est un fait de l'application, pas une affirmation du rapport, et retoucher une capture serait la falsifier |

### 5. Les largeurs se mesurent au rendu, elles ne s'estiment pas

Deux corrections successives à l'estime ont échoué sur la même colonne avant que sa largeur ne soit
relevée sur l'image à 300 points par pouce : `type_piece_identite` occupe 4,18 cm en chasse fixe. La
troisième, dimensionnée sur la mesure, a tenu.

### 6. Deux corrections ont dû être défaites, et c'est le résultat le plus utile de cette remise

**La première a fait disparaître l'en-tête des neuf chapitres.** Le remède de l'en-tête d'annexe
teste si une macro est vide par `\ifx`. Déclarée par `\newcommand`, elle est `\long` quand `\empty`
ne l'est pas ; `\ifx` compare aussi ce préfixe, le test rendait faux pour un contenu pourtant vide,
et la branche `\else` composait du vide. **Le document aurait été remis sans un seul en-tête de
chapitre.** Rien ne l'a signalé : la composition sort 0, le nombre de pages ne bouge pas, aucun
contrôle ne lit le PDF.

Ce qui l'a vu : la **comparaison image à image des 98 pages avant et après**, qui a signalé 82 pages
modifiées là où onze corrections locales en attendaient une trentaine. C'est cette disproportion qui
a conduit à regarder, puis à trouver.

**La seconde a déplacé un blanc au lieu de le supprimer** : rendre sécable le tableau de la
section 4.3 a rempli la page 28 et vidé la page 32. La même comparaison l'a montré, et le second
tableau a reçu le même traitement.

**Une correction se vérifie sur le rendu, pas sur le fait qu'elle compile.**

### 7. Le relevé des critères est refait dans l'état de remise

`docs/releve_des_criteres.md`. Quatorze critères qu'un contrôle établit — treize vrais, **un faux** —
et dix qu'aucun ne peut établir, vérifiés à la main un par un.

## Ce qui reste ouvert, et qui est assumé

### A3 — le contrôle des noms est ROUGE, et l'intégration continue avec lui

C'est le point bloquant de cette remise. Les secrets posés, le contrôle cesse de s'abstenir — **en
intégration continue aussi**, `ci.yml` les lui passant par `env:` — et il rougit sur douze
occurrences.

**Ce n'est pas une fuite, et la mesure le dit exactement.** Aucun des deux noms complets ne figure
dans l'arbre ; le nom de l'encadrant n'y paraît sous aucune forme. Les douze occurrences portent sur
trois mots du nom de l'auteur pris isolément : un prénom très répandu que le dépôt porte dix fois
comme **nom d'un autre hôpital** et comme prénom de fiches engendrées, et deux fragments contenus
dans **l'adresse du dépôt lui-même**.

Le contrôle avait annoncé ce point aveugle : sa documentation nomme le seuil de quatre caractères
comme une voie ouverte et assumée, et porte déjà un mécanisme d'exclusion étroite par variable,
employé pour `LICENSE`.

**Le remède est d'étendre ce mécanisme aux douze porteurs légitimes, pour le seul nom de l'auteur.**
Il n'a pas été appliqué : `tests/test_aucun_nom_de_personne.py` n'appartient pas aux fichiers
ouverts à l'écriture pour cette remise, et surtout **élargir un contrôle pour le faire verdir est le
geste que ce projet s'interdit sans décision explicite**. La décision revient à l'auteur.

### Deux défauts de fond, signalés et non corrigés

La règle veut qu'un défaut de composition se corrige et qu'un défaut de fond s'arrête et se
signale. Deux ont été trouvés, et ils sont laissés tels quels.

**Rapport, page 39.** « La couche analytique compte 19 modèles : 6 dimensions, 6 faits et 8
agrégats. » Les deux nombres sont justes et mesurés ; **l'égalité entre eux est fausse**, 6 + 6 + 8
faisant 20. La cause est connue et consignée : `agg_provenance_champs` est une vue posée **hors de
l'outil de transformation**, par un fichier de définition de schéma écrit à la main (ADR 0028). Elle
compte parmi les huit agrégats du schéma et non parmi les dix-neuf modèles. La correction est
purement rédactionnelle et n'exige aucune mesure nouvelle : cesser de poser le signe d'égalité.

**Support, planche 22.** La ligne « Variante C » porte **12 comparaisons**, quand
`linkage/ablation.csv` en mesure **6** pour cette variante. `slides/presentation.tex:622` appelle
`\chiffre{comparaisons-modele}`, l'identifiant du modèle complet, faute d'entrée au registre pour
cette grandeur. C'est **une valeur fausse dûment affichée**. La corriger demande une entrée
`ablation-comparaisons-variante-c` au registre, avec la commande qui la produit — sur le modèle
exact de `ablation-comparaisons-variante-a`, qui existe et qui est juste.

### Ce qui n'a pas été fait

La répétition chronométrée du support (B9). Trente planches, aucune mesure de durée.

## Conséquences

Le document est composé dans l'état de remise, 98 pages et 30 planches, et les deux PDF sont
produits par la chaîne avec les secrets posés. La branche principale porte une vérification rouge
tant qu'A3 n'est pas tranché.
