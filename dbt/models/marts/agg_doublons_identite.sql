{#
    Une ligne par critère de collision exacte, mesuré sur les patients de version
    courante de dim_patient. Cet agrégat COMPTE et EXPOSE des collisions exactes
    uniquement -- il ne réconcilie ni ne fusionne aucun patient. Un critère en
    collision exacte est un signal ; un rapprochement probabiliste relève d'un
    autre traitement, hors de cette couche.

    Deux critères retenus, mesurés non dégénérés en J0 :
      - nom_date_naissance : prénom (colonne nom, cf. generator/patients.py) + nom de
        famille 1 + date de naissance. Aucune valeur vide sur ce critère (0/25842).
      - piece_identite : type de pièce d'identité + numéro de pièce d'identité.
        268/25842 patients courants ont une valeur vide sur ce critère (case retirée
        du calcul des groupes, comptée séparément ci-dessous).

    Un troisième critère envisagé (numéro de téléphone) a été écarté en J0 : mesuré
    dégénéré, 24594/25842 (95 %) des patients courants concernés, jusqu'à 10 patients
    par valeur -- un partage de téléphone de foyer par construction du générateur, pas
    un signal de doublon. Il n'apparaît pas dans cet agrégat.

    patients_examines est le même sur toutes les lignes : le nombre total de patients
    de version courante, y compris ceux à valeur vide sur le critère (la colonne
    patients_valeur_vide indique combien en sont retirés avant le calcul des groupes).
    Les valeurs vides sont exclues du calcul des groupes ; nombre de patients concernés,
    taille du plus grand groupe et taille médiane des groupes ne portent que sur les
    patients à valeur renseignée sur le critère.
#}

with patients_courants as (
    select * from {{ ref('dim_patient') }}
    where est_courante
),

groupes_nom as (
    select count(*) as taille
    from patients_courants
    where
        nom is not null
        and nom != ''
        and nom_famille_1 is not null
        and nom_famille_1 != ''
        and date_naissance is not null
    group by nom, nom_famille_1, date_naissance
    having count(*) >= 2
),

groupes_piece as (
    select count(*) as taille
    from patients_courants
    where
        type_piece_identite is not null
        and type_piece_identite != ''
        and n_piece_identite is not null
        and n_piece_identite != ''
    group by type_piece_identite, n_piece_identite
    having count(*) >= 2
),

criteres as (
    select
        'nom_date_naissance' as critere,
        (select count(*) from patients_courants) as patients_examines,
        (
            select count(*) from patients_courants
            where nom is null or nom = '' or nom_famille_1 is null or nom_famille_1 = '' or date_naissance is null
        ) as patients_valeur_vide,
        (select count(*) from groupes_nom) as nombre_groupes,
        (select coalesce(sum(taille), 0) from groupes_nom) as patients_concernes,
        (select coalesce(max(taille), 0) from groupes_nom) as taille_plus_grand_groupe,
        (select percentile_cont(0.5) within group (order by taille) from groupes_nom) as taille_mediane_groupes

    union all

    select
        'piece_identite' as critere,
        (select count(*) from patients_courants) as patients_examines,
        (
            select count(*) from patients_courants
            where
                type_piece_identite is null
                or type_piece_identite = ''
                or n_piece_identite is null
                or n_piece_identite = ''
        ) as patients_valeur_vide,
        (select count(*) from groupes_piece) as nombre_groupes,
        (select coalesce(sum(taille), 0) from groupes_piece) as patients_concernes,
        (select coalesce(max(taille), 0) from groupes_piece) as taille_plus_grand_groupe,
        (select percentile_cont(0.5) within group (order by taille) from groupes_piece) as taille_mediane_groupes
)

select * from criteres
