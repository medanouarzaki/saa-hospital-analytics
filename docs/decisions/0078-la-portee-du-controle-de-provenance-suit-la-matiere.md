# ADR 0078 — La portée du contrôle de provenance suit la matière, jusque dans les annexes

**Statut.** Accepté.

---

## Contexte

Le chapitre du système d'information portait quatre tableaux de relevé exhaustifs, cent
vingt-six lignes au total. Un tableau de cette taille ne se lit pas : il se saute. La réécriture les
descend en annexe et laisse dans le corps une synthèse et un extrait.

**Le déplacement seul aurait cassé une propriété, et la mesure l'a montré avant l'écriture.**
`tests/test_provenance_des_chapitres.py` exige que chaque champ du relevé soit dans l'un de trois
cas : invoqué comme preuve par le registre des champs, cité par un fichier de chapitre, ou déclaré
non employé avec son motif. Il ne lisait que `report/chapitres/*.tex`.

```
champs au relevé                       143
invoqués par le registre des champs     70
déclarés non employés                   17
orphelins si les tableaux descendent    56
```

Les cinquante-six sont des onglets, des menus, des filtres et des colonnes de résultat —
des éléments d'écran qu'aucune colonne du modèle n'emploie. Ils ne tenaient que parce que le
chapitre les imprimait.

## Décision

**La portée du contrôle s'étend aux fichiers d'annexe.** Quand une matière se déplace, c'est la
portée du contrôle qui suit la matière, jamais la matière qui reste où le contrôle sait déjà
regarder. Un contrôle qui dicte l'emplacement du contenu n'est plus un contrôle, c'est une
contrainte de conception déguisée.

C'est le même geste que l'extension du contrôle d'image au dépôt entier (`0076`), et pour le même
motif.

### La portée est déclarative, jamais devinée

Les fichiers examinés sont énumérés dans une constante `ANNEXES`, et cette liste est **confrontée
aux inclusions de `report/annexes.tex` dans les deux sens**. Une seconde constante, `EXCLUS`, porte
ce qui est délibérément hors examen — aujourd'hui le dictionnaire de données, produit
mécaniquement depuis le registre des champs, qui ne porte aucune déclaration de provenance et n'a
pas à en porter.

Découvrir les fichiers par une convention de répertoire aurait fait entrer n'importe quel fichier
déposé là sans que personne ne l'ait décidé. Une liste non confrontée aurait laissé passer
l'inverse.

### Quatre voies par lesquelles ce contrôle serait vert sur un champ sans provenance

Elles ont été cherchées avant d'écrire l'extension, et les quatre sont fermées et éprouvées par
mutation.

| voie | ce qui arriverait | fermée par |
|---|---|---|
| un fichier d'annexe absent de `ANNEXES` | ses identifiants ne comptent pas, les champs tombent orphelins | la confrontation, premier sens |
| un fichier resté dans `ANNEXES` que le document n'inclut plus | ses identifiants comptent alors qu'il n'est plus composé | la confrontation, second sens |
| `annexes.tex` retiré du fichier principal | toutes les annexes sortent du document, aucune liste ne bouge | une propriété dédiée |
| un identifiant porté sans être déclaré, ou déclaré sans être porté | la déclaration cesse d'être vraie | la correspondance dans les deux sens, désormais appliquée aux annexes |

La deuxième est la dangereuse : c'est la seule où le contrôle resterait **vert** sur des champs
disparus du document.

## La preuve de non-perte

Le décompte des champs couverts est identique des deux côtés du déplacement, et c'est ce qui
établit qu'aucun élément n'est perdu.

```
                                  avant    après
champs au relevé                    143      143
couverts par le contrôle            143      143
  dont registre des champs           70       70
  dont cités par un fichier          56       56
  dont déclarés non employés         17       17
perdus : aucun          gagnés : aucun
```

## Ce qui a été écarté

**Garder un index des identifiants dans le corps du chapitre.** Écarté : trois quarts de page d'un
index que personne ne lit, pour éviter de toucher au contrôle.

**Laisser les tableaux dans le corps.** Écarté : c'est l'état que la réécriture corrige.

**Déclarer les cinquante-six champs non employés.** Écarté, et c'eût été faux : ils sont employés,
par l'annexe.

## Ce que cette décision ne peut pas voir

**Elle ne dit rien de ce qu'un fichier d'annexe contient.** Un tableau vidé de ses lignes mais dont
l'en-tête conserverait ses déclarations ferait rougir la correspondance, mais un tableau dont on
retirerait une ligne ET sa déclaration passerait sans bruit, exactement comme dans un chapitre.
C'est l'angle mort que le décompte de sections ferme pour les chapitres, et **aucun décompte
équivalent ne porte sur les lignes d'un tableau**.

**Elle ne voit pas le document composé.** Un fichier d'annexe inclus mais dont la composition
échouerait silencieusement — un environnement mal fermé qui avale son contenu — passerait ce
contrôle.
