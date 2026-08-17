# ADR 0048 — La corrélation délai/absentéisme est dédoublée : entre activités et à l'intérieur de chacune

**Statut.** Accepté.

---

## Contexte

La page des rendez-vous affichait une corrélation entre le délai médian d'obtention et le taux
d'absentéisme, calculée sur huit points — un par code d'activité — et valant **−0,4855**. Sa
définition au registre des indicateurs disait « position de chaque activité selon son délai médian
d'obtention et son taux d'absentéisme, avec la corrélation entre les deux séries », et la décision
qu'elle déclarait servir était « savoir si raccourcir le délai est un levier sur l'absentéisme ».

Trois mesures ont été prises avant toute réécriture.

**1. La grandeur affichée est déterminée par le rangement conjoint de deux tables de paramètres.**
`generator/config/rendez_vous.yml` porte `delai_rdv_par_specialite` et
`taux_absenteisme_par_specialite`, posées séparément et sans qu'aucun paramètre ne les lie. La
corrélation de Pearson entre ces deux colonnes de paramètres, calculée sur leurs huit valeurs,
vaut **−0,4918**. La valeur affichée, mesurée sur les données produites, vaut **−0,4855** : un
écart de 0,0063, soit 1,3 % en valeur relative.

**2. La relation réellement injectée est de signe contraire, et elle est interne à une spécialité.**
`pente_absenteisme_delai` vaut +0,012 par jour. Le code ne s'en sert pas pour fixer le nombre
d'absences — celui-ci est pris directement dans `taux_absenteisme_par_specialite`
(`generator/rendez_vous.py`, `p_abs = taux_absenteisme[activite]`, puis
`n_absences = round(total_active * p_abs)`) — mais pour biaiser, par échantillonnage par rejet, le
délai tiré pour les seules lignes d'absence (`_delai_biaise_longue_attente`, appelée dans la boucle
qui émet les absences). Les rendez-vous honorés, les annulations et les rendez-vous en instance
tirent leur délai sans biais.

**3. Cette relation interne est mesurable, et positive.** Mesure faite activité par activité, sur
les rendez-vous dont l'issue est connue et dont le délai est strictement positif :

| Activité | Médiane honorés | Médiane absences | Écart |
|---|---|---|---|
| 20 | 5 | 6 | +1,0 |
| 29 | 18 | 20 | +2,0 |
| 21 | 20 | 23 | +3,0 |
| 30 | 14 | 17 | +3,0 |
| 4 | 29 | 32 | +3,0 |
| 11 | 24 | 28,5 | +4,5 |
| 14 | 28 | 34 | +6,0 |
| 28 | 43 | 53,5 | +10,5 |

**Huit activités sur huit portent un écart positif.** En agrégat, sur 11 870 rendez-vous, la
corrélation entre le délai et le fait d'être une absence vaut **+0,0782** une fois l'activité
retirée des deux grandeurs par centrage. Sans distinguer les activités, elle tombe à **+0,0275** :
le rangement des activités efface presque entièrement la relation interne.

Les trois valeurs sont donc **−0,486 entre activités**, **+0,078 à l'intérieur des activités**, et
**+0,027 sans les distinguer**. Un lecteur à qui l'on ne montre que la première conclura que
l'attente ne fait pas manquer les rendez-vous, alors que la relation injectée dit le contraire à
activité donnée.

## Décision

**1. Les deux grandeurs sont produites et affichées, côte à côte, sur la même page.** La
comparaison entre activités conserve son entrée au registre ; une entrée neuve,
`rendez_vous_delai_et_absence_intra_activite`, porte l'écart mesuré à l'intérieur de chaque
activité. Les trois valeurs — entre activités, à l'intérieur des activités, sans les distinguer —
sont affichées dans une même rangée, chacune avec son signe et l'effectif sur lequel elle porte.

**2. La corrélation entre activités cesse d'être présentée comme une relation entre le délai et
l'absentéisme.** Sa définition dit désormais qu'elle compare les activités entre elles et non
l'intérieur d'une activité, et la décision qu'elle sert ne parle plus de levier : elle situe les
activités les unes par rapport aux autres, en disant que leur rangement conjoint est fixé par deux
tables de paramètres posées séparément.

**3. Une phrase d'écran explique pourquoi les deux signes diffèrent.** Elle nomme l'effet de
composition, et la troisième valeur la rend vérifiable à l'œil. Sans elle, deux nombres de signes
opposés se lisent comme une erreur de calcul.

**4. Les deux grandeurs sont marquées circulaires au registre des relations injectées.** `R-01`
précise sa forme — positive, interne à une spécialité, agissant sur le seul délai des lignes
d'absence — et nomme l'indicateur qui la donne à voir. Une entrée neuve, `R-21`, décrit la
corrélation entre activités pour ce qu'elle est : non pas une relation causale injectée, mais la
corrélation entre deux tables de paramètres, mesurée à −0,4918 sur les paramètres eux-mêmes.

## Ce qui a été écarté

**N'afficher que la corrélation entre activités**, c'est-à-dire ne rien changer. Écarté : la
grandeur est trompeuse seule, puisqu'elle suggère qu'allonger le délai réduit l'absentéisme, ce
qu'aucun paramètre n'écrit et que la mesure interne contredit.

**N'afficher que la mesure intra-activité**, en retirant la première. Écarté également, et pour
une raison symétrique : la comparaison entre activités est une information réelle sur le jeu de
données — les spécialités les plus attendues sont celles où l'on se présente le plus — et la
retirer ferait disparaître l'effet de composition au lieu de l'expliquer. Un lecteur qui
retrouverait ailleurs le nuage des huit points conclurait alors à une contradiction avec le
tableau de bord.

**Afficher les deux sans les commenter.** Écarté : c'est la configuration qui produit le pire
malentendu, deux nombres de signes opposés côte à côte sans dire pourquoi.

## Conséquence pour le rapport

**Le résultat central du chapitre d'analyse n'est pas cette corrélation.** Les deux grandeurs y
figurent comme illustration d'un effet de composition — une relation peut décroître entre les
groupes et croître à l'intérieur de chacun — et non comme une découverte sur l'absentéisme. Les
deux étant marquées circulaires au registre des relations injectées, la règle d'en-tête de ce
registre s'applique : ce que la chaîne démontre est qu'elle sait produire et distinguer les deux
mesures, pas ce que vaut la relation dans un établissement réel.

## Ce qui aurait invalidé cette décision

Une mesure intra-activité **nulle ou de signe négatif**. Le paramètre injecté aurait alors été sans
effet observable, et il n'y aurait eu qu'une seule grandeur à afficher — la comparaison entre
activités — accompagnée du constat que la pente déclarée ne se retrouve pas dans les données.

Cette mesure a été faite avant d'écrire quoi que ce soit. Elle est **positive sur les huit
activités**, avec un écart de +1,0 à +10,5 jours, et **+0,0782 en agrégat sur 11 870 rendez-vous**.
Un contrôle la reprend à chaque exécution et rougit si l'un des deux faits cesse d'être vrai.

## Vérification

`tests/test_tableau_de_bord.py` porte deux propriétés neuves : la première confronte chaque valeur
produite par la page à une seconde mesure écrite autrement — médianes et corrélation recalculées en
Python depuis les lignes brutes, la population étant reconstruite depuis le code d'état plutôt que
depuis les colonnes booléennes ; la seconde vérifie que l'écart est positif sur chaque activité et
que la corrélation agrégée l'est aussi.

`tests/test_relations_injectees.py` porte trois propriétés neuves : la page de destination d'une
relation existe ou l'entrée déclare explicitement qu'aucune ne l'affiche ; la prose de l'entrée dit
la même chose que ce champ ; et tout indicateur nommé par une entrée existe et siège sur la page
déclarée. La liste des pages est dérivée du registre des indicateurs, jamais recopiée.
