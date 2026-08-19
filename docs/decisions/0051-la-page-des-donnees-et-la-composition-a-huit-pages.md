# ADR 0051 — Le tableau de bord compte huit pages : une page donne les lignes derrière les chiffres

**Statut.** Accepté. **Remplace la composition fixée par l'ADR `0045`**, qui n'est pas modifié.

> **Forme de remplacement.** Le dépôt n'avait aucun précédent d'un enregistrement en remplaçant un
> autre : les quatre amendements existants portent la mention `**Amendée**` **dans l'enregistrement
> amendé lui-même**, et le seul emploi du mot « remplace » en tête de statut — ADR `0003` — vise le
> cadrage initial, non un autre enregistrement. La forme est donc posée ici : **l'enregistrement
> remplaçant nomme celui qu'il remplace, dit ce qu'il remplace exactement et ce qui a changé depuis,
> et l'enregistrement remplacé n'est pas touché.** Ce qui est remplacé est **la composition seule** ;
> tout le reste de l'ADR `0045` — les six indicateurs retirés, le retrait de la page de
> recommandations, et les mesures qui les fondent — reste en vigueur.

---

## Contexte

**Ce que l'ADR `0045` a fixé, et ce qui a changé depuis.** Il arrête la composition à sept pages, au
terme d'une campagne de mesure qui confrontait la liste du cadrage à ce que la chaîne produit. Cette
campagne portait sur des **grandeurs** : elle recensait des indicateurs, les classait calculables ou
non, et retirait ceux sans matière. **Elle n'a jamais examiné le besoin de consulter des lignes**,
parce que le cadrage n'en énonçait aucun.

**Le manque s'est révélé à l'usage.** Un responsable qui lit qu'une part des passages aux urgences
n'est pas facturée ne peut rien en faire tant qu'il n'a pas la liste de ces passages. Les sept pages
répondent toutes à « combien » ; **aucune ne répond à « lesquels »**. Le seul chemin vers les lignes
était le classeur produit chaque jour par le graphe, qui n'est ni filtrable ni consultable à l'écran.

**La composition passe donc de sept à huit pages.** L'ajout ne contredit aucune mesure de l'ADR
`0045` : il répond à un besoin que sa campagne ne mesurait pas.

## Décision

**Le tableau de bord compte huit pages** : activité, rendez-vous, urgences, séjours, facturation et
recouvrement, qualité des données, rapprochement d'identités, **et données**.

**La page « Données » montre quatre tables de faits**, choisies sur l'usage — celles qu'on consulte
pour agir :

| Table | Lignes | Colonnes | Consultée pour |
|---|---|---|---|
| `fct_passage_urgence` | 27 360 | 14 | savoir quels passages ont été orientés où, et lesquels n'ont pas abouti |
| `fct_facturation` | 21 066 | 17 | retrouver les factures d'un service sur une période, et leur état |
| `fct_rendez_vous` | 14 169 | 23 | lister les rendez-vous manqués d'une activité pour rappeler les patients |
| `fct_sejour` | 2 980 | 19 | retrouver les séjours d'un service, et ceux qui ne sont pas clos |

**Elle affiche au plus mille lignes, et le dit à l'écran**, tout en donnant le décompte complet de ce
que le filtre retient **avant** le tableau. Le plafond est dérivé et non choisi : le plus gros
tableau que le tableau de bord pousse déjà pèse **801 248 octets** une fois sérialisé ; la plus large
des quatre tables pèse **219 104 octets à mille lignes**, soit 27 % de cela, et **647 744 octets à
trois mille** sans que la lisibilité y gagne.

**Trois filtres** — période, service, activité — et **chacun porte une restriction réelle dans la
requête**. Aucune des quatre tables ne porte les trois colonnes : **un filtre sans colonne sur la
table choisie est désactivé et le dit à l'écran**, plutôt que d'être accepté sans effet.

**Un téléchargement porte la sélection entière, jamais le tableau tronqué**, au format et à
l'encodage des fichiers tabulaires du livrable quotidien, lus dans son module d'export et non
redécidés. La page dit en une ligne que cette extraction ne remplace pas ce livrable.

## Ce que la page ne montre pas, et pourquoi

**Les agrégats.** Les sept autres pages les portent déjà ; les reproduire ligne à ligne
n'apprendrait rien.

**La dimension des patients**, 29 107 lignes et 49 colonnes. La consulter ligne à ligne n'appelle
aucune action : on n'agit pas sur une fiche d'identité, on agit sur un passage, une facture, un
rendez-vous, un séjour. Un tableau de bord de pilotage n'a pas à exposer un annuaire.

**Les créances**, 5 876 lignes. C'est le cas le plus discutable, et il mérite d'être dit : ce sont
des lignes sur lesquelles on agit. Deux raisons l'écartent — la page de facturation les expose déjà
par tranche d'ancienneté, et surtout `int_creances` **ne porte ni colonne de service ni colonne
d'activité** : deux des trois filtres y seraient inapplicables, ce qui en ferait la table où la
promesse de la page est la plus faible.

## Ce qui a été écarté

**Montrer toutes les tables de l'instantané.** Vingt-six objets, dont des agrégats déjà affichés, des
dimensions à une colonne et les tables du rapprochement qui ont leur page. Une page qui montre tout
ne guide vers rien.

**Ne pas limiter le tableau.** Le plus gros objet retenu pousserait **4,1 Mo** par rendu, mesuré, et
personne ne parcourt vingt-sept mille lignes à l'écran. Le refus de plafonner aurait produit une page
lente et inutilisable, ou une troncature silencieuse — le pire des deux.

## Ce qui aurait invalidé cette décision

**Qu'aucun objet de l'instantané ne se consulte utilement ligne à ligne.** Si toutes les tables
n'étaient que des agrégats, ou si aucune ne portait d'identifiant permettant de retrouver un dossier,
la page n'aurait rien à montrer et le classeur quotidien resterait le seul chemin.

Ce n'est pas le cas : les quatre tables retenues portent chacune un identifiant de dossier
(`n_passage`, `n_facture`, `n_rdv`, `n_sejour`) **et** l'identifiant patient, ce qui est exactement ce
qu'il faut pour agir sur une ligne.

## Vérification

Quatre propriétés neuves au contrôle du tableau de bord, et **elles appellent la page** : chaque
filtre porte une restriction réelle, éprouvée en exécutant la clause et en comparant deux décomptes ;
le décompte affiché égale un décompte mesuré indépendamment ; le fichier téléchargeable porte la
sélection entière et non le tableau tronqué ; la page ne nomme aucun objet hors de l'instantané. La
propriété existante qui compare les pages déclarées aux pages du registre passe de sept à huit
**par calcul des deux côtés**, sans littéral.

## Sources

`docs/decisions/0045-composition-des-sept-pages.md` — la composition que cet enregistrement remplace,
et les six retraits d'indicateurs qui restent en vigueur.
`docs/decisions/0043-instantane-schema-dedie-du-tableau-de-bord.md` — ce que le tableau de bord lit.
`docs/decisions/0041-taches-export-instantane-vides.md` — le livrable quotidien, que l'extraction de
cette page ne remplace pas.
`docs/decisions/0050-libelles-de-dimension-la-ou-une-source-les-documente.md` — les libellés que la
page affiche, et les codes qu'elle laisse nus.
