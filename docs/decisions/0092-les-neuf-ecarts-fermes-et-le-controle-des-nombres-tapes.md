# ADR 0092 — Les neuf écarts fermés, le nombre tapé retiré, et une vérification déclarée due

**Statut.** Accepté.

---

## Contexte

Le relevé des critères portait un critère **faux** : `mesurer.py --verifier` rendait neuf écarts
entre le registre et ce que ses commandes rendent. Et le rapport portait **un nombre tapé en clair**,
`0,9995`, qu'aucun contrôle ne pouvait voir.

## Décision

### 1. La cause de chaque écart a été mesurée avant qu'un remède soit proposé — et elle n'était pas celle qu'on croyait

**Six des neuf écarts ne venaient pas d'une valeur devenue fausse. Ils venaient d'une commande
devenue aveugle.**

| écart | consigné | mesuré | cause **mesurée** | remède | valeur composée qui change |
|---|---|---|---|---|---|
| `relations-non-reprises` | 5 | 0 | la commande cherche `\relnonreprise{` sous `report/chapitres/` ; les cinq sont dans l'annexe de correspondance | **portée de la commande** | aucune |
| `conclusions-avec-relation` | 16 | 0 | idem | **portée** | aucune |
| `conclusions-sans-relation` | 6 | 0 | idem | **portée** | aucune |
| `releve-champs-non-employes` | 17 | 101 | la commande ne voit pas l'annexe du relevé des écrans, qui cite 84 identifiants | **portée** | aucune |
| `tdb-graphiques` | 23 | 18 | la commande compte quatre formes intégrées ; cinq tracés passent par une fonction commune | **forme comptée** | aucune |
| `tableau-de-bord-par-page` (série) | empreinte | empreinte | même cause | **forme comptée** | aucune |
| `sections-du-rapport` | 54 | 51 | trois sections fondues en une au chapitre du système d'information | **remesure** | « en 9 chapitres et **51** sections », introduction |
| `fichiers-de-controle` | 74 | 76 | deux contrôles ajoutés depuis | **remesure** | « **76** fichiers de contrôle la surveillent », conclusion |
| `instantane-volume` | 32 710 656 | variable | la taille des tables varie d'un rafraîchissement à l'autre | **aucun** — il a concordé de lui-même | aucune |

**Les valeurs consignées des six premiers étaient justes.** Reporter le zéro mesuré aurait écrit au
registre une valeur fausse dûment mesurée — exactement ce contre quoi la consigne mettait en garde.

**Deux valeurs composées changent, et deux seulement** : 54 → 51 sections, 74 → 76 fichiers de
contrôle. Aucune autre page du rapport ne bouge.

`mesurer.py --verifier` rend désormais `266 entrée(s) et 13 série(s) confrontée(s), 0 écart(s)`.

### 2. Le nombre tapé est remplacé par son appel

La F-mesure de la variante A vaut `0.999495204442201` — mesurée par sa commande sur le fichier
d'ablation, et non devinée. Elle reçoit une entrée au registre, le même format que ses voisines
(quatre décimales), et le tableau l'appelle. **Le rendu ne change pas** : il composait déjà 0,9995.

### 3. Le contrôle qui manquait existe, avec ses deux témoins et sa dette nommée

`tests/test_aucun_nombre_tape.py` rougit sur un chiffre littéral composé hors d'un appel au
registre. Ses exceptions sont **déclarées avec leur motif** — numéro d'article, année, date,
identifiant de relevé ou de source, renvoi interne, rang d'énumération —, et un **témoin négatif**
vérifie qu'il les laisse passer : sans lui, il rougirait partout et ne prouverait rien. Le **témoin
positif** porte le cas réel qui l'a motivé.

**Il trouve quarante-deux occurrences existantes**, et c'est le fait marquant de ce travail. Ce ne
sont pas des faux positifs : ce sont des nombres tapés — pourcentages de provenance, statistiques
régionales citées d'un recueil, couverture des règles de blocage, table de perturbation, chiffres
d'un rapport de contrôle. Les corriger toutes demande une entrée au registre par valeur, avec la
commande qui la produit, et ces valeurs vivent dans la prose d'un fichier de sources.

**Elles sont donc nommées une par une** dans le contrôle, fichier et ligne. Toute occurrence
nouvelle est rouge ; une occurrence corrigée doit sortir de la liste, et une seconde épreuve rougit
si la liste porte une ligne qui n'existe plus. La dette est explicite, comptée, et ne peut pas
grossir en silence.

### 4. La vérification est déclarée due avant toute remise

Les neuf écarts ne sont pas nés d'une négligence. Ils sont nés d'une **propriété du dispositif** :
`mesurer.py --verifier` ouvre la base et compare des valeurs mesurées sur la période entière, quand
l'exécuteur n'engendre que trois mois. Elle ne peut pas être un travail de la chaîne, et ne tourne
qu'à la main.

**Tout travail de rédaction qui déplace de la matière périme cette vérification** — descendre un tableau
en annexe, fondre trois sections en une, changer la forme d'un appel : rien ne casse visiblement, et
une commande devient aveugle. C'est écrit au relevé des critères comme une obligation avant remise,
non comme un conseil.

## Conséquences

Le rapport reste à **98 pages et 22 boîtes débordantes**, le support à **21 planches et 0 boîte**.

Le relevé des critères passe de douze à **treize critères qu'un contrôle établit — onze vrais, deux
non encore applicables, plus aucun faux**.

**Ce qui n'est pas fait** : les quarante et une autres occurrences de nombres tapés. Chacune demande
son entrée au registre et sa commande ; le travail est nommé, compté et borné, mais il déborde
ce qui est entrepris ici.
