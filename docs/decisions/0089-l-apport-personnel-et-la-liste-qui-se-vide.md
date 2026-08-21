# ADR 0089 — L'apport personnel, et la liste des emplacements qui se vide

**Statut.** Accepté.

---

## Contexte

Le rapport portait un dernier emplacement de rédaction personnelle, à la fin de la conclusion :
`\aRediger{apport-personnel}{...}`, une boîte encadrée visible à la compilation. L'auteur a fourni
et validé le texte qui devait y prendre place.

## Décision

### 1. Le texte est écrit tel quel

Il vient de l'auteur et n'a reçu que sa mise en forme : un `\section*{Apport personnel}` au lieu de
la boîte encadrée, la coupure des paragraphes, et le report du marqueur d'observation
`\releve{apport-personnel}` sur la première phrase — c'est lui qui rattache ce paragraphe à sa
provenance, et l'en-tête du chapitre continue de le déclarer.

Rien n'y a été ajouté, rien n'en a été retiré, aucun fait n'y a été inventé.

### 2. La liste des emplacements attendus se vide, et c'est une écriture hors liste fermée

**Ce point est signalé, non caché.** `tests/test_provenance_des_chapitres.py` n'était pas dans la
liste fermée de ce travail. Une ligne y a pourtant changé :

```python
EMPLACEMENTS_ATTENDUS: tuple[str, ...] = ()
```

Le motif est mécanique et sans échappatoire. Le contrôle confronte la liste déclarée aux fichiers
**dans les deux sens** : écrire le paragraphe sans vider la liste est rouge, tout comme ajouter un
emplacement sans le déclarer. Écrire le texte et ne pas toucher à la liste rendait donc
l'intégration continue rouge, et interdisait la publication.

Le contrôle demande lui-même ce geste, dans son message d'échec — « s'ils ont été écrits, retirez-les
de `EMPLACEMENTS_ATTENDUS` » — et dans son commentaire d'en-tête : « Elle se vide à mesure que le
rapport s'écrit, et le jour où elle est vide, plus aucun paragraphe n'attend. » Ce jour est celui-ci.

La propriété ne s'affaiblit pas : la liste vide reste confrontée aux fichiers, et **ajouter un
emplacement sans le déclarer reste rouge**.

## Conséquences

Le document passe de **97 à 98 pages**, et garde **22 boîtes débordantes**. La boîte encadrée « À
rédiger » disparaît : plus aucune marque de ce genre ne subsiste au document composé.

**Les deux nombres écrits en toutes lettres sont justes.** « Onze tables » : le registre porte
`source-tables` à 11. « Deux ans et demi » : le registre porte `periode-jours` à 912, soit 2,497
années — deux ans et demi valent 913 jours, l'écart est d'un jour. Les nombres en lettres échappent
au registre, et c'est la voie par laquelle deux décomptes du projet sont devenus faux ; ceux-ci ont
donc été vérifiés contre lui plutôt que crus.

**Deux formules du texte reprennent mot pour mot une phrase déjà employée ailleurs, et les deux le
font à bon droit.** « Un champ renseigné n'est pas un champ juste » énonce au chapitre du système
d'information la quatrième observation exploitable ; l'apport personnel raconte le moment où l'auteur
y est arrivé, ce qui n'est pas la même chose que la répéter. « En fin de projet alors qu'elle devait
être répartie » reprend l'aveu de méthode du chapitre de cadrage. Aucune autre suite de sept mots du
texte ne se retrouve ailleurs dans le rapport.

**Le téléphone inventé est raconté, non renvoyé.** Il apparaît par renvoi dans quatre chapitres —
conception, système d'information, qualité, recommandations. Ici il n'y a ni `\ref`, ni renvoi de
chapitre : la scène est décrite au poste d'accueil, et c'est un témoignage.
