# ADR 0084 — Le thème, le bandeau et la locale du tableau de bord

**Statut.** Accepté.

---

## Contexte

Le tableau de bord devait être photographié pour le rapport. Trois choses l'en empêchaient.

**Aucun fichier de configuration d'application n'existait** — ni `.streamlit/config.toml` au dépôt,
ni variable d'environnement, ni drapeau de ligne de commande. Le thème suivait donc la préférence du
navigateur : la même page rendait claire ou sombre selon la machine qui l'ouvrait.

**Le bandeau de développement** — bouton de déploiement et menu — s'affichait en haut à droite de
chaque page.

**Les mois s'affichaient en anglais** dans une application française.

## Décision

### 1. Un fichier de configuration unique et versionné

`.streamlit/config.toml`, à la racine du dépôt :

```toml
[theme]
base = "light"

[client]
toolbarMode = "minimal"
```

L'option est **lue et citée**, non supposée. La bibliothèque énumère elle-même ses sources par ordre
de précédence croissante : « 1. default values defined in this file / 2. the global
~/.streamlit/config.toml file / 3. per-project $CWD/.streamlit/config.toml files / 4. environment
variables such as STREAMLIT_SERVER_PORT / 5. command line flags ». Le répertoire de travail de
l'image étant `/app`, ce fichier occupe le rang 3.

`minimal` est retenu plutôt que `viewer` : `viewer` retire le bouton de déploiement mais laisse le
menu ; `minimal` retire l'un et l'autre.

Aucune variable d'environnement ne double ces deux réglages, ni dans la composition, ni ailleurs.

### 2. Une ligne de copie dans le Dockerfile

`docker/dashboard.Dockerfile` reçoit `COPY .streamlit/ .streamlit/`. Sans elle, le fichier versionné
n'atteint jamais l'image livrée : le service ne porte **aucun montage** — `docker inspect` rend
`Mounts: []` —, si bien que tout ce que le conteneur voit vient des couches de l'image.

Mesuré à l'intérieur du conteneur, avec la source de chaque valeur :

```
theme.base         = 'light'    (source : /app/.streamlit/config.toml)
client.toolbarMode = 'minimal'  (source : /app/.streamlit/config.toml)
```

### 3. Les étiquettes de date en français, par le tracé et non par la bibliothèque

**La bibliothèque n'expose aucune option de locale ni de format** : l'énumération de ses options ne
rend, sur ces deux mots, que `logger.messageFormat`. Le français ne pouvait donc venir que du tracé.

`dashboard/rendu.py` reçoit `tracer_temporel`, qui compose une spécification Vega-Lite portant un
`labelExpr` sur douze mois abrégés français, et rend l'étiquette sur deux lignes — le mois, puis
l'année —, forme que le moteur emploie lui-même pour un axe de temps.

**Aucune dépendance nouvelle.** Le tracé passe par `st.vega_lite_chart`, qui prend un dictionnaire.
Importer `altair` aurait été plus direct, mais `altair` n'est qu'une dépendance transitive de la
bibliothèque d'affichage : l'employer directement aurait créé un usage non déclaré.

**Les 23 tracés ont été examinés un par un, par leur abscisse.** Cinq portaient une date et sont
convertis — `activite` ×2, `urgences`, `facturation`, `sejours`. Les dix-huit autres ont une
abscisse catégorielle ou numérique et ne sont pas touchés.

## Conséquences

**La vérification porte sur le conteneur, jamais sur une exécution locale.** Image reconstruite,
pile montée, neuf pages ouvertes au navigateur, celui-ci **réglé pour préférer le sombre** : c'est le
seul réglage qui discrimine, une page qui reste claire alors que le navigateur demande du sombre
l'étant par la configuration livrée et par rien d'autre. Les neuf pages rendent un fond
`rgb(255,255,255)`, sans bouton de déploiement ni menu, et les cinq tracés temporels portent des
étiquettes françaises.

**La mutation le confirme dans les deux sens.** La ligne de copie retirée et l'image reconstruite,
`/app/.streamlit` n'existe plus, le fond redevient `rgb(14,17,23)` et le bandeau reparaît ; la ligne
restaurée et l'image reconstruite, le fond redevient blanc et le bandeau disparaît. Les six autres
voies par lesquelles le thème aurait pu être clair sans cette ligne — montage, configuration
globale, variable d'environnement, drapeau de ligne de commande, préférence du navigateur, cache de
construction — ont été mesurées et fermées une à une avant la mutation.

**Rien ne garantit qu'un tracé temporel futur passera par `tracer_temporel`** plutôt que par l'appel
intégré. Écrire ce contrôle demanderait d'ouvrir `tests/`, hors de la liste fermée de ce travail.
C'est une dette, et elle est écrite.

**Deux défauts constatés et non corrigés**, parce qu'ils débordent l'objet : les nombres des axes
gardent le séparateur anglais — `4,000,000` au lieu de `4 000 000` —, et la légende des tracés à
plusieurs mesures affiche les noms de colonnes bruts. Ce second défaut est antérieur : les tracés
intégrés faisaient déjà ainsi.
