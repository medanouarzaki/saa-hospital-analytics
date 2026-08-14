# ADR 0042 — Isolation d'un instrument jetable : composition arrêtée, `.env` déplacé hors du dépôt

**Statut.** Accepté.

---

## Contexte

Deux chemins distincts atteignent la base du projet réel sans qu'aucune variable de connexion
n'ait été demandée explicitement.

Le premier : `ingestion/appliquer_ddl.py` et `ingestion/chargeur.py` lisent les variables de
connexion depuis l'environnement du processus, puis complètent toute clé absente depuis `.env` à
la racine du dépôt (`variables.setdefault(...)`, jamais l'inverse). `.env` porte les paramètres
du projet réel. Toute invocation de l'un de ces deux scripts sans les quatre variables
`POSTGRES_HOST`/`POSTGRES_PORT`/`POSTGRES_DB`/`POSTGRES_USER` explicitement exportées cible donc
silencieusement la base réelle. `~/.dbt/profiles.yml`, hors dépôt, porte la même défaillance pour
`dbt` : ses valeurs par défaut (port 5433, base `saa`) sont celles du projet réel.

Le second : une commande exécutée à l'intérieur du conteneur PostgreSQL du projet (`docker
exec`) atteint la base réelle par une socket locale, sans jamais passer par un port TCP. Mesuré :
`SELECT current_database(), inet_server_port()` exécuté ainsi rapporte un port vide alors que
`current_database()` vaut bien `saa`. Aucune variable `POSTGRES_PORT`, aucun garde-fou fondé sur
le port, ne peut intercepter ce chemin.

Un garde-fou par commande (vérification de `current_database()` avant une écriture qu'on lui
soumet explicitement) a déjà été utilisé, et a déjà tenu son rôle sur les écritures qu'il
enveloppait. Il est structurellement insuffisant face aux deux chemins ci-dessus : il ne couvre
que les commandes qu'il enveloppe, jamais une commande tierce (script, `dbt`, `docker exec`) qui
ouvre sa propre connexion sans lui être soumise. Deux incidents mesurés l'ont montré : la
recréation, vide, des tables `source` de la base réelle, et une paire d'invocations `dbt run`
ayant ciblé la base réelle au milieu d'une série qui ciblait correctement un instrument jetable —
aucune des deux n'était une commande que le garde-fou par commande aurait pu voir passer.

## Décision

Pendant tout travail opérant sur un instrument jetable : la composition Docker du projet est
arrêtée (`docker compose stop`, jamais `down` avec suppression de volumes), et `.env` est déplacé
hors du dépôt — pas supprimé, pas renommé sur place. À la fin, `.env` est remis à son emplacement
d'origine et la composition redémarrée. Les deux opérations sont vérifiées par mesure aux deux
bouts : empreinte de `.env` avant déplacement et après remise, décomptes de la base après
redémarrage comparés à ceux d'avant arrêt.

## Justification des points non triviaux

### Pourquoi arrêter la composition plutôt que faire confiance à un garde-fou renforcé

Un garde-fou, aussi renforcé soit-il, reste une commande qu'il faut se souvenir d'appeler. Les
deux chemins d'accès ne passent par aucun point d'entrée commun où le placer une fois pour
toutes : l'un est un repli de bibliothèque dans un script tiers, l'autre une propriété du
conteneur lui-même. Rendre la cible injoignable — composition arrêtée, fichier de connexion
absent — élimine le besoin de se souvenir : aucune commande, aussi mal ciblée soit-elle, n'a plus
personne à qui parler.

### Pourquoi déplacer `.env` plutôt que le vider ou le supprimer

Vider ou supprimer `.env` le remplacerait par un fichier différent au retour (recréé à la main,
avec un risque de divergence non détecté). Le déplacer préserve son contenu exact, vérifiable par
une simple empreinte avant et après ; la remise est alors une opération réversible et mesurée,
pas une reconstruction.

### Pourquoi arrêter la composition plutôt que la seule base

Le second chemin (`docker exec`) ne dépend pas de la base seule : n'importe quel conteneur de la
composition ayant accès au réseau ou aux volumes du projet pourrait en théorie servir de point
d'entrée détourné. Arrêter la composition entière plutôt que le seul service `postgres` retire
cette possibilité sans avoir à énumérer tous les chemins qu'un conteneur pourrait offrir.

## Conséquences

Aucun travail sur un instrument jetable ne peut plus atteindre la base réelle par défaut, y
compris par une commande dont l'auteur du travail n'a pas anticipé qu'elle ouvrirait sa propre
connexion. Le coût est un arrêt et un redémarrage de la composition à chaque début et fin d'un tel
travail, mesurés à chaque fois.

## Ce qui aurait invalidé cette décision

Que la commande ayant causé le premier incident réussisse, ou écrive avant d'échouer, une fois
`.env` déplacé et la composition arrêtée — auquel cas le protocole ne protégerait pas et
n'aurait pas dû être consigné comme une décision acceptée. Que les décomptes de la base, après
remise de `.env` et redémarrage, diffèrent de ceux d'avant l'arrêt — auquel cas l'opération de
remise elle-même serait en cause.

## Sources

`ingestion/appliquer_ddl.py:29-38` (`charger_environnement`), `ingestion/chargeur.py`
(réutilisation de la même fonction), `~/.dbt/profiles.yml` (hors dépôt), mesures de connexion et
de journal effectuées avant cette décision.
