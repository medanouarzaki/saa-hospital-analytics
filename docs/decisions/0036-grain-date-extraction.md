# ADR 0036 — Le grain d'une exécution est la date d'extraction

**Statut.** Accepté.

---

## Contexte

Deux notions de date coexistent dans les données du projet : la date d'extraction du fichier
(portée à la fois par le nom du répertoire de partition et par une colonne `date_extraction`
homonyme à l'intérieur de chaque CSV) et la date de l'événement métier propre à chaque table
(`date_rendez_vous` pour `rendez_vous`, et de même pour les autres). Le graphe doit choisir
laquelle des deux définit ce qu'est « un jour » pour une exécution.

## Décision

Une exécution du graphe correspond à une date d'extraction, jamais à une date d'événement.
L'intervalle de données de l'exécution est rendu, dans les commandes shell des tâches, par le
filtre de gabarit qui produit `AAAA-MM-JJ` sur la date logique de l'exécution.

## Justification des points non triviaux

### Pourquoi la date d'extraction, pas la date d'événement

Mesure décisive : le fichier de rendez-vous d'une date d'extraction prise au hasard
(`2024-06-15`) porte une seule valeur de `date_extraction` mais 43 valeurs distinctes de
`date_rendez_vous`, étalées du 15 juin au 17 septembre 2024 — un fichier d'extraction est
l'instantané d'un carnet de rendez-vous, passés et futurs, pas le relevé d'une journée
d'activité. Filtrer par date d'événement rejouerait donc, à chaque exécution, une tranche
mouvante d'un même instantané ; filtrer par date d'extraction correspond exactement à ce que le
chargeur sait isoler nativement, partition par partition.

## Conséquences

Ce que le graphe traite un jour donné est ce que le système source exposait ce jour-là — un
instantané, pas un flux d'activité daté. Les indicateurs de la couche marts, eux, restent datés
par l'événement métier (`fct_rendez_vous.date_rendez_vous` et équivalents) : le grain d'exécution
du graphe et le grain d'analyse des indicateurs ne coïncident pas, et ne doivent pas être
confondus l'un avec l'autre dans la documentation ou le nommage des tâches.

## Ce qui aurait invalidé cette décision

Une extraction incrémentale du système source, qui ne porterait que l'activité du jour même
plutôt qu'un instantané cumulatif du carnet — dans ce cas, date d'extraction et date d'événement
coïncideraient et la distinction n'aurait plus lieu d'être.

## Sources

`generator/output/scenario_30/source.rendez_vous/2024-06-15/rendez_vous.csv` (colonnes
`date_extraction`, `date_rendez_vous`) ; filtre de gabarit `ds`
(`airflow.sdk.definitions._internal.templater.ds_filter`, version installée de l'orchestrateur) ;
`ingestion/chargeur.py` (`--date-debut`/`--date-fin`, filtrage par partition avant lecture du
fichier).
