# ADR 0096 — La fermeture : une propriété de contrôle corrigée, et deux phrases fausses

**Statut.** Accepté.

---

## Contexte

Trois points bloquaient la remise, consignés par l'enregistrement précédent : le contrôle des noms
rouge, une égalité fausse au rapport, une valeur fausse au support. L'arbitrage du premier revenait à
l'auteur ; il est rendu, et les trois sont levés.

## Décision

### 1. LE CONTRÔLE DES NOMS CHERCHE DÉSORMAIS DES NOMS, ET NON DES MOTS

**La propriété qu'il portait était fausse, et c'est le motif de l'élargissement.** Elle cherchait
chaque mot du nom pris isolément, dès quatre caractères. Un mot isolé n'identifie personne : sur
l'arbre réel, elle rougissait sur douze fichiers dont aucun ne portait de nom — dix fois sur un
prénom très répandu que le dépôt porte comme **nom d'un autre hôpital** du centre hospitalier et
comme prénom de fiches engendrées, deux fois sur des morceaux du nom de compte contenus dans
**l'adresse du dépôt** elle-même.

Un contrôle qui rougit là où rien n'est fautif n'est pas prudent : il apprend à être ignoré.

**La propriété corrigée** : toute suite d'au moins **deux mots consécutifs** du nom, normalisée sur
la casse et les diacritiques. Un mot isolé n'est cherché que dans un seul cas, celui d'un nom qui
n'en compte qu'un — il est alors le nom complet.

**Aucun mécanisme neuf.** `EXCLUSIONS_PAR_VARIABLE` existait déjà et sert au fichier de licence ; il
continue de servir, mesuré : `LICENSE` porte bien le nom complet de l'auteur. **Aucun autre fichier
n'a eu besoin d'y être ajouté** — la propriété corrigée rend zéro fautif sans exclusion
supplémentaire. C'est la preuve que le remède n'était pas une liste de dérogations.

**Cinq mutations sur l'arbre réel, et les trois dernières sont les seules qui prouvent quelque
chose.** Sans elles, la nature de la propriété n'aurait pas changé, seulement sa portée.

| mutation | attendu | mesuré |
|---|---|---|
| nom complet de l'encadrant dans un fichier suivi | rouge | `1 failed` |
| nom complet de l'auteur hors du fichier de licence | rouge | `1 failed` |
| **un mot du nom, isolé, dans un fichier de réserve** | **vert** | `1 passed` |
| **les mots du nom collés, comme dans une adresse** | **vert** | `1 passed` |
| un autre mot du nom, isolé | **vert** | `1 passed` |

**Les témoins ont changé avec la propriété.** Quatre témoins déclarés VUS sont devenus NON VUS —
aucun ne nommait personne. Le fichier porte vingt-cinq contrôles : dix formes qui doivent être vues,
neuf qui ne doivent pas l'être, et six sur la construction des suites elle-même.

**Cinq voies restent ouvertes, et elles sont écrites** : les mots du nom sans séparateur, un
séparateur autre qu'une espace, l'ordre des mots inversé, une césure à l'intérieur d'un mot, un nom
dans l'historique mais plus dans l'arbre. **Les trois premières sont le prix exact de la propriété
corrigée** : les fermer ramènerait la recherche par mot isolé, donc les douze faux positifs.

Est également écrit ce que le contrôle **ne peut pas voir** : il ne voit qu'un nom *écrit*. Une
adresse électronique, une photographie, une signature dans une image, un nom en métadonnées de
fichier binaire lui échappent. Il ne dit pas « personne n'est identifiable ».

### 2. LES DEUX DÉFAUTS DE FOND

**Rapport, page 39.** Le signe d'égalité est retiré. La phrase dit maintenant que les deux décomptes
ne sont pas le même et **ne s'additionnent pas**, l'un des agrégats étant une vue posée hors de
l'outil de transformation et n'étant donc pas l'un des modèles. Aucune valeur n'a bougé.

Le contrôle des nombres tapés a d'ailleurs attrapé la première rédaction de cette correction, qui
citait un enregistrement de décision **par son numéro** — un chiffre littéral. La phrase renvoie
désormais au fichier de propriétés de la vue, que le lecteur peut atteindre, plutôt qu'à un artefact
interne du dépôt. Le rapport ne citait d'ailleurs aucun enregistrement de décision par son numéro :
la référence était hors style autant que hors registre.

**Support, planche 22.** L'entrée `ablation-comparaisons-variante-c` est créée au registre, sur le
modèle exact de celle de la variante A — même commande, même fichier de mesure, seul le nom de la
variante change. L'appel de la planche la désigne désormais : **6 comparaisons et non 12**.

### 3. UN CRITÈRE NEUF, ET LE BALAYAGE QUI LE PORTE

Le défaut de la planche 22 a une forme que rien ne pouvait voir : **la valeur est juste, la phrase
est fausse**. Les deux identifiants existaient, les deux valeurs étaient exactes au registre, la
remesure rendait zéro écart. Aucun contrôle ne lit la prose autour d'un appel.

Trois balayages ont été écrits pour chercher la même forme ailleurs :

1. les égalités affirmées entre des nombres qui ne s'additionnent pas — seize phrases relevées,
   toutes examinées, **aucune fautive** ;
2. les totaux de tableau confrontés à la somme de leur colonne — **neuf colonnes, zéro écart** ;
3. les appels dont la prose voisine porte le qualificatif d'un identifiant frère.

**Le troisième a été mis en défaut avant d'être cru.** Le défaut de la planche 22 a été réintroduit,
et le balayage l'a nommé en donnant l'identifiant qui aurait dû être appelé. Restauré, il ne trouve
plus que six lignes portant l'intitulé générique « Total », toutes vérifiées justes à la main. Un
balayage qui ne trouve rien ne prouve rien tant qu'il n'a pas été éprouvé sur le défaut qu'il
cherche.

Le critère est consigné en B11 du relevé, avec ce que ces balayages **ne voient pas** : une phrase
dont la prose et l'identifiant s'accordent tous deux sur une grandeur qui n'était pas celle qu'il
fallait citer.

### 4. LA COMPARAISON IMAGE À IMAGE, DUE ET FAITE

98 pages et 30 planches recomposées et comparées à l'état précédent. **Cinq pages et une planche
modifiées, et pas une de plus** — toutes attribuables à une correction nommée :

| modifié | attribution |
|---|---|
| pages 39 à 42 | la phrase corrigée, plus longue de sept lignes, décale la section 5.7 |
| page v (table des matières) | la seule ligne modifiée est celle de la section 5.7, qui passe de 40 à 41 |
| planche 22 | la variante C passe de 12 à 6 comparaisons |

Le nombre de pages et de planches n'a pas bougé : 98 et 30.

## Conséquences

Le relevé des critères est refait : **quatorze critères qu'un contrôle établit, quatorze vrais**, et
onze qu'aucun contrôle ne peut établir dont un neuf. La remesure du registre porte sur 267 entrées et
rend zéro écart.

Reste ouvert et assumé : quarante-deux nombres tapés déclarés un par un, la répétition chronométrée
du support non faite, et une réserve sur le filtre de période d'une capture.
