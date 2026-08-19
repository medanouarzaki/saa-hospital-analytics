# ADR 0060 — Le service d'affichage est lancé par `python -m streamlit`, jamais par l'exécutable

**Statut.** Accepté, et appliqué depuis l'écriture du fichier de construction du service.

> **Enregistrement rétrospectif.** La décision a été prise et appliquée avant que sa consignation ne
> le soit ; elle est reprise ici du commentaire qui l'accompagne dans le fichier de construction,
> et non de mémoire.

---

## Contexte

Le tableau de bord est un ensemble de pages qui importent toutes le même préambule —
`from dashboard import lecture, rendu` — et le projet déclare `package = false` : il n'est installé
nulle part. Ce qui rend `dashboard` importable est donc, et seulement, la présence de la racine du
dépôt en tête du chemin d'import du processus.

Deux formes de lancement s'offraient, et elles ne placent pas le même chemin en tête.

## Décision

**Le service est lancé par `python -m streamlit run dashboard/app.py`, et jamais par l'exécutable
`streamlit`.**

La forme `-m` place le **répertoire de travail** — la racine du dépôt dans l'image — en tête du
chemin d'import ; l'exécutable ne le fait pas. La bibliothèque d'affichage, elle, n'ajoute que le
répertoire du script principal, soit `dashboard/`. Sans le répertoire de travail, `from dashboard
import …` en tête de chaque page reste introuvable et **aucune page ne rend**.

C'est le mécanisme déjà employé par toutes les tâches du graphe quotidien : répertoire de travail
fixé à la racine du dépôt, invocation par `uv run python -m <module>`. La décision aligne le service
sur cette forme plutôt que d'en introduire une seconde.

## Justification des points non triviaux

### Pourquoi cette décision est vérifiable, et par quoi

Un choix de ligne de commande consigné sans contrôle se perd au premier remaniement du fichier de
construction. Celui-ci est éprouvé par `tests/test_tableau_de_bord_contexte_conteneur.py`, qui rend
chaque page dans un processus fils **dont le chemin d'import est reconstruit à l'identique de celui
du service**, et cette reconstruction est dérivée des fichiers de construction et de composition,
jamais écrite en dur dans le contrôle. Le contrôle rougit donc si ces fichiers cessent de rendre la
racine du dépôt visible au service — quelle que soit la façon dont ils cessent de le faire.

## Conséquences

- Le service et le graphe quotidien partagent une seule forme d'invocation.
- Un remaniement du fichier de construction qui reviendrait à l'exécutable ferait rougir un
  contrôle, et non apparaître une page blanche en production.
- Le projet reste non installé : aucune décision d'empaquetage n'est prise ici, et la racine du
  dépôt en tête du chemin d'import demeure la seule chose qui le rende importable.

## Ce qui aurait invalidé cette décision

L'empaquetage du projet — `package = true` et une installation dans l'environnement — rendrait
`dashboard` importable sans dépendre du répertoire de travail, et les deux formes de lancement
deviendraient équivalentes.

## Sources

`docker/dashboard.Dockerfile` (instruction de lancement et son commentaire) ; `pyproject.toml`
(`package = false`) ; `airflow/saa_daily.py` (même forme d'invocation pour les tâches du graphe) ;
`tests/test_tableau_de_bord_contexte_conteneur.py`.
