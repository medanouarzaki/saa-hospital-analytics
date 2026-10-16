# ADR 0108 — La planification du projet, tirée de l'historique du dépôt

**Statut.** Accepté.

---

## Contexte

Le référentiel de la filière demande la planification du projet sous forme de diagramme de Gantt.
Le chapitre de cadrage nomme sept phases dans un tableau, avec ce que chacune produit, et une figure
de leurs dépendances ; il ne porte aucun calendrier. Une planification écrite à la main aurait
affirmé des dates qu'aucune trace ne soutient.

## Décision

### Les données

`docs/planification/planification.yml` porte la période du stage, la date de l'observation au
poste, et les sept phases du tableau, dans son ordre et sous leur nom exact. Chaque phase porte les
répertoires du dépôt où se trouve ce qu'elle produit, d'après la colonne « Ce qu'elle produit » du
tableau :

| phase | ce qu'elle produit | répertoires |
|---|---|---|
| Comprendre le service et relever les écrans | le relevé des écrans, élément par élément | `docs/observation`, `docs/champs` |
| Établir les sources et les chiffres de référence | le registre des sources et les volumes de référence | `docs/sources` |
| Concevoir et générer le jeu de données | le jeu de données et le registre des relations injectées | `generator` |
| Construire la chaîne de traitement | les couches d'ingestion, de quarantaine et de modélisation | `ingestion`, `dbt`, `airflow` |
| Rapprocher les identités et mesurer la qualité | le modèle de rapprochement et son évaluation | `linkage` |
| Restituer | le tableau de bord et le livrable quotidien | `dashboard`, `livraison`, `instantane` |
| Rédiger | le présent rapport | `report` |

Ce fichier est une convention de l'auteur ; le chapitre l'étiquette `decision-planification`.

### La construction

La série `planification` du registre des chiffres porte une ligne par phase : sa semaine ISO de
début et de fin, et son origine. Sa commande ne lit que le fichier de configuration et l'historique
du dépôt :

- les semaines d'une phase sont celles du premier et du dernier commit, par date d'auteur, qui
  touchent ses répertoires, dans la période du stage ;
- le commit qui crée la structure du dépôt est exclu : il pose un fichier vide par répertoire et ne
  témoigne d'aucun travail ; sans cette exclusion, six phases commenceraient la même semaine ;
- la première phase est ancrée au début du stage, au motif de la phrase du chapitre « Le travail a
  commencé par le service, et non par la technique » : l'observation au poste précède le premier
  commit, et son produit, le relevé, n'a été commis qu'ensuite ; sa semaine de début est la plus
  précoce de son premier commit et de cet ancrage ;
- la rédaction court jusqu'à la semaine de la fin du stage ;
- une dernière ligne porte le jalon de l'observation, à sa date ; il tombe dans la barre de la
  première phase.

La huitième phase que le chapitre mentionne, une relecture critique qui n'était pas prévue, n'a pas
de barre : la figure porte les sept phases du tableau.

Dans un clone superficiel, comme celui du travail d'intégration continue qui vérifie la forme des
commandes, l'historique manque : les semaines non ancrées valent alors `None`, et seule la
vérification sur le dépôt complet juge les valeurs.

### Ce que la planification n'affirme pas

Une barre dit qu'une phase a laissé des commits entre deux semaines. Elle ne dit pas que le travail
a été continu entre elles, ni qu'il s'arrêtait en dehors ; aucune présence jour par jour n'est
représentée.

### La figure, le contrôle, les fichiers produits

`docs/planification/to_tex.py` rend la série en diagramme de Gantt dessiné en TikZ,
`report/figures/planification.tex` : les semaines en colonnes, libellées depuis la série, les
phases en lignes, le jalon en losange. La figure s'inclut au chapitre de cadrage, après le passage
qui présente les phases, sans le modifier.

`tests/test_planification.py` vérifie que la figure est, octet à octet, le rendu du générateur ;
que les phases de la configuration et de la série sont celles du tableau du chapitre, dans l'ordre ;
que tout tient dans la période du stage et que le jalon tombe dans la barre de sa phase. La figure
s'ajoute aux fichiers produits que le contrôle des nombres tapés n'examine pas.

## Conséquences

La planification vieillit avec l'historique : un commit nouveau dans la période, ou une
correspondance changée, change la série, et le registre rougit tant qu'elle n'est pas réécrite.
