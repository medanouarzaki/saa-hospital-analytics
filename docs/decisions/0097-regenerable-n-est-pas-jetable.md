# ADR 0097 — Régénérable n'est pas jetable

**Statut.** Accepté.

---

## Contexte

Un nettoyage du disque a supprimé `generator/output/`, classé « régénérable à l'identique » par la
mesure qui l'avait précédé. La commande qui le reproduit était nommée, l'identité de la reproduction
était vérifiable. Le classement paraissait complet.

La remesure du registre a échoué aussitôt après :

```
FileNotFoundError: [Errno 2] No such file or directory:
'…/generator/output/scenario_30/verite_terrain.yml'
```

## Décision

### `generator/output/` est une dépendance de la vérification du registre

**Une entrée sur 267 le lit** : `vt-paires-injectees`, les paires de doublons **injectées par le
générateur avant tout chargement**. Cette grandeur n'existe dans aucune couche de la base — la
quarantaine en écarte cinq au chargement, et la base ne porte donc que les 991 présentes, jamais les
996 injectées. Seul le fichier de vérité terrain la donne.

`docs/chiffres/mesurer.py --verifier` ne peut pas rendre zéro écart sans ce répertoire.

### Le répertoire reste supprimable, et la régénération reste vérifiable

Rien de ce qui précède n'en fait un fichier à conserver. Il se supprime sans risque et se régénère
par la commande du fichier d'accueil :

```bash
uv run python -m generator generator/output      # mesuré : 1 min 12
```

Et l'identité de la régénération **se démontre plutôt qu'elle ne se suppose** :
`generator/output/manifeste.yml` porte une empreinte SHA-256 par fichier produit et aucun horodatage.
Confrontation faite après régénération : **18 956 fichiers, 18 956 identiques, zéro différent, zéro
manquant.**

### CE QUE CE PROJET RETIENT : RÉGÉNÉRABLE ET JETABLE NE SONT PAS LA MÊME CHOSE

Un répertoire peut être parfaitement reproductible **et** être une entrée d'une vérification. Son
gain de place est alors nul : il revient dès que la vérification doit tourner.

**Un classement qui range un répertoire en « régénérable » sans dire CE QUI EN DÉPEND est
incomplet.** La question à poser n'est pas « une commande le reproduit-elle ? » mais « qui le lit, et
quand ? ».

## Deux autres erreurs de mesure du même nettoyage

Elles se reproduiront au prochain, et elles sont écrites pour cela.

**La colonne de taille unique sous-estime une suppression groupée.** Quatre images de conteneur
déclaraient 867 kio de taille unique à elles quatre ; leur suppression en a libéré **1,151 Go**. La
colonne compte une couche comme partagée **sans dire avec qui** : une couche partagée entre plusieurs
images qu'on supprime ensemble est libérée, alors qu'elle n'était comptée unique pour aucune. Le
décompte fiable est la différence des totaux avant et après, pas la somme des tailles uniques.

**Une annonce faite sur un total de répertoire compte ce qu'on avait décidé de garder.** Les sorties
LaTeX intermédiaires étaient annoncées à 2,2 Mio ; elles pèsent **448 Kio**. Le total mesuré incluait
les deux PDF, c'est-à-dire précisément les fichiers que la même ligne ordonnait d'épargner.

## Conséquences

Une ligne est ajoutée au relevé des critères : **la régénération du jeu engendré est due avant toute
remesure du registre, au même titre que la remesure est due avant toute remise.**
