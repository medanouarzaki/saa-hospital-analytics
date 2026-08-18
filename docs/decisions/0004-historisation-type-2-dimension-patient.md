# ADR 0004 — La dimension patient conserve l'historique des versions plutôt que de l'écraser

**Statut.** Accepté, et appliqué depuis l'origine du projet.

> **Enregistrement rétrospectif.** Cette décision a été prise et appliquée avant que sa consignation
> ne soit écrite ; le présent enregistrement est rédigé le 18 août 2026, à partir de l'état du dépôt
> et des documents de suivi du projet. Le cadrage prescrit qu'un enregistrement soit écrit au moment
> de la décision et jamais rétrospectivement : il y est ici dérogé sciemment, pour qu'un numéro
> réservé et cité depuis l'origine cesse de renvoyer à un fichier absent.

---

## Contexte

Une fiche patient est modifiée dans le système observé : correction d'un nom mal saisi, d'une date
de naissance, ajout d'une pièce d'identité, changement d'adresse ou d'organisme après un
déménagement ou un changement de situation.

Un entrepôt qui écraserait la fiche à chaque extraction conserverait le dernier état et perdrait la
trace de ces corrections. Or ces corrections sont **précisément la matière du rapprochement
d'identités** : c'est parce qu'une même personne a été saisie deux fois, avec des variantes, qu'un
rapprochement probabiliste a un objet.

**La modification de fiche est mesurée, non supposée.** Sur les 25 842 patients distincts,
**3 265 portent plus d'une version** et 22 577 n'en portent qu'une ; le maximum observé est de deux
versions par fiche. Et ces versions diffèrent réellement : parmi les 3 265 fiches à deux versions,
l'adresse change dans 1 241 cas, le téléphone principal dans 976, la compagnie d'assurance dans 480,
l'état civil dans 367 et le type de patient dans 90.

## Décision

**La dimension patient est historisée par versions, avec bornes de validité semi-ouvertes et drapeau
de version courante**, plutôt qu'écrasée à chaque extraction.

Structure, lue dans le modèle :

```sql
    valide_de,
    lead(valide_de) over (partition by n_ipp order by valide_de) as valide_jusqu_a,
    lead(valide_de) over (partition by n_ipp order by valide_de) is null as est_courante
```

- `valide_de` vaut la date d'extraction de la version, et la borne est **incluse** ;
- `valide_jusqu_a` vaut la borne basse de la version suivante du même patient, et la borne est
  **exclue** ; elle reste vide pour la version la plus récente ;
- `est_courante` est vrai en l'absence de version suivante.

État mesuré : **29 107 lignes** pour **25 842 versions courantes**, soit exactement un identifiant
distinct par version courante.

## Justification des points non triviaux

### Le nombre de versions courantes n'est pas le nombre de lignes, et c'est la dépendance à citer

**Le rapprochement d'identités travaille sur les versions courantes, pas sur les lignes.** La
population qu'il extrait est filtrée sur le drapeau de version courante — c'est écrit dans
`linkage/population.py`, et l'agrégat des collisions exactes applique le même filtre.

La conséquence est chiffrée : le rapprochement porte sur **25 842 fiches** et non sur les 29 107
lignes de la dimension. Un traitement qui aurait pris les lignes sans filtrer aurait comparé une
fiche à sa propre version antérieure et compté 3 265 doublons parfaits qui n'en sont pas.

La mesure le confirme en aval : la table des grappes d'identité porte 25 842 lignes pour 25 842
identifiants distincts, et 5 014 paires candidates ont été évaluées.

### Pourquoi des bornes semi-ouvertes

La borne haute exclue est ce qui permet à deux versions consécutives de **se toucher sans se
chevaucher ni laisser de trou**. Trois contrôles de la couche de transformation le tiennent :
continuité, non-chevauchement, et unicité de la version courante par patient.

Le choix aligne en outre l'entrepôt sur la sémantique du générateur, qui retient la dernière version
dont la date d'extraction précède ou égale le jour considéré — le motif détaillé est consigné par
`docs/decisions/0021-dim-patient-scd2.md`, qui porte la mise en œuvre.

### Ce qui n'est pas historisé, et pourquoi ce n'est pas une omission

Les cinq autres dimensions ne portent que leur clé naturelle et n'ont donc pas d'attribut à
historiser. Aucune décision n'a eu à être prise pour elles.

## Conséquences

Toute lecture aval d'une colonne patient modifiable doit choisir **quelle version lire**. La règle
retenue est la version en vigueur à la date de l'événement, et elle est portée par
`docs/decisions/0017-version-en-vigueur-a-la-date-de-levenement.md` ; les six faits rattachent
d'ailleurs chacun leur ligne à une version précise, par un couple d'identifiant et de borne basse.

Le décompte de collisions exactes affiché au tableau de bord porte sur les versions courantes, et
son entrée au registre le dit.

## Ce qui aurait invalidé cette décision

**L'absence de modification de fiche dans les données** : si chaque patient n'avait qu'une version,
l'historisation serait une mécanique sans objet, coûteuse à maintenir et à expliquer.

Cette condition a été remesurée pour cet enregistrement, et elle n'est pas remplie : **3 265 fiches
sur 25 842, soit 12,6 %, portent deux versions**, et les colonnes qui changent entre elles sont
nommées et comptées ci-dessus.

## Sources

`docs/decisions/0017-version-en-vigueur-a-la-date-de-levenement.md` — quelle version lisent les
traitements aval.
`docs/decisions/0021-dim-patient-scd2.md` — la mise en œuvre des bornes et son alignement sur la
sémantique du générateur.
`docs/decisions/0023-grain-des-tables-de-faits-et-rattachement-patient.md` — le rattachement de
chaque fait à une version de patient.
`docs/decisions/0034-metrique-primaire-paire-secondaire-grappe.md` — la métrique du rapprochement.
