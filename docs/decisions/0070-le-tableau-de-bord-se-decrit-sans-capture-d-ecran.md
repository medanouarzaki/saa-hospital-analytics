# ADR 0070 — Le tableau de bord se décrit sans capture d'écran, et les séries acceptent deux types de commande

**Statut.** Accepté.

---

## Contexte

Le chapitre du rapport consacré au tableau de bord devait l'illustrer. Le plan du document
autorisait des captures d'écran, et c'était la voie la plus rapide. Deux questions se sont posées
au moment de l'écrire, et les deux ont été tranchées par mesure.

**1. Une capture d'écran est-elle acceptable dans ce dépôt ?** Deux dispositifs y interdisent toute
image du système d'information, et sont verts depuis l'origine du projet.

**2. Le registre des chiffres pouvait-il porter les données de ce chapitre ?** Ses séries
n'acceptaient qu'une commande SQL, et deux des tableaux à écrire ne viennent pas de la base : l'un
se lit dans le registre des indicateurs et les fichiers de page, l'autre dans le document qui porte
la correspondance avec la nomenclature nationale.

## Décision

### 1. Aucune capture d'écran, y compris du tableau de bord produit par ce projet

Le chapitre s'illustre par des maquettes redessinées et des graphiques composés, comme le chapitre
consacré au système d'information observé et celui consacré à l'architecture de la chaîne.

**Trois motifs, et les trois sont mesurés.**

**Le premier est de discipline.** L'interdiction d'image porte sur les fichiers suivis, sans
exception de nature. L'amender pour du confort d'illustration serait le premier relâchement d'un
ensemble qui n'en compte aucun, et l'exception une fois posée se rediscuterait à chaque chapitre.
Le dépôt a déjà refusé d'affaiblir un contrôle pour faire passer un déplacement de page ; il refuse
ici d'affaiblir une règle pour faire passer une figure.

**Le deuxième est de lisibilité, et il se vérifie.** Neuf pages sont à décrire dans l'espace dont ce
chapitre dispose. Les captures prises pour la vérification au navigateur mesurent 1 500 pixels de
large sur 2 257 pour la plus courte ; réduites à la largeur d'une colonne de texte, leurs libellés
d'axe et leurs mentions de filtrabilité cessent d'être lisibles à l'impression. Une capture qu'on
ne peut pas lire n'illustre rien.

**Le troisième est de traçabilité.** Une reconstitution composée se relit dans une comparaison de
versions ; une image ne s'y relit pas. Le projet s'en est déjà servi deux fois pour cette raison.
Et une maquette composée peut être tenue à **aucune donnée affichée** — ni valeur, ni nom, ni date
— là où une capture porte nécessairement l'état de la base au moment où elle a été prise.

**Ce que cette décision coûte, et il faut le dire :** le lecteur ne voit pas les couleurs, la
typographie ni la densité réelle de l'écran. La maquette montre un agencement, pas une apparence.

### 2. La vérification au navigateur remplace la capture, et elle est plus exigeante

Ce que la capture aurait montré au lecteur, la vérification l'établit pour l'auteur. Les neuf pages
ont été rendues dans un navigateur sans interface, piloté par le protocole de mise au point, et
**les quarante libellés d'indicateur du registre ont été retrouvés dans le texte que le navigateur
rend** — quarante sur quarante, page par page. Aucun contrôle côté serveur ne voit un écran ; celui-ci
en voit un.

L'attente avant capture est **réelle et conditionnée**, non un délai fixe : la boucle attend que le
squelette de chargement ait disparu. Trois captures vides avaient été prises avant que ce point ne
soit compris, et une quatrième parce que la première cible du protocole de mise au point n'est pas
l'onglet mais la page d'arrière-plan d'une extension.

### 3. Une série accepte les deux types de commande, et déclare son séparateur

Le registre des chiffres portait des séries `sql` seulement, quand ses scalaires acceptaient déjà
`sql` et `python`. L'asymétrie n'avait pas de motif ; elle est levée.

**Ce que le mode de vérification des formes peut prouver diffère selon le type, et c'est écrit dans
le code plutôt que supposé.** Une commande SQL nomme ses colonnes, et le registre confronte ces noms
à ce qu'il déclare. Une commande Python rend une liste de lignes et ne nomme rien : c'est alors la
**largeur** de chaque ligne qui est confrontée au nombre de colonnes déclarées. Une mutation le
vérifie — une colonne retirée de la commande fait rougir le contrôle en nommant la largeur obtenue.

**Le séparateur de colonnes est déclaré au registre**, virgule par défaut, tabulation pour les
séries dont les cellules sont du texte. Le motif est mesuré : une cellule du tableau de
correspondance porte à la fois une virgule et un point-virgule, et aucun des deux séparateurs
usuels ne la traverse. Le nom du séparateur est lu par le rendu et par le contrôle de fichier ;
aucun des deux ne l'écrit en clair.

## Ce qui a été écarté

**Amender le contrôle d'absence d'image pour tolérer un préfixe de captures.** Écarté : c'est
exactement la forme d'exception que le contrôle existe pour empêcher, et elle se serait étendue.

**Décrire les pages sans figure aucune.** Écarté : l'agencement en deux zones et la composition d'un
bloc d'indicateur ne se décrivent pas en prose sans que le lecteur ait à les imaginer.

**Recopier à la main le tableau de correspondance avec la nomenclature.** Écarté : seize lignes de
quatre colonnes recopiées sont seize occasions de diverger du document qui fait foi. La série les
lit dans ce document, et l'empreinte du fichier produit répond des deux côtés.

## Ce qui aurait invalidé cette décision

**Une vérification au navigateur qui aurait contredit le chapitre.** Le chapitre décrit neuf pages,
sept en pilotage et deux en méthode, et quarante indicateurs. Si l'écran en avait montré une
composition différente, c'est le chapitre qui aurait été faux, et aucune maquette ne l'aurait
rattrapé. La vérification a été faite avant la publication, et elle concorde.

## Ce que la vérification a trouvé et que ce travail ne corrige pas

La page des données porte, en trois endroits, la mention « les sept autres pages ». Le tableau de
bord en compte neuf : les autres sont donc huit. La mention date de la composition à huit pages et
n'a pas suivi l'ajout de la neuvième. **Le défaut est consigné ici et non corrigé** : ce travail
décrit le tableau de bord et n'a pas licence de le modifier. Le chapitre ne reprend pas la formule.

## Sources

`dashboard/app.py` ; `dashboard/indicateurs.yml` ; `dashboard/pages/donnees.py` ;
`docs/chiffres/mesurer.py` ; `docs/chiffres/registre_chiffres.yml` ;
`tests/test_registre_des_chiffres.py` ; `report/chapitres/tableau-de-bord.tex` ;
`docs/decisions/0010-aucune-image-du-systeme.md` ;
`docs/decisions/0043-instantane-schema-dedie-du-tableau-de-bord.md` ;
`docs/decisions/0053-separation-des-deux-publics.md` ;
`docs/decisions/0056-convention-unique-des-indicateurs-de-sejour-affiches.md` ;
`docs/decisions/0069-le-registre-des-chiffres-s-etend-aux-series-et-la-dette-de-correspondance-se-solde.md`.
