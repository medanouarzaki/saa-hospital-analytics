# ADR 0050 — Un code de dimension porte son libellé si une source l'établit, et reste nu sinon

**Statut.** Accepté.

---

## Contexte

Le tableau de bord affichait des codes nus : les activités en entiers (`4`, `11`, `20`…), les
services en abréviations (`HGO`, `HM`, `HPED`), les orientations de sortie en deux lettres (`RD`,
`TR`, `SC`), les niveaux de tri en chiffres. Un lecteur y lit « Activité 12 : 47 passages » et
n'apprend rien.

**La règle qui a produit cet état existe et elle est juste.** L'ADR `0020` pose qu'aucun libellé
n'est inventé pour les quatre dimensions à clé naturelle : on ne décide pas que `HGO` signifie tel
service si rien ne l'établit.

**Mais sa portée a été prise plus large qu'elle n'est.** Elle interdit d'inventer un libellé pour une
**valeur de code venue du système observé**. Elle n'interdit pas d'afficher un libellé qu'une
**source documentée** établit. C'est la même confusion que l'ADR `0049` a levée pour les
descriptions de colonnes : une prudence légitime sur les valeurs de code s'était étendue, sans être
réexaminée, à tout ce qui ressemblait à un libellé.

**Trois mesures ont été prises avant d'écrire quoi que ce soit.**

**1. Le recensement.** Treize emplois, sur quatre pages, portant cinq nomenclatures : activité
(6 emplois), niveau de tri (3), orientation de sortie (1), service (2), type d'épisode (2).
**28 codes distincts** au total.

**2. L'origine des valeurs, lue et non supposée.** Les cinq listes sont produites par le générateur
depuis sa configuration. Deux y portent l'étiquette `DOC` — `nomenclature_activite` sur `S-30`,
`nomenclature_orientation_sortie` sur `S-27` — et trois l'étiquette `HYP`. Le relevé du système
observé, interrogé sur le champ dont la colonne d'activité tire sa provenance, dit :
`REL-RDV.R02 … valeurs_observees: aucune_valeur_observee`. **Le champ a été relevé, aucune de ses
valeurs ne l'a été** : rien d'observé ne peut donc contredire une nomenclature documentée.

**3. Ce que chaque source établit, article par article.**

| Nomenclature | Source | Ce que la source dit | Décomptes |
|---|---|---|---|
| activité | `S-30` | donne les codes **et** les libellés, nomenclature nationale des spécialités médicales | 8 codes / 8 entrées reprises |
| orientation de sortie | `S-27` | les articles 42, 44, 46 et 47 **nomment** cinq issues du passage | 5 issues / **5 codes** |
| niveau de tri | `S-12` | distingue **trois** groupes de gravité | 3 groupes / **5 niveaux** |
| service | `S-27` | l'article 27 affirme une organisation en services **sans les nommer** | — |
| type d'épisode | `S-27` | l'article 36 établit une taxonomie **sans l'énumérer** | — |

## Décision

**1. Un code reçoit un libellé si, et seulement si, une source du registre l'établit, et cette
source est citée à l'écran.** Aucune autre condition, et aucune exception.

**2. Le libellé n'efface pas le code : il le suit.** La forme rendue est `code — libellé`. Deux
raisons, et aucune n'est esthétique : le code porte l'ordre de tri des axes — les codes d'activité
sont du texte, triés lexicographiquement, et les préfixer **conserve exactement l'ordre rendu
jusqu'ici** — et il reste le lien avec les exports, où seul le code figure.

**3. Une table de correspondance unique porte les 28 codes, documentés et non documentés.** Un
registre qui ne porterait que les codes documentés laisserait croire à l'exhaustivité. Chaque entrée
documentée cite l'identifiant de sa source **et le renvoi précis** — « tableau 38, pages 63-64 »,
« articles 42, 44, 46 et 47 » — un identifiant seul ne permettant pas de vérifier.

**4. Elle vit sous `dashboard/`, à côté du registre des indicateurs, et non sous `docs/`.** C'est
une décision de mesure et non de goût : l'image du service ne copie que `dashboard/` et `ingestion/`,
et `ls /app/docs` y répond *No such file or directory*. Un registre placé sous `docs/` serait
introuvable au rendu — le défaut qui avait déjà empêché les pages de rendre dans le conteneur. Les
registres lus à la construction ou au contrôle vivent sous `docs/` ; celui que le service lit vit
avec lui.

**5. Un code non documenté reste nu, avec la mention qui le dit.** Les mentions existantes des pages
sont conservées mot pour mot là où elles restent vraies, et corrigées là où la mesure les a rendues
fausses.

## Le décompte, mesuré

| Catégorie | Codes | Dimensions |
|---|---|---|
| **documenté** | **13** | activité (8), orientation de sortie (5) |
| **non documenté** | **15** | niveau de tri (5), service (7), type d'épisode (3) |
| **total** | **28** | cinq dimensions |

## Les codes restés nus, nommés, et pourquoi

**Niveaux de tri — `1`, `2`, `3`, `4`, `5`.** `S-12` ne distingue que **trois** groupes de gravité
— urgences vitales, urgences réelles non vitales, consultations non urgentes — là où les données
portent **cinq** niveaux. La configuration du générateur le déclare elle-même : *« Le nombre de
niveaux retenu ici, cinq, est une décision posée, non démontrée par une source. »* La nomenclature
est décrite, la correspondance de chaque code ne l'est pas. **Les décomptes ne concordent pas, cela
suffit.**

**Services — `CE`, `UR`, `HM`, `HGO`, `HPED`, `LAB`, `RAD`.** L'article 27 du règlement intérieur
affirme que l'hôpital s'organise en services **sans les nommer individuellement**. La source établit
qu'il existe des services, pas lesquels.

**Types d'épisode — `HOS`, `CE`, `UR`.** L'article 36 établit une taxonomie réglementaire des modes
d'utilisation **sans l'énumérer**. C'est le cas le plus tentant du lot : ces trois codes se lisent
immédiatement comme hospitalisation, consultation externe et urgences, et la configuration porte
déjà ces trois libellés — sous l'étiquette `HYP`. **La ressemblance n'est pas une source**, et le
raisonnement « cela ne peut être que cela » est précisément le signal de classer en non documenté.

## Ce qui aurait invalidé cette décision

**Qu'aucune source du registre ne documente aucune nomenclature.** Le lot n'aurait alors produit que
le registre des non-documentés — ce qui resterait utile, puisqu'il rend explicite et vérifiable ce
qui n'était jusque-là qu'une absence.

Ce n'est pas le cas : **deux nomenclatures sur cinq sont documentées**, par deux sources distinctes
dont le registre porte la vérification du contenu, et leurs décomptes concordent avec les données —
5 issues nommées pour 5 codes, 8 spécialités reprises pour 8 codes.

**Qu'une correspondance exige une source neuve.** Aucune ne l'a exigé : `S-27` et `S-30` étaient
déjà employées par le projet. Le champ d'usage de `S-30` au registre des sources est précisé pour
nommer le tableau dont ces libellés sont tirés, et rien d'autre n'y est ajouté.

## Vérification

`tests/test_libelles_dimensions.py` porte trois propriétés, et **elles observent ce que les pages
rendent** plutôt que ce que le registre déclare : tout libellé rendu a une entrée documentée et une
source qui existe au registre des sources ; registre et données se couvrent dans les deux sens ; et
un code classé non documenté n'affiche aucun libellé. Cinq mutations les font rougir, dont une qui
fait inventer un libellé à une page.

## Sources

`docs/sources/sources.yml` — `S-27` (règlement intérieur reproduit, source de droit `S-03`), `S-30`
(Santé en chiffres 2024), `S-12` (avis sur les urgences médicales).
`docs/observation/releve_champs.yml` — `REL-RDV.R02`, dont aucune valeur n'a été observée.
`docs/champs/registre_champs.yml` — la provenance déclarée de chaque colonne concernée.
`docs/decisions/0020-dimensions-simples-cle-naturelle.md` — la règle dont ce lot précise la portée.
`docs/decisions/0049-documentation-des-couches-aval.md` — la même distinction, appliquée aux
descriptions de colonnes.
`docs/decisions/0043-instantane-schema-dedie-du-tableau-de-bord.md` — ce que le service lit.
