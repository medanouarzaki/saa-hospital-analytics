# ADR 0039 — Les chemins de sortie du rapprochement deviennent paramétrables, valeur par défaut inchangée

**Statut.** Accepté.

---

## Contexte

Deux modules du rapprochement écrivent des fichiers tabulaires suivis par git à un chemin en dur
du dépôt : `linkage/ablation.py:73` (`CHEMIN_CSV = RACINE / "linkage" / "ablation.csv"`) et
`linkage/evaluation.py:382` (`chemin_csv = RACINE / "linkage" / "courbe_precision_rappel.csv"`).
Aucune variable d'environnement ne surcharge l'un ou l'autre. Mesuré sur instrument éphémère :
`linkage/ablation.py` modifie réellement son fichier à chaque exécution, y compris à population
identique, par un bruit de calcul flottant marginal sur sa variante qui réestime le modèle.

## Décision

Ces deux chemins se lisent désormais dans une variable d'environnement dont la valeur par défaut
reste le chemin actuel — sur le patron déjà employé par `VERITE_TERRAIN_PATIENTS`
(`linkage/evaluation.py:34`, `os.environ.get("VERITE_TERRAIN_PATIENTS", <défaut>)`).

## Justification des points non triviaux

### Pourquoi ne pas laisser les chemins en dur

Une exécution planifiée qui invoque ces deux modules laisserait, à chaque passage, une
modification non commise de deux fichiers suivis — mesuré : `git status --porcelain` montre ces
deux fichiers modifiés immédiatement après exécution locale. Depuis un dépôt monté en lecture
seule (le cas mesuré du conteneur de l'orchestrateur, `airflow/` monté `:ro`), ces deux modules
échoueraient purement à l'écriture ; depuis une copie en écriture, ils laisseraient un état de
dépôt divergent de ce qui est commis à chaque passage, sans qu'aucun mécanisme actuel ne le
commette, l'ignore ou le neutralise.

## Conséquences

Aucun comportement existant ne change : la valeur par défaut de la nouvelle variable reste le
chemin actuel, donc les tests et l'intégration continue, qui n'exportent rien de nouveau,
trouvent les fichiers exactement au même endroit qu'aujourd'hui. C'est la seule modification
apportée au module de rapprochement à ce stade — son cadrage la prévoyait explicitement, à
l'exclusion de toute autre.

## Ce qui aurait invalidé cette décision

Le retrait de ces deux fichiers du suivi de version (les traiter comme des artefacts générés,
gitignorés) aurait rendu cette paramétrisation inutile : plus rien à protéger d'une écriture
répétée sur un fichier suivi.

## Sources

`linkage/ablation.py:73` ; `linkage/evaluation.py:382` ; `linkage/evaluation.py:34`
(`VERITE_TERRAIN_PATIENTS`, patron repris) ; `git status --porcelain` mesuré immédiatement après
exécution locale de chaque module, sur instrument éphémère ; montage `airflow/` en lecture seule,
`docker/docker-compose.yml`.
