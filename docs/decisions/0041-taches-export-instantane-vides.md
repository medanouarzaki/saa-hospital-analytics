# ADR 0041 — Les tâches d'export et de rafraîchissement de l'instantané existent en aboutissement vide

**Statut.** Accepté.

---

## Contexte

Le cadrage fixe l'enchaînement complet du graphe, dont deux étapes finales — export et
rafraîchissement de l'instantané destiné au tableau de bord — dont le contenu appartient à un
travail ultérieur, hors de ce que ce document couvre.

## Décision

Ces deux tâches figurent dans le graphe dès à présent et n'accomplissent rien : ce fait est
explicitement vérifié plutôt que laissé tacite.

## Justification des points non triviaux

### Pourquoi les inclure vides plutôt que les omettre

La forme du graphe est elle-même un livrable à part entière — reprise telle quelle dans le
document final — et non un artefact intermédiaire à compléter silencieusement plus tard. La
découvrir incomplète plus tard coûterait une reprise de sa structure (dépendances entre tâches,
noms, position dans l'ordonnancement) plutôt que le seul remplissage d'un corps de tâche déjà en
place.

## Conséquences

Le graphe est complet dès maintenant dans sa forme, même si deux de ses tâches n'ont pas encore
de contenu opérant. Un contrôle interdit qu'une tâche reste vide par inadvertance une fois que
son contenu aura été écrit — sans quoi l'aboutissement vide, délibéré aujourd'hui, deviendrait un
oubli silencieux demain.

## Ce qui aurait invalidé cette décision

Le report de ces deux étapes hors du graphe, à ajouter plus tard comme des tâches entièrement
nouvelles plutôt que de compléter des tâches déjà présentes — un choix qui aurait dispensé de
vérifier leur vacuité actuelle, au prix de resoumettre la forme complète du graphe à un examen
ultérieur.

## Sources

Cadrage du projet (enchaînement complet du graphe, étapes d'export et de rafraîchissement de
l'instantané).

## Amendement — les deux tâches sont remplies

L'aboutissement vide est levé : la tâche de rafraîchissement invoque `instantane.rafraichir`, la
tâche d'export `livraison.exporter`, toutes deux avec le répertoire de travail du dépôt.

**L'ordre a dû être corrigé.** Le graphe plaçait l'export AVANT le rafraîchissement. L'export lit
l'instantané ; le lire avant qu'il ne soit constitué livrerait l'état de la veille. C'est le seul
défaut réel que l'aboutissement vide masquait, et l'inclusion des deux tâches dans leur forme
complète — motif de cette décision — est ce qui a permis de le voir avant qu'il n'opère.

Le second point que la vacuité masquait était l'absence de `cwd` : ces deux tâches étaient les
seules des douze sans répertoire de travail, alors que l'opérateur shell exécute sinon dans un
répertoire temporaire où `uv run` ne trouverait pas le projet.

Le contrôle qui interdisait qu'une tâche reste vide par inadvertance devenait faux par
construction ; il est **remplacé par quatre propriétés, non supprimé** : chaque tâche invoque le
module qui lui revient, chacune porte un répertoire de travail (attendu **dérivé des autres
tâches**, jamais recopié), le rafraîchissement précède l'export, et les deux restent en aval du
contrôle de qualité par remontée transitive des dépendances.
