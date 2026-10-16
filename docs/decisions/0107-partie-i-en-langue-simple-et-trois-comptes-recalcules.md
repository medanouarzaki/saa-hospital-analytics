# ADR 0107 — La première partie en langue simple, et trois comptes recalculés depuis l'objet compté

**Statut.** Accepté.

---

## Contexte

L'introduction et les trois chapitres de la première partie n'avaient pas reçu la charte de style
resserrée déjà appliquée aux deuxième et troisième parties, et dépassaient leur volume : environ
2,3 pages pour l'introduction, 3,2 pour le chapitre de l'organisme, 5,3 pour celui du système
d'information et 4,7 pour celui du cadrage.

Trois comptes du rapport ne lisaient pas l'objet qu'ils comptent, mais la phrase d'un enregistrement
de décision qui le décrivait : le facteur d'erreur du cadrage initial (« cinq à sept », lu dans
`0003`), les règles de blocage d'abord annoncées (lues dans `0030`) et les couches de la chaîne
(« cinq », lues dans `0088`, à propos d'une figure de pile technique qui n'est plus composée).

Le registre des chiffres portait un écart : `fichiers-de-controle` consigné à 78 pour 79 fichiers
mesurés. Sa cause : le dernier fichier de contrôle, celui de la langue, a été créé après la remesure
finale du registre, qui ne l'a donc pas vu.

## Décision

### La langue et le volume

Les quatre textes suivent la charte : phrases plus courtes, aucun point-virgule dans la prose
réécrite, une idée par paragraphe, voix active. Les coupes portent sur des redites (une phrase de
synthèse qui répète la section, une proportion que le tableau voisin donne déjà), sur une phrase
qui parlait du document lui-même, et sur des formulations négatives ou rares (« contractable »
devient « vendu à part »). Aucun contenu vérifié n'est supprimé, et rien n'est déplacé en annexe.
Volume composé après : 2,1 ; 2,8 ; 5,2 ; 4,5 pages, pour un budget de 2 ; 2,5 ; 5 ; 4, à une
demi-page près.

Les passages d'écriture personnelle ne changent pas, à une exception : dans celui du chapitre de
l'organisme, les mots de l'auteur sont rétablis là où des appels au registre les avaient remplacés
(« cinq » quatre fois, « quatre » une fois). Ils sont déclarés au contrôle des nombres écrits en
lettres, classe « personnel ».

### Les trois comptes

| compte | avant | après | ce qui est lu |
|---|---|---|---|
| facteur d'erreur du cadrage initial | « cinq à sept » | 3,5 sur la capacité, 7,3 sur les séjours | capacité annoncée et capacité fonctionnelle au registre ; taux d'occupation moyen et durée moyenne de séjour nationaux dans la fiche de S-30 ; admissions relevées dans la configuration de volumétrie |
| règles de blocage | quatre, « ajoutées aux trois prévues » | quatre ; la règle ajoutée l'est « au découpage d'abord annoncé », sans nombre | les fonctions de règle de `linkage/blocage.py` |
| organisation de la chaîne | cinq couches | sept schémas, nommés | les déclarations de schéma des DDL d'ingestion et de rapprochement, de la configuration dbt et du module de l'instantané |

Le rapport des séjours suit la dérivation du cadrage initial : capacité annoncée × 365 × taux
d'occupation national ÷ durée moyenne de séjour nationale, rapportée aux admissions relevées. Les
deux valeurs nationales, 54,6 % et 3,2 jours, sont ajoutées à la fiche de S-30, à la suite de ce
qu'elle porte : tableau 76, page 104, ligne Total. Elles ont été relues dans le fichier consulté,
dont l'empreinte est celle que la note de S-30 consigne. La fiche bibliographique n'en change pas :
ce champ n'est pas composé.

La règle ajoutée porte l'étiquette de l'enregistrement qui la consigne, sous la forme fixée par
`0099` : `decision-quatre-regles-de-blocage`, déclarée comme convention.

### Les entrées du registre

Ajoutées : `facteur-cadrage-capacite`, `facteur-cadrage-sejours` (en précision complète, non
employées, avec leur motif) et leurs arrondis à une décimale, `facteur-cadrage-capacite-arrondi` et
`facteur-cadrage-sejours-arrondi`, que le chapitre de conception compose. `pile-couches` compte
désormais les schémas déclarés. Retirées : `facteur-cadrage-min`, `facteur-cadrage-max`,
`regles-blocage-prevues`. `fichiers-de-controle` passe à 79, et la remesure finale du registre se
fait après la dernière écriture de fichier, fichiers de contrôle compris.

Chaque fichier dont les appels changent met à jour ses lignes d'en-tête de provenance.

### Le correctif

La documentation d'un contrôle des marqueurs portait une barre oblique inverse dans une chaîne non
brute, ce qui produisait un avertissement de syntaxe. La chaîne devient brute ; rien d'autre ne
change.

## Conséquences

Les trois comptes vieillissent avec l'objet qu'ils comptent : une règle de blocage, un schéma ou une
valeur nationale ajoutés changent la remesure, et le registre rougit tant que le texte ne suit pas.
Le facteur « cinq à sept » n'était pas faux, mais il arrondissait deux rapports différents en une
fourchette que rien ne recalculait. L'intégrité des passages d'écriture personnelle ne repose sur
aucun contrôle automatique : elle repose sur la relecture du différentiel.
