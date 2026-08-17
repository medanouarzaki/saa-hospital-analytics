# ADR 0045 — Le tableau de bord compte sept pages, et les indicateurs sans matière sont retirés

**Statut.** Accepté.

---

## Contexte

Le cadrage du projet énumérait les pages du tableau de bord et les indicateurs qu'elles
porteraient. Une campagne de mesure sur la base complète a confronté cette liste à ce que la chaîne
produit réellement. Plusieurs indicateurs prévus n'ont pas de matière : le champ manque, ou
l'activité n'existe pas dans l'établissement mesuré, ou la colonne qui semblait les porter s'avère
ne rien porter.

Ces deux causes ne se confondent pas, et l'ADR `0003` a déjà établi pourquoi : un indicateur non
calculable est un défaut du système d'information, un indicateur sans objet est une propriété de
l'établissement, et les confondre ferait reprocher au logiciel une absence de champ là où c'est
l'hôpital qui n'a pas l'activité.

## Décision

**Le tableau de bord compte sept pages :** activité, rendez-vous, urgences, séjours, facturation et
recouvrement, qualité des données, rapprochement d'identités.

**Les indicateurs suivants sont retirés**, chacun pour le motif mesuré indiqué :

| indicateur retiré | motif |
|---|---|
| consultations par médecin | aucun référentiel des médecins n'existe |
| accouchements | aucun marqueur d'accouchement n'existe |
| taux de césarienne | l'établissement n'exerce pas d'activité chirurgicale |
| interventions chirurgicales | même motif |
| capacité litière existante | aucun champ de structure n'existe |
| ventilation par organisme payeur | aucun fait ne référence la dimension correspondante |

**La page de recommandations prévue par le cadrage est retirée.** Les recommandations demeurent,
comme chapitre du rapport et non comme page du tableau de bord.

## Justification des points non triviaux

### Pourquoi les consultations par médecin sont retirées

Le numérateur est calculable, le dénominateur ne l'est pas. Aucune table du schéma source ne porte
d'effectif médical, et la recherche du champ a été conduite par deux chemins indépendants — le
registre des champs et le catalogue de la base — l'un et l'autre éprouvés au préalable contre des
noms de colonnes dont l'existence est certaine.

La colonne qui semblait pouvoir tenir lieu de référentiel n'en tient pas lieu, et c'est mesuré :
**ses 40 650 valeurs sont orphelines à 100 %** de la dimension des agents, sur 20 valeurs distinctes
formant un espace de codes disjoint. Il n'existe donc dans la base **aucun objet décrivant un
médecin** — ni son existence, ni sa spécialité, ni son temps de présence.

L'écart que produirait un affichage malgré tout est mesuré : 206,31 consultations par médecin en
divisant par les 20 identifiants observés, contre 518 publiées en divisant par les 8 médecins que
la source nationale dénombre pour ce tableau — **60,17 % d'écart, qui ne mesure pas une erreur de
calcul mais deux dénominateurs différents**. Afficher le premier en le présentant comme le second
serait faux.

### Pourquoi les accouchements sont retirés, et pourquoi le code diagnostique n'y suffit pas

Aucun marqueur d'accouchement n'existe dans la couche source, vérifié par les mêmes deux chemins.
Trois voies de contournement ont été examinées et les trois échouent.

La plus tentante est le code diagnostique international, dont l'une des valeurs désigne
explicitement un accouchement unique spontané et apparaît 731 fois. **La mesure l'interdit** :
**324 de ces 731 lignes portent sur des patients de sexe masculin**, et la valeur apparaît dans les
trois types d'épisode et les cinq services émetteurs avec une part comprise entre 3,30 % et 5,78 %
— soit, à la fluctuation près, une chance sur trente partout, ce que produit un tirage uniforme sur
les trente codes de la nomenclature. Le code ne porte **aucun signal obstétrical** : il est
indépendant du sexe, du type d'épisode et du service.

C'est le cas le plus net du dépôt où déduire le contenu d'une colonne de son nom aurait produit un
chiffre faux en le faisant passer pour mesuré.

Les deux autres voies échouent aussi : le service d'hospitalisation en gynéco-obstétrique compte
401 séjours, mais un séjour dans cette unité n'est pas un accouchement — l'unité admet toute la
pathologie gynécologique, et son libellé le dit ; et aucun acte d'accouchement ne figure au
catalogue des actes, dont les trente-quatre entrées se répartissent en quatre familles seulement.

### Pourquoi la chirurgie relève de l'absence d'activité et non de l'absence de champ

L'ADR `0003` établit cette absence par quatre contrôles indépendants : recherche exhaustive de la
dénomination de l'établissement sur le texte intégral des deux exercices publiés, avec un contrôle
positif portant sur les occurrences connues ; contrôle de somme entre les lignes visibles d'une
section et son total imprimé, exact sur les deux exercices et les deux colonnes ; cohérence de la
structure du document, dont les tableaux recensent une activité et non un parc d'établissements ; et
corroboration par un rapport de la Cour des comptes décrivant une gynéco-obstétrique fonctionnant
sans activité chirurgicale, huit ans plus tôt.

Cette absence est en outre vérifiée **en base plutôt que reprise** : aucun service chirurgical parmi
les sept de la dimension des services, aucune ligne de facture portant un acte chirurgical, et
surtout **la lettre clé de la chirurgie est absente des sept lettres effectivement employées**.

Le champ manque aussi. Mais le classer par le champ produirait la recommandation fausse dont l'ADR
`0003` met en garde : ajouter un champ de mode d'accouchement ne ferait pas apparaître de
césariennes dans un établissement qui n'en pratique pas. **C'est l'absence d'activité qui commande.**

### Pourquoi la ventilation par organisme payeur est retirée

La dimension des organismes existe et porte sept codes. **Aucun des six faits ne la référence** :
ni par un test de relation déclaré, ni par une colonne du modèle — aucune colonne d'organisme, de
compagnie ou de police n'existe dans les six faits. Le rattachement à l'organisme payeur n'existe
que sur la dimension des patients, qui n'est pas testée vers celle des organismes.

Une ventilation par organisme exigerait donc de joindre la dimension des patients à la place du
fait, ce qui produirait une ventilation par organisme **du patient** et non par organisme
**payeur de l'épisode** — deux grandeurs différentes qu'un titre de graphique ne distinguerait pas.

La part payée par un organisme reste affichée, elle : les colonnes correspondantes existent sur le
fait de facturation, et leur décomposition est exacte au centime, le résidu mesuré valant zéro sur
les quatre lignes de la ventilation par type d'épisode.

### Pourquoi la page de recommandations est retirée

C'est le point qui mérite d'être traité et non survolé, parce qu'il retire une page entière.

**Aucun élément de cette page ne serait recalculé depuis les données.** Une recommandation est un
jugement porté sur ce que les mesures montrent ; elle ne se dérive d'aucune table, aucune requête ne
la produit, et rien n'y casserait si les données changeaient. L'afficher à côté d'indicateurs
recalculés lui prêterait le même statut qu'eux, et c'est précisément l'inverse de ce que le cadrage
cherche à établir.

**Les recommandations demeurent, comme chapitre du rapport.** Leur cœur est constitué des trois
champs manquants que la mesure a nommés, chacun débloquant exactement un indicateur :

1. **une table de structure de l'établissement**, portant au minimum la capacité litière existante
   et son horodatage ;
2. **un référentiel des médecins**, dont découlerait l'effectif médical ;
3. **un marqueur d'accouchement** rattaché au séjour.

L'absence de chacun a été vérifiée par les deux chemins indépendants mentionnés plus haut.

## Conséquences

Sept pages, dont deux — qualité des données et rapprochement d'identités — ne portent aucun
indicateur de la nomenclature nationale et existent pour ce que la chaîne produit en propre.

Le rapport porte un chapitre de recommandations dont le contenu est nommé ici et dont la matière
est le document d'exigences statistiques.

Chaque retrait est traçable à une mesure, et le document d'exigences statistiques porte le tableau
complet, indicateur par indicateur, avec son classement en trois valeurs.

## Ce qui aurait invalidé cette décision

Qu'un référentiel des médecins existe quelque part dans la chaîne, auquel cas les consultations par
médecin seraient calculables et resteraient.

Que le code diagnostique porte un signal obstétrical — c'est-à-dire qu'il soit corrélé au sexe, au
service ou au type d'épisode. Il ne l'est sur aucun des trois, et sa présence sur 324 patients
masculins suffit à le trancher.

Qu'une ligne de l'établissement figure au tableau national des interventions chirurgicales sous une
graphie non testée, ou qu'un écart apparaisse entre la somme des lignes d'une section et son total
imprimé. Ni l'un ni l'autre.

## Sources

`docs/decisions/0003-volumetrie.md` — absence d'activité chirurgicale établie par quatre contrôles,
et distinction entre indicateur non calculable et indicateur sans objet.
`docs/exigences_statistiques.md` — tableau complet des indicateurs, classement, et champs manquants.
`docs/modules_non_observes.md` — nomenclature des indicateurs remontés et grille à trois valeurs.
`docs/champs/registre_champs.yml` et le catalogue de la base — les deux chemins de vérification
d'absence d'un champ.
