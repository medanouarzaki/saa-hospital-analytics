# ADR 0071 — L'annonce du plan est confrontée aux chapitres qui existent, et deux en-têtes courants mentaient

**Statut.** Accepté.

---

## Contexte

L'introduction générale annonce le plan du rapport. Rien n'obligeait ce plan à rester celui du
document : un chapitre renuméroté, renommé ou ajouté laissait l'annonce intacte et fausse, et
aucune compilation ne s'en plaint.

Ce n'est pas une crainte théorique. Le tableau de bord de ce projet a porté pendant plusieurs
travaux une mention annonçant « les sept autres pages » alors qu'il en comptait huit autres — un
décompte écrit à la main dans un libellé, devenu faux quand une neuvième page s'est ajoutée. **Il
n'a pas été trouvé par un contrôle mais en regardant l'écran**, et il est corrigé par le présent
travail. Une fois suffit à établir la règle.

## Décision

### 1. L'annonce du plan est un appareil de traçabilité, le sixième

Un titre annoncé s'écrit `\annonceChapitre{numéro}{titre}` et se compose au fil de la prose. Un
contrôle lit ces appels et les confronte **aux fichiers de chapitre**, dans les deux sens :

- tout chapitre annoncé existe, sous ce numéro et avec ce titre **exact** ;
- tout chapitre numéroté du rapport est annoncé.

S'y ajoutent deux propriétés qui ferment les voies restantes : aucun chapitre n'est annoncé deux
fois, et les numéros annoncés se suivent depuis un — sans quoi une annonce sous un numéro libre
passerait les deux sens.

**La structure est lue dans les fichiers, pas dans le sommaire composé.** L'ordre vient des
inclusions du fichier principal — c'est lui qui décide de l'ordre réel — et la numérotation en
découle, les chapitres étoilés ne comptant pas. Le contrôle s'exécute donc sur un clone frais, sans
distribution typographique, à l'emplacement où siègent les autres contrôles de sources du rapport.

**La comparaison porte sur l'égalité du titre, jamais sur son inclusion.** Un contrôle qui
vérifierait qu'un titre annoncé est *contenu* dans un titre réel accepterait « Analyse » pour
« Analyse de l'activité » ; un témoin construit sur deux titres dont l'un est le préfixe strict de
l'autre l'établit.

### 2. Les décomptes de structure ne s'écrivent plus à la main dans un libellé

La formulation retenue pour la mention corrigée **ne porte plus de décompte** : « les autres
pages », et non « les huit autres pages ». Un décompte écrit à la main dans un libellé affiché est
ce qui a produit le défaut, et le reproduire à neuf le reproduirait à l'identique dans six mois.

Un filet a cherché les autres, sur toutes les chaînes que les pages affichent : **il n'en reste
aucune.** Le filet a ses deux témoins — il trouve la mention sur le fichier d'avant la correction,
il ne trouve rien sur celui d'après, et il trouve quatre occurrences ailleurs, ce qui rend son
silence significatif. Ces quatre-là sont dans le registre des indicateurs, hors du périmètre
d'écriture de ce travail : **une seule est de la classe dangereuse** — « les huit activités », qui
est un décompte de données —, et elle est consignée ici plutôt que corrigée.

### 3. Deux textes portaient l'en-tête courant de ce qui les précédait

Mesuré en lisant le document composé, et par aucun autre moyen :

| page | en-tête courant porté | en-tête attendu |
|---|---|---|
| deuxième page de l'introduction | `TABLE DES MATIÈRES` | `Introduction générale` |
| deuxième page de la conclusion | `CHAPITRE 9. RECOMMANDATIONS` | `Conclusion générale` |

La cause est qu'un chapitre étoilé ne met pas à jour la marque de l'en-tête. Les deux textes posent
donc la leur explicitement, et les six pages portent désormais leur propre titre.

## Ce qui a été trouvé et n'est pas corrigé

**Les pages de l'annexe portent `BIBLIOGRAPHIE` en en-tête courant** — vingt-deux pages sur
vingt-trois, la première exceptée parce qu'elle est en style de page nu. C'est le même défaut, et il
est plus étendu que les deux précédents.

**Le remède évident n'a pas fonctionné, et c'est un fait mesuré.** Une marque posée explicitement
après le titre de l'annexe ne change rien à l'en-tête des pages suivantes ; une marque de sonde,
portant un texte unique, **n'apparaît sur aucune page**. La cause n'est donc pas celle des deux
textes d'encadrement, et elle n'est pas établie.

L'édition a été retirée plutôt que conservée : **une correction qui ne corrige pas est pire
qu'aucune**, parce qu'elle laisse croire que la question est réglée. Le défaut est consigné ici,
avec sa mesure et avec le fait que le remède habituel ne mord pas, pour qu'un travail ultérieur
reparte de là plutôt que de la case départ.

## Ce qui a été écarté

**Annoncer le plan en prose libre, sans commande.** Écarté : c'est l'état d'avant, et il n'offre
aucune prise à un contrôle.

**Lire la structure dans le sommaire composé.** Écarté : le sommaire est un artefact de
compilation, et le contrôle devrait alors vivre dans le travail qui compile, où il ne pourrait plus
s'exécuter sur un clone frais.

**Corriger l'en-tête de l'annexe sans en comprendre la cause.** Écarté pour la raison donnée
ci-dessus.

## Ce qui aurait invalidé cette décision

**Une annonce du plan qui ne pourrait pas être rendue conforme à la structure mesurée.** La
structure a été extraite avant d'écrire une ligne de l'introduction, et l'annonce a été écrite
d'après elle ; le contrôle est vert dès la première rédaction, et les deux mutations montrent qu'il
rougit dans les deux sens.

## Sources

`report/rapport.tex` ; `report/chapitres/introduction.tex` ; `report/chapitres/conclusion.tex` ;
`tests/test_annonce_du_plan.py` ; `dashboard/pages/donnees.py` ; `report/annexes.tex` ;
`docs/decisions/0070-le-tableau-de-bord-se-decrit-sans-capture-d-ecran.md`, qui a consigné la
mention devenue fausse sans avoir licence de la corriger.
