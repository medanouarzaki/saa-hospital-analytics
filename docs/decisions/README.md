# Enregistrements de décision

Une décision de conception par fichier, numérotée à la suite. Chacun porte ce qui a été mesuré avant
de trancher, ce qui a été écarté, et ce qui aurait invalidé la décision.

Cet index vit ici, à côté des fichiers qu'il liste, et non dans le fichier de présentation du dépôt :
il est ainsi tenu par le même contrôle qui vérifie les enregistrements, et un enregistrement ajouté
sans sa ligne fait rougir ce contrôle plutôt que de passer inaperçu.

**Le numéro 0009 est vacant.** Aucun fichier ne l'a jamais porté — vérifié sur l'historique entier du
dépôt. Il n'est pas comblé : renuméroter rendrait faux tout renvoi existant à un numéro, et un
enregistrement écrit pour occuper la place serait un enregistrement sans décision. La vacance est
donc déclarée ici, et le contrôle de numérotation l'admet nommément plutôt que de la découvrir à
chaque exécution.

| Numéro | Ce qu'il tranche |
| --- | --- |
| [0001](0001-postgresql-plutot-que-duckdb.md) | PostgreSQL plutôt que DuckDB pour la couche de persistance |
| [0002](0002-schema-en-etoile.md) | La couche analytique est organisée en schéma en étoile |
| [0003](0003-volumetrie.md) | Volumétrie du jeu de données |
| [0004](0004-historisation-type-2-dimension-patient.md) | La dimension patient conserve l'historique des versions plutôt que de l'écraser |
| [0005](0005-rapprochement-probabiliste-plutot-que-collision-exacte.md) | Le rapprochement des fiches patient est probabiliste ; la collision exacte reste comme témoin |
| [0006](0006-registre-de-provenance-unique.md) | Un registre unique porte la provenance de chaque champ, et quatre artefacts en dérivent |
| [0007](0007-grain-des-prises-en-charge.md) | Une prise en charge par épisode, et non par facture, par ligne ni par couverture |
| [0008](0008-quarantaine-plutot-que-suppression.md) | Une ligne rejetée est mise en quarantaine avec son motif, jamais supprimée |
| [0010](0010-aucune-image-du-systeme.md) | Aucune image du système d'information hospitalier |
| [0011](0011-grain-du-laboratoire.md) | Grain de l'activité de laboratoire |
| [0012](0012-mode-execution-orchestrateur.md) | Mode d'exécution de l'orchestrateur |
| [0013](0013-relations-injectees.md) | Registre des relations injectées |
| [0014](0014-typage-couche-source.md) | Typage et absence de contraintes dans la couche source |
| [0015](0015-inversion-derivation-taux-hospitalisation-urgences.md) | La part des séjours issus des urgences est posée, le taux d'hospitalisation aux urgences en est dérivé |
| [0016](0016-changements-metier-sur-les-fiches-reextraites.md) | Les fiches patient réextraites portent un changement métier tiré, enregistré en vérité terrain |
| [0017](0017-version-en-vigueur-a-la-date-de-levenement.md) | Les lecteurs aval d'une colonne patient modifiable utilisent la version en vigueur à la date de l'événement |
| [0018](0018-architecture-dbt-vues-et-nommage.md) | dbt matérialise en vues, `profiles.yml` vit hors dépôt, les macros de conversion s'appuient sur des formats mesurés |
| [0019](0019-seed-calendrier-marocain-et-dim-date.md) | le seed du calendrier marocain est dérivé mécaniquement, testé en équivalence et en synchronisation, `dim_date` couvre à partir d'août 2023 |
| [0020](0020-dimensions-simples-cle-naturelle.md) | quatre dimensions simples à clé naturelle, aucun libellé inventé, sans clé de substitution |
| [0021](0021-dim-patient-scd2.md) | dim_patient en SCD type 2, bornes semi-ouvertes alignées sur la sémantique du générateur |
| [0022](0022-strategie-ci-dbt.md) | la CI exécute dbt sur un sous-ensemble de trois mois, avec confrontation comptable des retraits légitimes du chargement |
| [0023](0023-grain-des-tables-de-faits-et-rattachement-patient.md) | Grain des six tables de faits et rattachement à la version du patient |
| [0024](0024-limites-documentees-des-faits.md) | Ce que les faits ne portent pas : quatre limites documentées plutôt que comblées |
| [0025](0025-methode-conformite-delai-rendez-vous.md) | Méthode de conformité du délai de rendez-vous : population, tolérance à deux termes |
| [0026](0026-garde-applicabilite-indicateurs-sejour.md) | Garde d'applicabilité des indicateurs de séjour : abstention plutôt que tolérance élargie |
| [0027](0027-materialisation-dbt-un-seul-fil.md) | La matérialisation dbt s'exécute sur un seul fil, les tests gardent leur parallélisme |
| [0028](0028-agregats-grain-perimetre-et-limites.md) | Les agrégats : grain de chacun, choix guidés par mesure, et le huitième maintenu hors dbt |
| [0029](0029-moteur-execution-en-memoire.md) | Le rapprochement s'exécute sur un moteur en mémoire, pas sur PostgreSQL |
| [0030](0030-quatre-regles-de-blocage.md) | Quatre règles de blocage, pas les trois annoncées au périmètre |
| [0031](0031-vacuite-convertie-en-valeur-absente-a-l-extraction.md) | La vacuité est convertie en valeur absente à l'extraction |
| [0032](0032-ddl-schema-linkage-ecrit-a-la-main.md) | Le DDL du schéma `linkage` est écrit à la main |
| [0033](0033-niveau-absence-unilaterale-piece-identite-conserve.md) | Le niveau d'absence unilatérale de la pièce d'identité est conservé |
| [0034](0034-metrique-primaire-paire-secondaire-grappe.md) | Métrique primaire au niveau de la paire, secondaire au niveau de la grappe |
| [0035](0035-seuil-choisi-sans-etiquettes.md) | Le seuil se choisit sur des propriétés observables sans étiquettes |
| [0036](0036-grain-date-extraction.md) | Le grain d'une exécution est la date d'extraction |
| [0037](0037-idempotence-portee-par-le-chargement.md) | L'idempotence est portée par le chargement, pas par la couche dimensionnelle |
| [0038](0038-generation-et-schemas-hors-du-graphe.md) | La génération et l'application des schémas restent hors du graphe |
| [0039](0039-chemins-sortie-rapprochement-parametrables.md) | Les chemins de sortie du rapprochement deviennent paramétrables, valeur par défaut inchangée |
| [0040](0040-controle-qualite-taux-rejet-cumule.md) | Le contrôle de qualité bloque sur le taux de rejet cumulé de la journée |
| [0041](0041-taches-export-instantane-vides.md) | Les tâches d'export et de rafraîchissement de l'instantané existent en aboutissement vide |
| [0042](0042-isolation-composition-arretee-env-deplace.md) | Isolation d'un instrument jetable : composition arrêtée, `.env` déplacé hors du dépôt |
| [0043](0043-instantane-schema-dedie-du-tableau-de-bord.md) | Le tableau de bord lit un schéma dédié de tables, rafraîchi par échange de noms |
| [0044](0044-registre-des-indicateurs-fichier-unique-teste.md) | La définition de chaque indicateur est portée par un registre unique, vérifié par test |
| [0045](0045-composition-des-sept-pages.md) | Le tableau de bord compte sept pages, et les indicateurs sans matière sont retirés |
| [0046](0046-filtre-de-periode-porte-par-page.md) | Le filtre de période est porté par page, et son absence est affichée plutôt que tue |
| [0047](0047-ecarts-assumes-au-cadrage.md) | Trois écarts au cadrage sont consignés plutôt que contournés |
| [0048](0048-correlation-inter-et-intra-specialite.md) | La corrélation délai/absentéisme est dédoublée : entre activités et à l'intérieur de chacune |
| [0049](0049-documentation-des-couches-aval.md) | Toute colonne des couches aval est déclarée et décrite ; le registre des champs n'est pas étendu |
| [0050](0050-libelles-de-dimension-la-ou-une-source-les-documente.md) | Un code de dimension porte son libellé si une source l'établit, et reste nu sinon |
| [0051](0051-la-page-des-donnees-et-la-composition-a-huit-pages.md) | Le tableau de bord compte huit pages : une page donne les lignes derrière les chiffres |
| [0052](0052-echantillon-de-donnees-au-depot.md) | Un échantillon de données est versé au dépôt, chaque ligne portant sa mention |
| [0053](0053-separation-des-deux-publics.md) | Le tableau de bord se sépare en deux publics, et le classement se dérive de la décision servie |
| [0054](0054-disjonction-structurelle-des-champs-synthetiques.md) | Aucun champ synthétique ne prend une valeur structurellement possible dans son espace réel |
| [0055](0055-le-filet-de-numerotation-interne-et-ses-temoins.md) | Un filet par motif textuel n'est éprouvé que si chaque forme a son témoin, dans les deux sens |
| [0056](0056-convention-unique-des-indicateurs-de-sejour-affiches.md) | Convention unique pour les quatre indicateurs de séjour affichés |
| [0057](0057-correspondance-entre-le-registre-des-indicateurs-et-l-usage.md) | Le registre des indicateurs, la couche que les pages lisent, et le contrôle qui les relie |
| [0058](0058-injection-des-doublons-d-identite.md) | Une personne retenue reçoit une seconde fiche, et une seule, ouverte à un épisode tiré |
| [0059](0059-la-divergence-des-durees-entre-sejour-et-passage-n-est-pas-regeneree.md) | Les deux faits ne s'accordent pas sur la fin d'un épisode, et le jeu n'est pas régénéré |
| [0060](0060-le-tableau-de-bord-est-lance-par-le-module-et-non-par-l-executable.md) | Le service d'affichage est lancé par `python -m streamlit`, jamais par l'exécutable |
| [0061](0061-les-grandeurs-decimales-sont-converties-a-l-affichage-seulement.md) | Une grandeur décimale est convertie en nombre à virgule pour être tracée, et là seulement |
| [0062](0062-l-etat-declare-du-document-et-ses-marqueurs-nominatifs.md) | Le document déclare son état, et cet état dit ce que ses marqueurs nominatifs doivent porter |
| [0063](0063-la-prose-du-rapport-porte-les-memes-etiquettes-de-provenance-que-les-colonnes.md) | La prose du rapport porte les mêmes étiquettes de provenance que les colonnes de l'entrepôt |
| [0064](0064-le-releve-de-champs-est-la-troisieme-etiquette-de-la-provenance-de-la-prose.md) | Le relevé de champs est la troisième étiquette de la provenance de la prose, et son sens manquant est écrit |
| [0065](0065-ce-qui-etablit-un-constat-et-ce-qu-un-indicateur-demontre.md) | Ce qui établit un constat et ce qu'un indicateur démontre sont deux choses, et le rapport les sépare |
| [0066](0066-le-registre-des-chiffres-et-ce-que-l-integration-continue-n-en-prouve-pas.md) | Aucun nombre du rapport n'est tapé : un registre des chiffres, et ce que l'intégration continue n'en prouve pas |
| [0067](0067-trois-grandeurs-la-personne-l-identifiant-et-la-version.md) | La personne, l'identifiant et la version sont trois grandeurs, et le registre des chiffres portait la confusion |
| [0068](0068-la-courbe-de-precision-et-de-rappel-est-composee-et-non-tabulee.md) | La courbe de précision et de rappel est composée par un paquet de tracé, et le choix a été tranché par mesure |
