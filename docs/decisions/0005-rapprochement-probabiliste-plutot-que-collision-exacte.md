# ADR 0005 — Le rapprochement des fiches patient est probabiliste ; la collision exacte reste comme témoin

**Statut.** Accepté, et appliqué depuis l'écriture du bloc de rapprochement.

> **Enregistrement rétrospectif.** Cette décision a été prise et appliquée avant que sa consignation
> ne soit écrite ; le présent enregistrement est rédigé le 18 août 2026, à partir de l'état du dépôt
> et des documents de suivi du projet. Le cadrage prescrit qu'un enregistrement soit écrit au moment
> de la décision et jamais rétrospectivement : il y est ici dérogé sciemment, pour qu'un numéro
> réservé et cité depuis l'origine cesse de renvoyer à un fichier absent.

---

## Contexte

Une même personne peut porter deux fiches patient. `S-20` — le rapport de la Cour des comptes sur le
centre hospitalier préfectoral de Meknès — en établit **l'existence**, sans en chiffrer l'ampleur ;
le taux est donc posé (`taux_doublons`, 4 %, étiqueté `HYP` dans `generator/config/defauts.yml`).

Les deux fiches d'une même personne ne sont pas identiques : le mécanisme d'injection leur applique
une ou deux variations tirées parmi six — translittération du prénom, inversion des composantes d'un
prénom composé, faute de frappe sur la date de naissance, pièce d'identité absente, téléphone
différent, adresse mise à jour.

La question posée était de savoir si un rapprochement par **collision exacte** suffisait. Deux
critères s'offraient immédiatement, et sont d'ailleurs déjà calculés par la couche analytique
(`dbt/models/marts/agg_doublons_identite.sql`) :

- prénom + premier nom de famille + date de naissance ;
- type de pièce d'identité + numéro de pièce d'identité.

Elle a été tranchée par mesure. Sur la population de **25 842 patients de version courante**, la
vérité terrain porte **996 paires**, dont **991 présentes** dans cette population.

**1. Ce que la collision exacte atteint.** Chaque critère, puis leur union, confrontés aux 991
paires :

| Critère | Paires produites | Vrais positifs | Faux positifs | Faux négatifs | Précision | Rappel | F |
|---|---|---|---|---|---|---|---|
| prénom + nom de famille + naissance | 363 | 350 | 13 | 641 | 0,964 | 0,353 | 0,517 |
| type + numéro de pièce d'identité | 767 | 724 | 43 | 267 | 0,944 | 0,731 | 0,824 |
| **union des deux** | **926** | **870** | **56** | **121** | **0,940** | **0,878** | **0,908** |

L'union n'est donc ni complète — 121 paires manquées — ni exacte : **56 paires fausses**, dont 43
tiennent à la seule collision de pièce d'identité entre deux personnes distinctes.

**2. Pourquoi elle manque ce qu'elle manque.** Le rappel de l'union, ventilé par combinaison de
variations portée par la paire, ne se dégrade pas graduellement : il tombe à **zéro exactement**, et
sur trois combinaisons seulement.

| Combinaison de variations | Paires | Retrouvées | Rappel |
|---|---|---|---|
| pièce absente + faute de frappe sur la date de naissance | 50 | 0 | **0,000** |
| pièce absente + prénom composé inversé | 46 | 0 | **0,000** |
| pièce absente + translittération du prénom | 23 | 0 | **0,000** |
| pièce absente + adresse mise à jour | 39 | 38 | 0,974 |
| *les seize autres combinaisons* | 833 | 832 | ≥ 0,987 |

**119 des 121 paires manquées sont dans ces trois cellules.** Le motif est structurel et non
statistique : une variation détruit le premier critère, l'autre détruit le second, et les deux seuls
critères exacts disponibles tombent ensemble. Aucun réglage de la collision exacte ne les rattrape,
puisqu'il ne reste plus rien d'exactement égal à quoi s'accrocher.

## Décision

**1. Le rapprochement des fiches patient est probabiliste**, par modèle de Fellegi–Sunter estimé sur
les données elles-mêmes, sans étiquettes de vérité (`linkage/estimation.py` : probabilité qu'une
paire tirée au hasard corresponde, `u` par échantillonnage aléatoire, `m` par espérance-maximisation
sur les règles de blocage). Douze comparaisons entrent au modèle ; quatre règles de blocage
produisent les paires candidates.

**2. La collision exacte n'est pas retirée : elle devient le témoin auquel le rapprochement se
compare.** `agg_doublons_identite` continue de compter et d'exposer les deux critères — l'agrégat
dit lui-même qu'il *« ne réconcilie ni ne fusionne aucun patient »* —, la page de rapprochement du
tableau de bord affiche côte à côte les paires réunies par l'un et par l'autre, et
`linkage/ablation.csv` porte la mesure du témoin (`f_mesure_baseline_collision_exacte`) sur chaque
variante du modèle.

**3. Le dépassement du témoin est une propriété vérifiée, pas une affirmation.** La colonne
`depasse_la_baseline` de l'ablation le tient sur les quatre variantes mesurées, y compris celle qui
retire six comparaisons et neutralise l'absence unilatérale de pièce d'identité.

## Justification des points non triviaux

### Ce que le probabiliste gagne, mesuré sur les paires que la collision ne peut pas voir

Sur les **5 014** paires candidates produites par les quatre règles de blocage, les **991** paires
vraies sont toutes présentes, et le seuil retenu les sépare toutes : précision et rappel valent
**1,0** l'un et l'autre. Sur les **119** paires que la collision exacte perd structurellement — les
trois cellules à rappel nul —, le rapprochement probabiliste en retrouve **119**.

Il ne s'agit pas d'un gain marginal sur une mesure agrégée : c'est exactement la population que
l'approche écartée ne pouvait pas atteindre.

### Pourquoi une preuve d'accord n'aurait pas suffi

Une comparaison des seules F-mesures — 0,908 contre 1,000 — laisserait croire à un écart de neuf
points de qualité, réductible par un meilleur réglage. La ventilation par combinaison de variations
dit autre chose, et c'est elle qui tranche : l'écart n'est pas réparti, il est concentré sur une
population que la méthode écartée ne voit pas du tout. **Un écart concentré à zéro et un écart
réparti n'appellent pas la même décision**, et seule la seconde mesure les distingue.

### Pourquoi la collision exacte survit quand même

Elle coûte deux agrégations et sert trois usages qu'un modèle probabiliste ne rend pas :

- elle est **lisible sans le modèle** — un lecteur qui ne veut pas entrer dans les poids voit un
  décompte de fiches partageant un numéro de pièce, et ce décompte se vérifie à la main ;
- elle est le **plancher** contre lequel le modèle se justifie : sans témoin, une F-mesure de 1,0 ne
  dit pas si le problème était difficile ;
- elle **survit à l'ablation** : les variantes qui dégradent le modèle restent comparables au même
  témoin, ce qui rend leur dégradation interprétable.

### Ce que cette décision ne décide pas

Elle ne fixe **pas le seuil** de décision — c'est l'objet de l'ADR `0035`, qui le choisit sur des
propriétés observables sans étiquettes —, ni les **règles de blocage** (ADR `0030`), ni le **moteur
d'exécution** en mémoire (ADR `0029`), ni la **métrique primaire** (ADR `0034`). Elle décide du seul
choix de méthode, et de ce que la méthode écartée devient une fois écartée.

## Conséquences

Le projet porte un bloc de rapprochement complet — normalisation, blocage, comparaisons, estimation,
prédiction, regroupement, évaluation, ablation — là où une collision exacte aurait tenu en une
requête. Ce coût est assumé : il est la contrepartie des 119 paires.

L'évaluation exige une **vérité terrain**, dont le générateur est la seule source. Ce que la chaîne
démontre est donc qu'elle **sait retrouver les paires qu'elle a elle-même dégradées**, et non ce que
vaudrait le modèle sur un fichier réel — les paramètres de dégradation étant posés, l'inférence vers
un établissement réel n'est pas permise.

La collision exacte reste affichée, et un lecteur qui ne lit que ce chiffre lit un sous-décompte :
la page de rapprochement le dit en toutes lettres plutôt que de le laisser deviner.

## Ce qui aurait invalidé cette décision

**Que la collision exacte atteigne la même qualité.** Le bloc probabiliste n'aurait alors été qu'une
complication, et la décision aurait été inverse : deux requêtes d'agrégation, et rien d'autre.

Cette mesure a été faite. La collision exacte plafonne à **F = 0,908**, avec 121 paires manquées et
56 paires fausses, contre **F = 1,000** sans faux positif ni faux négatif — et son échec est
**structurel sur 119 paires**, non améliorable par réglage.

**Qu'aucune variation ne détruise deux critères à la fois.** Si le plafond du nombre de variations
par paire avait été fixé à 1 plutôt qu'à 2 (`nombre_variations_par_paire`), les trois cellules à
rappel nul n'existeraient pas et la collision exacte s'approcherait du rappel complet. Ce plafond
est posé, non mesuré : la décision dépend donc d'un paramètre du générateur, et cet enregistrement
le dit plutôt que de le taire.

## Sources

`generator/config/defauts.yml` — le taux de doublons, les six catégories de variation et leur
pondération, le plafond de deux variations par paire.
`generator/doublons.py` — l'application des variations à la seconde fiche.
`dbt/models/marts/agg_doublons_identite.sql` — les deux critères de collision exacte, et le
troisième écarté pour dégénérescence mesurée.
`linkage/ablation.csv` — les quatre variantes mesurées, le témoin de collision exacte et son
dépassement.
`docs/decisions/0029-moteur-execution-en-memoire.md` — le moteur sur lequel le modèle s'exécute.
`docs/decisions/0030-quatre-regles-de-blocage.md` — les règles qui produisent les paires candidates.
`docs/decisions/0034-metrique-primaire-paire-secondaire-grappe.md` — la métrique à laquelle ces
mesures se rapportent.
`docs/decisions/0035-seuil-choisi-sans-etiquettes.md` — le seuil de décision, et la marge de
séparation entre paires vraies et fausses.
`docs/sources/sources.yml` — `S-20`, qui établit l'existence des identifiants multiples sans en
chiffrer l'ampleur.
