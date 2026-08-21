# ADR 0073 — Cinq marqueurs nominatifs ramenés à deux, et une ligne vide ne se compose plus

**Statut.** Accepté. Il révise l'`0062`, qui en déclarait cinq.

---

## Contexte

`report/marqueurs.tex` portait cinq marqueurs nominatifs : auteur, encadrant académique, encadrant
professionnel, président du jury, examinateur. L'`0062` les a posés ainsi, et il notait déjà que
**deux d'entre eux — le président du jury et l'examinateur — n'étaient pas connus de l'auteur**.

Ils ne le sont toujours pas, et pour une raison qui n'est pas un retard : **il n'y a ni jury nommé,
ni encadrant académique**. Le document est un rapport de stage d'application (`0072`). Il a un
auteur et un encadrant de stage, chef du service. Trois marqueurs sur cinq n'ont pas d'objet.

## Décision

### 1. Deux marqueurs nominatifs, et trois retirés

`\marqueurEncadrantAcademique`, `\marqueurPresidentJury` et `\marqueurExaminateur` sont **retirés du
fichier, pas laissés vides**. La distinction porte tout le motif : un marqueur vide est un oubli qui
attend. Il compose une ligne d'étiquette sans valeur sur la page de garde, et **une ligne vide se
remarque là où une ligne absente ne se remarque pas**.

`tests/test_marqueurs_nominatifs.py` porte désormais deux propriétés au lieu d'une : les deux
marqueurs restants s'accordent avec l'état déclaré, ET **aucun des trois retirés ne revient**, même
déclaré vide. La seconde est éprouvée par mutation : réintroduire `\marqueurPresidentJury{}` fait
rougir le contrôle en le nommant.

### 2. Aucun texte fixe n'entoure un marqueur qui peut être vide

C'est la généralisation du même défaut, et elle vaut pour tous les champs, pas seulement pour les
noms. `\siRenseigne{\marqueur}{ce qui compose}` ne compose son second argument que si le marqueur
porte une valeur. « Soutenu le » disparaît avec la date de soutenance ; « Réalisé par » disparaît
avec l'auteur ; le tableau des noms ne garde que la ligne de l'organisme d'accueil, qui est la seule
dont le marqueur est renseigné dans le fichier lui-même — et c'est elle qui empêche un tableau sans
aucune ligne.

**LE TÉMOIN DE VACUITÉ EST DÉCLARÉ, PAS EMPRUNTÉ AU NOYAU, ET C'EST UNE MESURE.** `\ifx\x\empty`
serait FAUX même sur un marqueur vide : `\newcommand` définit ses commandes avec le préfixe `\long`,
que `\empty` du noyau ne porte pas, et `\ifx` compare aussi les préfixes. Le témoin est donc défini
par `\newcommand`, comme les marqueurs — c'est le motif déjà employé par `\etatBrouillonAttendu`.

### 3. Les trois marqueurs de contexte sans nom de personne sont renseignés

Établissement de formation, filière et année universitaire portaient des valeurs vides. Ils n'ont
jamais relevé du contrôle des marqueurs nominatifs, et rien n'imposait de les laisser vides. Ils
sont renseignés. La date de soutenance, elle, n'est pas connue et reste vide : sa ligne disparaît.

## Ce qui a été écarté

**Conserver les cinq marqueurs et n'en renseigner que deux.** Écarté : c'est exactement l'état que
cette décision corrige, et l'`0062` montrait déjà qu'il produisait deux marqueurs perpétuellement
vides.

**Composer une ligne vide plutôt que de la faire disparaître.** Écarté par le même argument que le
retrait des trois marqueurs.

## Ce que cette décision ne peut pas voir

**Le contrôle des marqueurs lit `report/marqueurs.tex`, où les deux noms sont désormais TOUJOURS
vides** — ils viennent de `report/noms.tex`, qui n'est pas suivi (`0074`). En état de remise, le
contrôle exigera donc que `marqueurs.tex` porte les noms, c'est-à-dire exactement ce que `0074`
interdit. **Les deux décisions se contredisent au moment de la bascule**, et ce lot ne la fait pas.
Le lot qui basculera l'état devra trancher : écrire les noms dans le fichier suivi, ou déplacer la
propriété sur le fichier injecté, que ce contrôle ne lit pas. C'est consigné ici plutôt que découvert
le jour de la remise.
