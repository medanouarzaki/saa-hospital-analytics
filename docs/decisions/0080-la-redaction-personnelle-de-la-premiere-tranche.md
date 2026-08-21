# ADR 0080 — Quatre paragraphes de rédaction personnelle, et un cinquième qui ne peut pas s'écrire

**Statut.** Accepté.

---

## Contexte

Cinq emplacements du rapport attendaient une matière que le squelette ne pouvait pas produire :
la présentation du besoin, le rattachement du travail, l'organisation en phases, la composition du
service, et l'apport personnel. Quatre relèvent de la première tranche.

L'auteur a fourni la matière. Elle a été écrite telle qu'elle a été donnée, sans être enrichie ni
extrapolée.

## Décision

### 1. Un emplacement est retiré parce qu'il ne peut pas être écrit

`composition-du-service` demandait l'effectif du service, les intitulés de poste et la répartition
des postes entre les processus. **L'auteur ne les connaît pas.** Aucune source publiée ne les
porte, et l'observation ne les a pas relevés.

Il est retiré, et non laissé en attente. Un emplacement qui attend une matière que personne
n'ira chercher est une dette qui ne se solde jamais.

La section qu'il occupait dit désormais **ce que le service fait**, par ses missions prescrites et
par les profils applicatifs qui les portent. Elle ne décrit pas ce qui n'a pas été vu, et elle ne
s'en excuse pas.

### 2. L'organigramme est abandonné pour une figure entièrement sourcée

Un organigramme de service aurait demandé d'inventer une hiérarchie. À sa place, une figure met en
regard **les cinq missions de l'article 35 et les cinq profils applicatifs relevés à l'écran de
connexion**. Chaque ligne s'appuie sur le texte réglementaire d'un côté et sur un identifiant de
relevé de l'autre ; aucune n'est supposée.

Elle porte en outre un fait que l'organigramme n'aurait pas montré : le découpage de l'activité du
service tel que l'outil l'impose.

### 3. Le contrôle qui compte les emplacements mord de nouveau

`test_aucun_paragraphe_ne_reste_a_rediger` était conditionné à l'état `remise`, que le fichier des
marqueurs ne déclarera jamais depuis la décision `0077`. **Il ne mordait donc plus jamais**, et un
emplacement retiré comme un emplacement ajouté passaient tous deux en silence.

Il devient `test_les_emplacements_a_rediger_sont_exactement_ceux_qui_sont_declares`, et il ne
s'abstient plus. Une liste déclarative, `EMPLACEMENTS_ATTENDUS`, est confrontée aux fichiers dans
les deux sens.

La propriété est meilleure que celle qu'elle remplace. Elle n'exige pas que la liste soit vide :
elle exige qu'elle soit **vraie**. Écrire un paragraphe sans retirer son identifiant est rouge ; en
ajouter un sans le déclarer l'est aussi. Le jour où la liste est vide, plus aucun paragraphe
n'attend.

### 4. Une observation de saisie entre au rapport

Le relevé décrivait ce que les écrans portent. Il ne disait rien de ce que la saisie en fait.

**Le numéro de téléphone est parfois rempli d'un numéro inventé, lorsqu'une personne âgée ne
connaît pas le sien.** Cette observation ne se lit sur aucun écran, et elle porte loin : le taux de
renseignement d'une colonne mesure ce qui a été saisi, jamais ce qui est vrai.

Elle devient la quatrième observation exploitable du chapitre du système d'information, et elle
sera reprise **par renvoi** aux trois endroits qui s'en servent, jamais réécrite.

### 5. Une réserve est ajoutée là où le rapport pouvait laisser croire plus

L'auteur n'a jamais vu une recherche de patient rendre plusieurs résultats proches. Le rapport ne
doit donc pas laisser entendre que le problème des doublons a été constaté sur place.

La réserve est écrite au chapitre du système d'information, à côté de l'observation qui l'appelle.
Le chapitre du rapprochement a été relu : il établit le problème par l'existence de la fonction
dans l'outil et par le rapport d'audit, et **il n'affirme rien de plus**.

## Une mesure qui était fausse, et sa correction

Le rapport de la tranche précédente annonçait « zéro boîte débordante ». **C'était faux.** La
commande de comptage employée ne rendait rien, et son silence a été pris pour un zéro.

Le document en portait 183, dont quatre de 12,25 pt dans une table du chapitre du système
d'information — une colonne trop étroite pour le mot qu'elle devait tenir. Les cinq fichiers de
cette tranche n'en portent plus aucune ; le document en garde 178, dans des fichiers hors de portée
de ce travail.

Un contrôle par motif textuel qui ne rend rien peut être muet parce qu'il n'a rien trouvé, ou muet
parce qu'il ne cherche pas. La distinction n'avait pas été faite.

## Ce qui a été écarté

**Écrire la composition du service d'après ce qui est plausible.** Écarté : c'est exactement ce que
le rapport refuse partout ailleurs.

**Nommer la phase ajoutée par le vocabulaire interne du projet.** Écarté : les phases sont nommées
par ce qu'elles font, et le rapport ne porte aucune trace de son propre processus de fabrication.

## Ce que cette décision ne peut pas voir

**Rien ne vérifie que la matière écrite est celle qui a été donnée.** Le contrôle compte les
emplacements ; il ne lit pas ce qui les remplace. Un paragraphe de rédaction personnelle inventé
passerait tous les contrôles du dépôt, et seule la relecture de l'auteur l'établirait.

**Les trois reprises de l'observation de saisie ne sont pas encore écrites.** Elles appartiennent à
des chapitres hors de cette tranche, et rien ne rougirait si elles n'étaient jamais faites : aucun
contrôle ne lie une observation à ses emplois.
