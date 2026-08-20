# ADR 0069 — Le registre des chiffres s'étend aux séries, et la dette de correspondance se solde

**Statut.** Accepté.

---

## Contexte

Trois problèmes se sont présentés ensemble au moment d'écrire le chapitre d'analyse, et ils n'ont
qu'une seule bonne réponse chacun.

**1. Le registre des chiffres ne portait que des scalaires.** Sa règle est qu'aucun nombre du
rapport n'est tapé : chaque valeur vit au registre, avec la commande exacte qui la produit, et le
texte l'appelle par son identifiant. Le chapitre d'analyse trace des courbes, des histogrammes et
des tableaux à plusieurs lignes, c'est-à-dire des SÉRIES — et une série ne tient pas dans une
entrée de registre. La décision 0068 avait déjà dû ouvrir une exception nommée : les dix
coordonnées de la courbe de précision et de rappel sont écrites dans la source du chapitre et ne
sont couvertes par aucun registre. Une seconde exception aurait fait une règle.

**2. Les tableaux du chapitre auraient coûté quatre-vingts entrées recopiées.** Quatre tableaux à
plusieurs lignes — délais par activité, urgences par niveau de tri, facturation par type d'épisode,
qualité par table — représentent environ quatre-vingts cellules. Les verser une à une au registre
aurait été conforme à la lettre de la règle et contraire à son esprit : quatre-vingts occasions de
recopier de travers.

**3. La correspondance entre les relations injectées et les conclusions du rapport était une dette
ouverte.** L'en-tête du registre des relations injectées porte une règle bloquante : toute
conclusion du rapport qui repose sur une relation figurant au registre doit être présentée comme un
paramètre affiché et non comme une découverte. Rien ne vérifiait que le rapport le fasse, ni
surtout qu'il le fasse POUR CHACUNE.

## Décision

### 1. Une série est une commande dont le résultat est un fichier de données

Le registre des chiffres reçoit une seconde liste, `series:`, dans le MÊME fichier. Une entrée de
série porte les champs d'un scalaire — identifiant, type, commande, portée, note — et quatre de
plus : le chemin du fichier de données relatif au répertoire de composition, les en-têtes de
colonnes dans l'ordre, le nombre de lignes, et l'empreinte SHA-256 du fichier que la commande
produit.

Le rapport écrit `\serie{identifiant}` comme il écrit `\chiffre{identifiant}`. Les deux commandes
sont rendues dans le même fichier produit par le même script, et un identifiant inconnu arrête la
composition en le nommant, par le même mécanisme. **Aucune convention de plus n'est créée** : un
seul registre, un seul fichier produit, deux commandes qui se lisent pareil.

Un fichier de données sert deux usages : un tracé le lit par `\addplot table`, un tableau par
`\pgfplotstabletypeset`. Les quatre-vingts cellules du point 2 viennent donc d'une commande.

### 2. Deux liens, et jamais le même code pour les vérifier

```
commande  ==(mesurer.py --verifier)==>  empreinte du registre  ==(le contrôle du registre)==>  fichier lu
```

`docs/chiffres/mesurer.py --verifier` exécute la commande, reconstruit le texte du fichier et
confronte son empreinte à celle du registre ; il exige la base complète.
`tests/test_registre_des_chiffres.py` lit le fichier sur le disque, en calcule l'empreinte, et la
confronte au registre ; il n'ouvre aucune base.

**C'est cette séparation qui donne son sens à l'appareil, et elle a été éprouvée par mutation.**
Retoucher à la main une valeur d'un fichier de données fait rougir le second lien. Aligner ensuite
l'empreinte du registre sur le fichier retouché rend le second lien vert — et fait rougir le
premier. Il n'existe aucun état où une donnée falsifiée passe les deux.

Un troisième mode, `--ecrire-series`, est le SEUL chemin par lequel ces fichiers s'écrivent. Il ne
s'exécute jamais dans l'intégration continue : le garde d'arbre propre y rougirait.

### 3. Le mode qui vérifie l'exécution ailleurs couvre les séries

`--formes` exécute chaque commande de série et vérifie qu'elle rend **exactement les colonnes
déclarées** et au moins une ligne. Il ne compare ni valeur ni empreinte : la fenêtre de trois mois
de l'exécuteur ne peut pas les rendre. Ce que ce mode prouve — qu'aucune commande n'a été cassée
par une évolution du schéma — est ce qu'il a déjà attrapé deux fois.

La garde qui refuse une commande d'écriture a dû être renforcée. Les séries ont des expressions de
table communes, et refuser tout ce qui n'ouvre pas sur `select` les aurait toutes écartées. La
garde accepte donc `with`, ET refuse toute commande portant un mot-clé de modification : sans cette
seconde condition, `with x as (delete ... returning)` ouvrirait sur `with` et écrirait.

### 4. La correspondance s'écrit dans le chapitre, et se lit dans les deux sens

Le chapitre d'analyse porte deux tableaux composés et un contrôle les lit.

- **Premier sens.** Toute relation du registre des relations injectées est reprise par une
  conclusion du chapitre, avec l'amplitude injectée en regard de l'amplitude mesurée, ou déclarée
  non reprise avec son motif.
- **Second sens.** Toute conclusion du chapitre renvoie à une relation injectée, ou est déclarée
  comme n'en venant pas — auquel cas elle est un effet des autres choix du générateur et n'établit
  rien, ce que le texte dit.

Une seule des deux directions laisserait passer la moitié des défauts : la première seule tolère
une conclusion tombée du ciel, la seconde seule tolère une relation jamais confrontée. **Le
principe bidirectionnel vaut pour toute référence croisée de ce dépôt**, et c'est la quatrième fois
que ce projet doit l'ajouter après coup.

La liste des relations est LUE au registre à chaque exécution, jamais recopiée : une relation
ajoutée fait rougir le contrôle tant qu'aucune ligne ne la prend en charge.

### 5. Ce qui établit et ce qui démontre, appliqué à l'analyse

La distinction posée par la décision 0065 prend ici sa forme la plus dure, parce que tous les
nombres du chapitre viennent d'un jeu généré.

- Un résultat qui reproduit une relation injectée **démontre que la chaîne sait la retrouver** ; il
  n'établit rien sur le service.
- Un résultat qui ne correspond à aucune relation injectée est un effet des autres choix du
  générateur et **n'établit rien du tout**.
- Là où une source externe existe, **c'est elle qui établit**, et l'indicateur démontre.

Le chapitre porte vingt-deux conclusions. Seize reproduisent une relation injectée ; six n'en
reproduisent aucune. **Une seule est établie par la chaîne elle-même** — la distinction entre une
annulation et une absence, parce qu'elle porte sur une propriété du modèle de données et non sur
une grandeur injectée, ce que le registre des relations déclare explicitement.

## Ce qui a été écarté

**Verser les quatre-vingts cellules au registre, une par une.** Écarté : conforme à la lettre,
contraire à l'esprit, et quatre-vingts occasions de recopier de travers.

**Un cinquième appareil de traçabilité, avec son fichier et sa convention propres.** Écarté : le
projet en porte déjà quatre, et un cinquième aurait été un cinquième endroit où chercher.

**Ne vérifier l'empreinte qu'au niveau du fichier.** Écarté, et c'est le point : l'empreinte aurait
alors pu être calculée SUR LE FICHIER plutôt que sur la sortie de la commande, et une retouche à la
main serait passée. C'est la voie par laquelle la propriété aurait été vraie même si le code était
faux, et le second lien est ce qui la ferme.

**Une correspondance dans un seul sens.** Écarté pour la raison donnée au point 4.

## Conséquences

L'exception ouverte par la décision 0068 — les dix coordonnées de la courbe de précision et de
rappel écrites dans la source — **reste ouverte** : elle n'est pas reprise par ce travail, dont la
liste de fichiers autorisés ne couvre pas le chapitre concerné. Elle est désormais solvable, et
c'est ce qui change.

Le paquet de mise en tableau est celui du paquet de tracé déjà en place : `pgfplotstable.sty`
appartient au paquet `pgfplots`, mesuré et non supposé. Aucune distribution qui porte l'un ne peut
manquer l'autre.

Le rendu des nombres a dû être corrigé sur trois points, chacun trouvé sur le PDF composé : la
partie entière d'un décimal ne recevait pas le groupement des milliers, un nombre négatif recevait
un trait d'union au lieu du signe moins, et la comparaison du contrôle dépouillait les zéros de fin
des deux côtés, ce qui rendait « 3 » sur le décimal 30,0.

## Ce qui aurait invalidé cette décision

**Une mutation qui n'aurait fait rougir aucun des deux liens.** Si retoucher un fichier de données
à la main était passé, ou si aligner l'empreinte sur la retouche avait rendu tout vert, l'appareil
n'aurait rien prouvé de plus qu'un commentaire. Les deux mutations ont été jouées avant d'écrire
ces lignes, et elles mordent chacune sur son lien et sur lui seul.

## Sources

`docs/chiffres/registre_chiffres.yml` ; `docs/chiffres/mesurer.py` ;
`docs/chiffres/generer_chiffres_tex.py` ; `tests/test_registre_des_chiffres.py` ;
`tests/test_correspondance_relations_conclusions.py` ; `docs/relations_injectees.yml` ;
`report/chapitres/analyse-de-l-activite.tex` ; les décisions 0065, 0066, 0067 et 0068.
