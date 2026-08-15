# ADR 0047 — Trois écarts au cadrage sont consignés plutôt que contournés

**Statut.** Accepté.

---

## Contexte

Le cadrage pose trois exigences que la mesure ne permet pas de tenir intégralement : que tout
indicateur affiché soit recalculé depuis les tables de faits, que le tableau de bord lise la base
et rien d'autre, et que les valeurs affichées soient lisibles par un lecteur qui ne connaît pas les
codes du système d'origine.

Chacune peut être contournée sans que rien n'échoue. Un contournement silencieux laisserait croire
que l'exigence est tenue ; ces trois écarts sont donc écrits.

## Décision

**Trois écarts au cadrage sont consignés, chacun avec sa mesure et sa portée.**

## Justification des points non triviaux

### Premier écart — trois indicateurs ne sont pas recalculés depuis les tables de faits

La règle du cadrage veut que tout indicateur soit recalculé depuis les faits plutôt que repris
d'une colonne calculée en amont. Trois indicateurs y échappent, pour deux raisons différentes.

**Deux parce qu'aucune table de faits ne porte la matière**, et il faut nommer laquelle manque dans
chaque cas :

- **le taux de recouvrement et l'aboutissement des relances** lisent la couche intermédiaire.
  **Il n'existe ni fait des créances ni fait des relances** — les six faits du schéma en étoile
  sont les encaissements, la facturation, les passages, les passages aux urgences, les rendez-vous
  et les séjours, énumérés par le catalogue. Recalculer depuis les faits est ici impossible, non
  par choix mais par absence de la table ;
- **la complétude par champ et le taux de quarantaine** lisent les onze vues de la couche
  intermédiaire et les onze tables de quarantaine. Aucune table de faits ne porte de métadonnée de
  colonne, et sept des onze tables intermédiaires n'ont aucune contrepartie directe parmi les six
  faits.

**Un parce que le recalcul changerait sa valeur.** Le décompte des collisions d'identité est
mesuré sur les patients de version courante de la dimension des patients. Recalculé sur les
patients vus dans un fait, il porterait sur une population **strictement plus petite** :

| population | effectif mesuré |
|---|---|
| patients de version courante | **25 842** |
| identifiants distincts dans le fait des passages | **25 448** |
| **écart** | **394 patients**, soit 1,52 % |

Trois cent quatre-vingt-quatorze patients courants n'apparaissent dans aucun passage. L'écart
viendrait donc du **périmètre** et jamais de la formule, et appliquer la règle du cadrage
changerait le chiffre affiché sans l'améliorer.

Un écart du même ordre, mais bien plus grand, illustre pourquoi la règle mérite d'être suivie
partout où elle le peut : le taux de recouvrement vaut **21,5700 %** tel que l'agrégat le porte,
et **84,3660 %** recalculé depuis les faits — un écart de **62,80 points**. Les deux sont justes
et ne mesurent pas la même chose, seules **5 486 factures sur 21 066**, soit 26,04 %, donnant lieu
à une créance. Substituer l'un à l'autre sans le dire ferait afficher 84 % là où la gestion attend
22 %.

### Deuxième écart — la capacité litière n'est pas lisible depuis la base

Quatre indicateurs de la page des séjours en dépendent, et la valeur n'existe nulle part dans la
base. Trois vérifications l'établissent : **aucune table de paramètres, de structure ou de
configuration** dans la base ; le schéma des référentiels ne contient qu'un calendrier ; et les
variables de l'outil de transformation ne portent que les bornes de la dimension calendaire.

La valeur vit dans **trois fichiers du dépôt qui s'accordent tous** — un paramètre de volumétrie,
une répartition par unité dont la somme vaut la même valeur, et un enregistrement de décision. Leur
accord n'est d'ailleurs pas fortuit : il est **vérifié par un test existant**.

**Elle est donc portée par la table de paramètres de l'instantané**, remplie par la tâche de
rafraîchissement, **avec sa provenance** — l'identifiant de la source nationale et le tableau dont
elle est relevée.

Le point qui mérite d'être dit : **cette table tient exactement la place qu'occuperait la table de
structure d'établissement nommée comme premier champ manquant** par le document d'exigences
statistiques. C'est la même recommandation vue de l'autre côté — ce que le système d'information
devrait porter, le tableau de bord doit le porter à sa place en attendant, et le dire.

Une voie de reconstruction existe et n'est pas retenue : compter les identifiants de lit distincts
observés dans les mouvements rend exactement la valeur publiée. Elle est écartée parce qu'un lit
fonctionnel n'ayant accueilli aucun patient sur toute la période resterait invisible du décompte —
la mesure est un plancher, pas une capacité. La réserve est concrète : l'occupation simultanée
maximale mesurée est de trente-quatre, soit six lits jamais occupés en même temps que les autres.

### Troisième écart — les codes de dimension s'affichent tels quels

**Quatre dimensions sur six ne portent que leur clé naturelle, sans aucun attribut** : activités,
agents, organismes et services. Le décompte est mesuré : elles comptent respectivement 8, 8, 7 et 7
lignes pour **une seule colonne chacune**.

Ce n'est pas un oubli. Les quatre modèles portent la même justification écrite : clé naturelle,
**aucun libellé inventé**, union des colonnes de la famille correspondante, pas de clé de
substitution.

Le cas le plus dur est celui des activités : **huit entiers nus**, sans aucune sémantique portée
par la valeur. Un affichage ventilé par activité montrera donc ces entiers, sans qu'aucune
information de la base ne permette de dire ce qu'ils désignent. Les codes de service et d'agent sont
partiellement déchiffrables, ceux d'organisme hétérogènes — quatre sigles reconnaissables et trois
codes numériques opaques.

Une correspondance existe bien dans le dépôt, du côté de la configuration du générateur, mais elle
n'est **pas chargée en base** et sa provenance est une hypothèse : le texte réglementaire invoqué
affirme que l'hôpital s'organise en services **sans les nommer individuellement**. **Aucun des sept
codes de service ne correspond donc à une discipline réglementaire nommée par un texte.**

**Aucun libellé ne sera inventé, et cette abstention est un choix.** Écrire « Cardiologie » en face
du code 4 sur la foi d'une correspondance posée par convention reviendrait à afficher une hypothèse
avec l'apparence d'une donnée relevée — exactement ce que la distinction entre provenance observée,
documentée et hypothétique existe pour empêcher dans ce projet. Un code nu est illisible et le
montre ; un libellé faux est lisible et le cache.

## Conséquences

Les trois écarts sont visibles à l'endroit où ils comptent : le registre des indicateurs porte,
pour chaque entrée, ce dont sa valeur est recalculée, et la table de paramètres de l'instantané
porte la provenance de chaque valeur qu'elle contient.

Le rapport tire de ces trois écarts une part de son chapitre de recommandations : le premier
suggère deux tables de faits absentes, le deuxième nomme une table de structure, le troisième un
référentiel de libellés.

Le document d'exigences statistiques porte le tableau complet, avec la distinction entre champ
absent du système d'information et activité absente de l'établissement.

## Ce qui aurait invalidé cette décision

Qu'un fait des créances ou des relances existe dans le schéma en étoile, auquel cas le premier
écart disparaîtrait pour deux de ses trois indicateurs.

Que la capacité litière soit chargée quelque part en base — dans une table de référentiel ou une
variable de l'outil de transformation — auquel cas le deuxième écart n'existerait pas et la table
de paramètres serait inutile.

Qu'une correspondance entre code et libellé soit documentée par une source, et non posée par
convention, auquel cas le troisième écart deviendrait un simple chargement à faire.

## Sources

`docs/decisions/0003-volumetrie.md` — capacité litière fonctionnelle relevée, et sa provenance.
`docs/decisions/0020-dimensions-simples-cle-naturelle.md` — clé naturelle sans libellé inventé.
`docs/decisions/0043-instantane-schema-dedie-du-tableau-de-bord.md` — la table de paramètres de
l'instantané.
`docs/decisions/0044-registre-des-indicateurs-fichier-unique-teste.md` — le registre porte ce dont
chaque valeur est recalculée.
`docs/exigences_statistiques.md` — champs manquants et distinction structurante.
