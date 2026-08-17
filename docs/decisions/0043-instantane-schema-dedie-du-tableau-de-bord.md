# ADR 0043 — Le tableau de bord lit un schéma dédié de tables, rafraîchi par échange de noms

**Statut.** Accepté.

---

## Contexte

La chaîne de données reconstruit chaque jour les vingt vues du schéma `marts` et les onze vues de
la couche intermédiaire. Le tableau de bord doit lire ces grandeurs pendant que cette
reconstruction a lieu, et l'ADR `0041` a laissé ouvert ce que la tâche de rafraîchissement
accomplirait.

La question posée était de savoir si un lecteur peut se contenter de lire `marts` directement.
Elle a été tranchée par mesure, et non par supposition, à l'aide d'un témoin concurrent : une
session qui lit une vue en boucle, à environ treize lectures par seconde, pendant qu'une
reconstruction complète s'exécute.

Le témoin a d'abord été éprouvé contre deux événements dont l'issue était certaine — la lecture
d'un objet inexistant, puis la lecture d'une vue supprimée puis recréée après une pause d'une
seconde et demie. Sur le premier, douze tentatives et douze erreurs ; sur le second, vingt-quatre
tentatives, dix-sept succès et sept erreurs tombant exactement dans la fenêtre provoquée. Sans
cette épreuve, le silence du témoin n'aurait rien prouvé.

## Décision

**Le tableau de bord ne lit qu'un schéma dédié de tables, et rien d'autre.**

Ce schéma porte :

- une copie de chacun des vingt objets de `marts` ;
- une copie des trois tables du schéma de rapprochement ;
- une copie de la vue de la couche intermédiaire qui porte les créances ;
- une table de service portant l'horodatage du rafraîchissement et la date de référence des
  données ;
- une table de paramètres.

**Le grain de chaque table copiée est celui de l'objet d'origine : une copie, jamais une
ré-agrégation.**

**Le rafraîchissement construit des tables neuves sous des noms provisoires, puis échange les
noms, tous les échanges dans une seule transaction.**

**L'échange demande ses verrous d'un seul bloc et renonce plutôt que de disputer**, avec un délai
d'attente strictement inférieur au délai de détection d'interblocage du serveur, et réessaie.

## Justification des points non triviaux

### Pourquoi l'échange renonce au lieu de disputer, et pourquoi il verrouille d'un bloc

Un lecteur qui interroge plusieurs tables dans une même requête acquiert ses verrous dans l'ordre
où sa requête les nomme ; l'échange les acquiert dans l'ordre de sa liste. Les deux ordres se
croisent, et les deux transactions s'attendent mutuellement. Ce n'était pas un cas rare mais le cas
ordinaire : **une lecture perdue par rafraîchissement, dix fois sur dix**, et une fois sur cinq
c'est le rafraîchissement lui-même que le serveur désignait victime.

**Aucune discipline appliquée au seul échange ne peut aligner les deux ordres**, le lecteur n'étant
pas sous le contrôle de la chaîne : une page lit ses objets dans l'ordre qui lui convient. Il faut
donc soit renoncer à être victime, soit cesser de disputer ces verrous.

Trois conceptions ont été mesurées et écartées, sur trente exécutions chacune, sous deux charges :

| conception écartée | échecs de lecture | échecs d'échange | pourquoi elle est écartée |
|---|---|---|---|
| **renoncer sans verrouiller d'un bloc** | 0 | **30 sur 30** sous forte charge | l'échange n'aboutit jamais : il ne réunit jamais ses vingt-quatre verrous |
| **verrouiller d'un bloc sans renoncer** | **3 puis 2** | 2 sur 30 | des lectures échouent encore ; raccourcir la fenêtre n'aligne pas les ordres |
| **déplacer le verrou hors des tables** | — | — | **réfutée par lecture du serveur** : renommer un schéma prend un verrou exclusif sur chacune de ses tables, et remplacer une vue en prend un sur la vue et sur ses tables sous-jacentes |

**La conjonction des deux premières atteint ce qu'aucune n'atteint seule** : zéro échec des deux
côtés sous les trois charges éprouvées, dont 467 406 lectures sous la charge la plus intense. Les
deux moitiés sont nécessaires, et un contrôle le vérifie séparément pour chacune.

Le délai retenu est de deux cents millisecondes, contre mille pour la détection d'interblocage lue
dans le serveur. Il est posé pour la seule durée de la transaction, ce qui a été vérifié plutôt que
supposé. Aucun échange n'a dépassé six tentatives sur les dix permises, sous une charge plus dure
que celle du déploiement.

### Pourquoi un échec de lecture et un échec d'échange n'ont pas le même statut

Le critère d'acceptation est **asymétrique**, et c'est délibéré.

**Un échec de lecture est vu par l'utilisateur, sans recours** : il n'a rien demandé d'autre que
d'afficher une page, et rien ne rattrapera l'erreur pour lui. Il est donc exigé à zéro **sous toute
charge**, sans classe d'erreur exceptée.

**Un échec d'échange est vu par l'ordonnanceur**, journalisé avec sa cause, et relançable. Surtout,
**la transaction étant atomique, il ne laisse aucun renommage partiel** : l'instantané demeure dans
sa génération précédente, cohérente et complète. Il est donc exigé à zéro sous la charge de
déploiement, et toléré au-delà — mais seulement parce que cette atomicité tient, ce qu'un contrôle
vérifie en provoquant un renoncement et en confrontant décomptes et empreintes.

### Le modèle de charge sous lequel tout ceci est mesuré

Il distingue ce qui est mesuré de ce qui est assumé.

**Mesuré :** une rafale vaut huit lectures, nombre d'indicateurs de la page la plus lourde, relevé
au registre des indicateurs ; l'intervalle entre deux rafales vaut le temps d'afficher une page,
obtenu en divisant par sept la durée mesurée des sept pages contre les tables copiées, soit deux
cent huit millisecondes — **borne basse volontairement pessimiste**, puisqu'elle suppose un lecteur
qui change de page sans la lire.

**Assumé :** quatre lecteurs simultanés. Aucune mesure ne peut trancher ce point, le tableau de bord
n'étant pas en service ; c'est une hypothèse, retenue parce qu'il s'agit d'un outil interne à un
établissement et non d'une application publique. Pour ne pas la faire porter par l'argument, tout a
été également mesuré à **quarante** lecteurs.

Chaque lecture interrogeant plusieurs tables dans une même requête — c'est cette forme, et elle
seule, qui croise les ordres d'acquisition.

### La discipline d'attente, et pourquoi elle est vérifiée par une comparaison et non par un seuil

Ce schéma existe pour qu'un lecteur ne subisse rien pendant la reconstruction. Vérifier qu'il ne
voit ni objet absent ni état mêlé ne suffit pas : une conception qui recopierait les données en
tenant les verrous passerait ces deux contrôles **tout en faisant patienter le lecteur dix fois plus
longtemps** — c'est mesuré, cent quarante-trois millisecondes contre quinze.

Un contrôle borne donc le travail accompli sous verrou. **Il ne porte pas sur l'attente observée**,
qui ne distingue rien : sous forte charge, cette attente est bornée par le délai au bout duquel
l'échange renonce, et vaut donc autant pour toutes les conceptions. Il porte sur la durée de la
phase exclusive, rapportée au nombre d'objets, et la compare à un point calculé à chaque exécution
comme la moyenne géométrique de deux durées mesurées au même moment : le renommage d'une table, qui
est une opération de catalogue, et la copie d'une table de taille comparable au plus gros objet
copié, qui est une opération de données. Ces deux ancres sont séparées de plus d'un ordre de
grandeur.

La question posée est donc : ce que l'échange fait sous verrou ressemble-t-il à écrire un nom, ou à
recopier une table ? **Aucun seuil n'est écrit dans le contrôle** ; il est recalculé à chaque fois.

### Pourquoi le motif n'est pas le coût de lecture

L'écrire ainsi serait faux, et la mesure le montre. Lire les indicateurs des sept pages coûte
5,9379 s contre les vues et 1,4559 s contre des tables copiées, soit un rapport de 4,08 — un gain
réel mais qui ne justifierait pas à lui seul un schéma supplémentaire à maintenir.

Ce rapport moyen est en outre trompeur et il faut le dire : **seize des vingt-cinq indicateurs
comparés sont sous un rapport de trois**, le minimum mesuré est de 1,24, et le maximum de 32,92
tient à un seul objet — la vue de complétude, qui déplie les onze vues intermédiaires en paires
clé-valeur. En retirant cette seule page, le rapport global tombe à 3,03 ; en retirant en outre
l'indicateur de recouvrement recalculé depuis les faits, à 2,77. **Le gain est porté par une
minorité d'indicateurs, non réparti sur l'ensemble.**

### Pourquoi le motif est qu'un lecteur voit une erreur pendant la reconstruction

C'est la mesure décisive. Pendant une reconstruction complète, le témoin observe sur deux vues de
nature très différente :

| vue observée | tentatives | réussies | en erreur | fenêtre d'indisponibilité |
|---|---|---|---|---|
| une dimension simple | 200 | 193 | **7** | **0,352 s** |
| la vue de complétude, la plus coûteuse à produire | 200 | 194 | **6** | **0,284 s** |

Le message est unique et identique dans les deux cas :

    ERROR:  relation "<nom de la vue>" does not exist

**Ce n'est pas une attente mais une absence.** La durée maximale d'une lecture réussie reste de
56 ms sur la première vue et de 3,9 ms sur la seconde : rien ne bloque, l'objet n'existe
simplement plus pendant environ trois dixièmes de seconde.

Une lecture longue déjà commencée n'est en revanche jamais interrompue : quatre lectures d'un peu
plus d'une seconde chacune, traversant la reconstruction, ont toutes rendu leur résultat complet.
Le verrou qu'elles détiennent fait attendre la reconstruction plutôt que l'inverse — mesuré :
4,85 s pour la reconstruction pendant ces lectures, contre 3,14 à 3,37 s sans elles.

### Pourquoi la cause est la suppression en cascade, et non le renommage

La lecture du code de l'outil de transformation avait produit la prédiction inverse. Une vue y est
remplacée par une danse à trois noms : création sous un nom provisoire, renommage de l'ancienne
vers un nom de sauvegarde, renommage de la provisoire vers le nom cible, validation, puis
suppression de la sauvegarde. Les deux renommages étant dans une même transaction, on pouvait en
déduire qu'un lecteur attendrait le verrou plutôt que de rencontrer un trou.

**La mesure a réfuté cette prédiction, et une expérience dédiée en a isolé la cause** : la
suppression de la sauvegarde s'écrit avec une clause de cascade. Or renommer une vue ne déplace
pas ses dépendantes, qui pointent sur son identifiant interne et non sur son nom ; la suppression
de la sauvegarde emporte donc toutes les vues construites au-dessus d'elle, qui ne réapparaissent
qu'à leur propre rang dans l'ordre de reconstruction.

L'expérience, conduite sur une chaîne de deux vues soumise exactement à la même séquence, rend le
verdict en toutes lettres :

    NOTICE:  drop cascades to view <la vue dépendante>

La dimension observée dépend de huit vues de la couche intermédiaire, mesurées au catalogue :
chacune d'elles, en étant reconstruite, l'emporte. La fenêtre de 0,352 s est l'intervalle entre la
dernière de ces cascades et son propre rang, dix-neuvième sur trente, dans l'ordre d'exécution.

La restriction à un seul fil d'exécution, décidée par l'ADR `0027` pour éviter un interblocage sur
le catalogue système, **n'élimine pas cette fenêtre** : elle en sérialise seulement les
occurrences.

### Pourquoi l'échange de noms plutôt que le vidage et le rechargement

Les deux stratégies ont été mesurées sur une table de 40 650 lignes, avec le même témoin, en
enregistrant **la valeur du décompte à chaque lecture** et non le seul succès — le pire cas, une
lecture rendant une table à moitié remplie, devait être cherché activement plutôt qu'attendu.

| | vider puis recharger, une transaction | table neuve puis échange de noms |
|---|---|---|
| durée totale | 0,55 s | 0,58 s |
| lectures tentées | 120 | 120 |
| erreurs | **0** | **0** |
| valeurs de décompte distinctes | **une seule** | **une seule** |
| durée médiane de lecture | 4,550 ms | 4,346 ms |
| **durée maximale de lecture** | **485,624 ms** | **6,889 ms** |

**Aucune des deux ne montre jamais un décompte partiel** : les deux cent quarante lectures rendent
toutes le même nombre. La transaction protège dans les deux cas, et c'est un résultat en soi.

La différence porte sur l'attente. Le vidage prend un verrou exclusif que le lecteur subit pendant
tout le rechargement : 485 ms, soit cent sept fois la médiane. L'échange de noms construit la
table neuve sans toucher à l'ancienne et ne prend le verrou que le temps de deux mises à jour de
catalogue : la durée maximale reste du même ordre que la médiane.

**L'échange de noms est retenu parce qu'il est le seul des deux à ne rien faire attendre au
lecteur**, pour un coût de construction identique.

Un point mesuré qui explique pourquoi cette stratégie est sûre ici alors que la même séquence ne
l'est pas sur les vues : **une table de copie n'a aucune dépendante**. La cascade qui détruit les
vues construites au-dessus n'a, sur ce schéma, rien à détruire.

### Pourquoi une copie et jamais une ré-agrégation

Conserver le grain d'origine rend l'égalité entre chaque table et sa vue source **vérifiable
mécaniquement**, par un décompte de part et d'autre. Cette vérification a été conduite sur les
vingt objets copiés : **écart nul sur les vingt, sans exception**.

Une ré-agrégation supprimerait cette vérification et remplacerait une propriété testable par une
relecture. Elle rendrait de surcroît impossible la règle du cadrage selon laquelle un indicateur
se recalcule depuis les faits : ré-agréger, c'est précisément figer un calcul en amont.

### Pourquoi copier le schéma de rapprochement alors que le gain de coût y est nul

Ses trois objets sont déjà des tables, non des vues : les copier n'accélère rien, et la mesure le
confirme — leurs lectures coûtent de 0,0455 s à 0,2582 s, du même ordre des deux côtés.

Le motif n'est pas la vitesse mais **l'unicité de la source de lecture**. Une règle simple —
aucune page ne lit en dehors du schéma dédié — est vérifiable par un test qui inspecte les
requêtes ; une règle à exceptions ne l'est pas, ou seulement au prix d'une liste d'exceptions à
tenir à jour. La mesure a d'ailleurs établi que **six indicateurs sur trente et un lisent en
dehors du schéma de la couche `marts`** : sans cette copie, la règle aurait six exceptions dès le premier
jour.

## Conséquences

Le tableau de bord ne dépend plus du calendrier de la chaîne : il lit un état figé, daté par la
table de service, et une reconstruction en cours ne lui est pas visible.

La tâche de rafraîchissement laissée en aboutissement vide par l'ADR `0041` reçoit son contenu :
construire les tables neuves, échanger les noms dans une transaction unique, écrire l'horodatage.

Le coût de construction de la copie est mesuré à 5,203 s pour 29,12 Mio, soit 57 % de la borne
supérieure que constitue la taille du schéma source — les tables copiées étant dérivées de ces
données, elles ne peuvent en occuper davantage.

L'égalité entre chaque table et sa vue d'origine devient une propriété testable, et un test la
vérifiera objet par objet.

## Ce qui aurait invalidé cette décision

**Une reconstruction transparente pour le lecteur.** C'était l'issue attendue avant la mesure : la
lecture du code de l'outil montrait deux renommages dans une même transaction, dont on déduisait
qu'un lecteur attendrait au pire quelques millisecondes. Si le témoin n'avait rapporté aucune
erreur, l'argument principal de cette décision tombait, et le seul gain de coût — inégal, porté
par une minorité d'indicateurs — n'aurait pas suffi à justifier un schéma supplémentaire.

Une seconde issue l'aurait également invalidée : que l'une des deux stratégies de rafraîchissement
laisse voir un décompte partiel. Le témoin a cherché ce cas activement, en enregistrant la valeur
de chaque lecture ; il ne se produit dans aucune des deux, et l'échange de noms n'est donc pas
retenu pour cette raison-là mais pour la seule attente évitée.

## Sources

`docs/decisions/0027-materialisation-dbt-un-seul-fil.md` — restriction à un seul fil d'exécution,
et l'interblocage sur le catalogue système qui l'a motivée.
`docs/decisions/0041-taches-export-instantane-vides.md` — les deux tâches finales du graphe
existent en aboutissement vide, leur contenu étant renvoyé à un travail ultérieur.
Code de la matérialisation en vue de l'outil de transformation, version installée, et ses macros
de renommage et de suppression pour PostgreSQL.

## Amendement — la concurrence du rafraîchissement, et l'emplacement de ses contrôles

Le rafraîchissement effaçait ses résidus au démarrage, ce qui le protégeait d'une exécution
**interrompue** mais non d'une exécution **concurrente**. Défaut mesuré : trois paires
d'invocations simultanées sur trois donnaient une exception non traitée — une violation d'unicité
du catalogue système sur la création des tables provisoires. L'instantané y survivait (aucun
résidu, vingt-six tables, contrôles d'égalité verts) ; le dommage était l'échec obscur.

**Deux remèdes sont retenus, à deux portées différentes.** `max_active_runs=1` sur le graphe
empêche le recouvrement avant qu'il ne commence — sans lui la configuration de l'orchestrateur en
autoriserait seize, et `catchup=True` en produirait lors d'un rattrapage — mais ne couvre que les
exécutions du graphe. Un **verrou consultatif** dans le module couvre toute invocation, d'où
qu'elle vienne : la seconde renonce sans rien modifier, avec un **code de sortie qui lui est
propre** (3), distinct de celui d'un échec (1), afin qu'un ordonnanceur sépare « un autre
rafraîchissement était en cours » d'une défaillance à examiner. Mécanisme lu dans le serveur avant
emploi : `pg_try_advisory_lock` rend immédiatement, sa portée est la session — ce qu'il faut, le
rafraîchissement s'étendant sur plusieurs transactions — et il se relâche à la fermeture de la
connexion, y compris si le processus meurt, de sorte qu'aucun verrou périmé ne peut bloquer un
rafraîchissement ultérieur. Critère : trente paires, trente renoncements propres, zéro exception.

**Les contrôles de l'instantané ont quitté l'emplacement `dbt` de l'intégration continue** pour un
emplacement propre. Le point de coupe vient de la mesure : ces quatre fichiers partagent une
précondition qu'aucun autre n'a — l'instantané, qu'ils rafraîchissent eux-mêmes — et la marge de
l'emplacement d'origine jusqu'au plus court groupe de la matrice était tombée à 17 s (544 s contre
561 s). Le nouvel emplacement reconstruit ses préconditions au lieu de les hériter, et ne reprend
que ce que l'instantané copie : construction dbt, prédiction, évaluation — ni les contrôles dbt, ni
l'ablation, qui n'écrit aucune des trois tables de `linkage`.
