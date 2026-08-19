# ADR 0054 — Aucun champ synthétique ne prend une valeur structurellement possible dans son espace réel

**Statut.** Accepté.

---

## Contexte

### Le fait mesuré

Une relecture des lignes versées au dépôt, avant publication, a relevé ceci :

| Champ | Valeurs concernées | Ce qui les rend problématiques |
|---|---|---|
| `telephone_1` à `telephone_4` | **271 numéros** dans l'échantillon versé, dont **247 sur les préfixes 0661 à 0669** ; **31 649 valeurs** dans la couche source | dix chiffres, forme nationale valide, préfixes mobiles attribués |
| `email` | **51 adresses distinctes** dans l'échantillon, **6 405** dans la couche source | domaines `gmail.com`, `yahoo.fr`, `hotmail.com`, `outlook.com`, `menara.ma`, tous exploités |
| `n_assure` | **29 171 valeurs** | neuf chiffres, exactement le format de l'immatriculation à la caisse nationale de sécurité sociale |
| `police`, `num_inscription` | **29 171 valeurs** chacun | neuf chiffres, même famille de format |

**Ce qui commande la correction n'est pas qu'une promesse écrite au dépôt soit fausse.** C'est
qu'**un numéro tiré sur un préfixe attribué est le numéro de quelqu'un** — pas d'un patient, de
n'importe qui. Publié à côté d'un nom, d'une adresse de voie et d'une ville, dans un dépôt dont
l'intitulé annonce de l'analyse hospitalière, il produit quelque chose qui se lit comme un fichier
nominatif échappé et qui peut faire sonner un téléphone réel. Que la fiche soit fabriquée n'aide pas
la personne appelée. Une adresse chez un fournisseur exploité pose le même problème.

### La comparaison qui montre que c'est un oubli, pas un arbitrage

La pièce d'identité, elle, tenait déjà sa promesse. `generator/patients.py` la construit ainsi :

```python
n_piece_identite = f"{int(generateur.integers(1_000_000, 7_000_000)):09d}"
```

Neuf chiffres **sans lettre**, quand une carte nationale marocaine porte une ou deux lettres suivies
de chiffres. Aucune valeur produite ne peut être une carte réelle, et cela ne dépend d'aucune
décision administrative.

**Le générateur savait donc construire un espace disjoint. Il l'a fait une fois sur deux.** Les
quatre lignes qui suivent immédiatement celle-ci dans le même fichier produisaient un numéro de
police, un numéro d'assuré et un numéro d'inscription au même format de neuf chiffres, sans que la
question de l'espace réel visé ait été posée — et l'immatriculation de sécurité sociale compte,
elle, exactement neuf chiffres. C'est un oubli d'application, non un arbitrage entre deux exigences.

## Décision

### 1. L'invariant

> **Aucun champ synthétique ne prend une valeur structurellement possible dans son espace réel.**

Il porte sur tous les champs recensés, corrigés ou non, et s'exerce sur les **données produites** —
la couche source de la base et les fichiers versés au dépôt — jamais sur la configuration qui les
engendre. Une configuration corrigée dont la sortie ne l'est pas laisserait passer exactement ce que
l'invariant doit attraper.

### 2. Impossibilité structurelle, et non non-attribution

**Une plage non attribuée n'est pas une garantie.** L'attribution est administrative et mutable : un
préfixe libre aujourd'hui peut être ouvert dans deux ans, et la promesse redeviendrait fausse en
silence, sans que personne ne touche au dépôt et sans qu'aucun contrôle ne rougisse.

**Une impossibilité de structure est permanente**, vérifiable en une ligne, et cohérente avec le
champ qui tenait déjà sa promesse. Elle est donc retenue pour chaque champ :

| Champ | Propriété structurelle retenue | Pourquoi elle est permanente |
|---|---|---|
| `telephone_1` à `telephone_4` | **onze chiffres** | le plan de numérotation marocain donne exactement dix chiffres en forme nationale ; un onzième chiffre ne peut être attribué à personne |
| `email` | **domaine réservé par la RFC 2606** — `example.com`, `example.net`, `example.org`, et tout nom sous `.invalid` | la norme interdit leur enregistrement ; aucun registrar ne peut les vendre |
| `police`, `n_assure`, `num_inscription` | **douze chiffres** | l'immatriculation de sécurité sociale en compte neuf ; douze n'est le format d'aucun de ces registres |
| `n_piece_identite` | **aucune lettre** — inchangé | une carte nationale porte une ou deux lettres |
| `n_ipp`, et les identifiants d'enregistrement | **préfixe alphabétique** — inchangé | `IPP-`, `RDV-`, `FAC-` ; aucun registre national n'emploie ces préfixes |

### 3. La transformation préserve les égalités, par construction

**Le téléphone est un champ de comparaison du rapprochement** : `linkage/modele_estime.json` porte
la règle de blocage `nom_famille_1_norm = … AND telephone_1_norm = …`. Une transformation qui aurait
modifié la structure d'accord entre fiches aurait changé les paires candidates, l'estimation du
modèle et son évaluation.

**La correction ne change que la mise en forme.** Le préfixe tiré et l'entier tiré restent les mêmes,
et le seul changement est le nombre de chiffres de bourrage ; pour l'adresse, la liste de domaines
garde son cardinal et son ordre, si bien que le rang tiré désigne le même rang. Dans les deux cas la
correspondance entre l'ancienne valeur et la nouvelle est **injective**, donc deux fiches qui
coïncidaient coïncident encore et deux fiches qui différaient diffèrent encore.

**Ce n'est pas supposé, c'est mesuré**, sur la même population avant et après reconstruction :

```
                                  avant    apres
paires partageant telephone_1     43741    43741
valeurs distinctes telephone_1     8303     8303
paires partageant email            5900     5900
```

### 4. Ce que le périmètre exclut, et selon quel critère

**Les noms, prénoms, adresses de voie et villes ne sont pas dans le périmètre.** Le critère est
celui-ci : **un identifiant désigne une personne ou un compte ; un attribut la décrit.** « Fatima
Amrani » et « 113 Boulevard Mohammed V » décrivent une fiche sans désigner qui que ce soit — des
milliers de personnes portent ce nom, et une voie n'est l'adresse de personne en particulier.
Retirer le réalisme de ces colonnes viderait le jeu de ce qui en fait l'intérêt, et ne protégerait
personne.

## Ce qui a été écarté

**Revoir la promesse à la baisse** — écrire que les valeurs sont « plausibles » plutôt que disjointes.
Écarté : cela aurait rendu la phrase exacte et laissé le problème entier. Le défaut n'est pas dans
la phrase, il est dans les données.

**Chercher un préfixe non attribué.** Écarté pour la raison donnée plus haut : l'attribution est
révocable, et la garantie tomberait sans bruit. C'est le cœur de cette décision.

**Inventer un domaine de messagerie** — un `hopital-fictif.ma` qui n'existe pas aujourd'hui. Écarté :
n'importe qui peut le déposer demain, et l'adresse deviendrait alors joignable. Les domaines
réservés par la norme n'ont pas ce défaut.

## Ce qui a été publié, quand, et pourquoi ce n'est pas rattrapable

**Les anciennes valeurs sont dans un dépôt public.** Elles y sont entrées avec la couche source du
jeu de données, versée au fil des fusions successives ; l'échantillon de vingt-trois fichiers qui
les exposait le plus directement n'a, lui, **jamais été poussé** — la revue qui a trouvé ce défaut
l'a trouvé avant la publication de ce lot-là, et rien n'a été poussé depuis.

Ce qui a été publié ne se retire pas. **Un historique poussé reste accessible par référence directe
même après réécriture** : les objets restent servis par leur empreinte tant qu'ils ne sont pas
ramassés, et les copies, les miroirs et les caches d'index ne se rappellent pas. La seule annulation
propre serait la suppression du dépôt.

**On corrige donc en avant.** Aucun historique n'est réécrit, et cette décision consigne l'état :
c'est plus honnête qu'un historique nettoyé qui laisserait croire que rien n'a eu lieu, et c'est
l'illustration la plus nette de la frontière d'irréversibilité que ce projet documente depuis le
début — celle qui sépare ce qui se corrige de ce qui ne se corrige plus.

## Le coût mesuré sur l'évaluation du rapprochement

**Nul, et c'est ce que la préservation des égalités devait produire.** Toutes les grandeurs sont
identiques avant et après, à la valeur près :

| Grandeur | Avant | Après |
|---|---|---|
| Seuil retenu | 0,5 | 0,5 |
| Précision | 1 | 1 |
| Rappel | 1 | 1 |
| F-mesure | 1 | 1 |
| Vrais positifs / faux positifs / faux négatifs | 991 / 0 / 0 | 991 / 0 / 0 |
| Grappes prédites | 991 | 991 |
| Paires candidates | 5 014 | 5 014 |
| Apport : communes / probabiliste seul / collision seule | 870 / 121 / 56 | 870 / 121 / 56 |
| `probability_two_random_records_match` | 3,828588328212744e-06 | inchangé |

`linkage/courbe_precision_rappel.csv` et `linkage/modele_estime.json` sont **inchangés au fichier
près** après réengendrement complet. Ce que cela établit : la performance du rapprochement ne dépend
pas de la forme des valeurs mais de leur structure d'accord, et la transformation a préservé
celle-ci.

## Vérification

`tests/test_disjonction_structurelle.py` porte l'invariant, une exécution par champ recensé. Le
message d'échec nomme la table, la colonne, la valeur fautive, l'espace réel visé et la propriété
violée. **Chaque champ a été muté séparément** avec une valeur structurellement possible dans son
espace réel — un numéro de dix chiffres sur un préfixe attribué, une adresse chez un fournisseur
exploité, une carte à lettres, une immatriculation de neuf chiffres — et la propriété rougit à
chaque fois en nommant ce champ, et lui seul.

## Ce qui aurait invalidé cette décision

**Qu'aucune impossibilité structurelle ne soit disponible pour un champ recensé.** Il aurait alors
fallu soit retirer la colonne du jeu publié, soit admettre que le champ ne peut pas être garanti et
l'écrire. Aucun des champs recensés n'est dans ce cas.

**Que la transformation ne puisse pas préserver les égalités.** L'évaluation du rapprochement aurait
changé, et c'est un chapitre du rapport qui aurait bougé, pas un fichier de configuration. La mesure
a été faite : les trois décomptes d'accord sont identiques au chiffre près.
