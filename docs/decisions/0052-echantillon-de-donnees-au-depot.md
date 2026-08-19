# ADR 0052 — Un échantillon de données est versé au dépôt, chaque ligne portant sa mention

**Statut.** Accepté.

---

## Contexte

**Le projet produit 346 149 lignes que personne ne peut voir.** La couche source en porte 346 149 à
elle seule, réparties sur onze tables ; le schéma en étoile en porte autant sous une autre forme. Un
lecteur du dépôt ne peut en voir **aucune** sans cloner, installer l'environnement, monter la
composition de conteneurs, produire le jeu et charger la base — une chaîne de sept étapes.

**Le livrable tabulaire demandé existe et n'est visible nulle part.** `livraison/exporter.py` écrit
un fichier par table à chaque exécution du graphe quotidien, mais son répertoire de sortie n'est pas
suivi : `.gitignore` porte `exports/*`, et c'est délibéré — un livrable régénéré chaque jour n'a pas
sa place dans un historique de code.

**Ce qui manque est donc un extrait, petit, stable et lisible sans rien installer.**

## La contrainte qui domine

Le projet repose sur une décision de cadrage : **aucune donnée réelle ne sort du service.** Verser
des lignes dans un dépôt public — même synthétiques — exige que rien ne puisse être pris pour du
réel.

**Un fichier d'accompagnement ne suffit pas.** Un lecteur qui télécharge un fichier isolé ne lit pas
le répertoire dont il vient ; un fichier tabulaire circule seul, par pièce jointe ou par copie, et
perd son voisinage dès le premier partage.

## Décision

**Chaque fichier porte la mention dans ses propres octets, sur chacune de ses lignes**, en première
colonne :

```
donnees_synthetiques,n_ipp,nom,…
Donnees synthetiques simulees a partir de statistiques publiques ; aucun patient reel,IPP-000000,Fatima,…
```

**La forme a été tranchée par mesure, contre deux lecteurs standards, sans aucune option :**

| Forme | `pandas.read_csv` | `csv.DictReader` |
|---|---|---|
| commentaire `# …` en tête | **1 colonne**, le commentaire pris pour un titre | **champs illisibles** |
| **colonne d'avertissement** | 4 colonnes, titres corrects | champs corrects |

**Le commentaire en tête casse la lecture du fichier par un outil standard ; la colonne ne la casse
pas.** C'est ce qui décide, et non le goût.

**Ce que la forme retenue coûte** : une colonne de plus, répétée sur chaque ligne — **86 octets par
ligne mesurés**, soit environ 190 Kio sur l'échantillon entier, et une colonne qui n'appartient pas
à la table d'origine, dont le contrôle doit tenir compte. C'est le prix d'une garantie qui ne dépend
d'aucun fichier voisin.

**Un fichier d'accompagnement existe en plus**, et dit plus longuement ce que l'échantillon contient,
d'où il est extrait, et **ce qu'il ne faut pas en conclure** — il illustre la forme des données, il
ne mesure aucune activité.

## Ce qui est versé, et ce qui ne l'est pas

**23 fichiers, 2 632 lignes, 552 Kio mesurés.**

| Couche | Tables | Lignes par table | Motif |
|---|---|---|---|
| source | 11 | 200 | la nomenclature des champs est le livrable ; deux cents lignes font apparaître plusieurs services, plusieurs activités et trente mois distincts |
| analytique | 12 | jusqu'à 50 | colonnes dérivées, et les plus petites dimensions ne portent que sept ou huit valeurs au total |

**Ne sont pas versés** : les agrégats — ce sont des grandeurs que le tableau de bord affiche déjà, et
leur forme n'apprend rien sur celle des données — ni les tables du rapprochement, dont la page
dédiée montre le résultat.

**Les lignes sont prélevées systématiquement**, une sur *N* dans l'ordre d'une clé stable. Prendre
les premières ne montrerait qu'une période et qu'une tranche d'identifiants ; tirer au hasard ne
serait pas reproductible sans graine, et une graine serait un paramètre de plus à justifier.
**Mesuré sur l'extrait produit** : 8 activités sur 8, 5 niveaux de tri sur 5, 5 orientations de
sortie sur 5, 3 types d'épisode sur 3, et 30 mois distincts.

**Deux fiches sont forcées dans l'extrait des patients** : `IPP-002116` et `IPP-025034`, qui
désignent la même personne et ne diffèrent que par une variante graphique du prénom — *Mohammed* et
*Mohamed*. C'est ce qui montre d'un coup que les défauts du jeu sont délibérés et que le
rapprochement d'identités a quelque chose à rapprocher. Sans cette inclusion forcée,
l'échantillonnage systématique n'aurait aucune raison de retenir les deux.

**L'échantillon est engendré par un module versionné, jamais constitué à la main** : un extrait
recopié diverge en silence de ce dont il est extrait.

## Ce qui a été écarté

**Verser le jeu complet.** 346 149 lignes pour la seule couche source, et un historique de code qui
porterait des dizaines de mégaoctets régénérables. Le dépôt cesserait d'être clonable
raisonnablement, pour une information que deux cents lignes donnent aussi bien.

**Verser un extrait sans mention.** C'est la forme la plus simple et la plus dangereuse : un fichier
de lignes ressemblant à des dossiers patients, circulant sans rien qui dise ce qu'il est. Le fichier
d'accompagnement n'aurait protégé que le lecteur qui reste dans le répertoire.

**Ne rien verser.** C'est l'état antérieur, et il a un coût réel : une part importante du travail —
la forme des données, la nomenclature, le réalisme du jeu — reste invisible à qui ne fait pas tourner
la chaîne.

## Ce qui aurait invalidé cette décision

**Que la mention ne puisse pas être portée sans casser la lecture du fichier par un outil standard.**
Il aurait alors fallu choisir entre un fichier illisible et un fichier non protégé, et la règle du
projet impose de ne rien verser plutôt que de verser sans protection.

Ce n'est pas le cas, et c'est mesuré : la forme en colonne se lit correctement par les deux lecteurs
éprouvés, sans aucune option.

## Vérification

`tests/test_echantillon.py` porte cinq propriétés : chaque ligne de l'échantillon existe dans la
table dont elle est extraite et les colonnes sont celles de la table ; chaque fichier **suivi** porte
la mention sur chacune de ses lignes ; réengendrer rend le même contenu ; la paire de fiches en
double est présente et ses différences visibles ; le volume est celui que le module déclare. Le
contrôle part des fichiers **réellement suivis**, comme celui qui interdit les images : une règle
d'exclusion qui les rendrait invisibles à la publication serait un défaut.

## Sources

`livraison/exporter.py` — le format, l'encodage et le séparateur, repris et non redécidés.
`tests/test_aucune_image.py` — le précédent de dispositif restreignant ce qui entre au dépôt.
`docs/decisions/0041-taches-export-instantane-vides.md` — le livrable quotidien, que l'échantillon
n'est pas.
`docs/sources/sources.yml` — les sources publiques dont les paramètres du simulateur sont tirés.
