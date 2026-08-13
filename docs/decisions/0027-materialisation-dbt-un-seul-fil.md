# ADR 0027 — La matérialisation dbt s'exécute sur un seul fil, les tests gardent leur parallélisme

**Statut.** Accepté.

---

## Contexte

`dbt run` échouait de façon intermittente avec un `deadlock detected` PostgreSQL sur la
matérialisation des vues, sous la concurrence par défaut de dbt (4 fils). Diagnostiqué : quatre
fils exécutant en parallèle la séquence de remplacement d'une vue (création d'une vue temporaire,
renommage, suppression de l'ancienne) se disputent des verrous sur le catalogue système
(`pg_class`, classe de verrou `2618`) — deux processus peuvent chacun attendre un verrou détenu
par l'autre.

## Décision

1. **`cd dbt && uv run dbt run` devient `cd dbt && uv run dbt run --threads 1`**
   (`.github/workflows/ci.yml`, job `dbt`). Option lue et citée dans `dbt run --help` :
   `--threads INTEGER — Specify number of threads to use while executing models. Overrides
   settings in profiles.yml.`
2. **Fréquences mesurées dans les deux configurations** (10 exécutions chacune, lot de mesure
   6g, H0) : 3 échecs sur 10 à 4 fils (le défaut du profil), 0 échec sur 10 à 1 fil.
3. **Seule l'étape de matérialisation est restreinte.** `dbt seed` et `dbt test` gardent leur
   parallélisme à 4 fils (valeur inchangée du profil, `threads: 4`,
   `.github/workflows/ci.yml`) : les tests sont des lectures qui ne prennent aucun verrou
   exclusif sur le catalogue, non exposées au même interblocage, et leur durée est devenue la
   part longue de la chaîne dbt depuis l'ajout des agrégats de qualité de données (`dbt test`
   complet : 4,66 s avant l'écriture des agrégats de recouvrement/qualité/doublons, 17,43 s
   après).
4. **Le profil écrit par le job garde `threads: 4`, inchangé.** La correction reste visible à
   la lecture de l'étape `dbt run` qu'elle protège (`--threads 1` explicite sur la ligne de
   commande, qui l'emporte sur le profil), plutôt que dissimulée dans une valeur de profil que
   la lecture de l'étape ne révélerait pas.

## Justification des points non triviaux

### Pourquoi ne pas simplement mettre `threads: 1` dans le profil

Cela réduirait aussi la concurrence de `dbt seed` (une seule table, sans le mécanisme de
remplacement de vue qui cause l'interblocage — le gain de parallélisme y serait perdu sans
bénéfice) et masquerait, à la lecture du profil seul, quelle étape précise est protégée et
pourquoi. Un flag explicite sur la ligne de commande de l'étape concernée documente la portée de
la correction à l'endroit où elle s'applique.

## Conséquences

Le job `dbt` de la CI ne devrait plus jamais rencontrer l'interblocage sur `dbt run`. Un
exécutant local qui reproduit le projet à la main (profil hors dépôt, `~/.dbt/profiles.yml`,
`threads: 4` par défaut) reste exposé au même interblocage intermittent s'il ne passe pas
lui-même `--threads 1` — cette correction ne porte que sur le workflow CI, le profil local
n'étant pas un fichier du dépôt.

## Ce qui aurait invalidé cette décision

Une évolution de dbt-core changeant le mécanisme de remplacement de vue (par exemple un DDL
atomique remplaçant la séquence création/renommage/suppression) pourrait supprimer la cause de
l'interblocage et rendre cette restriction inutilement conservatrice — à re-mesurer après toute
montée de version de dbt-core ou de l'adaptateur postgres.

## Sources

`.github/workflows/ci.yml` (job `dbt`) ; `dbt run --help` ; mesures antérieures du diagnostic de
l'interblocage et de ses fréquences par configuration de fils, et de la durée de `dbt test`
avant/après l'écriture des agrégats de qualité de données ; `~/.dbt/profiles.yml` (hors dépôt,
non modifié).
