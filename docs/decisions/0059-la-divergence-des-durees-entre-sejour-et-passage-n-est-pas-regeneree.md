# ADR 0059 — Les deux faits ne s'accordent pas sur la fin d'un épisode, et le jeu n'est pas régénéré

**Statut.** Accepté. Complète le point 2 de
`docs/decisions/0024-limites-documentees-des-faits.md`, qu'il ne remplace pas.

---

## Contexte

Un épisode d'hospitalisation est écrit deux fois par le générateur : une ligne de passage de type
hospitalisé, et un séjour reconstitué depuis les mouvements. Les deux décrivent le même épisode, et
`0024` a établi qu'ils portent **deux durées tirées indépendamment**, sans clé directe entre les
deux tables.

Ce que `0024` ne dit pas : ce qu'il advient de cette divergence. Une chaîne qui produit deux
réponses à la question « combien de temps ce patient est-il resté ? » a un défaut, et un défaut se
corrige ou s'assume. Le présent enregistrement assume, et dit sur quelles mesures.

L'appariement est par ailleurs affiné. `0024` appariait par patient et **jour** d'admission, et
obtenait 2 982 paires pour 2 980 séjours, avec quatre ambiguïtés. La clé retenue ici est plus
fine — patient et **instant** d'admission — et les lève.

## Décision

**Le jeu de données n'est pas régénéré. La divergence est consignée, et l'appariement qui tient est
verrouillé par un contrôle.**

Trois mesures fondent cette décision, et chacune est reprise dans le contrôle ou dans le rapport de
mesure qui l'accompagne.

**1. L'appariement est de un à un, et prouvé dans les deux sens.** Sur le couple (patient, instant
d'admission) : 2 980 séjours, 2 980 passages de type hospitalisé, 2 980 paires, aucun séjour sans
passage, aucun passage sans séjour, et aucune clé portée par plus d'une ligne d'aucun des deux
côtés. **La structure, elle, est saine** : chaque épisode existe une fois de chaque côté.

**2. La divergence ne touche aucun chiffre affiché.** Sept indicateurs du tableau de bord lisent le
fait de passage ; aucun n'y lit une durée. Ils comptent des événements, des patients distincts, des
répartitions par jour de semaine ou par heure, et des épisodes non facturés. La seule durée de
passage affichée vient d'une autre table, celle des passages aux urgences.

**3. Régénérer invaliderait toute mesure publiée du projet.** Le jeu est produit par une graine ;
le régénérer avec une durée unique par épisode changerait chaque ligne de chaque table, et donc
chaque chiffre déjà consigné — volumétries, indicateurs de séjour, évaluation du rapprochement,
écarts au cadrage. Le coût est le projet entier ; le bénéfice est la disparition d'une divergence
qu'aucun indicateur n'expose.

## Justification des points non triviaux

### Ce que la décision laisse ouvert, et qui n'est pas atténué

**Les deux tables décrivent le même épisode et ne s'accordent pas sur sa fin.** Ce n'est pas une
approximation : c'est une contradiction interne du jeu de données. Mesuré sur les 2 955 paires dont
les deux durées sont définies — les 25 autres portent un séjour non clos des deux côtés :

- **aucune paire ne porte la même durée** ;
- l'écart va dans les deux sens, de −19,96 à +32,80 jours, médiane +0,63 ;
- le passage est plus court que le séjour dans 1 249 cas, plus long dans les 1 706 autres ;
- les sommes diffèrent de 1 966,74 jours, soit environ un dixième du volume de journées.

Quiconque comparerait les deux durées trouverait deux réponses. La limite est énoncée ici et dans
`0024` plutôt que corrigée, et un lecteur qui l'ignore obtient un résultat faux sans être averti
ailleurs.

### Pourquoi le contrôle ne verrouille que l'appariement

Un contrôle qui figerait la divergence — en asserant par exemple que les sommes diffèrent d'environ
1 967 jours — transformerait un défaut en propriété attendue, et une correction future le ferait
rougir à tort. **On ne fige pas un défaut par une assertion : on le consigne.** Le contrôle écrit
avec cet enregistrement ne porte donc que ce qui est vrai et doit le rester : l'appariement de un à
un, dans les deux sens.

### Pourquoi la clé est l'instant et non le jour

Deux épisodes du même patient le même jour existent dans le jeu. Apparier par jour les confond, et
c'est l'origine des quatre ambiguïtés de `0024`. L'instant d'admission les sépare, et le mesure :
aucune clé n'est portée par plus d'une ligne.

## Conséquences

- La divergence subsiste dans le jeu de données, et deux enregistrements la nomment.
- L'appariement de un à un est désormais un invariant contrôlé : le perdre ferait rougir un
  contrôle, avec le décompte des non-appariés de chaque côté.
- Aucun indicateur ne peut se mettre à lire une durée de passage sans qu'une déclaration d'objet
  change, ce que le contrôle de correspondance du registre verrait.
- Toute mesure publiée du projet reste valide, ce qui était l'objet de la décision.

## Ce qui aurait invalidé cette décision

Un indicateur qui viendrait afficher une durée ou un volume de journées depuis le fait de passage :
la divergence cesserait d'être sans effet, et il faudrait alors choisir laquelle des deux durées
fait foi. Ou une régénération décidée pour un autre motif, qui rendrait le coût nul et permettrait
de tirer une durée unique par épisode.

## Sources

`marts.fct_sejour`, `marts.fct_passage` ; `generator/mouvements.py`, `generator/passages.py` ;
`dashboard/indicateurs.yml` (objets déclarés par les sept indicateurs qui lisent le fait de
passage) ; `generator/config/nomenclatures_organisation_activite.yml::nomenclature_type_passage` ;
`docs/decisions/0024-limites-documentees-des-faits.md` ;
`tests/test_faits_sejour_et_passage.py`.
