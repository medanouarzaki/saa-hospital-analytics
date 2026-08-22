# ADR 0093 — La présentation reprise : une ouverture, un bloc technique, et une commande réemployée

**Statut.** Accepté.

---

## Contexte

Le support de soutenance entrait dans le sujet à la deuxième planche, montrait presque rien du
travail d'ingénierie — l'architecture y occupait **une** planche sur vingt et une — et sa planche de
titre ne portait pas les deux logotypes institutionnels que la page de garde du rapport porte.

## Décision

### 1. Les deux logotypes viennent de la commande du rapport, réemployée et non réécrite

**Elle n'était pas atteignable, et c'est mesuré et non supposé.** `\IfFileExists` cherche depuis le
répertoire de composition et **n'honore pas `\graphicspath`** : un document d'essai composé depuis
`slides/`, portant `\graphicspath{{../report/}}` et appelant `\logosInstitutionnels`, compose les
deux **cadres d'attente** et non les logotypes — la recherche de fichier échoue là où l'inclusion
aurait réussi.

`report/images.tex` déclare donc une racine de figures, **vide chez lui**, que le support redéfinit.
Le rapport ne s'en aperçoit pas : 98 pages, 22 boîtes, page de garde inchangée.

Écrire une seconde commande dans le support aurait donné deux vérités qui divergeraient — l'une
portant l'égalisation sur l'encre composée et l'alignement des médianes, l'autre les recopiant
jusqu'au jour où l'une des deux serait corrigée seule.

### 2. Quatre planches d'ouverture, avant tout le reste

Un jury qui ne connaît ni l'hôpital, ni le service, ni le logiciel était perdu à la deuxième
planche.

**Où j'étais** — le service, et ce qu'il fait, un geste par ligne : ouvrir un dossier, donner des
rendez-vous, admettre, orienter, facturer. **Ce que ce service produit sans le savoir** — chaque
geste laisse une trace, les traces s'accumulent, et la cinquième des neuf missions du règlement est
d'établir les statistiques. **Le problème, en une phrase** — entre les données saisies et les
indicateurs attendus, il manque un chemin. **Ce que je vais montrer** — quatre étapes en quatre
blocs, qui servent de fil.

### 3. Cinq planches techniques

C'était le défaut le plus sérieux. **La chaîne couche par couche** — ce que chacune reçoit, produit,
et pourquoi elle existe. **Les onze tables et le schéma en étoile** — défini avant d'être montré.
**La dimension historisée sur un exemple** — un changement de couverture, et une facture de février
qui ne doit pas se relire avec la couverture d'aujourd'hui. **L'orchestration quotidienne** —
l'idempotence et le rattrapage, dits par l'exemple et jamais par leur définition. **La
vérification** — et la doctrine qui est le meilleur résultat de méthode du projet : *une mutation
restée verte révèle presque toujours un contrôle défectueux, et non un code correct.*

### 4. Chaque terme technique reçoit une phrase, et une seule

Onze termes, chacun expliqué en français simple à sa première apparition : quarantaine, instantané,
schéma en étoile, dimension historisée, orchestration, idempotence, rattrapage, rapprochement
probabiliste, blocage, poids de correspondance, ablation.

**Le fil reste visible** : chaque planche porte en sous-titre, en gris et en petit, celle des quatre
étapes à laquelle elle appartient. Les quatre planches d'ouverture n'en portent pas — elles
précèdent le fil.

## Conséquences

Le support passe de **21 à 30 planches**, avec **zéro boîte débordante**. Le rapport reste à 98
pages et 22 boîtes.

**Une commande a dû être renommée, et le contrôle avait raison de mordre.** Le fil s'appelait
`\etape`, et `test_aucune_numerotation_interne` a rougi sur vingt-cinq emplois : son motif interdit
le mot « étape » suivi d'un chiffre, parce que c'est la forme d'une numérotation de travail. Le
contrôle ne peut pas distinguer une étape de processus d'une étape du propos ; la commande s'appelle
donc `\filDuPropos`, et les quatre étapes gardent leurs numéros dans le texte qu'elles composent.

**La déclaration de chiffres du support a été refaite**, deux identifiants neufs y étant appelés.

**La remesure du registre rend zéro écart**, et aucune entrée n'a eu à être ajoutée : les quatre
valeurs neuves appelées par les planches techniques existaient déjà.
