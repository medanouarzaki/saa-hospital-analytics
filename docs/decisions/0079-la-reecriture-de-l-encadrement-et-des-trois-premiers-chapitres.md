# ADR 0079 — La réécriture de l'encadrement, et ce qu'un budget de pages ne commande pas

**Statut.** Accepté.

---

## Contexte

L'introduction et les trois premiers chapitres étaient écrits dans un registre qui n'était pas
celui de leur lecteur. Phrases longues, réserves enchâssées dans la phrase qui portait le résultat,
décomptes d'appareil, tableaux exhaustifs de cent quarante-trois éléments.

Le rapport s'adresse à un encadrant de stage et à un jury d'école. Il n'est pas écrit contre une
relecture adverse.

## Décision

### 1. Une idée par paragraphe, une phrase par idée

Le résultat d'abord, le point, puis la réserve dans une phrase séparée. Une phrase de transition
entre deux sections quand le lien n'est pas évident — le style précédent les interdisait comme
creuses ; pour un lecteur qui découvre le sujet, elles ne le sont pas.

Chaque terme technique reçoit **une** phrase d'explication en français simple à sa première
apparition, et une seule fois dans tout le rapport. Cinq l'ont reçue : système d'information
hospitalier, données synthétiques et rapprochement probabiliste à l'introduction ; identifiant
patient permanent et index maître des patients au chapitre du système d'information.

### 2. La machinerie ne s'écrit plus dans la prose

Aucun décompte d'appareil de traçabilité, aucun renvoi au nombre d'entrées d'un registre, aucune
anecdote de développement de contrôle. Le lecteur n'a pas à connaître la machinerie pour lire le
résultat.

### 3. La méthode se dit une fois

Le chapitre de cadrage porte les trois principes — mesurer avant d'affirmer, vérifier ce qu'on
avance, tracer d'où vient chaque chiffre — en une demi-page, et ils ne se répètent nulle part
ailleurs. Le motif de l'absence d'images du système est dit au même endroit, une fois.

### 4. Une règle acquise était enfreinte, et elle est rétablie

Le chapitre de cadrage **tapait quatre nombres en clair** dans sa prose et dans son tableau de
provenance, alors que les quatre existaient au registre des chiffres avec leur commande. Ils
passent par leur identifiant. Aucun nombre mesuré par la chaîne n'est plus tapé dans ces quatre
pièces.

Les nombres qui viennent d'une source publiée restent écrits en clair avec leur citation : ce sont
des faits documentaires, pas des mesures de la chaîne, et le registre ne les porte pas.

## Ce qu'un budget de pages ne commande pas

Le cadrage visait dix-huit pages pour la tranche. La mesure en donne **seize**, et l'écart n'est pas
une troncature : rien de vérifié n'a été retiré pour tenir un budget.

| pièce | avant | cible | mesuré |
|---|---|---|---|
| introduction | 3 | 2 | 2 |
| l'organisme d'accueil | 4 | 5 | 4 |
| le système d'information | 10 | 6 | 6 |
| cadrage et méthodologie | 4 | 5 | 4 |
| **tranche** | **21** | **18** | **16** |

Les deux pièces sous leur cible sont exactement celles qui portent des paragraphes de rédaction
personnelle non encore écrits : une au chapitre de l'organisme d'accueil, trois au chapitre de
cadrage. Leur dernière page composée est à demi remplie, et c'est là que ces paragraphes viendront.
**Le budget n'est pas faux, il est prématuré.**

Le chapitre du système d'information gagne par ailleurs une figure — l'organisation de
l'établissement — que la source décrit et qu'aucun tableau ne rendait.

## Ce qui a été écarté

**Rembourrer pour atteindre la cible.** Écarté : un paragraphe ajouté pour occuper une page est un
paragraphe que personne ne lit.

**Dessiner l'organigramme du service.** Écarté : sa composition n'a pas été relevée, et aucune
source publiée ne la porte. La figure composée est celle de l'établissement, que la source décrit ;
sa légende dit explicitement que l'organisation interne du service n'y figure pas.

## Ce que cette décision ne peut pas voir

**Aucun contrôle ne tient le style.** Ni la longueur d'un paragraphe, ni la place d'une réserve, ni
le fait qu'un terme technique soit expliqué une fois et une seule. Ces propriétés sont
typographiques ou sémantiques, et elles ne se vérifient qu'à la lecture.

**Le décompte de pages n'est pas contrôlé non plus.** Il est mesuré à chaque composition et
rapporté, jamais vérifié par un contrôle : la pagination dépend de la distribution typographique,
et une propriété qui dépend du rendu n'est pas observable côté serveur.
