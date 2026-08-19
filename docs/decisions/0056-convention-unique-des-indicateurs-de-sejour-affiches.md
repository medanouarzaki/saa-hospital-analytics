# ADR 0056 — Convention unique pour les quatre indicateurs de séjour affichés

**Statut.** Accepté.

---

## Contexte

Quatre indicateurs de séjour — taux d'occupation moyen, durée moyenne de séjour, taux de rotation,
intervalle de rotation — étaient calculés dans le dépôt selon **trois conventions différentes**, et
la plus visible des trois était fausse.

| Où | Numérateur | Dénominateur temporel | Annualisation |
|---|---|---|---|
| Page des séjours | `sum(duree_jours)`, séjours non clos exclus | étendue observée des faits, 911 jours | **aucune** |
| Contrôle sur la couche modélisée | durées d'horodatages, séjours non clos **censurés** | 912 jours déclarés, puis 365 | × 365/912 |
| Reconstitution depuis la configuration | grandeur publiée | 365 | sans objet |

La première ne comptait pas les journées des séjours non clos au numérateur mais comptait leurs
admissions au dénominateur de la durée moyenne : deux populations mêlées, écart mesuré 0,846 %.
Surtout, elle n'annualisait pas. Le taux de rotation affiché valait donc **74,5** là où la valeur
publiée est 29,9 — faux d'un facteur voisin de 2,5, soit exactement 912/365, alors même que le
registre des indicateurs déclarait cette entrée `grandeur_annualisee` et que l'écran affichait à
côté du chiffre que « cette grandeur rapporte un volume à une année de référence ».

**Aucun contrôle ne pouvait le voir.** Ceux qui portaient sur ces grandeurs interrogeaient la couche
modélisée, quand la page interroge le schéma d'instantané. Celui qui portait sur la page
retranscrivait sa formule et se comparait à elle à 10⁻⁹ près : une comparaison vraie par
construction, incapable de départager une formule juste d'une formule fausse. Elle est restée verte
pendant toute la durée du défaut.

## Décision

**1. La page adopte la convention du contrôle.** Elle ne corrige pas le seul facteur manquant : elle
calcule ce que le contrôle calcule — durées d'horodatages, séjours non clos censurés à la date de
référence des données, annualisation, dénominateur en année de référence. Une seule convention
subsiste, donc un seul contrôle peut couvrir l'affichage et l'entrepôt. La censure donne une durée
à chaque séjour, ce qui supprime le défaut de population mixte sans traitement particulier.

**2. Aucune constante n'entre dans la page.** Quatre valeurs y entrent par lecture : la capacité
litière, la durée de l'année de référence et la durée de la période depuis la table de paramètres
de l'instantané, chacune avec le fichier et la clé d'où elle est tirée ; la borne de censure depuis
la table d'état. Le mécanisme de reprise, qui pointait un fichier unique, est généralisé en une
correspondance entre un nom de paramètre et le fichier qui le porte.

**3. La seconde mesure qui retranscrivait la formule cède la place à deux références qui ne le font
pas** : les valeurs publiées, lues dans la configuration et extérieures au code ; et l'accord entre
deux implémentations écrites séparément — la page en SQL sur l'instantané, la convention de
l'entrepôt en Python sur la couche modélisée.

**4. Le facteur d'annualisation est pris de la période déclarée, non de l'étendue observée.**

## Justification des points non triviaux

### Pourquoi la durée de période est lue et non mesurée sur les faits

C'est une **exception déclarée** au principe qui veut que tout indicateur soit recalculé depuis les
faits, et elle est motivée.

La durée de la période est une propriété de la **fenêtre d'extraction**, non de la donnée : elle dit
sur combien de jours l'établissement a été observé, ce qu'aucune ligne ne porte. L'étendue observée
des faits, elle, dépend du hasard des admissions à ses bornes. Ici les deux diffèrent d'un jour —
aucune admission ne tombe le 1er janvier 2024, la première est du 2 — et **cet écart d'un seul jour
déplace le taux d'occupation de 0,0586 point**, mesuré. Un établissement sans admission le premier
jour de la période verrait donc son taux réglementaire monter, sans qu'aucune journée
d'hospitalisation ait changé.

L'étendue observée reste calculée et **affichée** à côté des indicateurs : un lecteur voit les deux
durées et peut constater qu'elles ne coïncident pas.

### Pourquoi une seconde mesure qui retranscrit ne prouve rien

Une seconde mesure n'a de valeur que si elle peut être fausse quand la première l'est, et vraie
quand la première ne l'est pas. Une réécriture de la même formule ne le peut pas : ses deux membres
bougent ensemble. Les deux références retenues n'ont pas ce défaut. La première a son second membre
hors du code — aucune écriture du dépôt ne peut la rendre vraie. La seconde compare deux
implémentations dans deux langages, contre deux schémas ; une mutation portée sur l'une seule les
fait diverger, ce qui a été vérifié.

L'asymétrie entre les deux est elle-même une propriété utile : déplacer la borne de censure d'un
jour fait rougir l'accord entre implémentations — l'écart y vaut 0,0685 point — sans faire rougir
la conformité aux valeurs publiées, qui tolère 3 %. **Les deux ne font donc pas double emploi.**

## Conséquences

- Les quatre valeurs affichées deviennent 53,3639 %, 6,5326 j, 29,8163 et 5,7090 j, à
  0,81 %, 1,02 %, 0,28 % et 1,95 % des valeurs publiées — les quatre sous la tolérance de 3 %.
- Le taux de rotation affiché passe de 74,5 à 29,8.
- Un même écart de convention entre l'écran et l'entrepôt fait désormais rougir un contrôle, quel
  que soit celui des deux qui dérive.
- La table de paramètres de l'instantané porte trois entrées au lieu d'une ; le contrôle qui relit
  le fichier que chaque provenance désigne les couvre toutes sans modification.
- La durée de période lue est une entrée de configuration : la changer change les indicateurs
  publiés sans qu'aucune donnée bouge. C'est le prix de l'exception, et il est assumé.

## Ce qui aurait invalidé cette décision

Une divergence entre la date de fin de période de la configuration et la date de référence des
données de l'instantané : la page censure sur la seconde, la convention de l'entrepôt sur la
première. Elles coïncident aujourd'hui — 2026-06-30 des deux côtés — et l'accord entre
implémentations rougirait si elles cessaient de coïncider, ce qui est le comportement voulu.

## Sources

`dashboard/pages/sejours.py` ; `tests/test_indicateurs_sejour.py` ;
`tests/test_indicateurs_sejour_affiches.py` ; `dashboard/indicateurs.yml` ;
`instantane/rafraichir.py` ; `generator/config/volumetrie.yml` ; `generator/config/periode.yml` ;
`docs/decisions/0026-garde-applicabilite-indicateurs-sejour.md`.
