# ADR 0075 — Les étiquettes de provenance cessent d'imprimer, et l'appareil reste câblé

**Statut.** Accepté. Il révise le rendu posé par l'`0063` et l'`0064`, non leur mécanisme.

---

## Contexte

`\releve{...}` et `\convention{...}` composaient un exposant `[obs.]` et `[conv.]` au fil de la
prose. Le rapport en porte **trente-neuf appels** — trente-quatre relevés et cinq conventions —
répartis sur dix des onze fichiers de chapitre.

L'appareil a été écrit pour qu'un lecteur puisse dire, sur n'importe quelle affirmation, d'où elle
vient. C'était juste. Ce qui a changé, c'est ce qu'on sait du **destinataire** : ce document
s'adresse à un encadrant de stage, pas à une relecture adverse. Un exposant tous les deux
paragraphes est un appareil de défense, et il se lit comme tel.

## Décision

**Les deux commandes ne composent plus rien.** Leur corps devient vide.

**L'APPAREIL RESTE ENTIÈREMENT CÂBLÉ, IL CESSE SEULEMENT D'IMPRIMER.** L'argument reste
l'identifiant du relevé ou de la convention ; chaque fichier de chapitre continue de déclarer en
tête ce sur quoi il repose ; et `tests/test_provenance_des_chapitres.py` continue de confronter la
déclaration à ce que le fichier porte, dans les deux sens.

**C'est vérifié, pas supposé.** Ce contrôle lit les SOURCES DE COMPOSITION, jamais le PDF : rien de
ce qu'il vérifie ne dépend de ce que ces deux commandes composent. Après le changement, ses
dix-sept propriétés sont vertes, et `tests/test_provenance.py` — les quatre propriétés de provenance
des colonnes — aussi.

**Les citations `\cite{...}` de l'étiquette `DOC` restent visibles.** Renvoyer à une source publiée
est l'usage académique normal, et ce n'est pas un appareil de défense.

## Ce qui a été mesuré

Le document composé **passe de 99 à 98 pages**, et la cause est isolée : la même compilation faite
sur la révision d'origine avec ce seul fichier remplacé rend 98 pages. Les trente-neuf exposants
retirés valaient une page. Aucune autre modification de ce travail ne change la pagination — le titre
corrigé, le logotype en emplacement réservé et les lignes conditionnelles de la page de garde
laissent le document à 98 pages.

## Ce qui a été écarté

**Retirer les appels des fichiers de chapitre.** Écarté, et c'est le point de la décision : les
retirer aurait supprimé l'appareil, pas son impression. Un travail ultérieur qui voudrait le rétablir
n'aurait alors plus rien à rétablir.

**Composer les étiquettes en note de bas de page.** Écarté : le motif n'est pas que l'exposant soit
mal placé, c'est qu'il s'adresse à un lecteur qui n'est pas celui-ci.

## Ce que cette décision ne peut pas voir

**Aucun contrôle ne tient le fait que ces commandes soient muettes.** Rien ne rougirait si l'une
d'elles se remettait à composer, et rien ne rougit non plus aujourd'hui de ce qu'elles ne composent
plus. La propriété est typographique, donc observable seulement sur le PDF, que le dépôt ne suit
pas. Le seul témoin est le nombre de pages, et il est écrit ci-dessus.
