# ADR 0065 — Ce qui établit un constat et ce qu'un indicateur démontre sont deux choses, et le rapport les sépare

**Statut.** Accepté, et appliqué au chapitre des recommandations.

---

## Contexte

Le tableau de bord affiche quarante indicateurs, calculés sur un jeu de données produit pour ce
projet. Les relations qui gouvernent les valeurs de ce jeu y ont été **injectées délibérément**, et
le registre des relations en compte vingt et une, chacune avec son paramètre et sa conséquence.

**Sept de ces relations nomment explicitement une recommandation du rapport et déclarent circulaire
la mesure qui lui servirait de constat.** Quatre nomment la source externe à employer à la place ;
une n'en nomme aucune, portant `statut: HYP` et un champ de source vide.

Un chapitre de recommandations écrit sans cette précaution dirait : *le taux d'absentéisme vaut tant,
donc il faut rappeler les patients.* Le nombre viendrait d'un paramètre posé, et la recommandation
reposerait sur lui-même. C'est le mode de défaillance que ce projet traque partout ailleurs, et il
serait ici invisible : la valeur affichée est juste, sa provenance seule est en cause.

## Décision

**Chaque recommandation sépare deux choses, et chaque bloc les nomme.**

| Rubrique | Ce qu'elle porte |
|---|---|
| **Ce qui établit le constat** | une source extérieure au jeu de données — un rapport de contrôle, une publication statistique, une observation au poste. **Quand aucune n'existe, le rapport l'écrit.** |
| **Ce que l'indicateur démontre** | que la chaîne sait produire le nombre, à la maille utile, depuis les tables — une capacité, pas un constat |

**Ni l'effort ni l'effet ne sont chiffrés.** Un effort en jours et un gain en points seraient des
nombres qu'aucune commande ne produit. Le bloc porte à la place **ce que l'action suppose** — quel
champ existe déjà, quel processus change — et **la mesure qui permettrait de constater l'effet**, qui
elle se spécifie sans se chiffrer. L'effet lui-même, lorsqu'il est énoncé, l'est comme une attente.

## Justification des points non triviaux

**Pourquoi ne pas simplement omettre les indicateurs circulaires.** Parce qu'ils démontrent quelque
chose de réel, et que ce quelque chose est le livrable du projet : la chaîne calcule le délai
d'obtention par activité, le taux de recouvrement par type de débiteur, la part des passages relevant
d'une consultation ordinaire. Branchée sur les données du service, elle produira des constats. Les
omettre reviendrait à cacher le résultat pour éviter d'expliquer sa portée.

**Pourquoi nommer la source externe dans le texte plutôt qu'en note.** Un lecteur qui vérifie trois
affirmations au hasard doit trouver, à l'endroit de la recommandation, d'où vient le chiffre du
constat. Une note de bas de page laisserait croire à un détail bibliographique là où il s'agit de la
différence entre une observation et un paramètre.

**Pourquoi la recommandation la moins appuyée est écrite comme telle.** Sur la qualité du fichier
patient, aucune source externe n'établit le classement des champs par complétude, et la relation qui
déclare la circularité n'en nomme aucune. Le rapport l'écrit — « c'est la recommandation la moins
appuyée du chapitre, et il vaut mieux l'écrire que le taire ». Une recommandation dont on tait la
fragilité est une recommandation qu'un jury démolit en une question.

**Pourquoi une recommandation se retourne plutôt que de disparaître.** Le système n'expose pas quels
champs sont obligatoires à la saisie, et le relevé déclare n'avoir jamais observé ce caractère.
Recommander d'en rendre certains obligatoires supposait de savoir lesquels ne le sont pas.
**L'ignorance devient le constat** : la recommandation est d'établir d'abord quels champs sont
facultatifs. Ce n'est pas un contournement, c'est l'ordre réel des opérations.

## Conséquences

- Le chapitre des recommandations porte un chapeau qui pose la distinction une fois, et cinq blocs
  de forme fixe qui l'appliquent sans la réexpliquer.
- **Une seule des cinq recommandations ne dépend d'aucune donnée générée** : celle qui porte sur les
  champs absents du système. Le rapport le dit, et c'est la mieux appuyée du chapitre.
- Le chapeau n'a pas de budget de pages dans le plan, et le chapitre excède le sien de 0,22 page en
  conséquence. L'excédent est rapporté ; aucune affirmation vérifiée n'est tronquée pour le
  résorber.
- Une section entière et deux paragraphes passent au régime de la rédaction personnelle : le récit
  qu'un auteur fait de son propre travail n'est ni documentaire, ni observé, ni conventionnel, et il
  a déjà son marqueur.

## Ce que le rapport ne peut pas affirmer

**Qu'une recommandation soit bonne.** Ce chapitre établit qu'un problème existe, que la chaîne sait
le mesurer, et par quelle mesure on constaterait l'effet d'une action. Il n'établit pas que l'action
proposée soit la meilleure, ni qu'elle soit réalisable dans le service, ni que son effet serait
positif. Un effet attendu est une attente, et le rapport l'écrit sous ce mot.

Deux limites plus étroites s'y ajoutent :

- **Aucun effort n'est estimé.** Ce qu'une action suppose est décrit, sa charge ne l'est pas : rien
  dans ce projet ne mesure la charge d'un changement de processus dans un service hospitalier.
- **La mesure de l'effet suppose que la chaîne soit branchée sur les données réelles.** Tant qu'elle
  lit un jeu produit, la comparaison avant/après compare deux exécutions du même paramètre.

## Sources

- `docs/relations_injectees.yml` — les vingt et une relations, dont sept nomment une recommandation.
- `dashboard/indicateurs.yml` — les quarante indicateurs, leur définition et la décision qu'ils
  servent.
- `docs/exigences_statistiques.md` — les trois champs manquants et la distinction entre défaut du
  système et absence d'activité.
- `docs/decisions/0047-ecarts-assumes-au-cadrage.md` — les trois exigences du cadrage et leurs
  écarts.
