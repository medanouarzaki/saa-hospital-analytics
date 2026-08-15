# ADR 0044 — La définition de chaque indicateur est portée par un registre unique, vérifié par test

**Statut.** Accepté.

---

## Contexte

Le tableau de bord affiche des indicateurs dont la définition doit être écrite quelque part. Deux
emplacements sont possibles : au plus près de l'affichage, dans le code de chaque page, ou dans un
fichier unique séparé du code.

Le critère de terminé du travail en cours exige que la correspondance entre ce qui est affiché et
ce qui est défini soit **vérifiée par un test et non par une relecture**. Ce critère écarte à lui
seul la première option : une définition écrite dans le code de sa page ne peut pas être confrontée
à l'affichage, elle en fait partie.

Le dépôt porte déjà deux registres de ce genre — le registre des champs de la couche source et le
registre des sources — et un garde-fou de la chaîne d'intégration continue qui vérifie, dans les
deux sens, que tout fichier de test présent est exécuté et que tout fichier référencé existe.

## Décision

**La définition d'une phrase par indicateur est portée par un fichier unique, sur le modèle du
registre des champs.**

Chaque entrée porte au minimum :

- un identifiant ;
- la page qui l'affiche ;
- le libellé affiché ;
- la définition en une phrase ;
- la décision que l'indicateur sert ;
- les objets lus ;
- la filtrabilité par période ;
- la mention de ce dont la valeur est recalculée.

**Un test bidirectionnel vérifie la correspondance : tout indicateur affiché a une entrée au
registre, toute entrée du registre est affichée.**

## Justification des points non triviaux

### Pourquoi un fichier unique plutôt qu'une définition au plus près de l'affichage

Une définition écrite dans le code de sa page ne peut pas servir de référence contre laquelle
vérifier cette même page. Le fichier séparé crée les deux termes que le test compare ; sans lui, il
n'y a rien à comparer et la vérification retombe sur une relecture, que le critère de terminé
refuse.

Le registre a de surcroît un lecteur qui n'est pas la machine : la définition d'une phrase par
indicateur est ce qu'un lecteur du rapport consulte pour savoir ce qu'une courbe mesure. Dispersée
dans le code, elle ne se lit pas d'un trait.

### Pourquoi un test bidirectionnel plutôt qu'un contrôle dans un seul sens

Le garde-fou de collecte de la chaîne d'intégration continue est le précédent, et il casse déjà
dans les deux sens : un fichier de test présent sur le disque mais absent de la configuration
d'exécution ne serait jamais lancé sans qu'aucun échec ne le signale ; un fichier référencé mais
absent du disque échouerait tardivement et loin de sa cause.

Les deux défaillances symétriques existent ici. Un indicateur affiché sans entrée au registre est
un chiffre sans définition — exactement ce que le critère de terminé interdit. Une entrée sans
indicateur affiché est une définition morte, qui laisse croire à une couverture plus large que la
réalité. Un contrôle dans un seul sens laisserait passer l'une des deux.

### Pourquoi la filtrabilité par période figure au registre

Elle n'est pas un détail d'affichage mais une propriété de l'indicateur, mesurée et non choisie :
un indicateur porté par un objet sans colonne temporelle ne se filtre pas, quelle que soit
l'interface. L'inscrire au registre permet à l'affichage de la lire plutôt que de la redéclarer, et
au test de vérifier qu'aucun indicateur non filtrable ne se trouve sur une page qui porte un filtre
sans marquage. L'ADR `0046` décide de la règle correspondante.

### Pourquoi la mention de ce dont la valeur est recalculée

Le cadrage impose que les indicateurs soient recalculés depuis les tables de faits plutôt que repris
d'une colonne calculée en amont. Cette règle souffre des exceptions mesurées, consignées par l'ADR
`0047`. Porter au registre, pour chaque entrée, ce dont sa valeur est effectivement recalculée rend
ces exceptions visibles à l'endroit où elles comptent, plutôt que reléguées dans un document que
l'on ne relit pas.

## Conséquences

Un indicateur ne peut plus être ajouté à une page sans que son entrée soit écrite, ni retiré sans
que son entrée le soit : le test casse dans les deux cas.

Le registre devient la source de la table de correspondance du rapport, qui n'a plus à être tenue
séparément.

Le format du registre reprend celui du registre des champs : un en-tête en commentaires portant le
titre, la règle de preuve, et la liste explicite des exclusions avec leur motif ; puis les entrées.

## Ce qui aurait invalidé cette décision

Que la correspondance puisse être vérifiée sans registre séparé — par exemple si l'interface
exposait la liste des indicateurs affichés sous une forme lisible par un test, faisant du code de
la page son propre registre. Elle ne l'expose pas.

Que le nombre d'indicateurs soit assez faible pour qu'une relecture tienne lieu de vérification. Il
ne l'est pas : trente-sept indicateurs répartis sur sept pages ont été dénombrés, et une relecture
de trente-sept entrées à chaque modification est exactement le genre de contrôle qui se relâche.

## Ce que cet enregistrement ne fait pas

**Il ne fixe pas le contenu du registre.** Les entrées sont écrites ensuite, à partir des mesures,
et non par cet enregistrement.

## Sources

`docs/champs/registre_champs.yml` — forme d'en-tête et règle de preuve reprises.
`docs/sources/sources.yml` — second précédent de registre unique dans ce dépôt.
`tests/test_collecte_ci.py` — garde-fou bidirectionnel pris pour modèle, qui compare la liste
des fichiers de test présents sur le disque à celle des emplacements d'exécution déclarés.
`docs/decisions/0046-filtre-de-periode-porte-par-page.md` — règle de filtrabilité correspondante.
`docs/decisions/0047-ecarts-assumes-au-cadrage.md` — exceptions à la règle de recalcul.
