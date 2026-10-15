# ADR 0104 — Une troisième partie allégée, une conclusion en deux temps et des nombres arrondis à l'affichage

**Statut.** Accepté.

---

## Contexte

La troisième partie, la conclusion et les résumés occupaient trente pages composées : trois
pour l'environnement et les outils, dix pour l'analyse de l'activité, sept pour le tableau de bord,
six pour les recommandations, quatre pour la conclusion. Le chapitre d'analyse affichait trente-huit
nombres à trois décimales ou plus, répétait à chaque conclusion la limite des données générées, et
composait dans sa prose vingt-deux identifiants de conclusion et vingt identifiants de relation. Le
chapitre du tableau de bord s'ouvrait sur la concurrence d'accès en base et décrivait ses pages une
à une. La conclusion mêlait bilan et pistes, au présent, et finissait sur une phrase sur l'écriture.
Le résumé omettait deux des quatre classes de rubriques. Douze lignes de nombres tapés, déclarées
dans `RESTES_CONNUS` de `tests/test_aucun_nombre_tape.py`, vivaient dans ces textes sans commande
au registre. L'annexe des compléments techniques n'était pas parcourue par le contrôle des appels
de chiffres.

## Décision

### Le budget

Le budget, en pages composées, est de deux pages pour l'environnement et les outils, sept pour
l'analyse de l'activité, cinq pour le tableau de bord, quatre pour les recommandations, trois pour
la conclusion, une pour le résumé et une pour l'abstract, à une demi-page près. Les règles de
l'enregistrement 0103 s'appliquent : coupes motivées, puis charte, puis déplacement dans l'annexe
des compléments techniques, avec ses étiquettes, et le corps y renvoie par `\ref`. L'annexe reçoit
trois sections : deux tableaux de l'analyse (montants par type d'épisode, complétude et quarantaine
par table), les valeurs de l'analyse en précision complète, et le motif de l'instantané du tableau de
bord, avec sa figure des objets copiés. La hauteur des six graphiques du chapitre d'analyse est
réduite de six à huit dixièmes de centimètre.

### L'arrondi d'affichage par entrées dédiées

Dans la prose du chapitre d'analyse, un pourcentage et une moyenne s'affichent à une décimale, un
coefficient à deux. Chaque valeur arrondie est une entrée du registre dont la commande rend la valeur
arrondie : celle de l'entrée de précision complète, enveloppée dans `round`, côté SQL comme côté
Python. Elle porte l'identifiant de l'entrée source suivi de `-arrondi`. Le format d'affichage
`decimales` ne convient pas ici : il arrondit le rendu d'une valeur consignée, quand la remesure doit
comparer la valeur même que la prose affiche. L'entrée de précision complète reste employée, par
l'annexe de correspondance quand elle l'était, et par le tableau des valeurs en précision complète
de l'annexe des compléments techniques. Une valeur arrondie qui tombe sur un entier se rend sans
décimale (24 et non 24,0), selon la règle du zéro de fin de `generer_chiffres_tex.py`.

### Les marques de conclusion et l'annexe de correspondance

`\conclusion{C-nn}` ne compose plus rien. Elle pose une ancre et l'étiquette `conclusion:C-nn` à
l'endroit de la marque. L'ancre vient de `\phantomsection`, fourni par hyperref : sans elle, le lien
attaché à `\pageref` viserait le début de la section. Les vingt-deux marques restent dans la source,
à leur place, et le contrôle de correspondance les lit sans changement.

L'annexe de correspondance désigne chaque conclusion par sa page. Ses lignes gardent l'identifiant
en argument, parce que le contrôle les lit dans la source : son motif s'arrête à la première accolade
fermante, et une liste de renvois écrite en clair y perdrait le deuxième identifiant d'une ligne. La
composition de la colonne change, dans le groupe de chaque tableau : chaque identifiant de la liste
rend « p.~\pageref{conclusion:C-nn} ». Les identifiants de relation restent dans l'annexe, où ils
numérotent les lignes. La prose du corps ne compose plus aucun identifiant ; une phrase du chapitre
d'analyse renvoie une fois à l'annexe.

### Le scénario d'utilisation

Le guide d'utilisation du tableau de bord devient un scénario : le responsable du service se demande
s'il faut ouvrir des créneaux, et passe de la page d'activité à celle des rendez-vous, puis à celle
des données, qu'il exporte. Les autres pages tiennent en une phrase de récapitulation. L'incident du
taux de rotation est dit une fois, en entier, auprès des indicateurs réglementaires qu'il concernait.

### La conclusion en deux temps

La conclusion se compose d'un bilan, au passé, en trois volets — méthodologique, technique,
professionnel — puis de perspectives, au conditionnel, dont le passage à des données réelles. Elle
n'introduit aucun résultat. L'apport personnel devient le volet professionnel du bilan : ses faits
et sa première personne restent, ses phrases sur la rédaction du document en sortent, et deux
tournures impersonnelles en « on » changent de construction.

### Le contrôle des chiffres et l'annexe des compléments techniques

`ANNEXES` de `tests/test_registre_des_chiffres.py` nomme l'annexe des compléments techniques.
Les vingt-huit entrées qu'elle seule appelait perdent leur motif de non-emploi, devenu faux.

### Les registres

Cinquante-cinq entrées sont ajoutées au registre des chiffres, chacune avec sa commande : trente-six
valeurs arrondies, dont la part des consultations non appropriées exprimée en pourcentage, dix
valeurs publiées par quatre sources et lues dans leur champ `utilise_pour` de
`docs/sources/sources.yml`, huit codes d'activité lus dans la nomenclature du générateur, et le
nombre de rubriques au classement mixte, qui complète le décompte du résumé. Le décompte des
sections passe de quarante-six à quarante-cinq. Les douze lignes de `RESTES_CONNUS` de ces textes
sont retirées. Aucune entrée n'est retirée ; aucune entrée, aucune source et aucun élément du relevé
ne cessent d'être employés.

## Conséquences

Chaque chapitre de la partie s'ouvre sur la question qu'il traite et se ferme sur une synthèse qui
nomme la suite. Le statut de chaque conclusion — relation reproduite ou absence de relation — se lit
dans l'annexe de correspondance, et non plus conclusion par conclusion. Les nombres de la partie
passent tous par le registre, et tout nombre de l'annexe des compléments techniques est désormais
vérifié par le contrôle des appels de chiffres.
