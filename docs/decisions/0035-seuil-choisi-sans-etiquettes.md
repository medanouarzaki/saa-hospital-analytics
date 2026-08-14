# ADR 0035 — Le seuil se choisit sur des propriétés observables sans étiquettes

**Statut.** Accepté.

---

## Contexte

La vérité terrain — la liste des paires réellement doublonnées — existe dans ce projet, produite
par le générateur de données synthétiques. Elle n'existerait pas de la même façon en production :
un déploiement réel n'a pas accès à un étiquetage exhaustif de ses propres doublons au moment
de choisir un seuil de décision.

## Décision

Le seuil de probabilité utilisé pour la décision de rapprochement est choisi sur des propriétés
lisibles sans étiquettes de vérité terrain (la forme de la distribution des poids de
correspondance produite par le modèle), puis évalué a posteriori contre la vérité terrain
disponible ici — jamais l'inverse. Seuil retenu : 0,5 (`linkage/evaluation.py`,
`SEUIL_PROBABILITE`). À ce seuil, sur les 991 paires de vérité terrain présentes, précision et
rappel valent tous deux 1,0 (`linkage/courbe_precision_rappel.csv`, ligne `seuil_probabilite=0.5`
: `vrais_positifs=991, faux_positifs=0, faux_negatifs=0`).

## Justification des points non triviaux

### Pourquoi calibrer sur la vérité terrain serait ajuster sur la réponse

Le balayage de seuils (`linkage/courbe_precision_rappel.csv`) montre que le poids minimal des
paires de vérité terrain, dans le modèle complet, se situe loin au-dessus du poids maximal des
paires hors vérité terrain (`docs/decisions/0033-niveau-absence-unilaterale-piece-identite-conserve.md`,
marge de +270,87 unités de poids). Calibrer le seuil exactement au ras de ce minimum
produirait un chiffre de précision et de rappel parfait sur ce jeu de données précis, par
construction — puisque le seuil aurait été choisi en connaissant déjà la réponse qu'il doit
produire. Ce chiffre ne vaudrait alors que sur ce jeu : il ne dirait rien de la capacité du
seuil à généraliser à des données où la séparation entre les deux populations de poids ne
serait pas aussi nette.

## Conséquences

Le seuil de 0,5 n'est pas optimisé pour maximiser la f-mesure sur ce jeu précis — il se trouve
être optimal ici parce que la marge de séparation mesurée est large, pas parce qu'il a été
choisi pour l'être. Sa transférabilité à des données réelles reste non démontrée : la propriété
qui le justifie (une distribution de poids nettement bimodale) n'est vérifiable qu'après coup,
sur les mêmes données synthétiques dont l'injection de défauts est elle-même en question
(`docs/decisions/0033-niveau-absence-unilaterale-piece-identite-conserve.md`). Un déploiement
sur des données réelles devrait revérifier que cette même bimodalité s'observe avant de retenir
le même seuil, sans pouvoir s'appuyer sur une vérité terrain complète pour le confirmer.

## Ce qui aurait invalidé cette décision

Une distribution de poids de correspondance qui, sur un jeu de données futur, ne présenterait
pas de séparation nette entre deux populations lisible sans étiquettes rendrait le choix du
seuil à 0,5 arbitraire plutôt que fondé — à re-mesurer avant tout déploiement sur des données
dont la structure de bruit diffère substantiellement du jeu synthétique actuel.

## Sources

`linkage/evaluation.py` (`SEUIL_PROBABILITE`, fonction `composantes_connexes`) ;
`linkage/courbe_precision_rappel.csv` ;
`docs/decisions/0033-niveau-absence-unilaterale-piece-identite-conserve.md`.
