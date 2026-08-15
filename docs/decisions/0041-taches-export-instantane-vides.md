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
