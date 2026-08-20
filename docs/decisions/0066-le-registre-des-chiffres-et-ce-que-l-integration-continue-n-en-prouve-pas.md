# ADR 0066 — Aucun nombre du rapport n'est tapé : un registre des chiffres, et ce que l'intégration continue n'en prouve pas

**Statut.** Accepté, et appliqué au chapitre sur la conception du jeu de données.

---

## Contexte

Les chapitres qui restaient à écrire portent presque exclusivement des nombres produits par le
projet. Or ce projet a mesuré, sur son propre dossier, ce qui arrive à un nombre qu'on recopie :
**cinq valeurs ont circulé dans ses documents de suivi sans être rattachées à une commande, et les
cinq étaient fausses ou périmées.**

| Valeur | Ce qu'elle était |
|---|---|
| un total de lignes | il décrivait une génération écrasée depuis |
| un décompte de personnes | c'était un décompte d'identifiants, deux grandeurs distinctes |
| un mot d'indicateur | il recouvrait deux grandeurs différentes selon l'endroit |
| un décompte de paramètres | il était dépassé |
| un taux d'occupation | aucun artefact du dépôt ne le portait |

Aucune de ces cinq n'était une faute d'inattention isolée : elles ont toutes la même cause, qui est
qu'un nombre recopié cesse d'être rattaché à ce qui le produit dès l'instant où il est recopié.

## Décision

**Aucun nombre n'est écrit en clair dans une source du rapport.** Chaque valeur qu'un chapitre
affirme vit dans `docs/chiffres/registre_chiffres.yml`, avec la commande exacte qui la produit, et le
texte l'appelle par son identifiant : `\chiffre{source-lignes-total}`.

Le registre suit la convention des quatre registres déjà en place — un fichier de données sous
`docs/<domaine>/`, un en-tête énonçant sa règle de preuve, et un générateur adjacent qui en dérive
un artefact du rapport. Chaque entrée porte un identifiant, la valeur, l'unité, le type de commande,
la commande, la portée, et un motif quand elle n'est pas employée.

**Le registre s'ancre sur les données, non sur un horodatage.** Sept décomptes de tables constituent
l'ancrage : c'est l'état de la base auquel les valeurs correspondent. Un ancrage rompu invalide les
valeurs de portée `periode-entiere` **sans qu'aucune soit fausse**, et la commande de remesure le
signale par un code de sortie distinct plutôt que de rapporter soixante-et-onze écarts.

**Un identifiant inconnu arrête la composition** en nommant l'identifiant. Un chiffre absent doit
faire échouer le document, jamais laisser un blanc dans une phrase.

## Ce que l'intégration continue peut prouver, et ce qu'elle ne peut pas

**C'est le point de conception de cet appareil, et il se tranche par la mesure.**

L'exécuteur génère une fenêtre de trois mois ; le registre est mesuré sur la période entière. **Une
comparaison de valeurs y rougirait toujours**, et un contrôle rouge en permanence n'est plus un
contrôle — c'est un décor qu'on finit par désactiver.

| Ce qui s'exécute | Où | Ce que cela prouve |
|---|---|---|
| `mesurer.py --formes` | intégration continue, après la construction dimensionnelle | que chaque commande **s'exécute encore** et rend une valeur du type attendu — donc qu'aucune n'a été cassée par une évolution du schéma. Mesuré : 1,1 seconde pour les soixante-et-onze commandes |
| `tests/test_registre_des_chiffres.py` | intégration continue, sans base | que chaque nombre appelé existe, que chaque entrée sert ou porte son motif, et que le rendu correspond au registre |
| `mesurer.py --verifier` | **localement seulement** | que chaque valeur consignée est celle que sa commande rend aujourd'hui |

**Ce que l'appareil ne prouve pas, et il faut l'écrire :** que la valeur consignée soit la valeur
courante n'est établi que par une exécution locale sur la période entière. **L'intégration continue
ne peut pas s'en porter garante.** La commande de remesure est destinée à être rejouée avant la
remise, et c'est une opération manuelle.

La mesure qui l'établit est une mutation. Une valeur du registre a été remplacée par 346 403 — la
valeur fausse qui avait circulé dans ce projet —, le rendu régénéré pour rester cohérent, puis tout
a été rejoué :

- les sept propriétés hors base : **vertes** ;
- `mesurer.py --formes`, ce que l'exécuteur ferait : **vert** ;
- `mesurer.py --verifier` : **rouge**, `source-lignes-total : consigné 346403, mesuré 346149`.

**Une seule des trois voies voit la faute, et c'est celle qui ne peut pas s'exécuter là-bas.**

## Justification des points non triviaux

**Pourquoi deux identifiants pour un même nombre.** Le nombre 398 désigne les colonnes des couches
aval. Il décrit deux faits distincts : ce que le registre de provenance ne couvre pas, et ce que la
documentation des couches aval couvre. Ce sont les mêmes colonnes, et ce ne sont pas les mêmes
affirmations. Deux identifiants, deux notes, et le texte dit la différence — un identifiant unique
aurait fait passer une équivoque pour une coïncidence.

**Pourquoi une garde de lecture sur les commandes.** Le registre exécute ce qu'il porte. Un motif
refuse toute commande SQL qui n'ouvre pas sur une lecture, **avant** que la connexion soit ouverte :
un registre de chiffres ne doit pas pouvoir écrire dans la base par inadvertance.

**Pourquoi la question « par quelle voie cette propriété serait-elle vraie même si le code était
faux ? » est posée pour chacune.** Quatre mutations successives, sur ce projet, ont révélé un
contrôle défectueux plutôt qu'un code correct. La dernière est un cas d'école : une propriété
cherchait un identifiant n'importe où dans un fichier, où il figurait déjà pour une autre raison.
Chaque propriété du registre porte donc, en commentaire, la voie par laquelle elle passerait à tort
et la garde qui la ferme.

## Conséquences

- Le rapport porte **soixante-et-onze chiffres**, tous mesurés, aucun tapé.
- Une valeur qui change dans la base fait rougir la remesure locale, en nommant l'identifiant et les
  deux valeurs. Elle ne fait rougir rien d'autre.
- Le rendu `report/chiffres.tex` est produit mécaniquement et vérifié dans les deux sens contre le
  registre.
- Une entrée cesse d'être employée par le rapport : elle doit porter un motif écrit. C'est le second
  sens de la correspondance, que ce projet a dû ajouter après coup deux fois avant de le poser
  d'emblée.

## Ce que le registre ne dit pas

**Qu'une valeur soit la bonne.** Il établit qu'un nombre vient d'une commande, et que la commande
rend ce nombre. Il n'établit pas que la commande mesure ce que la phrase prétend : un décompte de
fiches présenté comme un décompte de personnes serait juste et faux à la fois. C'est exactement
l'une des cinq erreurs qui ont motivé ce registre, et **aucun appareil ne s'y substitue** — seule la
lecture de la commande en regard de la phrase la détecte.

## Sources

- `docs/chiffres/registre_chiffres.yml` — le registre, son ancrage et ses entrées.
- `docs/chiffres/mesurer.py` — les deux modes, et la différence entre eux.
- `docs/chiffres/generer_chiffres_tex.py` — le rendu et le mécanisme d'appel.
- `tests/test_registre_des_chiffres.py` — les propriétés, et la voie que chacune ferme.
