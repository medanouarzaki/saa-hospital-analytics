# ADR 0049 — Toute colonne des couches aval est déclarée et décrite ; le registre des champs n'est pas étendu

**Statut.** Accepté.

---

## Contexte

Trois mesures ont été prises avant d'écrire quoi que ce soit.

**1. Le contrôle de provenance ne couvre pas ce qu'on lui prête.**
`tests/test_provenance.py::test_couverture_bidirectionnelle` nomme les trois schémas dans sa
requête — `where c.table_schema in ('source', 'intermediate', 'marts')` — mais joint
`information_schema.tables` en filtrant `t.table_type = 'BASE TABLE'`. Or l'ADR `0018` matérialise
`intermediate` et `marts` **en vues**. Mesure :

```
 table_schema | table_type | colonnes
--------------+------------+----------
 intermediate | VIEW       |      175
 marts        | VIEW       |      223
 source       | BASE TABLE |      175
```

Une fois le filtre appliqué, la requête ne retient que les 175 colonnes de `source` : **zéro des
398 colonnes des deux couches qu'elle nomme**. Ce n'est pas un défaut de ce contrôle — l'ADR `0018`
documente ce filtre comme la conséquence voulue de la matérialisation en vues, et il tient
exactement ce qu'il doit tenir sur la couche source. **C'est un défaut de ce qui était affirmé de
lui.**

**2. La couverture documentaire des couches aval est nulle.** Trois nombres, trois périmètres :

| Nombre | Périmètre exact |
|---|---|
| **398** | colonnes réellement présentes au catalogue dans `intermediate` (175) et `marts` (223) |
| **185** | colonnes *déclarées* dans les 30 fichiers de propriétés de ces deux couches (61 en `intermediate`, 124 en `marts`) |
| **0** | colonnes déclarées portant une description non vide |

Il manque donc 213 déclarations, et aucune des 185 déclarations existantes ne dit ce que la colonne
contient. Le dictionnaire du classeur livré en porte la trace : ses 160 lignes affichaient toutes
la mention « Non documentée ».

**3. Le partage des colonnes des six dimensions, établi par lecture des modèles SQL et non des
noms.** 63 colonnes réelles :

| Nature | Colonnes | Où |
|---|---|---|
| Reprise directe | 41 | les 37 colonnes textuelles de `dim_patient`, et le code des quatre dimensions à clé naturelle |
| Reprise transformée | 9 | les colonnes de `dim_patient` que la couche intermédiaire convertit en date, horodatage ou booléen |
| Calcul du projet | 10 | toutes les colonnes de `dim_date` |
| Mécanique d'historisation | 3 | `valide_de`, `valide_jusqu_a`, `est_courante` de `dim_patient` |

## Décision

**1. Le registre des champs n'est pas étendu aux couches aval.** Ses étiquettes de provenance —
observée, documentée, posée — qualifient un **champ du système observé** : elles disent d'où l'on
sait qu'il existe et ce qu'il contient. Une colonne calculée par le projet a pour provenance son
propre calcul, et lui attribuer l'une de ces trois étiquettes n'aurait pas de sens. Étendre le
registre confondrait deux natures : ce qu'on a relevé chez autrui, et ce qu'on a soi-même construit.

**2. Toute colonne réelle des couches aval est déclarée à son fichier de propriétés, et toute
colonne déclarée porte une description.** Un contrôle distinct le tient,
`tests/test_documentation_couches_aval.py`, avec une propriété par exigence.

**3. Une description dit ce que la colonne contient, et sa forme suit sa nature :**

- **reprise** — le libellé exact relevé au système observé et la référence du relevé ;
- **reprise transformée** — la même chose, plus la transformation subie ;
- **calcul du projet** — la formule en toutes lettres et les colonnes qui y entrent, de sorte qu'un
  lecteur puisse refaire le calcul ;
- **mécanique** — sa fonction et le comportement attendu.

**Une colonne portant un code dont la signification est inconnue reçoit une description qui dit
précisément cela** : elle nomme la colonne source, énonce qu'aucune table de correspondance n'est
fournie par le système ni documentée par une source, et n'invente aucun libellé.

## La distinction qui a causé la dette

La règle « aucun libellé inventé » — posée par l'ADR `0020` pour les quatre dimensions à clé
naturelle — porte sur les **valeurs de code venues du système observé** : on ne décide pas que le
code `HGO` signifie tel service si aucune source ne l'établit.

**Elle ne s'étend pas aux descriptions de colonnes que le projet a lui-même conçues.** Décrire
`valide_jusqu_a` comme la borne haute exclue de validité d'une version n'invente rien : c'est ce
que le modèle calcule, et l'écrire est de la documentation, pas de la fabrication.

**La confusion des deux est ce qui a produit zéro description sur 398 colonnes.** Une prudence
légitime sur les valeurs de code s'est étendue, sans être réexaminée, aux colonnes elles-mêmes.
Cette décision sépare les deux explicitement.

## Ce qui aurait invalidé cette décision

Que le contrôle de provenance couvre réellement les couches aval : la propriété serait alors déjà
tenue, et un second contrôle ferait doublon. **Il ne les couvre pas**, et la mesure 1 le montre —
zéro colonne retenue sur les 398 des deux couches nommées.

## Portée et suite

Le contrôle porte sur les **deux couches entières** dès son écriture, et non sur les seules
dimensions traitées ici. Il est donc rouge à l'issue de ce travail, et c'est voulu : son message
d'échec nomme, modèle par modèle, ce qui reste à documenter. Il sert de compteur de progression et
ne sera placé en intégration continue qu'une fois les deux couches complètes, pour ne pas bloquer
la chaîne sur une dette connue et chiffrée.

État à l'issue de ce travail : les six dimensions sont complètes — 54 déclarations ajoutées et 63
descriptions écrites — et il reste 159 colonnes à déclarer et 176 à décrire.
