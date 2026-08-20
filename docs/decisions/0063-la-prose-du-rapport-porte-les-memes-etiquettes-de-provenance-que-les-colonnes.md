# ADR 0063 — La prose du rapport porte les mêmes étiquettes de provenance que les colonnes de l'entrepôt

**Statut.** Accepté, et appliqué au premier chapitre rédigé.

---

## Contexte

Chaque colonne de l'entrepôt porte sa provenance, et un contrôle bloque si une colonne n'en porte
pas. Trois étiquettes suffisent à couvrir tous les cas : `DOC` quand une source documentaire l'étaye,
`OBS` quand un relevé d'observation l'étaye, `HYP` quand ni l'une ni l'autre et qu'une convention a
été posée.

**La prose du rapport n'avait aucun équivalent.** Une affirmation pouvait s'écrire sans que rien ne
dise d'où elle venait. Une citation pouvait pointer vers une clé absente du fichier bibliographique
sans que rien ne le signale : la compilation se contente d'un point d'interrogation dans le texte, et
un document de plusieurs dizaines de pages ne se relit pas à la loupe avant chaque remise.

Deux défauts particuliers ont motivé l'écriture de l'appareil, l'un et l'autre rencontrés :

- une source **écartée** du projet — celles dont la vérification vaut `introuvable` et qui n'entrent
  pas au fichier bibliographique — reste citable en apparence : rien n'empêchait d'écrire son
  identifiant ;
- une section supprimée d'un chapitre emportait ses sources avec elle sans qu'aucun contrôle ne
  s'en aperçoive.

## Décision

**Chaque fichier de chapitre déclare en tête l'ensemble de ce sur quoi il repose, sous les trois
mêmes étiquettes que les colonnes, et un contrôle vérifie que la déclaration coïncide exactement avec
ce que le fichier porte.**

```latex
% Ce chapitre repose sur :
%   DOC: s01, s03, s05, s12, s20, s27, s28, s29, s30
%   OBS: composition-du-service
%   HYP: pyramide-des-ages
```

Dans le corps du texte, `DOC` se porte par la commande de citation ordinaire, `OBS` par `\releve{…}`
et `HYP` par `\convention{…}`, ces deux dernières composant une marque brève — `[obs.]`, `[conv.]` —
à l'endroit même de l'affirmation.

**Six propriétés**, dont deux conditionnées à l'état déclaré du document :

| Propriété | Conditionnée |
|---|---|
| toute clé citée existe au fichier bibliographique produit | non |
| la déclaration coïncide avec le contenu, **dans les deux sens**, pour les trois étiquettes | non |
| une entrée non citable du registre n'est pas citée | non |
| chaque chapitre déclare les trois étiquettes | non |
| toute entrée citable est citée quelque part, ou déclarée non employée avec son motif | **`remise`** |
| aucun paragraphe de rédaction personnelle ne subsiste | **`remise`** |

## Justification des points non triviaux

**Pourquoi la déclaration explicite, et pas la seule extraction.** Un contrôle qui se contenterait
d'extraire les citations vérifierait qu'elles existent, jamais qu'elles sont celles qu'on croit. La
déclaration est un engagement écrit à la main : elle rend visible dans le diff qu'un chapitre a
changé de sources, ce que le corps du texte, long et remanié, ne montre pas.

**Pourquoi la déclaration vide explicite.** Un fichier sans en-tête passerait la correspondance par
accident — ensemble déclaré vide contre ensemble porté vide. Une cinquième propriété, non demandée
mais nécessaire, exige les trois lignes dans chaque fichier. Les chapitres non encore rédigés
déclarent `(aucun)`.

**Pourquoi une propriété distincte pour les entrées non citables.** Une clé absente du fichier
bibliographique peut être une faute de frappe ; une clé correspondant à une entrée écartée du projet
est autre chose. Les deux propriétés rougissent ensemble, et leurs messages diffèrent : le second dit
que la source est inutilisable, pour que l'auteur ne corrige pas la clé au lieu de comprendre.

**Pourquoi les deux propriétés conditionnées le sont.** En état de brouillon, la plupart des
chapitres sont vides : exiger que les vingt-huit entrées citables soient employées signalerait la
quasi-totalité du registre à chaque exécution, et un contrôle rouge en permanence n'est plus un
contrôle. Le mécanisme d'état existant est réemployé, non dupliqué.

**Ajouter une entrée au registre et enrichir une entrée détenue ne sont pas la même opération, et
c'est la distinction qui a débloqué la rédaction.** Ajouter une entrée, c'est faire entrer une source
nouvelle dans le projet : cela engage une vérification de contenu, un contrôle d'URL, une
qualification de fiabilité. Enrichir le champ `utilise_pour` d'une entrée **déjà présente, déjà lue,
et dont le document est détenu sur disque**, c'est écrire ce que cette source étaie et que personne
n'avait encore relevé — le document ne change pas, seule la connaissance qu'on en a. La première
opération est refusée en cours de rédaction ; la seconde est permise, à la condition que la matière
soit **mesurée dans le document détenu** et citée avec ses pages. Enrichir une entrée dont le
document n'est pas détenu, ou dont le contenu n'est pas extractible, est impossible et ne se tente
pas.

## Conséquences

- **Le retrait d'une section est détecté**, par le second sens de la correspondance : la section
  emporte ses sources, la déclaration devient fausse, le contrôle nomme les sources orphelines. Les
  quatre sections du premier chapitre ont été retirées une à une, et les quatre retraits rougissent.
- **Une source écartée ne peut plus être citée par distraction.**
- Le jour de la remise, un seul mot change l'état du document, et les deux propriétés conditionnées
  s'activent en nommant ce qui manque, entrée par entrée et paragraphe par paragraphe.
- L'appareil coûte trois lignes de commentaire par fichier, et rien d'autre.

## Ce que cet appareil ne peut pas voir

**Il vérifie qu'une citation existe, jamais qu'une phrase dit ce que sa source dit.** Une
affirmation fausse, correctement citée vers une source qui affirme le contraire, passe tous les
contrôles. La correspondance entre une phrase et sa source relève de la lecture, et aucun motif
textuel ne s'y substitue.

Deux limites plus étroites s'y ajoutent, mesurées :

- **La détection du retrait d'une section est indirecte.** Elle repose sur le fait que chaque section
  porte au moins une source qu'aucune autre ne porte. Une section ne citant que des sources partagées
  disparaîtrait sans rien faire rougir. La propriété porte sur l'ensemble des sources du fichier, pas
  sur sa structure de sections.
- **Aucune mutation portée sur `utilise_pour` ne peut faire changer le fichier bibliographique**, ce
  champ n'entrant dans aucune notice. La vivacité de la chaîne registre → bibliographie a donc été
  établie par la mutation d'un champ qui, lui, compose la notice.

## Sources

- `tests/test_provenance_des_chapitres.py` — les six propriétés, et les onze témoins du motif
  d'extraction dans les deux sens.
- `report/provenance.tex` — les trois étiquettes et la marque de rédaction personnelle.
- `docs/sources/sources.yml` — le registre, dont la clé de citation se déduit de l'identifiant.
- `docs/sources/to_bibtex.py` — les champs qui composent une notice, et ceux qui n'y entrent pas.
