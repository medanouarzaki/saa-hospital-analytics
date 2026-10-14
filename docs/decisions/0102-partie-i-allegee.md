# ADR 0102 — Une première partie allégée, tenue par un budget et une charte

**Statut.** Accepté.

---

## Contexte

L'introduction et les trois chapitres de la première partie occupaient vingt et une pages. Le
chapitre de l'organisme d'accueil consacrait plus du tiers de ses lignes au système de santé
national et à la région, et ne nommait l'hôpital qu'après cinquante lignes. Le chapitre de cadrage
parlait davantage du document que de la méthode du projet. Quatre idées — le jeu de données
engendré, le profil unique ouvert au poste, l'interdiction d'image et l'absence d'activité
chirurgicale — revenaient en entier dans plusieurs chapitres. Le chapitre de l'organisme d'accueil
portait enfin dix lignes de nombres tapés, déclarées dans `RESTES_CONNUS` de
`tests/test_aucun_nombre_tape.py`.

## Décision

### Le périmètre et le budget

La première partie traite du domaine d'activité : l'hôpital et son service. Le budget, en pages
composées, est de deux pages pour l'introduction, deux pour l'organisme d'accueil, cinq pour le
système d'information hospitalier et quatre pour le cadrage, à une demi-page près. Pour le tenir, les
coupes motivées passent en premier, puis la charte de style, puis le déplacement en annexe. Un
contenu vérifié ne se supprime pas pour tenir un budget : il se déplace dans une annexe que le
contrôle de provenance examine, avec ses étiquettes, et le corps y renvoie. Faute d'une telle annexe
pour un contenu donné, le dépassement est constaté et laissé tel quel. Les tableaux de relevé du
chapitre du système d'information, que l'annexe du relevé porte en totalité, ne sont plus repris
dans le corps.

### Les cinq motifs de coupe

Toute coupe porte un motif et un seul : HORS-DOMAINE (hors de l'hôpital et du service), REDITE
(dite ailleurs, l'occurrence conservée étant nommée), META (discours sur le document, sa rédaction,
ses chapitres ou ses contrôles), GENERALITE (maxime sans terme propre au projet), INVENTAIRE
(énumération portée par une annexe, qui y renvoie).

### La charte de style

Sujet concret et verbe d'action ; un fait par phrase, de quinze à vingt-cinq mots, aucune phrase
réécrite au-delà de trente-cinq mots sauf énumération ; ni formule-choc, ni symétrie rhétorique, ni
phrase de chute ; la limite des données engendrées dite une fois par chapitre au plus ; aucun
discours sur le document hors de l'annonce du plan et des transitions ; vocabulaire du métier, le
vocabulaire interne du projet n'apparaissant qu'au chapitre de cadrage, expliqué une fois ; une
négation seulement quand elle porte l'information ; ponctuation sobre, pas de gras dans la prose
sauf un terme défini à sa première occurrence ; passé composé pour ce qui a été fait, présent pour ce
que montre une figure ; aucune formule toute faite.

### L'écriture personnelle

Les passages qui relatent le déroulement du stage gardent leurs faits et leur style ; la charte ne
s'y applique pas. Seules y sont admises : la personne, un mot de liaison, la suppression d'une redite
exacte dite ailleurs, et le retrait d'une phrase ou d'une demi-phrase de discours sur le document.

### Introductions, synthèses et personne

Chaque chapitre de la partie s'ouvre sur un paragraphe sans titre qui pose la question traitée, et
se ferme sur une section étoilée « Synthèse » qui dit ce que le chapitre a établi et nomme le
chapitre suivant par un renvoi. La section étoilée n'est pas comptée par la déclaration
`SECTIONS: n` du contrôle de provenance, qui ne lit que `\section{`. Le rapport est impersonnel : ni
« on » ni « nous » ; la première personne est réservée aux passages personnels, et la règle se dit
une fois, dans l'introduction.

### Les registres

Le registre des chiffres reçoit `capacite-annoncee`, la capacité litière annoncée par la dépêche
S-29, lue dans la note de cette source sur le modèle de `source-part-non-urgentes`. La capacité
fonctionnelle passe par l'entrée existante `capacite-fonctionnelle`. Les deux restent énoncées
séparément, sans rapport calculé. Aucune entrée n'est retirée ni passée en non-emploi : les entrées
appelées par l'introduction et le cadrage restent appelées. Aucune source ne cesse d'être citée :
S-05 reste citée pour la région de rattachement de l'hôpital, l'emploi que le générateur lui donne.
Aucun élément du relevé ne cesse d'être employé : l'annexe du relevé les cite tous.

### La dette de nombres tapés du chapitre de l'organisme d'accueil

Ses dix lignes de `RESTES_CONNUS` sont éteintes : sept par la coupe des sections nationale et
régionale, une par la coupe de la date de mise en fonction et de la superficie (HORS-DOMAINE), une
par la redite de la part urbaine, que le chapitre de conception porte par le registre, et les deux
capacités par le registre. La liste ne nomme plus ce fichier.

### L'état de repos du socle

Docker Desktop reste arrêté hors des travaux qui exigent la base. Son disque virtuel vit sur un
disque externe que la mise en veille sur batterie déconnecte, et un disque virtuel ouvert au moment
d'une déconnexion s'abîme. Docker Desktop est donc démarré pour un travail et arrêté à sa fin, et la
machine reste sur secteur pendant qu'il tourne.

## Conséquences

Le chapitre de l'organisme d'accueil nomme l'hôpital dès sa première phrase. Le chapitre de cadrage
expose la méthode du projet — observation, reconstruction documentaire, génération, chaîne,
vérification — en prose de lecteur, et la traçabilité en un seul paragraphe. Le dépassement de budget
qui subsiste est constaté au document composé ; aucun contenu vérifié n'a été supprimé pour le
réduire.
