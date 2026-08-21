# ADR 0091 — Un format d'affichage au registre, et un relevé daté des critères

**Statut.** Accepté.

---

## Contexte

Deux choses à vérifier, et une à écrire.

Le rapport du travail précédent affirmait que les décimales longues du support étaient « le rendu du
registre, et le rapport les compose à l'identique ». **L'affirmation devait être mesurée, non crue.**

Et le projet n'avait aucun relevé de ses critères de terminaison : la question *un critère a été
déclaré atteint alors qu'il ne l'était pas ; combien d'autres ?* n'avait pas de réponse écrite.

## Décision

### 1. L'affirmation est vérifiée : elle était vraie, et la vérification a trouvé autre chose

**Mesuré sur le PDF composé, page 57** : le rapport composait bien
`0,9984856133266027` — seize décimales —, exactement comme le support. L'affirmation tenait.

**Ce que la vérification a trouvé et que personne ne cherchait** : le `0,9995` que le tableau
d'ablation porte pour la variante A n'est pas une valeur du registre arrondie. Il est **tapé à la
main**, dans le tableau même où les trois autres valeurs viennent du registre, et **aucun contrôle
ne peut le voir** — celui du registre vérifie la correspondance entre appels et entrées, pas les
chiffres littéraux. Signalé, non corrigé : les chapitres n'étaient pas ouverts à ce travail.

### 2. Le registre porte un format d'affichage, et la valeur consignée ne bouge pas

**Arrondir n'est pas taper.** Une entrée peut désormais porter `decimales` : la valeur consignée
reste celle que la commande a rendue — c'est elle que `mesurer.py --verifier` confronte, à
l'égalité stricte —, et seul son **rendu** est arrondi.

Cinq entrées du registre, et cinq seulement, portaient plus de quatre décimales. Toutes les cinq
sont appelées par le support.

| grandeur | avant | après | format posé |
|---|---|---|---|
| F-mesure de la ligne de base | 0,9076682316118936 | **0,9077** | 4 décimales |
| F-mesure de la variante cumulée | 0,9984856133266027 | **0,9985** | 4 décimales |
| marge du modèle complet | 270,868434285775 | **270,87** | 2 décimales |
| marge de la variante A | −2,6554053556955406 | **−2,66** | 2 décimales |
| marge de la variante C | −9,571871091053188 | **−9,57** | 2 décimales |

Quatre décimales pour les proportions : c'est le format que le rapport emploie déjà pour ses
corrélations et ses taux. **Deux décimales pour les poids : ce format n'existait pas, il est posé
ici** — ce qui compte d'une marge est son signe et son ordre de grandeur, non sa quinzième décimale.

**Le rapport change avec le support, et c'est le but.** Une planche et un chapitre qui composeraient
la même valeur différemment seraient un défaut. Les cinq valeurs changent aux deux endroits à la
fois, parce qu'elles viennent du même fichier produit.

### 3. Un relevé daté des critères, sous `docs/`

`docs/releve_des_criteres.md`, daté, en deux parties : **douze critères qu'un contrôle établit**,
chacun avec sa commande et sa sortie brute, et **dix qu'aucun contrôle ne peut établir**, chacun
avec ce qui le vérifierait à la main.

Il n'entre pas dans le rapport.

## Conséquences

**Un critère est FAUX, et c'est la réponse à la question du jury.** `mesurer.py --verifier` rend
**neuf écarts** entre le registre et ce que ses commandes rendent aujourd'hui. Quatre sont
directement imputables aux travaux de rédaction récents — trois sections fondues en une, des
identifiants de relevé qui ont cessé d'être cités, cinq tracés du tableau de bord passés par une
fonction commune. Trois autres mesurent **zéro** là où le registre consigne cinq, seize et six :
la commande cherche sa matière là où elle n'est plus.

**Rien ne pouvait le voir.** Cette vérification n'est pas un travail d'intégration continue et ne
peut pas l'être : elle ouvre la base et compare des valeurs mesurées sur la période entière, quand
l'exécuteur n'engendre que trois mois. Le critère n'est vérifiable qu'à la main — ce que le relevé
vient de faire, pour la première fois.

**Il n'est pas corrigé ici** : corriger un écart demande de reporter une valeur remesurée au
registre, ce qui change une valeur composée par le rapport, et ni les chapitres ni les valeurs du
registre n'étaient ouverts à ce travail.

**Deux écritures hors liste fermée, signalées.**

`docs/chiffres/generer_chiffres_tex.py` et `tests/test_registre_des_chiffres.py`. La liste ouvrait
`report/chiffres.tex` « s'il est produit et qu'un format le change » — or ce fichier porte en tête
« Ne pas modifier à la main », et il n'existe aucune voie légitime pour changer un produit sans
changer son producteur ; et le contrôle qui confronte le produit au registre à l'égalité stricte
aurait rougi sur une valeur juste. Les deux changements sont minimaux et n'ont qu'un objet : faire
exister le format que ce travail devait poser.

**Le mécanisme est éprouvé dans les deux sens.** Un nouveau contrôle vérifie qu'une entrée formatée
se rend avec exactement le nombre de décimales déclaré, **et** que sa valeur consignée en porte
davantage — sans quoi le format n'arrondirait rien et le témoin ne prouverait plus qu'il agit.
Arrondir la valeur consignée au registre le fait rougir ; retirer un format sans refaire le rendu
fait rougir l'autre.
