# ADR 0007 — Une prise en charge par épisode, et non par facture, par ligne ni par couverture

**Statut.** Accepté, et appliqué depuis la construction de la table.

> **Enregistrement rétrospectif.** Cette décision a été prise et appliquée avant que sa consignation
> ne soit écrite ; le présent enregistrement est rédigé le 18 août 2026, à partir de l'état du dépôt
> et des documents de suivi du projet. Le cadrage prescrit qu'un enregistrement soit écrit au moment
> de la décision et jamais rétrospectivement : il y est ici dérogé sciemment, pour qu'un numéro
> réservé et cité depuis l'origine cesse de renvoyer à un fichier absent.

---

## Contexte

`source.prises_en_charge` porte la démarche par laquelle un organisme de couverture s'engage à payer
tout ou partie des frais d'un patient à la place du patient lui-même.

**Cette table n'a pas été relevée.** Sur ses dix colonnes, deux seulement portent une provenance
observée, et elles viennent de la fiche patient, non d'un écran de prise en charge : `n_ipp`
(`REL-PAT.D01`) et `n_assure` (`REL-PAT.A03`). Les huit autres sont documentées ou posées — `S-27`
pour l'identifiant, l'épisode, le type et la date de vérification, `S-15` pour l'organisme, `S-19`
pour l'état, `S-18` pour le taux, et une hypothèse pour la date d'extraction.

**Le grain ne pouvait donc pas être relevé : il devait être décidé.** Aucun écran ne dit combien de
lignes existent, ni ce qu'une ligne représente. Quatre grains se présentaient, et le choix devait
être justifié depuis une source, faute de pouvoir l'être depuis une observation.

**Ce que la source dit.** L'article 79 du règlement intérieur des hôpitaux (`S-27`, reproduisant le
texte dont `S-03` est la source de droit) énumère les formalités administratives de sortie. La
deuxième est *« facturation et règlement des frais d'hospitalisation **ou** signature des documents
de prise en charge »*.

**C'est une alternative, et elle est datée de la sortie.** Le texte n'oppose pas la prise en charge
à une ligne de facture ni à un acte : il l'oppose au **règlement des frais du séjour**, au moment où
le patient quitte l'établissement. La prise en charge est donc l'une des deux issues administratives
possibles d'un **épisode**, et non un attribut d'un document comptable ou d'une couverture.

## Décision

**Le grain de `source.prises_en_charge` est l'épisode : au plus une ligne par épisode, et une ligne
seulement pour les épisodes ayant donné lieu à une demande.**

`n_episode` est donc unique dans la table, et non seulement identifiant d'un rattachement. L'état
retenu par la ligne — accordée, refusée, encore en instance — est **l'issue de la démarche pour cet
épisode**, pas l'état d'une pièce comptable.

**Les épisodes sans demande n'ont pas de ligne.** Le grain ne prévoit pas de ligne « pas de demande
» : l'absence d'une prise en charge est portée par l'absence de la ligne, ce qui est exactement ce
que dit l'alternative de l'article 79 — l'autre branche, c'est le règlement des frais, dont la trace
est la facture, pas une prise en charge vide.

## Justification des points non triviaux

### Les trois grains écartés, et ce que chacun aurait coûté

Mesures faites sur l'état de la base.

| Grain | Lignes qu'il donnerait | Ce qu'il fait perdre |
|---|---|---|
| **Épisode** *(retenu)* | **16 430** | — |
| Facture | 16 430 | rien de mesurable ici, et c'est le problème (voir ci-dessous) |
| Ligne de facture | jusqu'à 160 936 | l'engagement porterait sur un acte, ce qu'aucune source n'établit |
| Couple patient / organisme | 12 593 | l'état par épisode : une même couverture porte jusqu'à 8 démarches |

**Le grain par ligne de facture** ferait de l'engagement un attribut d'acte. Aucune source ne le dit,
et l'article 79 dit le contraire : il oppose la prise en charge au règlement *des frais du séjour*,
pris comme un tout.

**Le grain par couple patient / organisme** ferait de la prise en charge une **couverture** — un
droit ouvert — plutôt qu'une **démarche** — une demande, une décision, une date. Les 16 430 lignes
se réduiraient à 12 593 couples, et les trois états mesurés (**15 016** accordées, **1 348**
refusées, **66** encore en instance) deviendraient inexprimables : un patient dont une démarche est
accordée et une autre refusée n'aurait plus qu'une ligne, et aucun état ne conviendrait. La
répartition par patient le montre : **1,31 démarche par patient en moyenne, jusqu'à 8**.

### Pourquoi « par épisode » et non « par facture », alors que les deux donnent le même compte

C'est le point le plus délicat de cette décision, et le seul que la mesure ne tranche pas.

Dans l'état actuel, facture et épisode sont **en correspondance de un à un** : 21 066 factures pour
21 066 épisodes distincts. Les deux grains produisent donc exactement les mêmes 16 430 lignes, et
**aucune mesure ne peut les départager**. Le générateur lui-même parcourt les factures pour émettre
les demandes, tout en clavant chaque ligne sur `n_episode`.

Le choix se justifie donc par la source et non par la donnée. L'article 79 rattache la prise en
charge à la **sortie du patient**, formalité d'épisode ; la facture est la trace de l'autre branche
de l'alternative. Retenir l'épisode fait porter le grain par la notion que la source nomme.

**La conséquence est que le jour où un épisode porterait deux factures, la table resterait
correcte** — une seule démarche, celle de la sortie — alors qu'un grain par facture en produirait
deux, sans qu'aucune source justifie de dédoubler l'engagement. La décision est prise en connaissance
du fait que sa portée est aujourd'hui invisible, et le restera tant que la correspondance tient.

### Ce que la table ne porte pas, et pourquoi ce n'est pas une omission

**Le motif d'un refus n'a pas de colonne.** Les 1 348 démarches refusées ne disent pas pourquoi.
Une répartition qualitative des raisons est bien posée en configuration
(`motifs_refus_prise_en_charge`), mais elle n'est **pas matérialisée** : aucune des dix colonnes
relevées ou documentées ne porte un motif, et en ajouter une excéderait le relevé. La configuration
le note explicitement là où le paramètre est déclaré.

**Les 66 démarches sans date de vérification** ne sont pas des lignes incomplètes : ce sont
exactement les démarches encore en instance à la fin de la période, dont la décision n'est pas
tombée. L'état `N` et l'absence de date disent la même chose, et se contrôlent l'un par l'autre.

## Conséquences

Toute jointure vers la prise en charge se fait par `n_episode`, et une jointure par patient est
nécessairement multiple.

Un épisode sans ligne se lit comme « pas de demande », jamais comme « donnée manquante ». Cette
lecture n'est pas déductible de la table seule : elle tient au grain, donc à cet enregistrement.
Sur 21 066 factures, **16 430** portent une demande.

Le taux de prise en charge ne prend que trois valeurs — **0,00, 0,80 et 1,00** — parce qu'il suit le
type d'épisode et un seuil de montant (`S-18`), et non l'organisme. Un lecteur qui attendrait une
distribution continue de taux négociés par organisme lirait autre chose que ce que la table porte.

## Ce qui aurait invalidé cette décision

**Qu'une source rattache l'engagement à autre chose qu'à l'épisode** — un acte, une ligne de
facture, un droit ouvert pour une période. La formule de l'article 79 aurait alors été une commodité
de rédaction plutôt qu'un rattachement, et le grain aurait suivi la source la plus précise.

**Qu'un épisode porte plusieurs factures.** Le choix entre les deux grains équivalents deviendrait
mesurable, et il faudrait vérifier laquelle des deux lectures correspond au relevé. La mesure a été
faite : la correspondance est de **un à un sur les 21 066 factures**, et la question reste donc
ouverte sans être bloquante.

## Sources

`docs/modules_non_observes.md` — l'article 79 et son alternative, dans le relevé réglementaire dont
cette décision découle directement.
`ingestion/ddl/05_prises_en_charge.sql` — les dix colonnes et leur provenance, portées jusque dans
les commentaires du catalogue.
`generator/config/prises_en_charge.yml` — les taux de demande par type d'épisode, le taux de refus,
et la note qui refuse de matérialiser le motif de refus.
`docs/sources/sources.yml` — `S-27` (règlement intérieur, dont `S-03` est la source de droit),
`S-15`, `S-18`, `S-19`.
`docs/decisions/0023-grain-des-tables-de-faits-et-rattachement-patient.md` — le grain des faits
construits en aval de cette table.
`docs/decisions/0024-limites-documentees-des-faits.md` — les limites que ce grain impose aux
grandeurs calculées.
