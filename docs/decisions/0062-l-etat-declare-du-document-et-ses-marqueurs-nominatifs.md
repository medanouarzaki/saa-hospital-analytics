# ADR 0062 — Le document déclare son état, et cet état dit ce que ses marqueurs nominatifs doivent porter

**Statut.** Accepté, et appliqué au squelette du rapport et à celui de la présentation.

---

## Contexte

Le squelette du rapport rassemble en un seul fichier les valeurs qui portent un **nom de personne** —
auteur, encadrant académique, encadrant professionnel, président du jury, examinateur — et les
valeurs de contexte qui n'en portent aucun. Rien d'autre dans les sources ne nomme quelqu'un : la
page de garde et la page de titre des diapositives lisent ces marqueurs, elles ne les recopient pas.

Une propriété était demandée : **un marqueur nominatif laissé vide doit rougir**, pour que le rapport
ne soit pas remis avec un cartouche incomplet. Elle est juste le jour de la remise, et fausse tous
les autres jours :

- le rapport n'est pas écrit, et les cinq marqueurs sont vides par construction ;
- deux de ces noms — le président du jury et l'examinateur — **ne sont pas connus** de l'auteur au
  moment où le squelette est posé ; ils sont désignés plus tard ;
- une règle du projet interdit d'écrire un nom de personne dans le dépôt à ce stade.

Écrire la propriété telle quelle rendrait donc l'intégration continue rouge en permanence, ce qui la
rendrait illisible : un contrôle rouge en permanence n'est plus un contrôle, c'est un décor. La
désactiver, à l'inverse, laisserait sans filet **l'erreur qui arrive réellement** — remettre le
document avec quatre marqueurs sur cinq renseignés.

## Décision

**Le document déclare son état, et cet état dit ce que les cinq marqueurs nominatifs doivent
porter.** Deux valeurs, et deux seulement :

| État déclaré | Ce que le contrôle exige des cinq marqueurs nominatifs | Ce que le document porte |
|---|---|---|
| `brouillon` | **tous vides** | une mention visible « Version de travail — document non remis » |
| `remise` | **tous renseignés** | plus aucune mention |

L'état est une commande unique du fichier des marqueurs. Une valeur autre que ces deux-là est
refusée, en nommant la valeur écrite : il n'existe pas d'état intermédiaire tacite.

La mention est **typographique**, pas conditionnelle à un contrôle : une commande compose son
argument en état de brouillon et rien en état de remise. Le document se suffit et ne dépend d'aucune
exécution extérieure pour dire ce qu'il est.

## Justification des points non triviaux

**Pourquoi la propriété est conditionnée et non affaiblie.** Un marqueur vide reste une faute — dans
l'état `remise`. Un marqueur renseigné reste une faute — dans l'état `brouillon`, où il annoncerait
un document qui n'existe pas. Aucun des deux cas n'est toléré : c'est la même exigence, énoncée
séparément pour chacun des deux moments du document.

**Pourquoi le remplissage partiel rougit dans les deux états.** C'est l'oubli qui arrive : quatre
noms sur cinq. Dans l'état `remise`, le contrôle nomme le marqueur manquant. Dans l'état
`brouillon`, il nomme le marqueur renseigné de trop. Les deux ont été **provoqués** et vus rouges,
et le message nomme dans chaque cas le seul marqueur en cause.

**Pourquoi la comparaison passe par `\ifx` sur deux commandes développées.** C'est la forme que le
noyau offre sans paquet supplémentaire ; elle compare les définitions caractère pour caractère. La
lecture par le contrôle, elle, normalise les espaces et la casse, pour qu'une différence
d'écriture ne se lise pas comme un autre état.

## Conséquences

- Passer à la remise **ne coûte qu'un mot** : l'état change, et le contrôle dit alors quel marqueur
  manque encore, un par un, par son nom.
- Un brouillon est **reconnaissable à l'œil**, sur le papier comme à l'écran, sans consulter le
  dépôt : la mention est sur la première page des deux documents.
- Les marqueurs de contexte — établissement, filière, année, organisme d'accueil, date de soutenance
  — ne sont pas soumis à cette règle : ils ne portent aucun nom de personne, et l'un d'eux est déjà
  renseigné.
- L'état livré est `brouillon`, les cinq marqueurs nominatifs sont vides, et **aucun nom de personne
  n'est écrit dans le dépôt**.

## Ce que cette décision laisse ouvert

**Un document laissé en `brouillon` le jour de la remise passerait le contrôle.** La propriété porte
sur l'accord entre l'état déclaré et les marqueurs, pas sur la justesse de l'état lui-même — aucun
contrôle ne peut savoir de l'extérieur si le document est remis. Ce qui protège de cet oubli n'est
pas une propriété mais **la mention visible en première page** : un document remis en portant
« Version de travail » se voit immédiatement, par n'importe qui, et d'abord par son auteur.

C'est un choix assumé : la garantie est déplacée du contrôle vers le document lui-même, là où
l'erreur se voit sans outil.

## Sources

- `report/marqueurs.tex` — l'état, les dix marqueurs, la commande de mention.
- `tests/test_marqueurs_nominatifs.py` — les valeurs admises, l'accord entre l'état et les cinq
  marqueurs, et les témoins des formes vides et renseignées.
- `report/liminaires/page-de-garde.tex` et `slides/presentation.tex` — les deux emplois de la
  mention.
