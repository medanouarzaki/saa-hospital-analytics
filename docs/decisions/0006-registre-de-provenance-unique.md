# ADR 0006 — Un registre unique porte la provenance de chaque champ, et quatre artefacts en dérivent

**Statut.** Accepté, et appliqué depuis l'origine du projet.

> **Enregistrement rétrospectif.** Cette décision a été prise et appliquée avant que sa consignation
> ne soit écrite ; le présent enregistrement est rédigé le 18 août 2026, à partir de l'état du dépôt
> et des documents de suivi du projet. Le cadrage prescrit qu'un enregistrement soit écrit au moment
> de la décision et jamais rétrospectivement : il y est ici dérogé sciemment, pour qu'un numéro
> réservé et cité depuis l'origine cesse de renvoyer à un fichier absent.

---

## Contexte

Le projet décrit un système d'information qu'il n'a pu observer qu'en partie. **Quatre des cinq
profils applicatifs n'ont pas pu être observés au poste** : les habilitations du logiciel cloisonnent
l'accès par profil, et le service n'a accordé qu'un seul profil, celui de la gestion des rendez-vous.
Le relevé effectué au poste le 28 juillet 2026 porte sur 4 écrans et 143 champs.

Le reste du modèle est reconstruit par voie documentaire. Sans dispositif, cette différence
disparaîtrait dans une note de bas de page, et un lecteur ne pourrait plus dire, champ par champ, ce
qui a été vu d'un écran et ce qui a été déduit d'un texte réglementaire ou d'une fiche d'éditeur.

## Décision

**Un fichier unique, `docs/champs/registre_champs.yml`, porte une entrée par colonne de la couche
source**, et chaque entrée porte une étiquette de provenance et une exigence de preuve.

Périmètre mesuré : **175 entrées**, couvrant **11 tables**, toutes du schéma `source` — et d'aucun
autre schéma.

**Trois étiquettes, et une exigence de preuve par étiquette :**

| Étiquette | Sens | Entrées | Ce que la preuve doit être |
|---|---|---|---|
| `OBS` | champ observé à l'écran | **81** | une référence de relevé, et le libellé reproduit à l'identique |
| `DOC` | champ déduit d'une source | **72** | un identifiant du registre des sources |
| `HYP` | champ posé sans preuve externe | **22** | la mention explicite qu'aucune preuve n'existe |

Les 22 entrées `HYP` portent toutes la mention d'absence de preuve externe, ce qui est mesuré et non
supposé.

**Quatre artefacts sont dérivés mécaniquement de ce registre**, chacun par un générateur dédié :

| Artefact | Générateur |
|---|---|
| DDL du schéma `source`, un fichier par table | `docs/champs/generer_ddl.py` |
| DDL du schéma `quarantaine`, un fichier par table | `ingestion/generer_ddl_quarantaine.py` |
| Fichier de sources de l'outil de transformation | `docs/champs/generer_schema_yml.py` |
| Dictionnaire des données, en deux formats | `docs/champs/generer_dictionnaire.py` |

Les artefacts produits portent en tête l'avertissement qu'ils sont produits mécaniquement et ne
doivent pas être modifiés à la main.

## Justification des points non triviaux

### Ce que le contrôle de provenance vérifie réellement, et ce qu'il ne vérifie pas

Ce point est le plus important de cet enregistrement, et il n'est pas adouci.

`tests/test_provenance.py` porte quatre propriétés : la couverture bidirectionnelle entre le
registre et le catalogue, la présence des commentaires de provenance en base, la cohérence des
preuves avec le registre des sources, et la synchronisation des artefacts dérivés.

**La propriété de couverture nomme trois schémas dans sa requête** — `source`, `intermediate` et
`marts` — mais joint le catalogue des tables en filtrant sur les tables de base. Or les deux couches
aval sont matérialisées en vues. Mesure :

```
 table_schema | table_type | colonnes
--------------+------------+----------
 intermediate | VIEW       |      175
 marts        | VIEW       |      223
 source       | BASE TABLE |      175

-- une fois le filtre du contrôle appliqué :
 table_schema | colonnes_retenues
--------------+-------------------
 source       |               175
```

**La couverture ne porte donc effectivement que sur les 175 colonnes de la couche source, et sur
aucune des 398 colonnes des deux couches qu'elle nomme.** Ce n'est pas un défaut du contrôle : le
filtre est la conséquence voulue de la matérialisation en vues, consignée par
`docs/decisions/0018-architecture-dbt-vues-et-nommage.md`. C'est un défaut de ce qui pourrait être
affirmé de lui, et la règle qui comble le manque pour les couches aval est posée par
`docs/decisions/0049-documentation-des-couches-aval.md`.

Un enregistrement qui présenterait cette couverture comme portant sur trois schémas serait faux, et
une seule commande le démentirait.

### Pourquoi le registre ne s'étend pas aux couches aval

Les trois étiquettes qualifient **un champ du système observé** : elles disent d'où l'on sait qu'il
existe. Une colonne calculée par le projet a pour provenance son propre calcul, et lui attribuer
l'une des trois n'aurait pas de sens. Le motif complet est consigné par
`docs/decisions/0049-documentation-des-couches-aval.md`.

### La provenance est portée jusque dans la base

Les étiquettes ne restent pas dans un fichier : elles sont écrites en commentaire sur chaque colonne
du schéma `source`, et une vue les recompte directement sur le catalogue. Mesure sur la base :

```
 etiquette | count
-----------+-------
 DOC       |    72
 HYP       |    22
 OBS       |    81
```

Les trois décomptes coïncident exactement avec ceux du registre, ce qui est la propriété que la
couverture bidirectionnelle défend.

## Conséquences

Toute colonne ajoutée à la couche source passe par le registre, faute de quoi la couverture
bidirectionnelle rougit dans l'un des deux sens.

Le dictionnaire livré et le DDL appliqué ne peuvent pas diverger du registre, puisqu'ils en sont
dérivés et qu'un contrôle vérifie leur synchronisation.

Le rapport dispose d'un chiffre non recopiable sur la part du modèle qui repose sur l'observation :
la vue le recalcule à chaque lecture, sur le catalogue.

## Ce qui aurait invalidé cette décision

Que les cinq profils applicatifs aient pu être observés : la distinction entre observé et documenté
n'aurait plus eu d'objet, et une simple liste de champs aurait suffi.

Que le registre ne soit dérivé en rien — un fichier de documentation que rien ne consomme diverge du
code sans que rien ne le signale. Quatre artefacts en dérivent, et un contrôle les tient synchrones.

## Sources

`docs/modules_non_observes.md` — les quatre profils non observés et la méthode de reconstruction.
`docs/observation/releve_champs.yml` — le relevé au poste, ses écrans et ses champs.
`docs/sources/sources.yml` — les sources auxquelles les étiquettes documentées renvoient.
`docs/decisions/0014-typage-couche-source.md` — le typage intégralement textuel de la couche source.
`docs/decisions/0018-architecture-dbt-vues-et-nommage.md` — la matérialisation en vues, dont découle
le filtre du contrôle.
`docs/decisions/0032-ddl-schema-linkage-ecrit-a-la-main.md` — le schéma que le registre ne régit pas.
`docs/decisions/0049-documentation-des-couches-aval.md` — la règle qui couvre les couches aval.
