# ADR 0058 — Une personne retenue reçoit une seconde fiche, et une seule, ouverte à un épisode tiré

**Statut.** Accepté, et appliqué depuis l'écriture du générateur de patients.

> **Enregistrement rétrospectif.** Le mécanisme a été écrit et appliqué avant que sa consignation ne
> le soit ; le présent enregistrement est rédigé à partir du code et de la configuration, non de
> mémoire. Le cadrage veut qu'un enregistrement soit écrit au moment de la décision : il y est
> dérogé sciemment, pour que le mécanisme central du bloc de rapprochement cesse de n'être justifié
> que par la note d'un paramètre.

---

## Contexte

Le rapprochement probabiliste d'identités est évalué contre une vérité terrain : les paires de
fiches qui désignent la même personne sont connues, parce que le générateur les a produites. Tout
ce que le bloc de rapprochement mesure — précision, rappel, seuil retenu, apport face à la
collision exacte — repose donc sur la façon dont ces doublons sont injectés.

`docs/decisions/0005-rapprochement-probabiliste-plutot-que-collision-exacte.md` en porte deux
éléments, mais dans son **contexte** et non comme décision : le taux de 4 %, posé faute de source
chiffrée, et l'existence de six variations. **Le reste du mécanisme n'est consigné nulle part** : il
vit dans `generator/doublons.py` et dans la note de trois paramètres de
`generator/config/defauts.yml`. Une note de paramètre dit ce qu'une valeur serait si elle était
fausse ; elle ne dit pas pourquoi le mécanisme a cette forme-là.

## Décision

**1. Une personne retenue reçoit une seconde fiche, et une seule.** Le mécanisme n'ouvre jamais une
troisième fiche pour la même personne, et ne change le nombre de personnes d'aucune façon —
seulement le nombre de fiches qui les portent. La vérité terrain est donc faite de paires, jamais
de grappes de trois.

**2. Le nombre de personnes retenues est calculé, puis exactement ce nombre est choisi sans
remise** — `n_cible = round(taux × effectif)` —, et non tiré indépendamment personne par personne.
Les deux procédés donnent la même distribution marginale ; l'allocation exacte supprime la variance
sur le total, de sorte que le nombre de paires de la vérité terrain ne dépend pas de la graine.

**3. Seules sont éligibles les personnes portant au moins deux épisodes à des dates distinctes.**
Une personne dont tous les épisodes tombent le même jour n'a aucun point de scission qui sépare
réellement deux périodes de sa trajectoire.

**4. Le point de scission est tiré uniformément** parmi les épisodes strictement postérieurs au
premier (`loi_ouverture_seconde_fiche: uniforme`). Les épisodes antérieurs restent sur la première
fiche, ceux qui suivent passent sur la seconde : aucun épisode n'est inventé, supprimé ni déplacé
dans le temps.

**5. Chaque paire porte une ou deux variations, jamais plus, et jamais deux sur le même champ.**
Les six variations sont regroupées par champ touché — la translittération du prénom et l'inversion
d'un prénom composé portent toutes deux sur `nom` — et la sélection choisit au plus une variation
par champ.

## Justification des points non triviaux

### Pourquoi une seule seconde fiche, et pas une loi sur le nombre de fiches

Une loi sur le nombre de fiches par personne produirait des grappes de trois ou plus, et l'évaluation
du rapprochement cesserait d'être une évaluation de paires : précision et rappel se calculeraient
sur des composantes connexes, dont la définition même prête à discussion. Le projet a préféré une
question plus étroite et entièrement mesurable. **Ce que cette décision laisse ouvert :** un système
réel produit des grappes de plus de deux fiches, et rien ici ne l'imite.

### Pourquoi un plafond de deux variations

`nombre_variations_par_paire` borne à deux, et sa note en donne le motif : au-delà, les deux fiches
d'une même paire divergeraient au point de ne plus rien partager d'identifiant, **ce qui viderait le
problème d'appariement de sa difficulté**. Un plafond plus bas — une seule variation — rendrait au
contraire les paires plus faciles à séparer. Le plafond est donc un réglage de la difficulté du
problème posé au bloc de rapprochement, et il est posé, non mesuré.

### Pourquoi le regroupement par champ touché

Deux variations portant sur la même colonne se contrediraient : appliquer une translittération du
prénom *et* l'inversion d'un prénom composé laisse indéterminé laquelle l'emporte. Le regroupement
par champ rend la question sans objet, plutôt que de la trancher par un ordre d'application que rien
ne justifierait.

## Conséquences

- La vérité terrain est un ensemble de paires disjointes ; aucune grappe de trois n'existe, ni par
  construction ni par accident.
- Le nombre de paires ne varie pas d'une graine à l'autre, à effectif de population égal.
- Toute mesure d'apport du rapprochement face à la collision exacte porte sur cette population de
  paires, et non sur une population de doublons réelle : elle dit ce que la chaîne sait faire, non
  ce que vaudrait le rapprochement dans un établissement.
- Une personne dont les deux fiches sont scindées tard porte peu d'épisodes sur sa seconde fiche :
  la difficulté du rapprochement varie donc d'une paire à l'autre, et c'est voulu.

## Ce qui aurait invalidé cette décision

Une source chiffrant l'ampleur réelle des doublons d'identité dans l'établissement, ou décrivant une
loi de tirage du point de scission différente d'une loi uniforme — un biais vers une scission
tardive, par exemple. Le taux et la loi sont tous deux étiquetés `HYP`, et rien n'est prétendu de
plus.

## Sources

`generator/doublons.py` ; `generator/config/defauts.yml::taux_doublons`,
`::distribution_variations`, `::nombre_variations_par_paire`, `::loi_ouverture_seconde_fiche` ;
`generator/execution.py` (ordre d'appel après la génération des patients) ;
`docs/decisions/0005-rapprochement-probabiliste-plutot-que-collision-exacte.md` ;
`docs/relations_injectees.yml::R-14`.
