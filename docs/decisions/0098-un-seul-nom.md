# ADR 0098 — Un seul nom

**Statut.** Accepté. Il révise l'`0073` et l'`0074` sur le nombre de noms, non sur le mécanisme
d'injection.

---

## Contexte

Le document portait deux marqueurs nominatifs depuis l'`0073`, et l'`0074` les injectait à la
compilation depuis deux secrets de dépôt. Le second désignait une fonction d'encadrement que le
stage n'a pas comportée : aucune personne ne l'a tenue. Le marqueur, le secret qui le renseignait,
la ligne de page de garde, la ligne de la présentation et les remerciements qui lui étaient
adressés décrivaient donc un rôle sans titulaire.

## Décision

### Le document ne porte qu'un nom : celui de l'auteur

- `report/marqueurs.tex` ne déclare plus que `\marqueurAuteur`. `\marqueurEncadrantProfessionnel`
  rejoint les marqueurs RETIRÉS que `tests/test_marqueurs_nominatifs.py` interdit de redéclarer.
- La page de garde et les planches de titre et de fin de la présentation perdent leur ligne
  d'encadrement, sans ligne de remplacement.
- Les remerciements s'adressent à l'équipe du service qui a accueilli le stage, et ne composent
  plus aucun marqueur.
- Le chapitre de cadrage ne prête plus à personne une reprise orale du cahier de charges : la
  phrase est retirée, et avec elle l'étiquette de provenance qui ne portait qu'elle.
- L'intégration continue ne lit plus qu'un secret, `RAPPORT_AUTEUR`, et compose l'état de remise
  dès qu'il est renseigné. `tests/test_aucun_nom_de_personne.py` ne cherche plus que ce nom.
- Les commentaires des fichiers vivants — sources du rapport et de la présentation, workflow,
  `.gitignore`, contrôles — décrivent le mécanisme tel qu'il est : un nom, un secret.

### Deux propriétés empêchent le retour

- **Les variables de nom lues par le workflow sont exactement celles que le contrôle d'absence de
  nom cherche**, dans les deux sens. Sans elle, un second secret réintroduit dans le workflow
  composerait un nom que rien ne chercherait.
- **Aucune source vivante du rapport, de la présentation ni `.gitignore` ne mentionne un
  encadrement**, commentaires compris. La recherche est une sous-chaîne bornée à droite : elle voit
  un identifiant qui porte le mot, et laisse passer le mot suivi d'une minuscule — ce qui épargne
  une interpolation entre « valeurs encadrantes », au prix déclaré du pluriel et du féminin.

### Ce qui n'est pas réécrit

Les enregistrements de décision antérieurs, le relevé daté des critères et les notes de
préparation de soutenance décrivent un état passé ou ne décrivent pas le mécanisme : ils restent
tels quels.

## Ce qui est perdu

- **La recherche du second nom** par le contrôle d'absence de nom. Elle n'a plus d'objet tant que
  le second nom n'est déclaré nulle part, et la propriété sur les variables de nom ferait rougir
  sa réintroduction.
- **Les artefacts passés** de l'intégration continue qui composaient le second nom : ils sont
  supprimés une fois le présent changement publié et vérifié, et le secret qui portait ce nom
  l'est avec eux.

## Limite écrite

**Un artefact déjà téléchargé par un tiers ne se rappelle pas.** La suppression retire ce que la
plateforme sert ; elle ne retire rien de ce qui a déjà été copié ailleurs. La vérification que le
second nom n'a jamais été commis à l'historique du dépôt a été faite avant ce changement, sous
quatre formes, et rend zéro occurrence : le dépôt lui-même ne le porte nulle part.
