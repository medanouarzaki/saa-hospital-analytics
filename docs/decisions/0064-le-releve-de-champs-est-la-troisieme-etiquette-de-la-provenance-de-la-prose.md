# ADR 0064 — Le relevé de champs est la troisième étiquette de la provenance de la prose, et son sens manquant est écrit

**Statut.** Accepté, et appliqué au chapitre du système d'information hospitalier.

---

## Contexte

La prose du rapport porte trois étiquettes de provenance : une source documentaire, un relevé
d'observation, une convention posée. Deux étaient outillées — les sources par le fichier
bibliographique produit à partir du registre, les conventions par un identifiant libre. **La
troisième ne l'était pas** : un relevé d'observation se citait par un identifiant que rien ne
vérifiait, et qui pouvait aussi bien désigner un champ inexistant.

Un second défaut, plus ancien, existait du côté des colonnes. Le registre des champs invoque un
champ du relevé comme preuve d'observation, et un contrôle vérifie que cette preuve existe. **Rien
ne vérifiait l'inverse.** Mesuré : sur les 143 champs relevés à l'écran, **70 sont invoqués par le
registre et 73 ne le sont par rien** — dont 24 champs de saisie. Un champ vu au poste, jamais porté
au registre ni cité par le rapport, disparaissait du modèle sans qu'aucun contrôle ne bronche.

## Décision

**Le relevé de champs devient la troisième étiquette de l'appareil de provenance de la prose, et le
sens manquant de sa correspondance est écrit.**

Un identifiant de champ se cite de deux façons, l'une et l'autre reconnues : par la commande de
relevé dans le corps du texte, et **en clair dans un tableau** — un tableau de relevé porte ses
identifiants comme données, non comme citations, et il serait absurde de les redoubler d'une
commande.

**Un champ relevé est employé de trois façons, et une seule suffit :**

1. une entrée du registre des champs l'invoque comme preuve d'observation ;
2. un chapitre du rapport le cite ;
3. le relevé le **déclare non employé, avec un motif écrit**.

**Aucun champ ne reste sans l'une des trois.** La troisième voie est nouvelle : elle vit dans le
relevé, sous une clé `champs_non_employes` qui groupe les champs par motif homogène.

## Justification des points non triviaux

**Pourquoi une troisième voie plutôt qu'une exigence d'emploi.** Un relevé exhaustif consigne des
boutons, des onglets, des entrées de menu. Exiger qu'une colonne du modèle dérive du bouton
« Imprimer » serait absurde. Mais laisser ces éléments sans statut revient à ne pas distinguer le
champ délibérément écarté du champ oublié — et c'est cette distinction que le contrôle rendait
impossible. Le motif écrit fait la différence, et il se relit.

**Pourquoi la garde de fin dans le motif d'identifiant.** L'identifiant a la forme `REL-XXX.YNN`.
Sans garde, `REL-PAT.D100` livrerait `REL-PAT.D10`, qui existe et désigne un autre champ. La garde
interdit qu'un chiffre suive, et un témoin négatif l'éprouve.

**Pourquoi le décompte de sections est déclaré.** Le retrait d'une section à l'intérieur d'un
chapitre n'est détecté par la correspondance que si la section emportait un identifiant qu'aucune
autre ne porte. **Mesuré : sur les huit sections du chapitre du système d'information, six sont
ainsi détectées et deux ne le sont pas** — celle qui expose la méthode et celle qui tire les
observations, parce qu'elles ne citent que des identifiants déjà cités dans les tableaux. Une ligne
de déclaration ferme cet angle mort, et les huit retraits rougissent alors.

## Conséquences

- **Le sens manquant mord.** Retirer le motif d'un groupe de champs non employés rend le contrôle
  rouge, en nommant chaque champ concerné ; retirer la déclaration entière le rend rouge autrement,
  en disant qu'aucune des trois voies ne s'applique. Les deux messages diffèrent.
- Un tableau de relevé exhaustif vaut citation : le rapport, en publiant ses 126 lignes de champs,
  emploie effectivement 56 champs que le registre n'invoquait pas.
- **Une section disparaît du plan faute de source.** Le plan prévoyait une section sur la place du
  produit dans une stratégie ministérielle ; aucune entrée du registre des sources ne porte quoi que
  ce soit là-dessus, et la vérification l'a établi avant toute rédaction. Ce que le relevé établit —
  l'existence d'un index maître et d'une recherche pondérée dans l'installation observée — descend
  dans la section de l'écran de recherche, où il fonde le chapitre du rapprochement.

## Ce que cet appareil ne peut toujours pas voir

**Il vérifie qu'un identifiant de champ existe, jamais qu'une phrase dit ce que ce champ dit.** Un
paragraphe qui décrirait `REL-RDV.R11` comme un champ de date, en le citant correctement, passerait
tous les contrôles. La correspondance entre une phrase et son relevé relève de la lecture.

Deux limites plus étroites s'y ajoutent, mesurées :

- **Le décompte de sections ne voit pas une permutation.** Retirer une section et en ajouter une
  autre laisse le décompte inchangé. La déclaration porte sur le nombre, pas sur les titres.
- **Le relevé lui-même n'est pas rejouable.** Il date d'une observation ponctuelle sur un profil et
  quatre écrans. Aucun contrôle ne peut vérifier qu'il correspond encore à l'écran ; il ne dit pas
  ce que le système est, il dit ce qui a été vu, un jour donné.

## Sources

- `tests/test_provenance_des_chapitres.py` — les huit propriétés, et les témoins des motifs dans
  les deux sens.
- `docs/observation/releve_champs.yml` — le relevé, et la déclaration des champs non employés.
- `docs/champs/registre_champs.yml` et `tests/test_provenance.py` — le sens déjà vérifié, laissé
  inchangé.
