# Questions de soutenance, et ce que le projet peut soutenir

**Préparation. Ce document n'est pas destiné au jury** : il n'entre ni au rapport ni au support. Il
sert à ce qu'aucune question ne trouve une réponse improvisée.

**Le principe qui gouverne toutes les réponses : dire la limite avant que le jury la trouve.** Un
jury qui découvre seul la faiblesse d'un résultat cesse de croire les autres. Chaque réponse
ci-dessous s'appuie sur une mesure du dépôt ou sur une source, et aucune ne prétend plus que ce que
le projet établit. Là où le projet répond mal, la réponse le dit.

Les réponses sont écrites **à la première personne**, comme elles se diront.

---

## I. La nature des données — 4 questions

### 1. « Vos données sont inventées. Qu'est-ce que votre analyse démontre ? »

Elle démontre qu'une chaîne sait produire ces grandeurs, à la maille où une décision se prend. Elle
n'établit rien sur ce service. C'est la distinction que le rapport tient partout : un résultat
**démontre** une capacité, il **établit** un fait — et sur un jeu que j'ai construit, seule la
première moitié est vraie. Concrètement : quand je retrouve que l'absentéisme croît avec le délai à
l'intérieur d'une spécialité, je ne prouve rien d'autre que la capacité de la chaîne à retrouver ce
que j'y ai mis. Chacune des conclusions chiffrées du rapport dit laquelle des 21 relations injectées
elle reproduit, ou déclare qu'elle n'en reproduit aucune.

*S'appuie sur* : le chapitre de l'analyse, où chaque conclusion porte sa relation ; les 21 relations
injectées du registre, dont 5 qu'aucune conclusion ne reprend.

### 2. « Comment savez-vous que votre jeu ressemble à de vraies données ? »

Je ne le sais pas, et je ne le prétends nulle part. Ce que je sais est plus modeste : les
**volumes** ne sont pas inventés — ils viennent du recueil statistique du ministère, où
l'établissement est nommé, avec une capacité fonctionnelle de 40 lits, 7 851 journées et 1 197
admissions pour l'exercice. Les **distributions** sont calibrées sur des sources publiées quand il
en existe une, et **posées** quand il n'en existe pas. La ressemblance est donc une hypothèse de
construction, jamais une mesure : aucune donnée réelle n'existe pour la confronter, et c'est la
limite centrale du travail.

*S'appuie sur* : `capacite-fonctionnelle`, `journees-2024`, `admissions-2024` au registre ; le
chapitre de conception, section des distributions et de leurs sources.

### 3. « Y a-t-il une grandeur que vous n'avez pas mesurée, et qu'avez-vous fait ? »

Oui, et plusieurs. L'exemple que je donne toujours est la composition du service : aucune source
consultée ne la donne, et le rapport écrit qu'elle est **inconnue** plutôt que de la supposer. Même
chose pour l'ampleur du Ramadan sur l'activité : seules les dates viennent d'une source, le
coefficient est posé. La règle que je me suis donnée est que ce qui est posé porte une marque dans
le texte, et que le tableau de bord distingue à l'écran la part du modèle qui repose sur
l'observation de celle qui repose sur l'hypothèse.

*S'appuie sur* : la page « Provenance et paramètres » du tableau de bord ; les marques de convention
dans les chapitres.

### 4. « Votre modèle est-il observé ou inventé ? »

Le **modèle** est observé, les **valeurs** ne le sont pas, et c'est l'asymétrie centrale du travail.
81 colonnes sur 175 viennent d'un relevé d'écran, chacune sous un identifiant qu'on retrouve en
annexe ; mais seulement 5 paramètres de génération sur 256 reposent sur une observation. Autrement
dit, je sais quels champs le système porte, et je ne sais presque rien des valeurs qu'ils
contiennent.

*S'appuie sur* : `colonnes-source-obs` et `colonnes-source-registre` ; `parametres-obs` et
`parametres-total`.

---

## II. La méthode — 4 questions

### 5. « Vous avez des centaines de contrôles. Qu'est-ce que cela prouve ? »

Rien en soi, et c'est le point. 76 fichiers de contrôle s'exécutent à chaque modification, mais leur
nombre ne dit rien de leur valeur. Ce qui vaut, ce sont les **mutations** : on casse délibérément ce
qu'un contrôle surveille, on vérifie qu'il rougit, puis on restaure. Et la leçon que j'en retire est
celle-ci — **une mutation restée verte révèle presque toujours un contrôle défectueux, pas un code
correct.** Je l'ai vérifié plusieurs fois, et le projet en porte les traces.

*S'appuie sur* : `fichiers-de-controle` ; la doctrine de mutation, écrite au chapitre de cadrage et
répétée dans les enregistrements de décision.

### 6. « Donnez-moi un exemple de contrôle qui n'a rien vu. »

Le meilleur est celui du taux de rotation. La page affichait 74,5 là où la statistique nationale
publie 29,9 : faux d'un facteur 2,4986, exactement le rapport de la durée de la période à l'année de
référence — la page n'annualisait pas. Le contrôle censé le surveiller **est resté vert pendant
toute la durée du défaut**, parce qu'il retranscrivait la formule de la page et se comparait à elle :
une comparaison vraie par construction, incapable de départager une formule juste d'une formule
fausse. Le contrôle qui l'a remplacé ne retranscrit rien : il appelle la page et confronte ses
sorties à deux références qui ne peuvent pas bouger avec elle.

*S'appuie sur* : `rotation-affichee-avant`, `trot-publie`, `facteur-annualisation`,
`rotation-affichee` ; le chapitre du tableau de bord.

### 7. « Comment garantissez-vous les chiffres de votre rapport ? »

Aucun nombre n'est tapé dans la prose : chaque valeur vit dans un registre avec **la commande exacte
qui la produit**, et le texte l'appelle par son identifiant. Le motif est mesuré, pas théorique :
cinq valeurs ont circulé dans les documents de ce projet sans être rattachées à une commande, et les
cinq étaient fausses ou périmées. Un contrôle vérifie dans les deux sens que tout identifiant appelé
existe et que toute entrée est employée ou déclarée non employée.

*S'appuie sur* : `docs/chiffres/registre_chiffres.yml` et son en-tête ;
`tests/test_registre_des_chiffres.py`.

### 8. « Ce registre ne peut donc pas vous protéger de tout ? »

Non, et j'en connais trois trous. **Le premier** : il vérifie la correspondance entre appels et
entrées, pas les chiffres littéraux — un nombre tapé n'appelle rien, donc rien ne le voyait. J'ai
écrit le contrôle qui manquait, et il en trouve 42 qui subsistent. **Le deuxième** : il ne voit pas
un nombre écrit en toutes lettres, et c'est par là que deux décomptes du projet sont devenus faux.
**Le troisième** : la vérification qui confronte le registre à ses commandes ouvre la base sur la
période entière, et ne peut donc pas tourner en intégration continue. Je l'ai lancée à la main, elle
rendait neuf écarts, et je les ai fermés.

*S'appuie sur* : `tests/test_aucun_nombre_tape.py` ; `docs/chiffres/mesurer.py --verifier` ;
`docs/releve_des_criteres.md`.

---

## III. Le rapprochement d'identités — 4 questions

### 9. « Précision et rappel à 1,00 ? C'est trop beau. »

Vous avez raison de le relever, et je dis pourquoi avant qu'on me le demande. Ce chiffre parfait ne
tient pas à la qualité du modèle : il tient à ce que **le générateur recopie certains champs à
l'identique** entre les deux fiches d'un doublon, et le modèle apprend à s'y fier. Je l'ai démontré
par une ablation : en privant le modèle de ces champs, la F-mesure ne bouge presque pas — elle passe
de 1 à 0,9995 — mais la **marge** entre les paires vraies et les paires fausses s'effondre, de 270,87
à −2,66. Une marge négative signifie qu'aucun seuil ne sépare les deux populations. Sur un fichier
réel, ces champs ne seraient pas identiques par construction, et la marge y ressemblerait davantage à
celle des variantes ablatées.

*S'appuie sur* : `f-mesure-seuil-retenu`, `ablation-f-variante-a`, `ablation-ecart-complet`,
`ablation-ecart-variante-a` ; chapitre de la qualité.

### 10. « Pourquoi un modèle probabiliste, et pas un simple regroupement sur nom et date de naissance ? »

Parce que je l'ai mesuré, et que la collision exacte manque précisément la population qu'il faut
retrouver. Sa F-mesure vaut 0,9077 — honorable —, mais elle ne peut rien voir de **268 fiches dont
la pièce d'identité est vide** : une collision exacte a besoin de deux valeurs égales, et une valeur
absente n'est égale à rien. Or c'est exactement la population que le service saisit le moins bien.
Le modèle probabiliste, lui, estime la probabilité que deux fiches désignent la même personne à
partir de douze comparaisons, et n'exige pas l'égalité.

*S'appuie sur* : `baseline-f-mesure`, `collision-vides-piece`, `comparaisons-modele`.

### 11. « Votre vérité terrain vient du générateur. N'est-ce pas circulaire ? »

Si, et c'est écrit tel quel dans le rapport. Je connais les 996 paires injectées parce que je les ai
injectées ; 991 se retrouvent dans la population après les filtres. Sur des données réelles, cette
connaissance n'existe pas : il faudrait un échantillon annoté à la main, avec son coût et son
incertitude propres, et précision et rappel cesseraient d'être mesurables tels quels. Ce que
l'évaluation établit malgré cela est plus modeste et plus solide : la chaîne sait estimer un modèle
sans étiquettes, bloquer efficacement, et **mesurer sa propre fragilité** — c'est ce que fait
l'ablation.

*S'appuie sur* : `vt-paires-injectees`, `vt-paires-presentes` ; chapitre de la qualité, section des
limites.

### 12. « Comment évitez-vous de comparer toutes les paires ? »

Par un blocage : un tri grossier qui écarte d'emblée les paires qui n'ont aucune chance. Il fait
passer 333 891 561 paires possibles à 5 014 paires candidates, par quatre règles — nom et adresse,
nom et téléphone, pièce d'identité, parents et naissance. Son rappel sur la vérité terrain est
**total** : aucune paire vraie n'est perdue au blocage, et je le vérifie plutôt que de l'espérer.

*S'appuie sur* : `paires-possibles`, `paires-candidates` ; le contrôle du rappel de blocage.

---

## IV. L'analyse de l'activité — 3 questions

### 13. « Comment construisez-vous le délai d'obtention d'un rendez-vous ? »

C'est l'écart entre la date de création du rendez-vous et la date du rendez-vous lui-même. Aucun des
deux champs ne porte cette grandeur : c'est leur différence, et je l'ai vue au poste avant de la
calculer. Sur le rendez-vous que j'ai observé, cette différence valait une seconde — un rendez-vous
donné pour l'instant même. Le cas est extrême et il est instructif : il montre que le système accepte
un délai nul, donc que la grandeur est bornée à zéro et non strictement positive.

*S'appuie sur* : le relevé de l'écran de prise de rendez-vous, blocs de contrôle des modifications
et du rendez-vous.

### 14. « Vous publiez une corrélation qui change de signe selon la façon de la calculer. Laquelle est vraie ? »

Les deux, et c'est pour cela que je les publie ensemble. Entre activités, le lien entre délai et
absentéisme vaut −0,4878 ; à l'intérieur de chaque activité, +0,0782 ; sur les rendez-vous pris
ensemble, 0,028 — presque rien. C'est un paradoxe de composition : publier l'une des trois seule
serait un artefact. Le tableau de bord porte les deux premières côte à côte, et jamais l'une sans
l'autre. J'ajoute que ces deux mesures sont marquées **circulaires** au registre des relations
injectées : leur valeur est fixée par construction, et aucune décision de service ne peut s'y
adosser.

*S'appuie sur* : `relation-inter-ensemble`, `relation-intra-ensemble`, `relation-brute-ensemble` ;
la page « Provenance et paramètres ».

### 15. « Vous donnez deux décomptes différents de rendez-vous honorés. Lequel est le bon ? »

Les deux sont justes, et ils ne comptent pas la même population. 10 280 rendez-vous sont honorés ;
10 256 ont une fiche patient dans la couche produite, 24 n'en ont pas — leurs fiches sont en
quarantaine. Et sur les 10 280, 6 845 sont un artefact de génération, soit 66,7414 %, ce qui laisse un
complément de 3 411 rendez-vous sur lesquels le délai se lit sans cet artefact. Le rapport publie
donc les deux médianes : 17 jours sur l'ensemble, 16 sur le complément. **Une valeur sans sa
population ne veut rien dire**, et c'est le genre d'erreur que ce projet a commis avant de la
corriger.

*S'appuie sur* : `honores-total`, `honores-avec-fiche`, `honores-sans-fiche`, `artefact-nombre`,
`artefact-part`, `complement-nombre`, `delai-mediane-ensemble`, `delai-mediane-complement`.

---

## V. Le périmètre et l'honnêteté — 3 questions

### 16. « Vous n'avez observé qu'un profil sur cinq. Que vaut votre modèle ? »

Il vaut ce qu'un relevé d'un poste peut valoir, et le rapport le dit à chaque fois qu'il s'appuie
dessus. J'ai observé l'écran de démarrage, la recherche d'identifiant, la fiche patient et l'écran
de prise de rendez-vous — c'est-à-dire le profil des rendez-vous. Les quatre autres exigent des
habilitations qu'un stagiaire ne reçoit pas. Ce que cela change : la fiche patient et l'identité sont
observées de près, la facturation et le recouvrement le sont par la documentation de l'éditeur et par
un rapport de contrôle, pas par l'écran.

*S'appuie sur* : le chapitre du système d'information, section de la méthode de relevé.

### 17. « Qu'est-ce qui, dans votre travail, ne marche pas ? »

Plusieurs choses, toutes mesurées et écrites. **Un** : deux tables décrivent le même épisode
d'hospitalisation avec des durées tirées indépendamment — la chaîne donne donc deux réponses à
« combien de temps ce patient est-il resté ». Je ne l'ai pas corrigé ; j'ai vérifié que l'appariement
est de un à un sur 2 980 séjours, et qu'aucun indicateur affiché ne lit cette durée. **Deux** : un
indicateur réglementaire a été affiché faux d'un facteur 2,4986 pendant des semaines, sous un
contrôle vert. **Trois** : 42 nombres sont encore tapés en clair dans les sources du rapport, alors
que la première règle du projet est qu'aucun ne le soit ; je les ai nommés un par un plutôt que de
les taire. **Quatre** : j'ai posé un aplat derrière le titre de la page de garde pour l'ancrer, il
l'alourdissait, et je l'ai retiré — une correction qui ne corrige pas se défait.

*S'appuie sur* : ADR 0059 ; le chapitre du tableau de bord ; `tests/test_aucun_nombre_tape.py` ;
ADR 0086.

### 18. « Avez-vous constaté des doublons dans le fichier réel ? »

**Non, et c'est important.** Aucune recherche conduite au poste n'a rendu plusieurs résultats proches
d'un même patient. Le problème n'est pas constaté sur place. Il est établi autrement : par l'outil,
dont l'écran porte un onglet de recherche **pondérée** sur l'index maître des patients et une
colonne de **probabilité** en regard de chaque résultat — un système qui offre cela admet que la
recherche exacte ne suffit pas ; et par un rapport de contrôle consacré à l'établissement. Le jeu de
données en injecte donc une part connue — 0,04 en proportion —, et la chaîne en retrouve
3,9878 %.

*S'appuie sur* : le relevé de l'écran de recherche ; `defaut-taux-doublons`,
`doublons-part-mesuree`.

---

## VI. Ce que le relevé des critères ouvre — 3 questions

### 19. « Un critère a été déclaré atteint alors qu'il ne l'était pas. Combien d'autres ? »

Un seul, et je l'ai trouvé en écrivant le relevé daté des critères. Sur treize critères qu'un
contrôle établit, onze étaient vrais, deux ne sont pas encore applicables, et **un était faux** : la
concordance du registre avec ses commandes, qui rendait neuf écarts. Je les ai fermés, et la
remesure rend zéro écart. Ce qui compte plus que la correction : **six des neuf ne venaient pas d'une
valeur devenue fausse, mais d'une commande devenue aveugle** — un tableau descendu en annexe, une
fonction de tracé changée, et la commande cherchait sa matière là où elle n'était plus.

*S'appuie sur* : `docs/releve_des_criteres.md` ; la sortie de `mesurer.py --verifier`.

### 20. « Et les critères qu'aucun contrôle ne peut établir ? »

Il y en a dix, et je les ai nommés un par un avec ce qui les vérifierait à la main. Le plus parlant :
**aucun contrôle ne lit le PDF**. Ni le nombre de pages, ni les boîtes débordantes, ni une planche
qui déborde, ni une valeur illisible de loin, ni une ligne veuve. C'est par la relecture en image que
les quatre derniers travaux de rédaction ont trouvé une vingtaine de défauts, et par elle seule.
S'ajoutent : la fidélité d'une citation, la fraîcheur d'une capture, et la ressemblance du jeu de
données au réel — que rien ne peut établir tant que la contrainte de confidentialité tient.

*S'appuie sur* : `docs/releve_des_criteres.md`, partie B.

### 21. « Pourquoi cette vérification ne tourne-t-elle pas automatiquement ? »

Parce qu'elle ne le peut pas, et c'est une propriété du dispositif, pas un oubli. Elle ouvre la base
et compare des valeurs mesurées sur la période entière — 912 jours —, quand l'exécuteur de
l'intégration continue n'engendre que trois mois. Elle ne tourne donc qu'à la main. La conséquence
est écrite au relevé : **elle est due avant toute remise, et toute campagne de rédaction qui déplace
de la matière la périme.**

*S'appuie sur* : l'en-tête du registre des chiffres ; `docs/releve_des_criteres.md`.

---

## VII. Les nombres tapés — 2 questions

### 22. « Votre dépôt contient un contrôle qui liste 42 nombres tapés. Expliquez. »

C'est moi qui l'ai écrit, et c'est moi qui les ai listés. En vérifiant une affirmation sur le format
des décimales, j'ai trouvé un nombre tapé à la main dans un tableau dont les trois autres valeurs
venaient du registre. Aucun contrôle ne pouvait le voir. J'ai corrigé celui-là — il vaut
0,999495204442201, mesuré par sa commande — puis j'ai écrit le contrôle qui manquait, et il en a
trouvé 42 autres. **Ce ne sont pas des faux positifs** : ce sont des pourcentages de provenance, des
statistiques citées d'un recueil, la couverture des règles de blocage, une table de perturbation.

*S'appuie sur* : `tests/test_aucun_nombre_tape.py` ; ADR 0091 et 0092.

### 23. « Pourquoi ne les avez-vous pas tous corrigés ? »

Parce que corriger chacun demande une entrée au registre **avec la commande qui la produit**, et que
ces valeurs vivent dans la prose d'un fichier de sources, pas dans une table : c'est un travail par
valeur, et je ne l'ai pas mené. Ce que j'ai fait à la place : les nommer un par un dans le contrôle,
fichier et ligne. Toute occurrence **nouvelle** est rouge ; une occurrence corrigée doit sortir de la
liste, et une seconde épreuve rougit si la liste porte une ligne qui n'existe plus. **La dette est
explicite, comptée, et ne peut pas grossir en silence.** Je préfère une dette écrite à une règle
qu'on affirme et qu'on ne tient pas.

*S'appuie sur* : `tests/test_aucun_nombre_tape.py`, tuple des restes et ses deux épreuves.

---

## VIII. Les questions techniques d'un jury d'ingénierie — 5 questions

### 24. « Pourquoi un serveur de base de données relationnelle, et pas un moteur embarqué ? »

Parce que trois services attaquent la même base par le réseau, et que le chargement écrit pendant que
le tableau de bord lit. Un moteur embarqué tient dans un fichier et n'arbitre pas deux écrivains
distants ; il aurait fallu sérialiser les accès à la main. Ce n'est pas un choix de performance —
aucun de mes choix ne l'est : c'est la propriété que le dossier doit démontrer, ou la contrainte
qu'il ne faut pas violer.

*S'appuie sur* : le tableau des choix techniques au chapitre de cadrage ; ADR 0001.

### 25. « Pourquoi une dimension historisée ? »

Parce qu'une fiche patient change, et qu'une facture ancienne doit se relire avec l'état de la fiche
**au moment où elle a été émise**. Un patient déclare sa couverture en mars : sans historisation, la
facture de février se lirait avec la couverture d'aujourd'hui, et la part payée par l'organisme
deviendrait fausse — rétroactivement, et sans que rien ne le signale. La chaîne porte donc 29 107
versions de fiche pour 25 842 identifiants distincts, dont 3 265 en portent plus d'une.

*S'appuie sur* : `dim-patient-lignes`, `identifiants-distincts`,
`dim-patient-fiches-plusieurs-versions` ; ADR 0021.

### 26. « Qu'apporte un orchestrateur qu'un script enchaînant les commandes n'apporterait pas ? »

Trois choses que j'ai eu besoin d'avoir. **L'ordre est déclaré**, pas écrit : les 12 tâches
s'enchaînent par leurs dépendances, et la contrainte qui compte — les dimensions se construisent
avant les faits — se lit dans le graphe. **La reprise est partielle** : une tâche qui échoue
n'oblige pas à tout rejouer. Et **l'état est observable** : je sais quelle journée a été traitée et
laquelle a échoué, sans relire un journal. Un script ferait tourner les mêmes commandes ; il ne
donnerait aucune de ces trois propriétés.

*S'appuie sur* : `taches-graphe` ; le chapitre de l'architecture, section de l'orchestration.

### 27. « Comment votre chaîne se comporterait-elle à plus grande échelle ? »

Je ne le sais pas, et je n'en tire aucun argument : la volumétrie est celle d'un établissement de
cette taille — 346 149 lignes sur 11 tables et 912 jours —, pas celle d'une épreuve de charge. Ce que
je peux dire est ce qui casserait en premier. Le rapprochement compare 5 014 paires candidates après
blocage ; le blocage est quadratique dans le pire cas, et c'est lui qu'il faudrait revoir avant tout
le reste. Le rafraîchissement de l'instantané, lui, échange des noms de table en une transaction :
son coût ne dépend pas du volume, et il tiendrait.

*S'appuie sur* : `source-lignes-total`, `source-tables`, `periode-jours`, `paires-candidates` ; le
chapitre de l'architecture.

### 28. « Pourquoi un schéma figé plutôt que lire directement la couche analytique ? »

Parce que c'est mesuré. Une reconstruction de la couche analytique fait disparaître ses vues pendant
environ trois dixièmes de seconde, et un lecteur concurrent y rencontre une erreur d'objet
inexistant — pas une attente. Le rafraîchissement construit donc des tables neuves sous des noms
provisoires, puis échange **tous les noms dans une seule transaction**, si bien qu'un lecteur ne voit
jamais un état mi-neuf mi-ancien. Je précise que la chaîne **vise** cette propriété : aucun contrôle
du dépôt ne l'établit formellement.

*S'appuie sur* : le chapitre du tableau de bord, section de l'instantané ;
`tests/test_instantane_transparence.py`.

---

## IX. Deux questions qu'on peut me poser et auxquelles je réponds mal

Elles sont ici pour que je ne les découvre pas devant le jury.

### 29. « Votre tableau de bord a-t-il été utilisé par le service ? »

**Non.** Il tourne dans un conteneur, sur un jeu engendré, et personne du service ne l'a ouvert. Je
n'ai donc aucun retour d'usage : ni sur l'ergonomie, ni sur la pertinence des indicateurs retenus, ni
sur ce qui manquerait. Les 9 pages et les 40 indicateurs sont dérivés de ce que le règlement demande
et de ce que la statistique nationale attend, pas de ce qu'un agent a réclamé. C'est une limite que
je ne peux pas contourner : la contrainte de confidentialité m'a tenu à distance des données, et le
calendrier du stage à distance des utilisateurs.

### 30. « Combien de temps une journée complète met-elle à se traiter, de bout en bout ? »

**Je ne l'ai pas mesuré**, et je ne veux pas l'inventer. J'ai mesuré une seule durée de la chaîne, et
c'est celle du rafraîchissement de l'instantané, parce qu'elle conditionnait une propriété que je
devais démontrer. Le reste — le chargement, la couche de transformation, le rapprochement — n'a
jamais été chronométré, parce qu'aucune conclusion du rapport n'en dépendait. Si le jury veut un
ordre de grandeur, je préfère dire que je ne l'ai pas mesuré plutôt que de donner un chiffre que je
ne pourrais pas soutenir.
