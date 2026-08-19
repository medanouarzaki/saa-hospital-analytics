# ADR 0057 — Le registre des indicateurs, la couche que les pages lisent, et le contrôle qui les relie

**Statut.** Accepté.

---

## Contexte

Le registre des indicateurs déclare, pour chacune de ses quarante entrées, les objets que
l'indicateur lit. Une mesure a établi que **les quarante entrées sur quarante déclarent des objets
que leur page ne lit pas** : le registre nomme `marts`, `intermediate` et `linkage`, quand les pages
lisent le schéma d'instantané, leur chemin de recherche y étant réduit.

Deux contrôles existaient déjà et ne pouvaient pas le voir. Celui du registre vérifie que chaque
objet cité **existe au catalogue** — un objet déclaré que nul ne lit y passe, et une table lue que
rien ne déclare y passe aussi. Celui de l'instantané vérifie que chaque objet cité **existe dans
l'instantané**, et que chaque copie a le même contenu que son origine. Aucun ne compare la
déclaration à l'usage.

Trois indicateurs n'étaient par ailleurs couverts par aucun contrôle lisant leurs objets réels :
`facturation_taux_recouvrement`, `facturation_aboutissement_relances` et
`qualite_provenance_champs`.

## Décision

**1. La divergence de schéma n'est pas un défaut : c'est un invariant, et il est désormais écrit.**
Le registre nomme la couche modélisée parce que c'est là qu'est la provenance analytique — un objet
y est produit par un modèle, documenté et testé. Les pages lisent l'instantané parce qu'une
reconstruction de la couche modélisée fait disparaître ses vues le temps qu'elle dure, et qu'un
lecteur y rencontrerait une erreur d'objet inexistant. **Les deux ont raison.** L'invariant qui les
relie est le nom de table : *pour chaque page, l'ensemble des tables que ses requêtes nomment, privé
de son schéma, égale l'ensemble des tables que ses entrées déclarent, privé du sien.* Le registre
n'est donc pas réécrit pour nommer l'instantané.

**2. Trois déclarations étaient en défaut réel et sont corrigées.** Elles omettaient une table que
leur page lit : `instantane_etat` pour `sejours_non_clos` et `facturation_anciennete_creances`,
`instantane_etat` et `instantane_parametres` pour `sejours_indicateurs_reglementaires`. Ces deux
tables de service **n'existent que dans l'instantané**, dont elles décrivent l'état et les
paramètres ; elles n'ont aucun homologue modélisé, et sont déclarées sous le seul schéma où elles
existent. C'est l'unique exception à la règle du point 1, et elle est de nature : ce ne sont pas des
copies, ce sont les tables propres de l'instantané.

**3. Le contrôle de correspondance observe les requêtes émises, il n'analyse pas le code source.**
Une extraction syntaxique s'est déjà trompée dans ce dépôt — elle attribuait une table à une requête
qui ne la nomme pas — et elle ne résout pas une requête construite par interpolation, dont le texte
n'existe qu'à l'exécution. Le point de lecture porte donc un journal facultatif, `None` en usage
normal, qu'un contrôle ouvre pour recueillir ce que la page émet réellement.

**4. Le contrôle porte par page, non par indicateur, et c'est une forme plus faible assumée.**
`interroger` ne reçoit que du SQL ; l'identifiant de l'indicateur n'accompagne la requête à aucun
niveau commun aux neuf pages. Le contrôle voit une table lue que rien ne déclare et une table
déclarée que rien ne lit ; il ne voit pas une table déclarée par la mauvaise entrée d'une même page.

**5. Les trois indicateurs non couverts le sont, chacun sous la référence qu'il admet, et pas
au-delà.** La provenance des champs a une référence **externe** — le registre des champs, un fichier
du dépôt, contre un agrégat construit depuis les commentaires du catalogue : deux artefacts
indépendants portant la même grandeur. Les deux indicateurs de recouvrement n'en ont **aucune** :
`agg_recouvrement` est le seul artefact qui porte ces montants, et les recalculer retranscrirait le
modèle qui les produit. Ils reçoivent donc une propriété de **cohérence interne** — un recouvré
n'excède pas un dû, des relances abouties n'excèdent pas des relances émises, un taux tombe entre
zéro et un — déclarée comme plus faible qu'une égalité.

## Justification des points non triviaux

### Pourquoi chaque page est rendue dans un processus fils

Trois rendus successifs dans un même processus se terminent **sans trace ni code d'erreur** à
l'intérieur de l'image du service ; un rendu par processus rend la main normalement. La même
observation était déjà consignée sur la machine de développement. Un contrôle qui rendrait les neuf
pages dans son propre processus mourrait donc en silence, et **un contrôle mort ne rougit pas** : la
forme à processus fils n'est pas une précaution de style, c'est la condition pour que ce contrôle
existe.

### Pourquoi chaque option de chaque sélecteur est exercée

La page des données ne lit qu'**une** table par rendu, celle que son sélecteur retient, alors que
ses deux entrées en déclarent quatre. Sans parcourir les sélections, l'égalité serait fausse pour
cette page — et la corriger en n'y déclarant qu'une table serait pire, l'utilisateur pouvant lire
les trois autres.

### Ce que le journal de requêtes ne prouve pas

Si une page lisait une table qu'aucune entrée ne déclare **et** que le journal perdait précisément
cette requête, l'écart disparaîtrait des deux côtés et le contrôle serait vert à tort. La
bidirectionnalité de la propriété rattrape toute perte portant sur une table déclarée — vérifié par
mutation — mais pas ce cas-là, qui n'est pas couvert et n'est pas prétendu l'être.

## Ce qui n'a pas été fait, et pourquoi

**Les trente-sept autres entrées ne sont pas réécrites.** Leur divergence de schéma est l'invariant
du point 1, désormais écrit et vérifié ; les réécrire ferait perdre la provenance analytique que le
registre porte.

**Aucun bloc de seconde mesure n'est corrigé.** L'audit des quatre blocs restants a établi qu'aucun
n'est dans le cas de celui qui a été retiré : les taux et délais de rendez-vous se comparent à des
agrégats calculés par d'autres colonnes, les séjours non clos à la colonne brute dont le drapeau
dérive. Deux réserves sont consignées sans être traitées : les effectifs des urgences ne vérifient
que l'exhaustivité, et la consultation ordinaire réécrit sa règle de sélection en n'y gardant qu'un
degré de liberté — la constante de la page contre un littéral.

**Aucune page n'est modifiée.** La correction porte sur trois déclarations et sur le point de
lecture, qui gagne un journal sans changer de comportement en usage normal.

## Conséquences

- Une table lue et non déclarée, ou déclarée et non lue, fait rougir un contrôle — dans les deux
  sens, et en nommant la page et la table.
- Le journal de requêtes du point de lecture devient un outil disponible pour tout contrôle futur
  qui devrait observer plutôt que déduire.
- Les trois indicateurs qui n'avaient aucun contrôle en ont un ; deux d'entre eux sous une propriété
  de bornes qu'il ne faut pas lire pour une équivalence.
- La correspondance reste aveugle à l'attribution d'une table à la bonne entrée d'une même page.
  Faire porter le contrôle par indicateur exigerait que l'identifiant accompagne la requête jusqu'au
  point de lecture, ce qu'aucune des neuf pages ne fait aujourd'hui.

## Sources

`dashboard/indicateurs.yml` ; `dashboard/lecture.py` ;
`tests/test_correspondance_registre_usage.py` ; `tests/test_indicateurs_sans_seconde_mesure.py` ;
`tests/test_registre_indicateurs.py` ; `tests/test_instantane.py` ;
`docs/decisions/0043-instantane-schema-dedie-du-tableau-de-bord.md` ;
`docs/champs/registre_champs.yml`.
