# ADR 0010 — Aucune image du système d'information hospitalier

**Statut.** Accepté.

---

## Contexte

Les écrans d'un système de dossier patient en production affichent des identifiants de
session, des libellés de compte utilisateur et la structure des dossiers d'un
établissement de soins. Le projet porte sur un établissement réel et son dépôt est
public.

## Décision

Aucune photographie ni capture d'écran du système observé n'entre dans le projet, ni
dans le dépôt, ni dans le rapport, ni dans les diapositives. Les captures de
l'application produite par le projet restent autorisées : elle ne contient aucune
donnée réelle ni élément de session hospitalière.

## Justification des points non triviaux

### Ce qui remplace les images

Le relevé de champs par écran — quatre écrans, cent quarante-trois lignes, chacune
portant le nom exact du champ affiché, son bloc, son type apparent et les valeurs
observées le cas échéant. C'est le livrable qu'un analyste fonctionnel produit à
l'issue d'une observation de poste : référençable depuis le modèle de données, lisible
sans zoom, et plus exploitable qu'une photographie. S'y ajouteront des schémas d'écran
redessinés, restituant l'agencement des blocs sans aucun contenu.

### Deux dispositifs pour la même règle

Un motif d'exclusion dans le fichier de configuration de Git, et un test bloquant qui
échoue si un fichier suivi porte une extension d'image sous le répertoire du rapport ou
à la racine. Le premier seul ne protège pas d'une indexation forcée.

## Conséquences

L'annexe de captures d'écran disparaît. Les relevés qui la remplacent sont placés au
chapitre du système d'information, où ils servent l'argumentation au lieu d'être
relégués. Le motif de l'absence d'images est écrit une seule fois, au chapitre de
cadrage méthodologique, et ne se répète nulle part.

## Ce qui aurait invalidé cette décision

Un accord écrit de l'établissement autorisant la reproduction d'écrans anonymisés, ou
un environnement de démonstration sans données réelles, dont aucun n'était disponible.

## Sources

Aucune source externe : décision de méthode et de protection des personnes, prise lors
de l'observation de poste, non un fait mesuré dans une source tierce.
