# ADR 0077 — L'état du document sort du dépôt avec les noms, et la contradiction se lève

**Statut.** Accepté. Il tranche ce que l'`0073` avait consigné sans arbitrer.

---

## Contexte

L'`0073` avait laissé une contradiction ouverte, écrite dans sa propre section « ce qu'il ne peut
pas voir » :

- `tests/test_marqueurs_nominatifs.py` exigeait, en état de remise, que `report/marqueurs.tex`
  porte les deux noms de personne ;
- l'`0074` interdisait au dépôt de les porter, où que ce soit.

Les deux ne pouvaient pas être vraies en même temps. La bascule à la remise était donc impossible
sans casser l'une des deux règles.

## Décision

**`report/marqueurs.tex` déclare `brouillon`, et il le déclarera toujours.** L'état de remise ne
s'écrit pas dans un fichier suivi.

**`report/noms.tex` porte les trois valeurs ensemble** : l'auteur, l'encadrant de stage, et l'état.
Il n'est jamais commis, et l'intégration continue l'écrit avant les deux compilations.

C'est le déplacement d'une frontière, pas un assouplissement. Les trois valeurs qui font un
document remis sont exactement celles qui ne doivent pas être publiées ; les faire voyager ensemble
est plus simple que de les séparer, et cela supprime l'état intermédiaire où le dépôt annonçait une
remise sans pouvoir la porter.

### Ce que le contrôle devient

Sa propriété est désormais **permanente** : le fichier commis déclare `brouillon` et ses deux
marqueurs nominatifs sont vides. Elle est vraie aujourd'hui, elle le restera, et le contrôle ne
changera plus.

Une propriété neuve la garde : **l'état de remise écrit dans le fichier commis est rouge**, et le
message nomme `noms.tex`. Sans elle, basculer le fichier suivi passerait, et la contradiction
reviendrait telle quelle.

### Des secrets, et non des variables de dépôt

Le travail précédent employait `vars.RAPPORT_AUTEUR` et `vars.RAPPORT_ENCADRANT`. Deux mesures ont
fait changer d'avis :

- le journal d'un travail d'intégration continue **recopie le texte du script**, ligne à ligne — ce
  qui a été vu dans le journal réel, et ce qui justifiait déjà de passer par un bloc `env:` ;
- `gh variable list` **affiche la valeur** d'une variable de dépôt en clair.

Un secret est masqué par la plateforme partout où il apparaîtrait. Le nom d'une personne sur une
page de garde n'est pas un secret d'exploitation, mais il n'a pas à être lisible par quiconque
accède au dépôt.

## La mesure

Composition sans `noms.tex` : la mention « Version de travail — document non remis » est présente,
et les deux lignes de noms sont absentes. Composition avec un `noms.tex` témoin portant les trois
redéfinitions : la mention disparaît, et les deux noms figurent. Le témoin n'est pas commis.

## Ce qui a été écarté

**Écrire les noms dans le fichier suivi au moment de la remise.** Écarté : c'est la branche de la
contradiction que l'`0074` interdit.

**Déplacer la propriété du contrôle sur `noms.tex`.** Écarté : ce fichier n'est pas suivi, un
contrôle ne peut pas s'appuyer sur ce qui peut ne pas exister, et il s'abstiendrait en permanence.

## Ce que cette décision ne peut pas voir

**Rien de `noms.tex`.** Ni les noms qu'il pose, ni l'état qu'il déclare, ni sa syntaxe. Un fichier
mal formé ferait composer un document remis sans nom, et aucun contrôle ne broncherait. Seule la
lecture du document composé l'établirait, et le dépôt ne suit pas le PDF.

**Une conséquence de bord, mesurée et assumée.** Deux propriétés de
`tests/test_provenance_des_chapitres.py` — celle qui exige que toute source citable soit citée, et
celle qui interdit qu'un paragraphe reste à rédiger — s'abstiennent tant que l'état lu vaut
`brouillon`. Ce contrôle lit `marqueurs.tex`, jamais `noms.tex` : **elles s'abstiendront désormais
toujours.** Elles ne sont pas supprimées, et le travail qui voudra les faire mordre devra les
adosser à autre chose que l'état déclaré.
