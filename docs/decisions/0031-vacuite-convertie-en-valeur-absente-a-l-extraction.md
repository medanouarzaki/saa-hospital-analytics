# ADR 0031 — La vacuité est convertie en valeur absente à l'extraction

**Statut.** Accepté.

---

## Contexte

L'égalité SQL est vraie entre deux chaînes vides. Une règle de blocage portant sur un champ
vide apparie donc toutes les fiches vides entre elles, quel que soit le champ. Mesure
(`linkage/population.py`) : 268 fiches courantes portent la valeur vide sur le champ pièce
d'identité, soit 268 × 267 ÷ 2 = 35 778 paires fantômes qu'un blocage naïf sur ce champ
produirait.

## Décision

Toute chaîne vide, dans les colonnes comparées et leurs colonnes normalisées, est convertie en
valeur absente (`None`) au moment de l'extraction de la population
(`linkage.population.extraire_population`, fonction `_convertir_vides_en_manquant`) — jamais
au stockage. L'égalité SQL n'est en revanche jamais vraie entre deux valeurs absentes, la forme
attendue par les niveaux « valeur manquante » du modèle de rapprochement (`NullLevel`).

## Justification des points non triviaux

### Pourquoi la conversion se fait à l'extraction et pas au stockage

`marts.dim_patient` conserve la chaîne vide telle qu'elle existe dans la couche source, sans
distinction avec une valeur réellement absente à ce niveau — une distinction que d'autres
lecteurs de `marts.dim_patient` peuvent vouloir observer autrement. Convertir au stockage
imposerait cette interprétation à tout consommateur de la table, y compris ceux qui n'ont pas
le problème du blocage sur champ vide. La conversion reste donc locale au module qui en a
besoin.

## Conséquences

La distinction entre vide et absent devient une propriété du module d'extraction du
rapprochement, pas une propriété du stockage : un lecteur direct de `marts.dim_patient`, hors
du module de rapprochement, voit toujours la chaîne vide d'origine. Toute nouvelle colonne
comparée introduite dans le rapprochement doit être ajoutée à l'ensemble des colonnes
convertibles en manquant, faute de quoi elle reproduit le même risque de bloc géant sur valeur
vide sans qu'aucun test ne le signale automatiquement.

## Ce qui aurait invalidé cette décision

Un besoin futur de distinguer, à l'intérieur même du rapprochement, une fiche à champ
réellement absent d'une fiche à champ vide (par exemple pour pondérer différemment ces deux
cas) romprait l'hypothèse que les deux se traitent de façon identique une fois converties — à
réévaluer si un tel besoin apparaît.

## Sources

`linkage/population.py::_convertir_vides_en_manquant`, `::extraire_population`.
