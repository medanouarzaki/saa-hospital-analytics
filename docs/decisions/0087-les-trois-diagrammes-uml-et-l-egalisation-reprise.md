# ADR 0087 — Les trois diagrammes UML, et une égalisation que le rendu a reprise

**Statut.** Accepté.

---

## Contexte

Trois choses manquaient au rapport, et deux étaient fausses.

**La déclaration de rapport de la capture reprise était périmée.** La capture de la page
« Activité » avait été reprise après la mise en français des étiquettes de date ; le fichier
mesurait désormais 3386×1698 pixels, quand `\declarerCapture{page-activite}` portait encore la
valeur mesurée sur la capture précédente.

**Les deux hauteurs de logotype venaient d'un fichier qui n'existe plus.** Le logotype du HCP a été
redéposé en 450×88 pixels, là où le précédent faisait 3790×1088. Les hauteurs déclarées, mesurées
sur l'ancien, composaient 86,3 mm d'encre pour le HCP contre 15,2 mm pour l'INSEA.

**Le rapport ne portait aucun diagramme.** Six figures composées, aucune vue de structure.

## Décision

### 1. La déclaration de la capture suit le fichier

`0.40724` devient `0.50148`, soit 1698/3386. Les trois captures composent désormais à la même
largeur — 147,3, 147,1 et 147,2 mm pour `0.92\linewidth` —, contre 119,6 mm pour la première avant
la correction.

### 2. Le logotype du HCP est accepté tel quel, et l'égalisation se refait sur lui

**Le rognage et la définition sont des arbitrages rendus, non des défauts tolérés.** L'emblème du
fichier redéposé mesure 99 pixels de large pour 88 de haut, quand un cercle en ferait 99 des deux
côtés : il est tranché en haut et en bas. Et 450 pixels composés sur 60 mm ne font que 189 points
par pouce. L'auteur retient le fichier ainsi.

**La conséquence sur l'égalisation est écrite : l'encre tranchée n'est pas comptée**, et
l'égalisation sous-estime donc le poids de ce logotype de quelques pour cent. C'est un moindre mal :
les hauteurs de l'ancien fichier appliquées au nouveau donnaient un rapport de cinq à un.

| fichier | dimensions | boîte utile | encre pondérée | hauteur déclarée | médiane d'encre composée |
|---|---|---|---|---|---|
| `INSEA-logo.png` | 1200×1304 | 983×1110 | 582 198 px | **20,00 mm** | 42,86 mm |
| `HCP-logo.png` | 450×88 | 441×88 | 5 195 px | **11,81 mm** | 42,90 mm |

**La mesure est pondérée par l'opacité, non seuillée** : les deux concordent à 1 %, mais à 450
pixels de large la part des pixels de bord partiellement opaques n'est plus négligeable, et un seuil
les jette tous du même côté.

**LE RENDU A DÉMENTI LE CALCUL, ET C'EST LE RENDU QUI A TRANCHÉ.** L'égalisation sur l'encre du
FICHIER donnait 14,29 mm. Composée à cette hauteur, l'encre du HCP couvrait 224 mm² sur la page
contre 142 pour l'INSEA : une fois et demie de trop, visible à l'œil nu. Le motif est mesurable — un
fichier de 450 pixels agrandi jusqu'à 60 mm voit chacun de ses pixels en devenir près de deux, et
ses traits fins s'épaissir d'un tiers, quand la marque pleine de l'INSEA, déjà à 1200 pixels, ne
gagne rien. **L'égalisation porte donc sur l'encre COMPOSÉE**, relevée sur l'image du PDF à 300
points par pouce — la résolution à laquelle l'œil lit une feuille à distance de lecture. Elle donne
11,81 mm, et le relevé confirme : 142,4 mm² contre 152,9, sept pour cent d'écart. C'est la seconde
fois qu'un rendu corrige un calcul d'égalisation sur cette page ; la première, la boîte utile
donnait 8,6 mm et la marque y disparaissait.

### 3. Trois diagrammes UML, composés en TikZ

Pas de générateur externe, pas d'image : `pgfplots` charge déjà TikZ, et une septième figure
technique aurait été une dépendance de plus et un fichier qu'aucune comparaison de versions ne sait
lire. Les six bibliothèques nécessaires sont **mesurées dans l'image de composition** —
`ghcr.io/xu-cheng/texlive-alpine:latest`, TeX Live 2026, `Package: pgf 2025-08-29` — par un document
d'essai qui y compose sans erreur.

**Cas d'utilisation**, au chapitre du système d'information : les neuf missions de l'article 35 du
règlement intérieur, reproduites dans les termes du texte, et les cinq profils applicatifs sous leur
libellé exact. Quatre missions reçoivent un profil, **cinq n'en reçoivent aucun et restent visibles
sans lien**, et le profil de recouvrement est posé à l'écart : le recouvrement ne figure pas à
l'article 35.

**Classes du domaine**, au chapitre de conception : les neuf entités et leurs cardinalités. Le
diagramme existe pour rendre visible ce que trois documents de travail de ce projet ont confondu —
personne, identifiant et version sont trois grandeurs, non deux —, et les cardinalités le disent
sans commentaire : une personne porte un ou plusieurs identifiants, un identifiant une ou plusieurs
versions.

**Séquence**, au chapitre de l'architecture : les douze tâches du graphe quotidien dans leur ordre,
entre les six participants réels. Deux traits que la prose dit mal y deviennent visibles — les
dimensions se construisent avant les faits, et le rafraîchissement de l'instantané est une
substitution en une seule transaction.

**Aucun nombre n'est tapé dans un diagramme.** Aucune valeur mesurée n'y figure : ce sont des vues
de structure, et le registre des chiffres n'a rien à leur fournir.

## Conséquences

Le document passe de **95 à 98 pages**, une par diagramme, et garde **22 boîtes débordantes**. Les
trois diagrammes composent à 154,2, 127,7 et 140,2 mm pour un bloc de texte de 160 mm : aucun n'a eu
à être resserré ni tourné en paysage.

`report/rapport.tex` reçoit une ligne, `\usetikzlibrary`, et rien d'autre.

**Un défaut est signalé, hors liste fermée et non corrigé.** Le tableau du chapitre premier range
« Recouvrer les sommes dues à l'hôpital » parmi les missions que l'article 35 prescrit au service.
Le texte de l'article, lu intégralement pour composer le diagramme, ne la porte pas : le recouvrement
relève de l'article 9, paragraphe b, qui en charge le pôle des affaires administratives — ce que
`docs/modules_non_observes.md` disait déjà. Le diagramme ne reprend pas l'erreur ; le tableau du
chapitre premier la porte encore, et `report/chapitres/organisme-d-accueil.tex` n'était pas dans la
liste fermée de ce travail.

**La définition du logotype du HCP reste une dette déclarée** : 189 points par pouce à la hauteur
composée, contre 584 pour les captures.
