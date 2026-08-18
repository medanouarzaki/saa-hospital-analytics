# ADR 0002 — La couche analytique est organisée en schéma en étoile

**Statut.** Accepté, et appliqué depuis l'origine du projet.

> **Enregistrement rétrospectif.** Cette décision a été prise et appliquée avant que sa consignation
> ne soit écrite ; le présent enregistrement est rédigé le 18 août 2026, à partir de l'état du dépôt
> et des documents de suivi du projet. Le cadrage prescrit qu'un enregistrement soit écrit au moment
> de la décision et jamais rétrospectivement : il y est ici dérogé sciemment, pour qu'un numéro
> réservé et cité depuis l'origine cesse de renvoyer à un fichier absent.

---

## Contexte

La couche analytique pouvait s'organiser de trois façons : en tables dénormalisées, une par écran ;
en vues ad hoc, une par indicateur ; ou en schéma en étoile, dimensions et faits séparés.

Les deux premières partagent un défaut : elles rendent un indicateur **dépendant de la forme sous
laquelle il a été préparé**. Un chiffre repris d'une colonne agrégée en amont ne peut plus être
recalculé, ni confronté à une seconde mesure écrite autrement.

## Décision

**La couche analytique est un schéma en étoile : des dimensions et des faits, séparés.**

L'état mesuré de la couche `marts` :

| Famille | Objets | Type |
|---|---|---|
| dimensions | **6** | vues |
| faits | **6** | vues |
| agrégats | **8** | vues |
| **total** | **20** | toutes en vues |

**Les douze tables du schéma en étoile** sont les six dimensions — `dim_activite`, `dim_agent`,
`dim_date`, `dim_organisme`, `dim_patient`, `dim_service` — et les six faits — `fct_encaissement`,
`fct_facturation`, `fct_passage`, `fct_passage_urgence`, `fct_rendez_vous`, `fct_sejour`.

**Ce sont exactement ces douze qui alimentent le classeur exporté** : la production du classeur ne
retient du schéma d'instantané que les objets dont le nom commence par l'un des deux préfixes de
l'étoile, à l'exclusion des huit agrégats.

**Que tous ces objets soient des vues est une décision distincte**, portée par
`docs/decisions/0018-architecture-dbt-vues-et-nommage.md`, et elle n'est pas redite ici.

## Justification des points non triviaux

### Ce que l'étoile permet, et qui est la règle du tableau de bord

Le schéma en étoile est ce qui permet à un indicateur d'être **recalculé depuis un fait** plutôt que
repris d'une colonne agrégée en amont. C'est la règle que le tableau de bord applique : chaque
entrée de son registre porte ce dont sa valeur est effectivement dérivée, et les entrées qui
dérogent sont visibles à ce titre plutôt que reléguées.

La règle a une conséquence vérifiable : un indicateur recalculé depuis un fait peut être confronté à
une seconde mesure écrite par un autre chemin, ce que plusieurs contrôles du dépôt font
effectivement.

### Le grain de chaque fait

Il n'est écrit ni dans les modèles ni dans leurs fichiers de propriétés : il est déclaré par
`docs/decisions/0023-grain-des-tables-de-faits-et-rattachement-patient.md`, dont le premier point
l'énonce fait par fait. Décomptes mesurés à ce jour :

| Fait | Grain déclaré | Lignes mesurées |
|---|---|---|
| `fct_sejour` | un séjour | 2 980 |
| `fct_rendez_vous` | un rendez-vous | 14 169 |
| `fct_facturation` | une facture | 21 066 |
| `fct_encaissement` | un encaissement | 23 231 |
| `fct_passage_urgence` | un passage aux urgences | 27 360 |
| `fct_passage` | un passage, les trois types réunis | 40 650 |

### Sur le nombre de dimensions prévues : ce que le dépôt établit, et ce qu'il n'établit pas

**Le dépôt ne porte aucun décompte de dimensions prévues.** Le document de cadrage n'y figure pas,
et la recherche d'une mention d'un nombre attendu de dimensions ne rend rien. **Cet enregistrement
ne peut donc pas dire combien de dimensions avaient été prévues, et il ne l'invente pas.** Un
lecteur qui cherche cette information doit se reporter au cadrage lui-même, hors dépôt.

Ce que le dépôt permet en revanche d'établir, et qui répond à la même question par une autre voie :
**quelles familles de codes des faits ne portent aujourd'hui aucune dimension.** Mesure faite sur les
fichiers de propriétés des six faits :

- **21 colonnes de fait sont rattachées à une dimension** par un contrôle relationnel, vers quatre
  dimensions seulement — `dim_date` (6 rattachements), `dim_agent` (7), `dim_service` (7),
  `dim_activite` (1) ;
- **17 colonnes de nature « code » n'en portent aucun** : les modes de règlement, d'admission, de
  sortie, d'arrivée et de prise en charge ; les types d'épisode, de facture et de passage ; les
  états de facture et de rendez-vous ; le niveau de tri, le motif de recours, l'orientation de
  sortie, l'origine, le code d'agenda et le code diagnostic.

Une seule de ces absences est nommée dans le dépôt : `dbt/models/marts/fct_facturation.sql` écrit
que le code diagnostic est un « attribut sans dimension (aucune `dim_diagnostic` n'existe dans ce
dépôt) ». **Les seize autres ne sont documentées nulle part comme des absences** — elles sont
simplement des attributs conservés tels quels.

Les deux dimensions restantes, `dim_patient` et `dim_organisme`, existent mais ne sont visées par
aucun contrôle relationnel depuis un fait : `dim_patient` est rattachée par un couple d'identifiant
et de borne de version, `dim_organisme` par aucun fait — absence mesurée et consignée par
`docs/decisions/0047-ecarts-assumes-au-cadrage.md`, qui en tire le retrait d'un indicateur.

**Que quatre des six dimensions ne portent que leur clé naturelle**, sans aucun libellé, est
également consigné : `docs/decisions/0020-dimensions-simples-cle-naturelle.md` en pose la règle et
`docs/decisions/0047-ecarts-assumes-au-cadrage.md` en assume l'écart à l'affichage.

## Conséquences

Le registre des indicateurs porte, pour chaque entrée, les objets qu'elle lit et ce dont sa valeur
est recalculée ; c'est là que se lit l'application effective de la règle.

Le classeur livré ne porte que les douze tables de l'étoile, et son dictionnaire décrit leurs 160
colonnes.

Les huit agrégats ne font pas partie de l'étoile : ils en dérivent, et leur grain propre est déclaré
par `docs/decisions/0028-agregats-grain-perimetre-et-limites.md`.

## Ce qui aurait invalidé cette décision

Qu'un seul écran de restitution existe, sans confrontation possible entre deux mesures : la
séparation des dimensions et des faits n'apporterait alors rien qu'une vue dénormalisée ne donne.

Qu'aucun indicateur n'ait à être recalculé depuis les faits — c'est-à-dire que toutes les grandeurs
affichées soient reprises d'une couche amont. La mesure dit l'inverse : la règle est tenue partout
sauf dans les écarts consignés.

## Sources

`docs/decisions/0018-architecture-dbt-vues-et-nommage.md` — la matérialisation en vues.
`docs/decisions/0020-dimensions-simples-cle-naturelle.md` — quatre dimensions à clé naturelle, sans
libellé inventé.
`docs/decisions/0023-grain-des-tables-de-faits-et-rattachement-patient.md` — le grain des six faits.
`docs/decisions/0028-agregats-grain-perimetre-et-limites.md` — le grain des agrégats.
`docs/decisions/0044-registre-des-indicateurs-fichier-unique-teste.md` — le registre porte ce dont
chaque valeur est recalculée.
`docs/decisions/0047-ecarts-assumes-au-cadrage.md` — les écarts assumés, dont l'affichage des codes
nus et la dimension des organismes que ne référence aucun fait.
