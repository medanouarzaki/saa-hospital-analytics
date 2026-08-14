# ADR 0033 — Le niveau d'absence unilatérale de la pièce d'identité est conservé

**Statut.** Accepté.

---

## Contexte

La comparaison composite « pièce d'identité » du modèle de rapprochement porte un niveau
« manquant d'au moins un côté » (`linkage/modele_estime.json`, comparaison `piece_identite`).
Mesure : ce niveau porte un facteur de Bayes de 20,25 (`m_probability` ÷ `u_probability` =
0,3272450532643204 ÷ 0,01616399795276742), une information réelle et non négligeable dans le
modèle estimé. Mais ce facteur est un artefact du mode d'injection des défauts par le
générateur de données synthétiques, pas une propriété observée du monde réel : l'absence
unilatérale de pièce d'identité y est corrélée au fait d'être un doublon injecté d'une façon
qui ne se généraliserait pas nécessairement à une extraction réelle.

## Décision

Le niveau est conservé dans le modèle. Son coût — la dépendance du modèle à ce mode
d'injection plutôt qu'à une propriété générale des identités — est mesuré par une étude
d'ablation, pas seulement supposé ou écarté par précaution.

Mesure de l'ablation (`linkage/ablation.csv`) : retirer les six champs recopiés verbatim par le
générateur entre fiche source et doublon injecté (`nom_famille_1`, `nom_famille_2`, `nom_mere`,
`nom_pere`, `quartier`, `ville`) fait passer la marge de séparation entre le poids de
correspondance maximal des paires hors vérité terrain et le poids minimal des paires de vérité
terrain de +270,87 à −2,66 unités de poids de correspondance — les deux populations de poids se
recouvrant désormais, alors qu'elles étaient nettement séparées dans le modèle complet.

## Justification des points non triviaux

### Ce que l'ablation mesure, et ce qu'elle ne mesure pas

L'ablation retire des champs de la comparaison mais laisse les règles de blocage identiques :
l'ensemble des paires candidates soumises au modèle ne change pas entre la variante complète et
la variante sans les six champs recopiés. Elle chiffre donc l'effet de la perte de ces champs
sur la séparation des poids de correspondance à l'intérieur d'un ensemble candidat déjà
constitué — pas l'effet de leur perte sur la constitution de cet ensemble candidat lui-même.
Deux des quatre règles de blocage retenues (`docs/decisions/0030-quatre-regles-de-blocage.md`)
s'appuient sur `nom_famille_1` ou sur `nom_pere`/`nom_mere` : leur perte réduirait aussi le
rappel du blocage, un effet distinct et vraisemblablement plus sévère, que cette ablation ne
chiffre pas.

## Conséquences

Le modèle reste dépendant d'un signal (l'absence unilatérale de pièce d'identité) dont la
validité hors du contexte de génération synthétique n'est pas établie. Toute évolution du
générateur qui changerait la façon dont les défauts d'identité sont injectés invaliderait le
facteur de Bayes mesuré ici, sans qu'un test actuel ne le détecte automatiquement — seule une
nouvelle exécution de l'estimation le referait apparaître.

## Ce qui aurait invalidé cette décision

Une mesure de l'effet du retrait des six champs recopiés sur le rappel du blocage lui-même
(plutôt que sur la seule séparation des poids à ensemble candidat fixé), si elle s'avérait plus
sévère que la dégradation observée sur la marge de séparation, renforcerait l'argument pour
retirer ce niveau plutôt que de le conserver — mesure non conduite ici, signalée comme manquante
plutôt que supposée.

## Sources

`linkage/modele_estime.json` (comparaison `piece_identite`, niveau « manquant d'au moins un
côté ») ; `linkage/ablation.csv` (lignes `complet` et `A_sans_champs_recopies`) ;
`docs/decisions/0030-quatre-regles-de-blocage.md`.
