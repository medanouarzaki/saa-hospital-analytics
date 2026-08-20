# saa-hospital-analytics

Une chaîne de données, du jeu de données jusqu'au tableau de bord, pour le service
d'accueil et d'admission d'un hôpital : génération, chargement, entrepôt dimensionnel,
rapprochement d'identités, orchestration, restitution.

## Le problème

Un service d'accueil et d'admission enregistre des rendez-vous, des passages aux urgences, des
séjours et des factures dans un progiciel hospitalier. Les données existent ; les grandeurs qui
permettraient d'arbitrer — délai d'obtention d'un rendez-vous, taux d'absence par activité,
ancienneté des créances, part des dossiers en double — n'en sortent pas. Ce dépôt construit la
chaîne qui les produirait, et la fait tourner de bout en bout.

Il ne la fait pas tourner sur les données du service : elles ne sont pas sorties de
l'établissement, et un stagiaire n'a accès qu'à un seul des cinq profils applicatifs. Le jeu sur
lequel elle tourne est donc **entièrement simulé**, à partir de paramètres relevés dans des
statistiques publiques et des textes réglementaires marocains quand une source les établit, et
posés quand aucune ne le fait.

## Ce qu'il faut savoir avant de lire un chiffre

**Aucune donnée n'est réelle.** Ni patient, ni dossier, ni établissement. Identifiants, numéros de
pièce d'identité et numéros de téléphone sont tirés dans des espaces disjoints des séries
réellement émises. Les 23 fichiers de `echantillon/` portent la mention sur chacune de leurs
lignes, dans leurs propres octets.

**Un seul profil applicatif sur cinq a été observé au poste**, `MSM - GESTION DE RDV` ; les quatre
autres sont reconstruits par voie documentaire. Le registre des champs le porte champ par champ :
sur 175 champs, 81 sont observés, 72 documentés par une source écrite, 22 posés faute de source.

**Aucun chiffre du tableau de bord ne mesure l'activité d'un établissement réel.** Une relation
qu'on y lit peut avoir été mise dans les paramètres du générateur ; le registre des relations
injectées liste celles qui le sont, et le tableau de bord les marque à l'écran. Ce que la chaîne
démontre est qu'elle sait calculer ces grandeurs, non ce qu'elles vaudraient ailleurs.

## Ce que fait la chaîne

Le générateur produit 912 jours d'activité, du 1er janvier 2024 au 30 juin 2026, à partir de
fichiers de paramètres versionnés. Le chargement les verse dans 11 tables de couche source, en
mettant en quarantaine plutôt qu'en écartant les lignes qui violent une règle. L'entrepôt les
modélise en 11 modèles intermédiaires puis en 6 dimensions, 6 tables de faits et 7 agrégats, la
dimension des patients étant historisée. Le rapprochement d'identités compare les fiches deux à
deux et les regroupe au-dessus d'un seuil dont la précision et le rappel sont mesurés. Un schéma
d'instantané de 26 objets fige ce que le tableau de bord lit, et le tableau de bord affiche 40
indicateurs sur 9 pages, chacun défini dans un registre et confronté à une seconde mesure par un
contrôle.

## Faire tourner la chaîne

Le dépôt ne contient aucune donnée : elles se produisent en local. Tout ce qui suit la mise en
route de la composition est indispensable, faute de quoi le tableau de bord démarre sans rien
pouvoir afficher — le schéma `instantane` qu'il interroge n'existe pas encore.

Il faut Docker, Docker Compose, `uv` et Python 3.12.

1. Copier `.env.example` vers `.env`, puis renseigner **toutes** ses clés. Aucune n'a de valeur par
   défaut : nom de projet Docker Compose, hôte, port, base, utilisateur et mot de passe PostgreSQL,
   identifiant d'utilisateur du système pour Airflow (`AIRFLOW_UID`, la valeur de `id -u`), ports
   publiés d'Airflow et de Streamlit, clé Fernet et clé d'API d'Airflow, identifiants de son
   administrateur. La clé Fernet est une clé de 32 octets encodée en base64 URL :
   `python -c "import base64, secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"`.
2. Installer l'environnement Python : `uv sync --frozen`.
3. Lancer `docker compose -f docker/docker-compose.yml --env-file .env up --wait`.
4. Exporter les variables de connexion dans le shell, en plus du fichier : `set -a; . ./.env; set +a`.
   Les modules d'ingestion lisent `.env` mais ceux de rapprochement attendent les variables dans
   l'environnement.
5. Produire le jeu de données : `uv run python -m generator generator/output`.
6. Appliquer les schémas : `uv run python ingestion/appliquer_ddl.py` puis
   `uv run python -m linkage.appliquer_ddl`. Les deux sont **rejouables** : chaque objet est
   supprimé s'il existe avant d'être recréé, si bien qu'une seconde application aboutit et laisse
   le catalogue dans le même état. Elles **détruisent en revanche les données déjà chargées** des
   tables qu'elles recréent : les rejouer impose de recharger les données.
7. Charger les données : `uv run python -m ingestion.chargeur generator/output/scenario_30`.
8. Déclarer le profil de connexion de dbt. Il ne figure pas dans le dépôt : écrire un
   `profiles.yml` sous `~/.dbt/` ou pointer `DBT_PROFILES_DIR` sur un répertoire qui en contient un,
   avec les variables `DBT_POSTGRES_HOST`, `DBT_POSTGRES_PORT`, `DBT_POSTGRES_USER`,
   `DBT_POSTGRES_PASSWORD` et `DBT_POSTGRES_DB` renseignées. Le fichier de workflow d'intégration
   continue en donne un exemple complet.
9. Construire l'entrepôt, puis le valider :
   `cd dbt && uv run dbt seed && uv run dbt run --threads 1 && uv run dbt test`, **puis revenir à
   la racine du dépôt** (`cd ..`) : les commandes suivantes s'exécutent depuis la racine, et lancées
   depuis `dbt/` elles échouent sur `No module named 'linkage'`.
10. Rapprocher les identités puis constituer l'instantané que lit le tableau de bord :
    `uv run python -m linkage.prediction`, `uv run python -m linkage.evaluation`,
    `uv run python -m instantane.rafraichir`. Le rapprochement lit la vérité terrain du scénario
    produit par la génération ci-dessus (`VERITE_TERRAIN_PATIENTS`). Ses deux artefacts tabulaires
    (`linkage/courbe_precision_rappel.csv`, `linkage/ablation.csv`) sont versionnés et réécrits à
    chaque exécution : pour ne pas salir l'arbre de travail, rediriger le premier avec
    `CHEMIN_COURBE_PRECISION_RAPPEL`. Le second se redirige avec `CHEMIN_CSV_ABLATION`, mais son
    contrôle lit le chemin par défaut : le rediriger lui ferait lire un fichier périmé.
11. Ouvrir le tableau de bord sur le port déclaré par `STREAMLIT_PORT` dans `.env`.
12. Facultatif, et seul moyen de peupler `exports/` : `uv run python -m livraison.exporter` produit
    le classeur et les fichiers tabulaires de restitution à partir de l'instantané. Le répertoire
    reste vide tant que cette commande n'a pas été lancée.

Le graphe quotidien (`airflow/saa_daily.py`) enchaîne génération, chargement, construction,
rapprochement et rafraîchissement pour une date d'extraction donnée, une fois les schémas en place.

## Le tableau de bord

Ses 9 pages sont rangées en deux sections nommées par leur public. **Pilotage du service** porte
les 34 indicateurs dont la valeur peut changer une décision : activité, rendez-vous, urgences,
séjours, facturation, qualité des données, et une page qui rend les lignes derrière un chiffre
agrégé. **Évaluation de la chaîne** porte les 6 autres — ce que vaut le rapprochement d'identités,
d'où viennent les définitions du modèle, et les deux corrélations qui ne font que rendre visible un
paramètre posé d'avance.

## L'échantillon versé au dépôt

`echantillon/` contient 23 fichiers à séparateur virgule, un par table, prélevés systématiquement
— une ligne sur *N*, dans l'ordre d'une clé stable — et reproductibles. Ils montrent la **forme**
des données. Ils ne mesurent rien : un extrait d'une ligne sur *N* ne porte aucun total, aucune
moyenne et aucune proportion exploitables, et les compter donnerait des chiffres faux. Le document
qui les accompagne le redit et dit d'où ils sortent.

## Où trouver quoi

| Répertoire | Rôle |
| --- | --- |
| `generator/` | Génération du jeu de données simulé et de sa configuration |
| `ingestion/` | Chargement des données générées vers l'entrepôt, et quarantaine |
| `dbt/` | Modélisation dimensionnelle de l'entrepôt |
| `linkage/` | Rapprochement probabiliste d'identités et son évaluation |
| `instantane/` | Schéma figé que lit le tableau de bord |
| `airflow/` | Orchestration des traitements |
| `dashboard/` | Tableau de bord de restitution, et le registre de ses indicateurs |
| `livraison/` | Production du classeur et des fichiers de restitution |
| `exports/` | Fichiers produits par la commande de restitution ; vide tant qu'elle n'a pas été lancée |
| `echantillon/` | Extrait de chaque table, chaque ligne portant sa mention de simulation |
| `extraction/` | Engendrement de cet extrait |
| `docker/` | Socle de conteneurisation |
| `tests/` | 62 fichiers de contrôle, 454 propriétés |
| `report/` | Bibliographie et dictionnaire de données du rapport ; le rapport lui-même n'y est pas encore |
| `slides/` | Emplacement du support de présentation, vide à ce jour |
| `docs/` | Registres de champs et de sources, relevé d'observation, reconstruction documentaire, et 52 enregistrements de décision |

Les décisions de conception ne sont pas dans ce fichier : chacune a son enregistrement sous
`docs/decisions/`, avec ce qui a été mesuré avant de trancher, ce qui a été écarté, et ce qui
aurait invalidé la décision. Les champs du modèle sont dans `docs/champs/`, leurs sources — 32 —
dans `docs/sources/`.

## Contrôles

L'intégration continue exécute 6 jobs : style et garde-fou de collecte, la matrice des contrôles,
la provenance des colonnes, l'entrepôt dbt, la chaîne complète jusqu'au tableau de bord, et la
composition du rapport et de la présentation. Les contrôles n'affirment aucune volumétrie écrite
d'avance : chaque attendu est une égalité entre deux mesures calculées séparément.

Le rapport et la présentation sont composés à chaque exécution et publiés en artefacts. **La
compilation qui fait foi est celle de l'intégration continue** : aucun PDF n'est versé au dépôt, et
une distribution locale ne sert qu'à relire. Les sources vivent sous `report/` et `slides/` ; les
noms de personnes ne figurent que dans `report/marqueurs.tex`, dont un contrôle vérifie qu'aucun
n'est resté vide.
