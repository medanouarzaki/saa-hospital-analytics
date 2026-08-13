# ADR 0024 — Ce que les faits ne portent pas : quatre limites documentées plutôt que comblées

**Statut.** Accepté.

---

## Contexte

Quatre lacunes ont été identifiées en construisant les six tables de faits, chacune tentante à
combler par une colonne ou un modèle supplémentaire. Chacune a été mesurée avant toute décision,
et dans les quatre cas la mesure a montré qu'une fabrication serait soit sans fondement dans la
source, soit hors du périmètre du grain déjà fixé (`docs/decisions/0023-...md`).

## Décision

1. **Aucune distinction obstétrique n'est fabriquée.** Ni colonne, ni acte, ni paramètre de
   configuration ne distingue un accouchement d'un autre séjour du service `HGO`. Mesuré :
   401 séjours au service `HGO`, âges de 0 à 120 ans à l'admission (l'étendue complète d'un
   service généraliste, pas celle d'une population en âge de procréer), un taux de décès de
   10,10 % (40/396 séjours clos, code `D` de `nomenclature_mode_sortie`) statistiquement
   indiscernable du taux tous services confondus (10,08 %, 298/2 955 séjours clos) — le service
   ne se distingue pas des autres par ce critère non plus. 731 factures portent le diagnostic
   CIM-10 `O80` (accouchement unique spontané), tout type d'épisode confondu ; 102 seulement
   relèvent d'un épisode d'hospitalisation, et 20 seulement s'apparient (par le mécanisme
   n_ipp + jour du point 2, déjà ambigu) à un séjour du service `HGO` — le diagnostic
   d'accouchement n'est donc, à travers la facturation, ni majoritairement ni fiablement
   rattachable au service. Décision : ne rien fabriquer, documenter la limite.
2. **Aucun lien entre `fct_sejour` et le passage d'hospitalisation (`fct_passage` filtré sur
   `type_passage = 'H'`).** Deux durées tirées indépendamment par le générateur (établi par
   mesure antérieure), aucune clé directe entre les deux tables. Un appariement par `n_ipp` et
   jour d'admission commun produit 2 982 paires pour 2 980 séjours — l'excédent vient de 4
   ambiguïtés d'appariement (une clé `n_ipp` + jour portée par plus d'une ligne d'un côté).
   Zéro écart de durée nul sur les 2 982 paires (aucune coïncidence), somme des écarts signés
   ≈ 1 968 jours. Le service porté par le passage d'hospitalisation est unique (`HM`, les
   2 980 lignes `H` de `fct_passage`) là où `service_accueil` de `fct_sejour` se répartit sur
   trois services distincts (`HGO` 401, `HM` 2 384, `HPED` 195). Décision : aucun lien entre ces
   deux faits.
3. **Le praticien reste un attribut, sans relation à `dim_agent`.** `fct_passage.medecin` porte
   20 valeurs distinctes ; `dim_agent` ne porte qu'une clé naturelle (`code_agent`, cf.
   `docs/decisions/0020-dimensions-simples-cle-naturelle.md`) sans rôle ni distinction
   praticien/agent système. Rattacher `medecin` à `dim_agent` supposerait une correspondance
   que la source ne fournit pas explicitement. Conservé en texte brut sur le fait, sans clé
   étrangère.
4. **Aucune dimension des actes n'est créée**, bien que mesurée constructible sans orpheline :
   34 codes d'acte distincts observés dans `intermediate.int_lignes_facture`, 34 codes dans
   `nomenclature_actes` (`generator/config/actes.yml`), 0 orphelin dans un sens comme dans
   l'autre. Aucun des six faits écrits n'est cependant au grain de la ligne de facture — le
   grain le plus fin écrit est la facture (`fct_facturation`) ou l'encaissement, pas la ligne
   d'acte — une dimension des actes n'aurait aucun fait à rattacher à ce grain.

Chacune de ces quatre limites : ce qu'il faudrait pour la lever. (1) une colonne source
distinguant explicitement l'accouchement du reste du service `HGO`, absente aujourd'hui. (2) une
clé commune entre mouvement et passage d'hospitalisation dans la source, ou l'abandon de
l'hypothèse d'un appariement par proximité temporelle. (3) une table source associant `medecin`
à un rôle ou une spécialité. (4) un futur fait au grain de la ligne de facture
(`fct_ligne_facture`), non écrit à ce jour.

## Justification des points non triviaux

### Pourquoi l'absence de coïncidence de durée (point 2) est la preuve décisive, pas l'absence de clé

L'absence de clé directe pourrait à elle seule justifier de ne pas lier les deux faits ; mais
elle laisserait ouverte la possibilité qu'un appariement approché (patient + jour) retrouve la
même grandeur par un autre chemin. Le zéro écart nul sur 2 982 paires ferme cette possibilité :
même appariées, les deux durées ne convergent jamais, confirmant qu'il s'agit de deux tirages
indépendants et non de deux vues de la même durée réelle.

## Conséquences

Quatre limites documentées ici plutôt que comblées par une hypothèse non mesurée. Un lecteur qui
chercherait à comparer la durée d'un séjour à celle du passage d'hospitalisation qui l'a précédé,
ou à isoler les accouchements du reste de l'activité `HGO`, trouve la limite énoncée ici plutôt
qu'un résultat silencieusement approximatif.

## Ce qui aurait invalidé cette décision

Une future colonne source portant explicitement un indicateur d'accouchement, un diagnostic
détaillé par ligne d'acte, ou une clé de rapprochement entre mouvement et passage
d'hospitalisation invaliderait respectivement les points 1 et 2 — à re-mesurer avant toute
tentative de comblement.

## Sources

`marts.fct_sejour`, `marts.fct_passage`, `marts.fct_facturation`, `intermediate.
int_lignes_facture` ; `generator/config/actes.yml::nomenclature_actes`,
`generator/config/nomenclatures_clinique.yml` (code `O80`) ; `docs/decisions/
0020-dimensions-simples-cle-naturelle.md` ; mesures antérieures sur l'identité de troncature du
délai de rendez-vous et l'indépendance des durées de séjour et de passage d'hospitalisation.
