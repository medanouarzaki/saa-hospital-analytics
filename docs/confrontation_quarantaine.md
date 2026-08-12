# Confrontation de la quarantaine à la vérité terrain

Le générateur du jeu de données synthétique produit, à côté des fichiers de partition,
une vérité terrain : la liste exacte des défauts qu'il a injectés, catégorie par
catégorie, avec l'identifiant de chaque enregistrement touché. La chaîne d'ingestion
n'a jamais accès à cette vérité terrain en fonctionnement normal — elle ne connaît que
les contrôles déclarés dans `ingestion/controles.yml` et le code qui les applique dans
`ingestion/controles.py`. Ce document confronte les deux, une fois, pour vérifier que ce
que la quarantaine rattrape et ce qu'elle laisse passer correspond exactement à ce que la
conception des contrôles prévoit — ni plus, ni moins.

La confrontation est produite par `ingestion/confrontation.py`, qui lit la vérité terrain
comme un fichier de données parmi d'autres, jamais via le code qui l'a produite. Les
chiffres ci-dessous sont mesurés sur le scénario retenu (`scenario_30`, graine 42) ; ils
changeraient avec la graine ou le scénario, mais le mécanisme qu'ils illustrent — quelles
catégories sont, par construction, rattrapables — ne dépend d'aucun des deux.

## Les huit catégories, une à une

### `dates_aberrantes` — rattrapée intégralement

Les 42 dates aberrantes injectées portent toutes sur `source.rendez_vous.date_rendez_vous`,
avec la valeur sentinelle `01/01/1900 09:00:00 AM`. Cette valeur est syntaxiquement bien
formée — elle passe le contrôle de typage — mais tombe sous la borne basse déclarée pour
les colonnes événementielles (`2000-01-01`, `ingestion/controles.yml`). Le contrôle de
plage la rejette donc systématiquement, sans exception possible : c'est la seule
catégorie où la couverture est totale par construction, parce que la totalité des
défauts qu'elle porte tombe dans le domaine d'un seul contrôle déterministe.

Mesuré : 42 identifiants dans la vérité terrain, 42 en quarantaine, égalité d'ensembles
parfaite dans les deux sens (aucun manquant, aucun excédentaire).

### `ages_incoherents` et la part `faute_frappe_date_naissance` de `doublons` — rattrapées partiellement, le reste vérifié conforme

Ces deux catégories touchent la même colonne, `source.patients.date_naissance`, mais
n'y injectent pas systématiquement une valeur hors bornes : une incohérence d'âge ou une
faute de frappe sur la date de naissance ne produit une date implausible (antérieure à
1890, ou postérieure à la date d'extraction de la fiche) que dans une partie des cas —
le reste est une date qui reste dans les bornes déclarées, simplement incohérente avec
une autre donnée (l'âge apparent, ou la fiche jumelle du doublon) que la chaîne
d'ingestion ne rapproche pas au chargement.

Mesuré : 463 entrées concernées (identifiants distincts, `ages_incoherents` et paires
`doublons` à variation `faute_frappe_date_naissance`, fiche seconde `n_ipp_2`), dont 65
rattrapées par le contrôle de plage ou la règle intra-ligne `naissance_future`, et 398
non rattrapées. Les 398 ont été vérifiées une à une depuis la base : chacune porte une
`date_naissance` qui reste dans les bornes déclarées (postérieure ou égale à 1890,
non postérieure à sa `date_extraction`) — 0 exception. Ce n'est pas un manque du
contrôle : ces 398 dates sont, individuellement, des dates plausibles ; seule leur
confrontation à une autre donnée (l'âge apparent du patient, ou l'autre fiche de la
paire) révélerait l'incohérence, et cette confrontation n'entre pas dans le périmètre
d'un contrôle d'entrée ligne à ligne.

Aucune paire à faute de frappe n'a sa fiche première (`n_ipp_1`) elle-même en
quarantaine — la faute de frappe, par construction du générateur, n'affecte que la
fiche seconde.

### `champs_manquants` — laissée passer par conception : vacuité acceptée

Une valeur vide n'est jamais soumise au typage, à la plage ou au domaine — c'est une
règle explicite d'`ingestion/controles.py`, testée par mutation
(`tests/test_controles.py`) : traiter une valeur vide comme une valeur invalide
confondrait l'absence d'une donnée avec une donnée mal formée, deux défauts de nature
différente, dont seul le second relève d'un contrôle de format. Une ligne à
`champs_manquants` a une valeur absente, pas une valeur fausse : elle passe donc
systématiquement, par conception.

Mesuré : 28313 entrées, 20336 identifiants distincts, 0 rattrapage réel — les 51
occurrences où l'identifiant apparaît en quarantaine sont des coïncidences (le même
patient porte par ailleurs une `date_naissance` incohérente), pas des rattrapages de
`champs_manquants` lui-même.

### `defauts_surface` — laissée passer par conception : altération restant typable

Une altération de surface (casse, accents, translittération d'un prénom, mise à jour
d'une adresse) change la forme d'une valeur sans en changer le format : une adresse en
minuscules sans accent reste une chaîne de texte valide, une date au mauvais registre de
casse n'existe pas dans ce jeu de défauts (seules les colonnes non typées — texte libre
— portent des défauts de surface). Aucun contrôle de typage, de plage ou de domaine ne
peut détecter une différence purement orthographique sur une colonne texte.

Mesuré : 1165 entrées, 1165 identifiants distincts, 1 seule coïncidence en quarantaine
(pour une autre raison), 0 rattrapage réel.

### `doublons` (hors faute de frappe de date de naissance) — laissée passer par conception : identifiants distincts hors du champ de l'unicité

Le contrôle d'unicité (`controler_unicite`) détecte une clé naturelle répétée **dans un
même fichier**. Une paire de doublons du générateur, c'est délibérément deux fiches à
deux `n_ipp` **distincts** — l'unicité ne les voit jamais en conflit, puisqu'elles ne
partagent aucune clé. Rapprocher deux identités distinctes est un travail de
réconciliation d'identité, hors du périmètre d'un contrôle d'entrée qui ne compare
chaque ligne qu'à elle-même et aux autres lignes du même fichier par leur clé.

Mesuré : 996 paires (1992 identifiants `n_ipp_1`/`n_ipp_2`), 5 coïncidences en
quarantaine (toutes pour `naissance_future`, sans lien avec le doublon lui-même), 0
rattrapage réel.

### `factures_sans_pec` — laissée passer par conception : absence d'un lien, pas d'une valeur

Une facture sans prise en charge associée est une incohérence référentielle entre deux
tables (`source.factures` et `source.prises_en_charge`), jamais une valeur mal formée
dans une seule ligne. Le schéma source ne porte aucune clé étrangère (décision de
conception documentée dans `docs/decisions/0014-typage-couche-source.md`) et
`ingestion/controles.py` ne contrôle que la ligne qu'il a sous les yeux : il ne peut pas
constater l'absence d'une ligne dans une autre table.

Mesuré : 384 entrées, 384 identifiants distincts, 0 coïncidence, 0 rattrapage.

### `rdv_doublon_creneau` — laissée passer par conception : identifiants distincts, même raison que `doublons`

Deux rendez-vous positionnés sur le même créneau portent deux `n_rdv` distincts : comme
pour les doublons d'identité patient, l'unicité par fichier ne les voit jamais en
conflit, puisqu'elle ne compare que les valeurs d'une même clé. Détecter un créneau
partagé exigerait de comparer les *valeurs* d'autres colonnes (agenda, horodatage) entre
lignes différentes, un contrôle d'un autre ordre que ceux déclarés.

Mesuré : 123 entrées, 123 identifiants distincts, 0 coïncidence, 0 rattrapage.

### `absence_structurelle` — laissée passer par conception : vacuité acceptée, comme `champs_manquants`

Même mécanisme que `champs_manquants` : une valeur structurellement absente (une colonne
qui n'a jamais existé pour cet enregistrement, par opposition à une colonne existante
mais vidée) reste une valeur vide au moment où `controler_ligne` l'examine, et la
vacuité passe tout.

Mesuré : 36178 entrées, 23937 identifiants distincts, 59 coïncidences (toutes
`naissance_future`), 0 rattrapage réel.

## Les absences structurelles ne sont ni des rejets ni des défauts détectés

`absence_structurelle` ne désigne pas un défaut que la chaîne aurait dû attraper et n'a
pas attrapé : c'est une propriété du jeu de données lui-même (certaines colonnes de
certaines lignes n'ont jamais reçu de valeur), qui n'a pas vocation à être détectée par
un contrôle d'entrée — elle est déjà, par construction, une valeur vide légitime.

Deux preuves indépendantes établissent qu'aucune absence structurelle n'a produit, par
accident, un rejet ou une perte de ligne :

**La réconciliation.** `ingestion/reconciliation.py`, exécuté contre le manifeste du
générateur, établit pour chacune des onze tables l'égalité exacte
`count(source) + count(quarantaine) = décompte du manifeste`. Une ligne dont une colonne
serait structurellement absente est comptée normalement des deux côtés : la somme
n'aurait pas tenu si `controler_ligne` avait, par erreur, transformé une absence en rejet
silencieux ou en ligne perdue.

**L'inventaire des motifs.** `ingestion/confrontation.py` décompose chaque motif de
rejet en trois segments (nom, colonne, valeur) et vérifie qu'aucun ne porte sur une
valeur vide — 0 trouvé, sur les 106 lignes actuellement en quarantaine. Une absence
structurelle qui aurait, par erreur, déclenché un contrôle produirait nécessairement un
motif à valeur vide (puisque la valeur examinée est vide par définition) ; l'absence
totale d'un tel motif est la preuve mécanique que la vacuité n'a jamais été le fait
générateur d'un rejet.
