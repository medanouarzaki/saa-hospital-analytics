# ADR 0074 — Les deux noms de personne sortent du dépôt et sont injectés à la compilation

**Statut.** Accepté.

---

## Contexte

Le dépôt est public. Deux noms de personne doivent figurer sur la page de garde : l'auteur et
l'encadrant de stage. Les commettre, c'est les publier, et une révision publiée ne se retire pas
proprement : elle survit dans l'historique, dans les clones et dans les caches.

L'`0062` avait déjà posé que les marqueurs restent vides tant que le document n'est pas remis. Cela
ne suffit pas : la bascule à la remise les aurait écrits dans un fichier suivi.

## Décision

### 1. Les noms vivent dans `report/noms.tex`, qui n'est jamais commis

Ce fichier redéfinit les deux marqueurs. `report/marqueurs.tex` le charge par `\IfFileExists`, et
compose sans noms s'il est absent. `.gitignore` porte `report/noms.tex`, et `git check-ignore -v` le
confirme sur le fichier réel plutôt que sur une lecture du motif.

**DEUX CHEMINS SONT ESSAYÉS, ET C'EST MESURÉ.** Le rapport se compose depuis `report/`, où le
fichier est `noms.tex` ; la présentation se compose depuis `slides/` et charge le même fichier de
marqueurs par `\input{../report/marqueurs}`, où le même fichier est `../report/noms.tex`. Les deux
compilations ont été faites avec le fichier en place : les deux documents portent les noms.

### 2. L'intégration continue l'écrit depuis deux variables de dépôt

Le travail `document` dépose `report/noms.tex` depuis `vars.RAPPORT_AUTEUR` et
`vars.RAPPORT_ENCADRANT`, avant les deux compilations. **Si l'une des deux manque, l'étape n'écrit
rien et n'échoue pas** : tant que l'état vaut `brouillon`, un document composé sans noms est le
résultat attendu, et la page de garde fait disparaître les deux lignes plutôt que de les laisser
vides (`0073`).

**Les valeurs ne sont jamais journalisées.** Elles passent par `env:` et non par une interpolation
`${{ }}` dans le corps du script : le texte de la commande ne les porte donc pas. `printf` écrit
dans le fichier, jamais sur la sortie standard, et aucune autre étape du travail ne lit ces
variables.

### 3. Un contrôle tient l'autre bout, et il ne porte pas les noms qu'il interdit

`tests/test_aucun_nom_de_personne.py` cherche les deux noms dans l'ensemble des fichiers suivis. Il
les lit dans deux variables d'environnement : les écrire dans le contrôle reviendrait à commettre
exactement ce que le contrôle existe pour empêcher.

**SANS LES VARIABLES, IL S'ABSTIENT, ET L'ABSTENTION EST DÉCLARÉE.** Un `pytest.skip` dont le message
dit ce qui manque, et non un vert silencieux : un contrôle vert sans avoir rien regardé est une
assurance fausse, un contrôle sauté apparaît dans la sortie et se compte. C'est l'état ordinaire tant
que les variables ne sont pas posées.

**Sept voies par lesquelles un nom passerait ont été cherchées avant d'écrire une ligne.** Quatre
sont fermées — casse, accents composés autrement, espaces multiples ou saut de ligne entre les mots,
fichier d'encodage inattendu. Trois restent ouvertes et sont écrites dans le contrôle : un nom coupé
par une césure à l'intérieur d'un mot, un nom présent dans l'historique mais plus dans l'arbre, et un
fragment de trois caractères ou moins, que le contrôle ne cherche pas seul pour ne pas rougir sur des
mots ordinaires.

## Ce qui a été écarté

**Un secret de dépôt plutôt qu'une variable.** Écarté : un nom de personne sur une page de garde
n'est pas un secret, et le masquage automatique des secrets dans les journaux aurait donné une
assurance que le mécanisme ne doit pas à ce masquage — les valeurs ne sont pas journalisées parce
que le script ne les porte pas.

**Écrire les noms dans le dépôt et réécrire l'historique le jour de la remise.** Écarté : une
réécriture d'historique sur un dépôt déjà cloné ne retire rien.

## Ce que cette décision ne peut pas voir

**Le contrôle lit l'arbre suivi, jamais l'historique.** Un nom déjà commis dans une révision
antérieure lui est invisible, et aucune vérification faite ici ne l'a cherché. **Il ne voit pas non
plus l'intérieur d'une image** : un nom lisible sur une capture déposée sous
`report/figures/tableau-de-bord/` passerait les deux dispositifs — celui-ci et `0075`.
