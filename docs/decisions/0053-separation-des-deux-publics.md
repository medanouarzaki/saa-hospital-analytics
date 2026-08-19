# ADR 0053 — Le tableau de bord se sépare en deux publics, et le classement se dérive de la décision servie

**Statut.** Accepté.

---

## Contexte

Le tableau de bord comptait huit pages et quarante indicateurs, présentés sur un pied d'égalité
dans une barre latérale unique. Deux publics y lisaient la même liste sans savoir lequel des deux
un écran donné visait.

**Trois mesures ont été prises avant d'écrire quoi que ce soit.**

**1. Six indicateurs sur quarante ne décrivent pas l'activité du service.** Le partage a été
DÉRIVÉ de la `decision_servie` que chaque entrée du registre déclare, jamais décrété. La règle est
unique :

> Un indicateur reste **opérationnel** si sa valeur peut changer une décision du service. Il passe
> en **méthode** s'il décrit la chaîne — sa performance, sa provenance, ses paramètres — et non
> l'activité.

Appliquée aux quarante décisions servies, elle donne **trente-quatre en pilotage et six en
méthode**. Aucune décision servie n'a manqué de trancher. Le cas le plus discutable est le délai
de prise en charge aux urgences — « Vérifier que le tri produit bien une priorisation » pourrait se
lire comme l'évaluation d'un mécanisme — mais le tri dont il s'agit est **une procédure du service,
exercée par ses infirmiers**, et la seconde moitié de la phrase le confirme : « repérer où la file
se forme ». Il reste en pilotage.

**2. Deux indicateurs sont nommés par le registre des relations injectées, et ce sont les deux
corrélations.** Les vingt et une entrées ont été parcourues, chacun de leurs champs confronté aux
quarante identifiants du registre des indicateurs. `R-01` nomme
`rendez_vous_delai_et_absence_intra_activite`, `R-21` nomme `rendez_vous_delai_et_absence` ; aucune
autre entrée ne nomme d'indicateur. Trois entrées emploient le mot « circulaire » — `R-15`, `R-20`,
`R-21` — mais les deux premières marquent circulaire *une recommandation du chapitre 9*, non un
chiffre affiché.

La règle classe ces deux indicateurs en méthode. **Aucun indicateur circulaire n'est classé
opérationnel** : la contradiction que le partage pouvait produire ne se présente pas.

**3. Le mécanisme de sections existe dans la version installée.** Lu dans sa signature :

```
navigation(pages: 'Sequence[PageType] | Mapping[SectionHeader, Sequence[PageType]]', *,
           position: "Literal['sidebar', 'hidden', 'top']" = 'sidebar', expanded: 'bool | int' = False)
```

Passer un dictionnaire fait de chaque clé l'intitulé d'une section. Aucune barre latérale seconde,
aucun mécanisme à écrire.

## Décision

**1. Une seule barre latérale, deux sections nommées par leur public** : « Pilotage du service » et
« Évaluation de la chaîne ». Les intitulés nomment le public et non le sujet — « Qualité » ou
« Technique » désigneraient un domaine et laisseraient un responsable de service se demander si la
seconde section le concerne.

**2. Chaque entrée du registre des indicateurs porte une `section`**, `pilotage` ou `methode`, et
aucune autre valeur. La règle de partage est écrite en tête du registre, et une troisième
réconciliation s'y ajoute : la somme des indicateurs des deux sections égale le nombre d'entrées,
chaque membre calculé de son côté.

**3. La composition suit le classement, et une page se scinde.** La page de rapprochement portait
cinq indicateurs de deux natures : combien de dossiers sont en cause — opérationnel — et ce que vaut
le modèle qui les regroupe — méthode. Les deux premiers rejoignent la page de qualité, les trois
autres restent. Une page neuve, « Provenance et paramètres », reçoit la provenance des champs et les
deux corrélations.

**4. Chaque page dit où son contenu est parti**, en une ligne et avec un lien. Un lecteur qui
cherchait une grandeur ne conclut pas qu'elle a disparu.

**5. Les adresses ne changent pas.** `url_path` est fixé explicitement sur chaque page ; grouper une
page dans une section ne la déplace pas, et un lien noté avant la réorganisation continue de
fonctionner.

## Ce que les champs d'emplacement du registre des relations sont, et ce qu'ils ne sont pas

**Les champs du registre des relations qui désignent l'emplacement d'affichage d'un indicateur —
`page_tableau_de_bord` et `ou_apparait` — sont des pointeurs et suivent l'indicateur ; ce que le
registre établit — le paramètre, la forme de la relation, sa conséquence, sa circularité — n'est pas
touché par un déplacement de page.**

**Cette phrase vaut règle pour la suite**, et il faut dire comment elle a été établie : un
contrôle a bloqué le déplacement. Déplacer les deux corrélations invalidait le
`page_tableau_de_bord` de `R-01` et de `R-21`, et ce contrôle l'a signalé en nommant les deux
entrées et les deux pages. Deux issues s'offraient : corriger le pointeur, ou corriger le contrôle.

**C'est le pointeur qui a été corrigé, et jamais le contrôle.** Un contrôle qui signale que deux
fichiers ont divergé fait exactement son travail ; l'affaiblir pour faire passer un déplacement
reviendrait à casser le thermomètre. Ce dépôt a déjà trouvé onze contrôles défectueux là où l'on
croyait tenir une propriété, et il n'en ajoutera pas un douzième volontairement.

## Ce qui a été écarté

**Deux barres latérales, ou deux applications.** Écarté : les deux publics ne sont pas étanches — le
responsable qui doute d'un chiffre veut savoir d'où il vient — et séparer les applications
obligerait à changer d'adresse pour le savoir.

**Classer les indicateurs à la main, page par page.** Écarté : un classement décrété se discute sans
fin et se défait au premier ajout. Le dériver de la décision servie que chaque entrée déclare déjà
le rend vérifiable par un contrôle, et rend la question de tout indicateur neuf mécanique.

**Retirer la page de rapprochement en versant tout à la qualité.** Écarté : la performance du modèle
et le nombre de dossiers en cause ne s'adressent pas au même lecteur, et les remettre ensemble
rétablirait exactement ce que la séparation défait.

## Ce qui aurait invalidé cette décision

**Un indicateur circulaire que la règle aurait classé opérationnel.** Le classement aurait alors
affiché comme mesure de l'activité une grandeur que le registre des relations déclare produite par
construction, et la règle aurait dû être amendée avant d'être appliquée. La mesure a été faite avant
d'écrire : les deux seuls indicateurs nommés par une relation sont classés en méthode par la règle
seule, sans exception à poser.

**Une décision servie qui n'aurait pas tranché.** La règle aurait alors laissé un indicateur sans
section, et il aurait fallu soit l'écrire à la main — ce que cette décision refuse — soit reformuler
la décision servie, c'est-à-dire changer le registre pour faire entrer un indicateur dans un
classement. Aucune des quarante n'est dans ce cas.

## Vérification

`tests/test_tableau_de_bord.py` porte quatre propriétés neuves : le classement se dérive de la
décision servie, dans le seul sens qu'il puisse tenir — une décision qui nomme un objet de la chaîne
désigne un indicateur de méthode, la réciproque étant fausse et non affirmée ; tout indicateur nommé
par le registre des relations est en méthode ; la navigation et le registre déclarent les mêmes
sections avec la même composition, chaque membre calculé de son côté ; aucune page déclarée n'est
vide, aucun fichier de page ne manque et aucun n'est laissé non déclaré.

Le lexique de la première a été **éprouvé contre un cas positif et un cas négatif**, et le cas
négatif n'est pas construit : c'est une décision servie réelle. Le mot « rappel » y figurait
d'abord, et la mesure a montré qu'il reconnaissait « Décider d'un rappel de rendez-vous », qui est
une action de guichet. Il a été retiré, et cette phrase est devenue le témoin négatif.

`tests/test_relations_injectees.py` n'a **pas** été touché, et sa propriété sur les indicateurs
cités est vérifiée verte après la mise à jour des pointeurs. C'est elle qui avait bloqué le
déplacement ; c'est elle qui atteste maintenant que les deux registres se répondent.
