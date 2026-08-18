# ADR 0001 — PostgreSQL plutôt que DuckDB pour la couche de persistance

**Statut.** Accepté, et appliqué depuis l'origine du projet.

> **Enregistrement rétrospectif.** Cette décision a été prise et appliquée avant que sa consignation
> ne soit écrite ; le présent enregistrement est rédigé le 18 août 2026, à partir de l'état du dépôt
> et des documents de suivi du projet. Le cadrage prescrit qu'un enregistrement soit écrit au moment
> de la décision et jamais rétrospectivement : il y est ici dérogé sciemment, pour qu'un numéro
> réservé et cité depuis l'origine cesse de renvoyer à un fichier absent.

---

## Contexte

Le projet a besoin d'une couche de persistance pour la zone d'atterrissage, la couche de
transformation et la couche de restitution. Deux moteurs se présentaient : PostgreSQL, client-serveur
et transactionnel, et DuckDB, embarqué et orienté colonnes.

**La volumétrie ne départage pas les deux.** L'état mesuré de la base le confirme : la table la plus
volumineuse de la couche source porte 160 936 lignes, et les six tables de faits en portent ensemble
129 456. À cette échelle, les deux moteurs répondent en un temps qui ne se distingue pas à l'usage.
Le cadrage interdit d'ailleurs expressément d'employer la volumétrie comme argument de performance.

## Décision

**La couche de persistance est PostgreSQL**, en version 16, servie par l'image `postgres:16-alpine`
déclarée par la composition de conteneurs.

**Le motif n'est pas la performance : il est que le dépôt doit démontrer un usage professionnel.**
Un moteur client-serveur apporte quatre propriétés qu'un moteur embarqué ne met pas en jeu, et que
ce projet exerce effectivement :

- le **modèle client-serveur** lui-même — trois services de la composition attaquent la même base
  par le réseau, chacun avec ses propres identifiants ;
- les **transactions concurrentes** — le chargement écrit pendant que le tableau de bord lit ;
- un **catalogue interrogeable**, dont le projet se sert comme d'une source de vérité : la vue de
  provenance des champs est calculée directement sur les commentaires de colonnes du catalogue, et
  deux contrôles confrontent le registre des champs à `information_schema` ;
- des **rôles** et un chemin de recherche, dont la couche de restitution se sert pour se restreindre
  structurellement au seul schéma d'instantané.

## Justification des points non triviaux

### DuckDB n'est pas absent du projet, et la décision n'est donc pas binaire

Le point mérite d'être dit, faute de quoi cet enregistrement laisserait croire à un choix exclusif
qu'un lecteur démentirait en une commande.

**DuckDB est présent et employé.** Il est installé en version 1.5.5, et le moteur de rapprochement
probabiliste s'en sert : trois modules de la couche de rapprochement importent son interface depuis
la bibliothèque de rapprochement et l'instancient pour exécuter les règles de blocage et le modèle.

Sa présence est **transitive et non déclarée** : `pyproject.toml` ne le cite pas, et c'est la
bibliothèque de rapprochement qui l'exige.

Ce que la décision partage est donc net : **la persistance est PostgreSQL, le calcul de
rapprochement est en mémoire sur DuckDB**. Le motif de ce second choix est consigné par
`docs/decisions/0029-moteur-execution-en-memoire.md` et n'est pas repris ici.

### Ce que la décision n'a pas coûté

L'image pèse 411 Mo. C'est le seul coût mesurable attribuable au choix, et il porte sur
l'environnement de développement, non sur la chaîne.

## Conséquences

Les schémas de la base sont posés par des fichiers de définition appliqués en préalable, et la
couche de transformation matérialise en vues — décision distincte, portée par
`docs/decisions/0018-architecture-dbt-vues-et-nommage.md`.

Le catalogue étant interrogeable, plusieurs contrôles du dépôt s'y adossent plutôt que de recopier
une liste : la couverture du registre des champs, la vue de provenance, et le contrôle de
documentation des couches aval.

## Ce qui aurait invalidé cette décision

**Une contrainte d'exécution sans serveur** — un livrable qui devrait tourner sans démon, sur le
poste d'un lecteur. Le projet n'en a aucune : sa chaîne s'exécute derrière une composition de
conteneurs.

**Une volumétrie justifiant un moteur en colonnes.** Elle n'existe pas davantage : le plus gros
objet du dépôt porte 160 936 lignes.

## Sources

`docker/docker-compose.yml` — l'image et la version déclarées.
`docs/decisions/0018-architecture-dbt-vues-et-nommage.md` — la matérialisation en vues.
`docs/decisions/0029-moteur-execution-en-memoire.md` — le moteur en mémoire du rapprochement.
`docs/decisions/0043-instantane-schema-dedie-du-tableau-de-bord.md` — le schéma dédié que lit la
restitution, et la restriction du chemin de recherche.
