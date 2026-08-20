# ADR 0067 — La personne, l'identifiant et la version sont trois grandeurs, et le registre des chiffres portait la confusion

**Statut.** Accepté, et appliqué au registre des chiffres et aux chapitres qui l'emploient.

---

## Contexte

Le registre des chiffres a été créé pour empêcher qu'un nombre circule sans être rattaché à la
commande qui le produit. Son enregistrement fondateur cite cinq valeurs fausses qui avaient circulé
faute d'un tel rattachement, dont l'une était **un décompte de personnes confondu avec un décompte
d'identifiants**.

**Ce registre portait lui-même cette confusion.** Une entrée nommée `personnes-distinctes`, d'unité
« personnes », portait la valeur 25 842, produite par la commande :

```sql
select count(*) from marts.dim_patient where est_courante
```

Cette commande compte les **versions courantes** de la dimension patient, soit exactement un
enregistrement par **identifiant** distinct. Elle ne compte pas des personnes. Le jeu de données
injecte délibérément des doublons d'identité : une même personne peut porter deux identifiants, et
c'est même l'objet du chapitre sur le rapprochement.

L'entrée portait une note avertissant de ne pas la confondre avec le décompte de fiches. La note
était juste et insuffisante : elle protégeait d'une confusion et en commettait une autre.

## La mesure

Trois grandeurs distinctes, et non deux :

| Grandeur | Commande | Valeur |
|---|---|---|
| **versions** de fiche | `select count(*) from marts.dim_patient` | 29 107 |
| **identifiants** distincts | `select count(distinct n_ipp) from marts.dim_patient` | 25 842 |
| **personnes** estimées | `select count(distinct grappe_id) from linkage.grappes_identite` | 24 851 |

L'écart entre les deux dernières est mesuré et s'explique : 991 grappes réunissent plus d'un
identifiant, et 24 851 + 991 = 25 842.

## Décision

**Le registre porte trois entrées, chacune avec une note qui renvoie explicitement aux deux
autres.** L'entrée fautive est renommée `versions-de-fiches`, son unité corrigée, et sa note dit ce
qu'elle était et pourquoi c'était faux — le rapport ne l'emploie plus, et elle porte donc un motif de
non-emploi.

**Le chapitre qui l'employait est corrigé.** Il affirmait « tant de fiches pour tant de personnes » ;
il énonce désormais les trois grandeurs, avec l'écart et sa cause.

## Justification des points non triviaux

**Pourquoi conserver l'entrée fautive au lieu de la supprimer.** Sa commande mesure quelque chose de
réel — les lignes de version courante — et cette grandeur coïncide aujourd'hui avec le nombre
d'identifiants distincts *parce que* trois contrôles imposent qu'un identifiant porte une version
courante et une seule. La coïncidence cesserait si l'un de ces contrôles était retiré. Conserver
l'entrée avec son motif de non-emploi préserve cette information ; la supprimer l'effacerait.

**Pourquoi une note ne suffisait pas.** L'entrée fautive en portait une, et la confusion a passé.
Ce qui manquait n'était pas l'avertissement mais **le nom et l'unité** : `personnes-distinctes` avec
l'unité « personnes » affirme une nature, et une note en petits caractères ne corrige pas une
affirmation portée par le nom. Le nom et l'unité sont les deux champs qu'un lecteur pressé lit.

**Ce qui a détecté la faute.** Non pas un contrôle, mais la rédaction d'un chapitre qui devait
décrire la dimension historisée et a dû mesurer ses trois décomptes séparément. **Aucun appareil du
dépôt ne l'aurait trouvée** : la valeur était juste, sa commande la produisait bien, et toutes les
propriétés étaient vertes. C'est exactement la limite que l'enregistrement fondateur du registre
énonce — il établit qu'un nombre vient d'une commande, jamais que la commande mesure ce que la
phrase prétend.

## Conséquences

- Le registre porte trois entrées là où il en portait une, et la troisième — les personnes estimées
  — n'existait pas du tout auparavant.
- La mutation qui remplace 24 851 par 25 842 est désormais un témoin utile : elle rejoue exactement
  la confusion, et **seule la remesure locale la voit**, les propriétés hors base et le mode de
  l'intégration continue restant verts.
- Le chapitre sur la conception du jeu de données porte l'énoncé des trois grandeurs, et celui sur
  l'architecture le reprend pour la dimension historisée.

## Ce que cette décision ne règle pas

**Rien n'empêche la même faute de se reproduire sur une autre grandeur.** Le registre ne peut pas
vérifier qu'une unité décrit ce que sa commande mesure : c'est une correspondance entre un mot
français et une requête, et aucun motif textuel ne l'établit. La seule parade est celle qui a
fonctionné ici — écrire un chapitre qui oblige à mesurer séparément ce qu'on croyait identique.

## Sources

- `docs/chiffres/registre_chiffres.yml` — les trois entrées et leurs notes croisées.
- `docs/decisions/0066-le-registre-des-chiffres-et-ce-que-l-integration-continue-n-en-prouve-pas.md`
  — l'enregistrement fondateur, dont la rubrique finale annonçait précisément ce cas.
- `dbt/tests/dim_patient_une_version_courante.sql` — le contrôle dont dépend la coïncidence entre
  versions courantes et identifiants distincts.
