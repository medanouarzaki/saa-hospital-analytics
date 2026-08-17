"""Contrôles du tableau de bord : navigation, restriction de couche, indicateurs de la page écrite.

Aucun travail au niveau du module : ni connexion, ni lecture de variable d'environnement, ni
chargement du registre à l'import. Le fichier se collecte sur un clone frais sans base ni variable
exportée.

Aucun littéral de volumétrie. Chaque attendu est une égalité entre deux calculs indépendants — la
valeur qu'une requête de page produit contre une seconde mesure écrite autrement, la date affichée
contre celle mesurée sur la couche source.

Les propriétés qui interrogent la base établissent leur précondition : elles rafraîchissent
l'instantané si son état ne peut être lu, plutôt que de supposer qu'un travail antérieur l'a fait.
"""

from __future__ import annotations

import ast
import re
from datetime import date
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
DASHBOARD = RACINE / "dashboard"
REGISTRE = DASHBOARD / "indicateurs.yml"
POINT_ENTREE = DASHBOARD / "app.py"
PAGES = DASHBOARD / "pages"


# Les pages écrites à ce jour. Ce n'est pas un attendu de volumétrie : c'est le sujet des
# propriétés qui portent sur les indicateurs, et les autres s'y ajouteront à mesure qu'elles
# existeront. La liste se dérive des fichiers présents plutôt que d'être tenue à la main.
def pages_ecrites() -> list[str]:
    return sorted(fichier.stem for fichier in PAGES.glob("*.py"))


PAGE_ECRITE = "activite"

MOTIF_PAGE_DECLAREE = re.compile(r"""st\.Page\(\s*["']pages/([a-z_]+)\.py""")

# Les affectations de la page dont les contrôles ont besoin, lues sans rendre la page.
_NOEUDS_LUS = ("FAMILLES", "_UNION_JOURS", "REQUETES")


def _registre() -> dict:
    return yaml.safe_load(REGISTRE.read_text(encoding="utf-8"))


def _pages_declarees() -> list[str]:
    return MOTIF_PAGE_DECLAREE.findall(POINT_ENTREE.read_text(encoding="utf-8"))


def _requetes_de_page(nom: str) -> dict[str, str]:
    """Les requêtes d'une page, lues sans exécuter la page.

    Exécuter le module rendrait la page, ce qui exige un contexte d'affichage ; n'évaluer que ses
    affectations de premier niveau donne la même valeur sans rien rendre. Les affectations dont
    l'évaluation échoue — celles qui dépendent d'un import d'affichage — sont ignorées : seules
    comptent celles dont `REQUETES` a besoin.
    """
    arbre = ast.parse((PAGES / f"{nom}.py").read_text(encoding="utf-8"))
    local: dict = {}
    for noeud in arbre.body:
        if not isinstance(noeud, ast.Assign):
            continue
        module = ast.Module(body=[noeud], type_ignores=[])
        try:
            exec(compile(module, "page", "exec"), local)
        except Exception:
            continue
    assert "REQUETES" in local, f"la page {nom} ne définit pas de requêtes lisibles"
    return local["REQUETES"]


def _lecture():
    """Importé à l'appel, jamais à l'import : le module ouvre des connexions."""
    from dashboard import lecture

    return lecture


def _instantane_pret(lecture) -> dict:
    """Précondition établie ici, non héritée : si l'état ne peut être lu, on rafraîchit."""
    try:
        etat = lecture.etat()
    except Exception:
        etat = None
    if etat is None or etat.get("rafraichi_le") is None:
        from instantane import rafraichir

        reussite, message = rafraichir.rafraichir()
        if not reussite:
            pytest.fail(f"l'instantané ne peut être constitué : {message}")
        etat = lecture.etat()
    return etat


def test_la_navigation_ne_declare_que_des_pages_du_registre() -> None:
    """La navigation et le registre déclarent exactement les mêmes pages.

    La correspondance est vérifiée dans les DEUX sens, et leurs décomptes sont comparés : chaque
    membre est calculé de son côté — les pages déclarées lues dans le point d'entrée, les pages
    distinctes lues dans le registre — et jamais comparé à un littéral.
    """
    declarees = _pages_declarees()
    connues = set(_registre()["pages"])

    assert declarees, "le point d'entrée ne déclare aucune page"
    assert len(declarees) == len(set(declarees)), f"pages déclarées en double : {declarees}"

    inconnues = sorted(set(declarees) - connues)
    assert not inconnues, f"pages déclarées mais absentes du registre : {inconnues}"

    non_declarees = sorted(connues - set(declarees))
    assert not non_declarees, f"pages du registre non déclarées à la navigation : {non_declarees}"

    assert len(set(declarees)) == len(connues), (
        f"{len(set(declarees))} pages déclarées contre {len(connues)} pages distinctes au registre"
    )

    sans_fichier = [nom for nom in declarees if not (PAGES / f"{nom}.py").exists()]
    assert not sans_fichier, f"pages déclarées sans fichier : {sans_fichier}"


def test_la_restriction_de_couche_est_effective() -> None:
    """Garantie structurelle, éprouvée et non affirmée : une lecture non qualifiée d'une autre
    couche échoue, parce que le chemin de recherche ne porte que le schéma d'instantané."""
    lecture = _lecture()
    _instantane_pret(lecture)

    dans_l_instantane = lecture.interroger("select count(*) as n from fct_sejour")
    assert dans_l_instantane["n"][0] > 0, "l'instantané paraît vide"

    with pytest.raises(Exception) as capture:
        lecture.interroger("select count(*) from patients")
    assert "does not exist" in str(capture.value), (
        f"une table d'une autre couche a été atteinte sans qualification : {capture.value}"
    )


def test_aucune_page_n_ouvre_de_connexion() -> None:
    """Toute lecture passe par le module unique : aucune page n'importe de connecteur."""
    interdits = ("psycopg", "sqlalchemy", "chargeur", "appliquer_ddl")
    fautifs = []
    for fichier in sorted(PAGES.glob("*.py")):
        arbre = ast.parse(fichier.read_text(encoding="utf-8"))
        for noeud in ast.walk(arbre):
            noms = []
            if isinstance(noeud, ast.Import):
                noms = [alias.name for alias in noeud.names]
            elif isinstance(noeud, ast.ImportFrom):
                noms = [noeud.module or ""] + [alias.name for alias in noeud.names]
            for nom in noms:
                if any(interdit in nom for interdit in interdits):
                    fautifs.append(f"{fichier.name} importe {nom}")
    assert not fautifs, "des pages ouvrent leur propre accès à la base : " + " | ".join(fautifs)


def test_les_indicateurs_des_pages_et_du_registre_se_correspondent() -> None:
    """Correspondance dans les deux sens, pour chacune des pages écrites."""
    for page in pages_ecrites():
        _correspondance_d_une_page(page)


def _correspondance_d_une_page(page: str) -> None:
    source = (PAGES / f"{page}.py").read_text(encoding="utf-8")
    attendus = {
        entree["identifiant"] for entree in _registre()["indicateurs"] if entree["page"] == page
    }
    assert attendus, f"le registre ne déclare aucun indicateur pour la page {page}"

    # Le contrôle textuel est éprouvé contre un cas positif construit AVANT que son silence ne
    # soit cru : un identifiant qui figure certainement dans la source doit être trouvé, et un
    # identifiant certainement absent ne doit pas l'être.
    # La recherche porte sur le MOT ENTIER : une simple inclusion de chaîne trouverait
    # `activite_profil_horaire` à l'intérieur de `activite_profil_horaire_retire`, et un
    # indicateur renommé passerait pour présent. Le tiret bas étant un caractère de mot, une
    # limite de mot ne se place pas entre lui et ce qui le suit — c'est précisément ce qui fait
    # que la forme suffixée n'est pas reconnue.
    def cite(identifiant: str) -> bool:
        return re.search(rf"\b{re.escape(identifiant)}\b", source) is not None

    temoin_present = sorted(attendus)[0]
    assert cite(temoin_present), "le contrôle ne trouve pas un identifiant pourtant présent"
    assert not cite(temoin_present + "_temoin_absent"), (
        "le contrôle trouve un identifiant pourtant absent"
    )

    manquants = sorted(identifiant for identifiant in attendus if not cite(identifiant))
    assert not manquants, f"indicateurs du registre absents de la page {page} : {manquants}"

    requetes = _requetes_de_page(page)
    en_trop = sorted(set(requetes) - attendus)
    assert not en_trop, f"indicateurs rendus par la page {page} et absents du registre : {en_trop}"

    # Citer un identifiant ne suffit pas : la page doit l'AFFICHER. Les appels au rendu du titre
    # d'indicateur sont relevés dans l'arbre syntaxique, ce qui observe le rendu plutôt que la
    # simple présence du nom dans le fichier — une mutation retirant un affichage est restée verte
    # tant que le contrôle se contentait de chercher la chaîne.
    rendus = set()
    for noeud in ast.walk(ast.parse(source)):
        if not isinstance(noeud, ast.Call):
            continue
        cible = noeud.func
        nom = cible.attr if isinstance(cible, ast.Attribute) else getattr(cible, "id", "")
        if nom == "titre_indicateur" and noeud.args:
            premier = noeud.args[0]
            if isinstance(premier, ast.Constant) and isinstance(premier.value, str):
                rendus.add(premier.value)

    non_rendus = sorted(attendus - rendus)
    assert not non_rendus, f"indicateurs du registre non affichés par la page {page} : {non_rendus}"
    rendus_inconnus = sorted(rendus - attendus)
    assert not rendus_inconnus, (
        f"indicateurs affichés par la page {page} et absents du registre : {rendus_inconnus}"
    )


def test_chaque_indicateur_egale_sa_seconde_mesure() -> None:
    """Chaque valeur produite est confrontée à un calcul écrit autrement, jamais à un littéral."""
    lecture = _lecture()
    _instantane_pret(lecture)
    requetes = _requetes_de_page(PAGE_ECRITE)

    total_evenements = int(
        lecture.interroger(
            """select count(*) as n from (
                 select date_rendez_vous as j from fct_rendez_vous
                 where date_rendez_vous is not null
                 union all select date_entree from fct_passage where date_entree is not null
                 union all select jour_admission from fct_sejour where jour_admission is not null
               ) as tous"""
        )["n"][0]
    )

    ecarts = []

    volumes = lecture.interroger(requetes["activite_volume_journalier"])
    if int(volumes["evenements"].sum()) != total_evenements:
        ecarts.append(
            f"volume journalier : {int(volumes['evenements'].sum())} contre {total_evenements}"
        )

    patients = lecture.interroger(requetes["activite_patients_distincts"])
    if int(patients["evenements"].sum()) != total_evenements:
        ecarts.append(
            f"patients distincts : {int(patients['evenements'].sum())} contre {total_evenements}"
        )

    for identifiant in ("activite_effet_ramadan", "activite_effet_calendaire"):
        table = lecture.interroger(requetes[identifiant])
        if int(table["evenements"].sum()) != total_evenements:
            ecarts.append(
                f"{identifiant} : {int(table['evenements'].sum())} contre {total_evenements}"
            )

    # Le profil de semaine se confronte ligne à ligne, les deux membres étant calculés séparément
    # et divisés en dehors du serveur.
    profil = lecture.interroger(requetes["activite_profil_semaine"])
    evenements = lecture.interroger(
        """select extract(isodow from j)::int as jsi, f as famille, count(*) as n from (
             select date_rendez_vous as j, 'Consultations' as f from fct_rendez_vous
             where date_rendez_vous is not null
             union all select date_entree, 'Passages' from fct_passage where date_entree is not null
             union all select jour_admission, 'Admissions' from fct_sejour
             where jour_admission is not null
           ) as tous group by 1, 2"""
    )
    jours = lecture.interroger(
        """with b as (select min(j) as d, max(j) as f from (
              select date_rendez_vous as j from fct_rendez_vous where date_rendez_vous is not null
              union all select date_entree from fct_passage where date_entree is not null
              union all select jour_admission from fct_sejour
              where jour_admission is not null) as t)
           select extract(isodow from date_jour)::int as jsi, count(*) as n
           from dim_date, b where date_jour between b.d and b.f group by 1"""
    )
    par_jour = dict(zip(jours["jsi"], jours["n"], strict=True))
    seconde = {
        (int(ligne.jsi), ligne.famille): float(ligne.n) / par_jour[int(ligne.jsi)]
        for ligne in evenements.itertuples()
    }
    for ligne in profil.itertuples():
        cle = (int(ligne.jour_semaine_iso), ligne.famille)
        attendu = seconde.get(cle, 0.0)
        if abs(float(ligne.moyenne_journaliere) - attendu) > 1e-9:
            ecarts.append(f"profil de semaine {cle} : {ligne.moyenne_journaliere} contre {attendu}")

    horaire = lecture.interroger(requetes["activite_profil_horaire"])
    total_horaire = int(
        lecture.interroger(
            """select count(*) as n from (
                 select date_heure_entree as h from fct_passage where date_heure_entree is not null
                 union all select date_heure_arrivee from fct_passage_urgence
                 where date_heure_arrivee is not null
                 union all select date_heure_admission from fct_sejour
                 where date_heure_admission is not null
               ) as tous"""
        )["n"][0]
    )
    if int(horaire["evenements"].sum()) != total_horaire:
        ecarts.append(f"profil horaire : {int(horaire['evenements'].sum())} contre {total_horaire}")

    assert not ecarts, "valeurs divergentes de leur seconde mesure : " + " | ".join(ecarts)


def test_les_indicateurs_des_trois_pages_egalent_leur_seconde_mesure() -> None:
    """Chaque valeur confrontée à un calcul écrit par un autre chemin.

    Les taux des rendez-vous sont recalculés par les pages depuis le code d'état brut ; la seconde
    mesure vient des agrégats de la chaîne, qui les calculent depuis les colonnes booléennes. Les
    deux chemins sont donc réellement distincts, et non deux variantes du même.
    """
    lecture = _lecture()
    _instantane_pret(lecture)
    ecarts = []

    def sans_filtre(page: str, identifiant: str) -> str:
        requete = _requetes_de_page(page)[identifiant]
        return requete.format(filtre="") if "{filtre}" in requete else requete

    # Rendez-vous : les taux, contre l'agrégat d'absentéisme de la chaîne.
    agregat = lecture.interroger(
        "select code_activite, taux_absenteisme, taux_annulation from agg_absenteisme"
    ).set_index("code_activite")
    for identifiant, colonne_page, colonne_agregat in (
        ("rendez_vous_taux_absence", "taux_absence", "taux_absenteisme"),
        ("rendez_vous_taux_annulation", "taux_annulation", "taux_annulation"),
    ):
        page = lecture.interroger(sans_filtre("rendez_vous", identifiant)).set_index(
            "code_activite"
        )
        for code in page.index:
            attendu = float(agregat.loc[code, colonne_agregat])
            obtenu = float(page.loc[code, colonne_page])
            if abs(obtenu - attendu) > 1e-12:
                ecarts.append(f"{identifiant}[{code}] : {obtenu} contre {attendu}")

    # Rendez-vous : le délai, contre l'agrégat des délais.
    delais_agregat = lecture.interroger(
        "select code_activite, mediane_delai_positif_jours, p90_delai_positif_jours "
        "from agg_delai_rendez_vous"
    ).set_index("code_activite")
    delais = lecture.interroger(
        sans_filtre("rendez_vous", "rendez_vous_delai_obtention")
    ).set_index("code_activite")
    for code in delais.index:
        for colonne_page, colonne_agregat in (
            ("mediane_jours", "mediane_delai_positif_jours"),
            ("p90_jours", "p90_delai_positif_jours"),
        ):
            attendu = float(delais_agregat.loc[code, colonne_agregat])
            obtenu = float(delais.loc[code, colonne_page])
            if abs(obtenu - attendu) > 1e-12:
                ecarts.append(f"délai[{code}].{colonne_page} : {obtenu} contre {attendu}")

    # Urgences : les effectifs, contre un décompte direct de la table de faits.
    passages = int(lecture.interroger("select count(*) as n from fct_passage_urgence")["n"][0])
    for identifiant, colonne in (
        ("urgences_passages_par_niveau", "passages"),
        ("urgences_orientation_sortie", "passages"),
    ):
        obtenu = int(lecture.interroger(sans_filtre("urgences", identifiant))[colonne].sum())
        if obtenu != passages:
            ecarts.append(f"{identifiant} : {obtenu} contre {passages}")

    # Urgences : la part relevant d'une consultation ordinaire, contre les deux derniers niveaux
    # de tri déterminés par une requête séparée.
    ordinaire = lecture.interroger(sans_filtre("urgences", "urgences_consultation_ordinaire")).iloc[
        0
    ]
    seconde = lecture.interroger(
        """with derniers as (
               select distinct niveau_tri from fct_passage_urgence where niveau_tri is not null
               order by niveau_tri desc limit 2
           )
           select count(*) filter (where niveau_tri in (select niveau_tri from derniers))::numeric
                  / count(*) as part
           from fct_passage_urgence"""
    )["part"][0]
    if abs(float(ordinaire["part"]) - float(seconde)) > 1e-12:
        ecarts.append(f"consultation ordinaire : {ordinaire['part']} contre {seconde}")

    # Séjours : les grandeurs réglementaires, recalculées ici depuis les mêmes ingrédients bruts.
    capacite = int(
        lecture.interroger(
            "select valeur from instantane_parametres where nom = 'capacite_litiere_fonctionnelle'"
        )["valeur"][0]
    )
    reglementaires = lecture.interroger(
        sans_filtre("sejours", "sejours_indicateurs_reglementaires") % {"capacite": capacite}
    ).iloc[0]
    ingredients = lecture.interroger(
        """select count(*) as sejours, sum(duree_jours) as journees,
                  max(coalesce(jour_sortie, jour_admission)) - min(jour_admission) + 1 as jours
           from fct_sejour"""
    ).iloc[0]
    attendus = {
        "taux_occupation": float(ingredients["journees"]) / (int(ingredients["jours"]) * capacite),
        "duree_moyenne_jours": float(ingredients["journees"]) / int(ingredients["sejours"]),
        "rotation": int(ingredients["sejours"]) / capacite,
    }
    for colonne, attendu in attendus.items():
        obtenu = float(reglementaires[colonne])
        if abs(obtenu - attendu) > 1e-9:
            ecarts.append(f"{colonne} : {obtenu} contre {attendu}")

    # Séjours : les non clos, contre l'absence de date de sortie plutôt que le drapeau.
    non_clos = lecture.interroger(sans_filtre("sejours", "sejours_non_clos")).iloc[0]
    seconde_non_clos = int(
        lecture.interroger("select count(*) as n from fct_sejour where date_heure_sortie is null")[
            "n"
        ][0]
    )
    if int(non_clos["non_clos"]) != seconde_non_clos:
        ecarts.append(f"séjours non clos : {int(non_clos['non_clos'])} contre {seconde_non_clos}")

    assert not ecarts, "valeurs divergentes de leur seconde mesure : " + " | ".join(ecarts)


def test_les_indicateurs_de_facturation_et_de_qualite_egalent_leur_seconde_mesure() -> None:
    """Chaque valeur confrontée à un calcul écrit par un autre chemin."""
    lecture = _lecture()
    _instantane_pret(lecture)
    ecarts = []

    def sans_filtre(page: str, identifiant: str, **parametres) -> str:
        requete = _requetes_de_page(page)[identifiant]
        if "{filtre}" in requete:
            requete = requete.format(filtre="")
        return requete % parametres if parametres else requete

    # Facturation : les montants, contre un décompte direct de la table de faits.
    total = lecture.interroger(
        "select sum(montant_total) as montant, count(*) as factures, "
        "sum(part_organisme) as organisme, sum(part_patient) as patient from fct_facturation"
    ).iloc[0]

    montants = lecture.interroger(sans_filtre("facturation", "facturation_montants_par_type"))
    if abs(float(montants["montant"].astype(float).sum()) - float(total["montant"])) > 1e-6:
        ecarts.append("montants par type : somme différente du total facturé")
    if int(montants["factures"].sum()) != int(total["factures"]):
        ecarts.append("montants par type : décompte différent")

    parts = lecture.interroger(sans_filtre("facturation", "facturation_part_organisme_patient"))
    for colonne, attendu in (
        ("part_organisme", total["organisme"]),
        ("part_patient", total["patient"]),
    ):
        if abs(float(parts[colonne].astype(float).sum()) - float(attendu)) > 1e-6:
            ecarts.append(f"part organisme/patient : {colonne} divergente")

    # Le taux de recouvrement lit l'agrégat ; la seconde mesure repart des créances brutes, en ne
    # retenant que le dernier instantané de chaque créance — une créance y porte une ligne par
    # extraction, et les sommer toutes la compterait plusieurs fois.
    taux = lecture.interroger(sans_filtre("facturation", "facturation_taux_recouvrement")).iloc[0]
    seconde = lecture.interroger(
        """with dernier as (
               select distinct on (n_creance) montant_du, montant_recouvre
               from int_creances order by n_creance, date_extraction desc)
           select sum(montant_recouvre) / sum(montant_du) as taux from dernier"""
    )["taux"][0]
    if abs(float(taux["taux"]) - float(seconde)) > 1e-9:
        ecarts.append(f"taux de recouvrement : {taux['taux']} contre {seconde}")

    encaissement = lecture.interroger(
        sans_filtre("facturation", "facturation_taux_encaissement")
    ).iloc[0]
    attendu = lecture.interroger(
        "select (select sum(montant) from fct_encaissement) "
        "/ (select sum(montant_total) from fct_facturation) as taux"
    )["taux"][0]
    if abs(float(encaissement["taux"]) - float(attendu)) > 1e-12:
        ecarts.append("taux d'encaissement divergent")

    # Épisodes non facturés : la seconde mesure emploie une sous-requête d'existence plutôt qu'une
    # jointure à gauche.
    non_factures = lecture.interroger(
        sans_filtre("facturation", "facturation_episodes_non_factures")
    )
    par_famille = lecture.interroger(
        """select p.type_passage as famille, count(*) as episodes,
                  count(*) filter (where not exists (
                      select 1 from fct_facturation f where f.n_episode = p.n_passage))
                      as non_factures
           from fct_passage p group by p.type_passage"""
    ).set_index("famille")
    groupes = non_factures.groupby("famille")[["episodes", "non_factures"]].sum()
    for famille in groupes.index:
        for colonne in ("episodes", "non_factures"):
            if int(groupes.loc[famille, colonne]) != int(par_famille.loc[famille, colonne]):
                ecarts.append(f"épisodes non facturés [{famille}].{colonne} divergent")

    # Qualité : les décomptes de complétude, contre un décompte direct de l'agrégat.
    completude = lecture.interroger(sans_filtre("qualite", "qualite_completude_champs")).iloc[0]
    controle = lecture.interroger(
        "select count(*) as couples, count(*) filter (where taux_completude >= 1) as complets, "
        "count(distinct nom_table) as tables from agg_qualite_donnees"
    ).iloc[0]
    for colonne, attendu in (
        ("couples_examines", controle["couples"]),
        ("couples_complets", controle["complets"]),
        ("tables_examinees", controle["tables"]),
    ):
        if int(completude[colonne]) != int(attendu):
            ecarts.append(f"complétude : {colonne} divergent")

    provenance = lecture.interroger(sans_filtre("qualite", "qualite_provenance_champs"))
    if abs(float(provenance["part_pourcent"].astype(float).sum()) - 100.0) > 0.2:
        ecarts.append("provenance : les parts ne somment pas à cent")

    assert not ecarts, "valeurs divergentes de leur seconde mesure : " + " | ".join(ecarts)


def test_l_anciennete_des_creances_part_de_la_date_de_reference() -> None:
    """L'ancienneté se compte depuis la date des données, jamais depuis l'horloge.

    Le contrôle distingue réellement les deux : il vérifie d'abord que les deux dates diffèrent —
    sans quoi il ne prouverait rien — puis compare l'ancienneté maximale rendue par la page à celle
    qu'on obtient en partant de la date de référence, et vérifie qu'elle diffère de celle qu'on
    obtiendrait en partant de la date du jour.
    """
    lecture = _lecture()
    _instantane_pret(lecture)

    ecarts = lecture.interroger(
        "select max(date_reference_donnees) as reference, current_date as horloge, "
        "current_date - max(date_reference_donnees) as jours from instantane_etat"
    ).iloc[0]
    assert int(ecarts["jours"]) > 0, (
        f"la date de référence {ecarts['reference']} coïncide avec la date du jour : le contrôle "
        "ne distinguerait pas les deux origines et ne prouverait rien"
    )

    tranches = _requetes_de_page("facturation")["facturation_anciennete_creances"]
    from dashboard.pages import facturation as page_facturation  # noqa: PLC0415

    bornes = page_facturation.TRANCHES_ANCIENNETE
    rendue = lecture.interroger(
        tranches
        % {
            "borne_a": bornes[0],
            "borne_b": bornes[1],
            "borne_c": bornes[2],
            "borne_d": bornes[3],
        }
    )
    maximum_rendu = int(rendue["anciennete_maximale"].max())

    attendus = lecture.interroger(
        """with dernier as (
               select distinct on (n_creance) montant_restant, date_naissance_creance
               from int_creances order by n_creance, date_extraction desc)
           select max((select max(date_reference_donnees) from instantane_etat)
                      - date_naissance_creance) as depuis_reference,
                  max(current_date - date_naissance_creance) as depuis_horloge
           from dernier where montant_restant > 0"""
    ).iloc[0]

    assert maximum_rendu == int(attendus["depuis_reference"]), (
        f"ancienneté maximale rendue {maximum_rendu}, attendue "
        f"{int(attendus['depuis_reference'])} depuis la date de référence"
    )
    assert maximum_rendu != int(attendus["depuis_horloge"]), (
        f"ancienneté maximale rendue {maximum_rendu} égale celle qu'on obtiendrait depuis "
        "l'horloge : l'origine du calcul n'est pas la date de référence"
    )


def test_les_indicateurs_du_rapprochement_egalent_leur_seconde_mesure() -> None:
    """Les cinq valeurs de la page, confrontées à des calculs écrits autrement.

    Le croisement des deux méthodes est reconstruit ici **en dehors du serveur**, à partir des
    deux ensembles de paires obtenus séparément : c'est un chemin réellement distinct de la
    jointure externe que la page emploie.
    """
    lecture = _lecture()
    _instantane_pret(lecture)
    requetes = _requetes_de_page("rapprochement")
    ecarts = []

    seuil = lecture.interroger(requetes["rapprochement_seuil"]).iloc[0]
    porte = lecture.interroger("select distinct seuil from grappes_identite")["seuil"][0]
    if abs(float(seuil["seuil_applique"]) - float(porte)) > 1e-12:
        ecarts.append(f"seuil : {seuil['seuil_applique']} contre {porte}")

    grappes = lecture.interroger(requetes["rapprochement_grappes"])
    compte = lecture.interroger(
        "select count(distinct grappe_id) as grappes, count(*) as enregistrements "
        "from grappes_identite"
    ).iloc[0]
    for colonne in ("grappes", "enregistrements"):
        if int(grappes[colonne].sum()) != int(compte[colonne]):
            ecarts.append(
                f"grappes.{colonne} : {int(grappes[colonne].sum())} contre {int(compte[colonne])}"
            )

    courbe = lecture.interroger(requetes["rapprochement_courbe"])
    seuils = int(lecture.interroger("select count(*) as n from evaluation")["n"][0])
    if len(courbe) != seuils:
        ecarts.append(f"courbe : {len(courbe)} points contre {seuils}")

    collisions = lecture.interroger(requetes["rapprochement_collisions_exactes"])
    agregat = lecture.interroger(
        "select critere, nombre_groupes, patients_concernes from agg_doublons_identite"
    )
    if int(collisions["nombre_groupes"].sum()) != int(agregat["nombre_groupes"].sum()):
        ecarts.append("collisions : décompte de groupes divergent")

    apport = lecture.interroger(requetes["rapprochement_apport"]).iloc[0]
    probabiliste = lecture.interroger(
        "select a.n_ipp as x, b.n_ipp as y from grappes_identite a "
        "join grappes_identite b on a.grappe_id = b.grappe_id and a.n_ipp < b.n_ipp"
    )
    collision = lecture.interroger(
        """with courants as (select * from dim_patient where est_courante)
           select a.n_ipp as x, b.n_ipp as y from courants a
           join courants b on a.n_ipp < b.n_ipp and a.nom = b.nom
              and a.nom_famille_1 = b.nom_famille_1 and a.date_naissance = b.date_naissance
           where a.nom <> '' and a.nom_famille_1 <> '' and a.date_naissance is not null
           union
           select a.n_ipp, b.n_ipp from courants a
           join courants b on a.n_ipp < b.n_ipp
              and a.type_piece_identite = b.type_piece_identite
              and a.n_piece_identite = b.n_piece_identite
           where a.type_piece_identite <> '' and a.n_piece_identite <> ''"""
    )
    ensemble_p = set(zip(probabiliste["x"], probabiliste["y"], strict=True))
    ensemble_c = set(zip(collision["x"], collision["y"], strict=True))
    attendus = {
        "paires_communes": len(ensemble_p & ensemble_c),
        "regroupees_par_le_probabiliste_seul": len(ensemble_p - ensemble_c),
        "reunies_par_la_collision_seule": len(ensemble_c - ensemble_p),
        "paires_distinctes": len(ensemble_p | ensemble_c),
    }
    for colonne, attendu in attendus.items():
        if int(apport[colonne]) != attendu:
            ecarts.append(f"apport.{colonne} : {int(apport[colonne])} contre {attendu}")

    assert not ecarts, "valeurs divergentes de leur seconde mesure : " + " | ".join(ecarts)


def test_les_quatre_effectifs_du_croisement_sont_coherents() -> None:
    """La somme des trois parts égale le cardinal de l'union, calculé indépendamment.

    Sans cette égalité, les trois effectifs pourraient être justes séparément et décrire des
    ensembles qui ne se recouvrent pas comme ils le prétendent.
    """
    lecture = _lecture()
    _instantane_pret(lecture)
    apport = lecture.interroger(_requetes_de_page("rapprochement")["rapprochement_apport"]).iloc[0]

    somme = (
        int(apport["paires_communes"])
        + int(apport["regroupees_par_le_probabiliste_seul"])
        + int(apport["reunies_par_la_collision_seule"])
    )
    assert somme == int(apport["paires_distinctes"]), (
        f"la somme des trois effectifs vaut {somme} pour une union de "
        f"{int(apport['paires_distinctes'])}"
    )

    # Et chaque total partiel se retrouve de son côté : les paires du rapprochement d'une part,
    # celles de la collision d'autre part.
    total_probabiliste = int(
        lecture.interroger(
            "select count(*) as n from grappes_identite a "
            "join grappes_identite b on a.grappe_id = b.grappe_id and a.n_ipp < b.n_ipp"
        )["n"][0]
    )
    attendu = int(apport["paires_communes"]) + int(apport["regroupees_par_le_probabiliste_seul"])
    assert attendu == total_probabiliste, (
        f"{attendu} paires attribuées au rapprochement contre {total_probabiliste} mesurées"
    )


def test_le_marquage_de_filtrabilite_est_conforme_au_registre() -> None:
    """Ce que l'ÉCRAN marque se déduit du registre, dans les deux sens.

    Le contrôle observe ce que la fonction de marquage émet réellement, et non ce que le registre
    dit : vérifier la seule lecture du registre reviendrait à comparer un résultat à lui-même, et
    laisserait passer un marquage retiré ou ajouté à tort — c'est ce qu'une mutation a montré.

    La vérification porte aussi sur la clause de période effectivement produite : un indicateur
    marqué hors filtre ne doit recevoir aucune restriction, sans quoi l'écran et la requête
    diraient deux choses différentes.
    """
    from dashboard import rendu

    periode = (date(2024, 1, 1), date(2024, 12, 31))
    emis: list[str] = []
    origine = rendu.st.warning
    rendu.st.warning = lambda message, **_: emis.append(str(message))
    try:
        fautifs = []
        for page in pages_ecrites():
            for entree in _registre()["indicateurs"]:
                if entree["page"] != page:
                    continue
                identifiant = entree["identifiant"]
                attendue = entree["filtrabilite"]

                emis.clear()
                rendu.mention_de_filtrabilite(identifiant)
                marque = len(emis)

                if attendue == "oui" and marque:
                    fautifs.append(f"{identifiant} : filtrable mais marqué « {emis[0][:60]} »")
                if attendue != "oui" and not marque:
                    fautifs.append(f"{identifiant} : déclaré {attendue} mais non marqué")
                if attendue == "non" and marque and rendu.MENTION_HORS_FILTRE not in emis[0]:
                    fautifs.append(f"{identifiant} : marqué sans la mention hors filtre")
                if attendue == "oui_sous_reserve" and marque:
                    if rendu.MENTION_SOUS_RESERVE not in emis[0]:
                        fautifs.append(f"{identifiant} : marqué sans la mention de réserve")
                    if " ".join(entree["reserve"].split())[:40] not in emis[0]:
                        fautifs.append(
                            f"{identifiant} : la réserve affichée n'est pas celle du registre"
                        )

                clause = rendu.clause_periode(identifiant, periode)
                if attendue == "non" and clause:
                    fautifs.append(
                        f"{identifiant} : déclaré hors filtre mais restreint par « {clause} »"
                    )
                if attendue != "non" and not clause:
                    fautifs.append(f"{identifiant} : déclaré filtrable mais sans restriction")
    finally:
        rendu.st.warning = origine

    assert not fautifs, "marquage non conforme au registre : " + " | ".join(fautifs)


def test_la_mention_de_source_est_conforme_au_registre() -> None:
    """Un indicateur non recalculé depuis les faits le dit, et lui seul.

    Le contrôle observe ce que la fonction de mention ÉMET, en interceptant les appels
    d'affichage : vérifier la seule lecture du registre reviendrait à comparer un résultat à
    lui-même, faiblesse déjà mesurée sur le marquage de filtrabilité.

    Le comportement se déduit du registre — toute valeur de recalcul autre que « faits » entraîne
    une mention. Les indicateurs que l'enregistrement de décision sur les écarts nomme en sont un
    sous-ensemble strict : la vérification porte donc sur le registre, et l'appartenance des
    indicateurs nommés est vérifiée en plus.
    """
    from dashboard import rendu

    emis: list[str] = []
    origine = rendu.st.caption
    rendu.st.caption = lambda message, **_: emis.append(str(message))
    try:
        fautifs = []
        for page in pages_ecrites():
            for entree in _registre()["indicateurs"]:
                if entree["page"] != page:
                    continue
                identifiant = entree["identifiant"]
                source = entree["recalcule_depuis"]

                emis.clear()
                rendu.mention_de_source(identifiant)
                marque = [message for message in emis if rendu.MENTION_SOURCE in message]

                if source == "faits" and marque:
                    fautifs.append(f"{identifiant} : recalculé depuis les faits mais marqué")
                if source != "faits" and not marque:
                    fautifs.append(f"{identifiant} : recalculé depuis « {source} » mais non marqué")
                if source != "faits" and marque:
                    lisible = rendu.SOURCES_LISIBLES.get(source)
                    if lisible and lisible not in marque[0]:
                        fautifs.append(
                            f"{identifiant} : la mention ne dit pas ce que l'indicateur lit"
                        )
    finally:
        rendu.st.caption = origine

    assert not fautifs, "mention de source non conforme au registre : " + " | ".join(fautifs)


def test_les_indicateurs_nommes_par_l_enregistrement_portent_une_mention() -> None:
    """Les indicateurs que l'enregistrement de décision nomme sont bien marqués.

    L'enregistrement en nomme moins que le registre n'en compte : son premier écart ne couvre que
    les indicateurs lisant une couche amont là où une table de faits pourrait exister. Ce contrôle
    vérifie l'inclusion, non l'égalité — exiger l'égalité contredirait la règle selon laquelle le
    comportement se déduit du registre.
    """
    from dashboard import rendu

    nommes = {
        "facturation_taux_recouvrement",
        "facturation_aboutissement_relances",
        "facturation_anciennete_creances",
        "qualite_completude_champs",
        "qualite_taux_quarantaine",
        "rapprochement_collisions_exactes",
    }
    ecrits = {
        entree["identifiant"]
        for entree in _registre()["indicateurs"]
        if entree["page"] in pages_ecrites()
    }
    a_verifier = sorted(nommes & ecrits)
    assert a_verifier, "aucun des indicateurs nommés n'appartient à une page écrite"

    sans_mention = [
        identifiant for identifiant in a_verifier if rendu.source_de_valeur(identifiant) == "faits"
    ]
    assert not sans_mention, (
        f"des indicateurs nommés par l'enregistrement seraient marqués comme recalculés depuis "
        f"les faits : {sans_mention}"
    )


def test_une_page_sans_indicateur_filtrable_affiche_pourquoi() -> None:
    """La troisième branche du mécanisme : pas de filtre, et le motif AFFICHÉ.

    Vérifier que la page ne porte pas de filtre ne suffit pas : la décision veut qu'elle dise
    pourquoi, faute de quoi un lecteur chercherait un filtre absent. Le contrôle observe donc ce
    que la fonction émet, et non seulement ce qu'elle rend comme valeur — une mutation retirant le
    message est restée verte tant qu'il ne l'observait pas.
    """
    from dashboard import rendu

    for page in pages_ecrites():
        valeurs = {entree["filtrabilite"] for entree in rendu.indicateurs_de(page)}
        attendu = valeurs != {"non"}
        assert rendu.page_porte_un_filtre(page) is attendu, (
            f"page {page} : filtre {'attendu' if attendu else 'non attendu'} "
            f"pour des filtrabilités {sorted(valeurs)}"
        )

    sans_filtre = [page for page in pages_ecrites() if not rendu.page_porte_un_filtre(page)]
    assert sans_filtre, (
        "aucune page écrite n'est dépourvue de filtre : la branche correspondante du mécanisme "
        "n'est éprouvée sur aucun cas réel"
    )

    emis: list[str] = []
    origine = rendu.st.info
    rendu.st.info = lambda message, **_: emis.append(str(message))
    try:
        for page in sans_filtre:
            emis.clear()
            resultat = rendu.filtre_de_page(page)
            assert resultat is None, f"page {page} : un filtre a été rendu malgré tout"
            assert emis, f"page {page} : aucun motif affiché à la place du filtre"
            motifs = {
                rendu.MOTIFS_LISIBLES.get(entree.get("motif"), entree.get("motif", ""))
                for entree in rendu.indicateurs_de(page)
            }
            manquants = [motif for motif in motifs if motif and motif not in emis[0]]
            assert not manquants, f"page {page} : le motif affiché ne reprend pas {manquants}"
    finally:
        rendu.st.info = origine

    mixtes = [
        page
        for page in pages_ecrites()
        if len({entree["filtrabilite"] for entree in rendu.indicateurs_de(page)}) > 1
    ]
    assert mixtes, "aucune page écrite ne mêle des filtrabilités : le cas mixte n'est pas éprouvé"

    # Chaque page doit demander SON PROPRE filtre. Vérifier le seul comportement de la fonction
    # partagée laisserait passer une page qui l'appellerait avec le nom d'une autre — elle
    # afficherait alors le filtre d'autrui, ou le tairait à tort.
    fautifs = []
    for page in pages_ecrites():
        arbre = ast.parse((PAGES / f"{page}.py").read_text(encoding="utf-8"))
        constantes = {
            cible.id: noeud.value.value
            for noeud in arbre.body
            if isinstance(noeud, ast.Assign) and isinstance(noeud.value, ast.Constant)
            for cible in noeud.targets
            if isinstance(cible, ast.Name)
        }
        appels = [
            noeud
            for noeud in ast.walk(arbre)
            if isinstance(noeud, ast.Call)
            and getattr(noeud.func, "attr", getattr(noeud.func, "id", "")) == "filtre_de_page"
        ]
        if not appels:
            # La page d'activité porte son propre filtre, écrit avant que le mécanisme partagé
            # n'existe. Ce n'est pas une faute de conformité — tous ses indicateurs sont
            # filtrables, et elle n'a donc rien à marquer — mais une divergence à résorber quand
            # ce fichier sera rouvert. L'absence d'appel est donc relevée sans être assertée.
            continue
        for appel in appels:
            argument = appel.args[0] if appel.args else None
            if isinstance(argument, ast.Constant):
                demandee = argument.value
            elif isinstance(argument, ast.Name):
                demandee = constantes.get(argument.id)
            else:
                demandee = None
            if demandee != page:
                fautifs.append(f"{page} : demande le filtre de « {demandee} »")
    assert not fautifs, "pages demandant le filtre d'une autre : " + " | ".join(fautifs)


def _module_de_page(nom: str) -> dict:
    """Le module d'une page, chargé sans être rendu.

    L'appel de rendu final est retiré avant exécution : le module s'évalue alors entièrement —
    imports, constantes et fonctions — sans exiger de contexte d'affichage. C'est ce qui permet
    d'éprouver ce que la page FAIT, et non seulement ce qu'elle contient.
    """
    source = (PAGES / f"{nom}.py").read_text(encoding="utf-8")
    source = source.replace("\nrendre()\n", "\n")
    espace: dict = {}
    exec(compile(source, f"{nom}.py", "exec"), espace)
    return espace


def test_la_capacite_affichee_egale_celle_de_la_table_de_parametres() -> None:
    """La valeur et sa provenance, séparément, telles que LA PAGE les obtient.

    Le contrôle appelle la fonction de la page plutôt que d'interroger la table lui-même :
    interroger la table reviendrait à comparer un résultat à lui-même et laisserait passer une
    page qui afficherait une provenance inventée — c'est ce qu'une mutation a montré.

    Un taux d'occupation affiché sans dire sur quelle capacité il est calculé n'est pas un
    indicateur, c'est un nombre ; la provenance doit donc désigner un fichier qui existe et une
    clé qui nomme ce paramètre.
    """
    lecture = _lecture()
    _instantane_pret(lecture)

    page = _module_de_page("sejours")
    nom_parametre = page["PARAMETRE_CAPACITE"]
    obtenu = page["_capacite"]()

    porte = lecture.interroger(
        "select valeur, provenance_fichier, provenance_cle from instantane_parametres "
        f"where nom = '{nom_parametre}'"
    )
    assert not porte.empty, f"paramètre absent de la table de paramètres : {nom_parametre}"
    ligne = porte.iloc[0]

    for colonne in ("valeur", "provenance_fichier", "provenance_cle"):
        assert obtenu[colonne] == ligne[colonne], (
            f"la page obtient {colonne} = « {obtenu[colonne]} » là où la table de paramètres "
            f"porte « {ligne[colonne]} »"
        )

    fichier = RACINE / obtenu["provenance_fichier"]
    assert fichier.exists(), (
        f"la provenance affichée désigne {obtenu['provenance_fichier']}, qui n'existe pas"
    )

    contenu = yaml.safe_load(fichier.read_text(encoding="utf-8"))
    attendue = {entree["nom"]: entree["valeur"] for entree in contenu["parametres"]}.get(
        nom_parametre
    )
    assert attendue is not None, f"{nom_parametre} absent de {obtenu['provenance_fichier']}"
    assert str(attendue) == obtenu["valeur"], (
        f"capacité {obtenu['valeur']} affichée contre {attendue} dans le fichier que sa "
        "provenance désigne"
    )
    assert nom_parametre in obtenu["provenance_cle"], (
        f"la clé de provenance « {obtenu['provenance_cle']} » ne nomme pas {nom_parametre}"
    )


def test_le_cache_s_invalide_au_rafraichissement() -> None:
    """Un rafraîchissement fait bien réexécuter les requêtes, et pas seulement avancer une date.

    La sonde est une requête dont le résultat change à CHAQUE exécution : si elle rend deux fois la
    même valeur, c'est que le cache a servi ; si elle en rend une nouvelle, c'est qu'elle a été
    réexécutée. Les deux faits sont vérifiés, dans cet ordre — sans le premier, le second passerait
    trivialement avec un cache inopérant.

    Vérifier seulement que l'horodatage avance ne prouverait rien sur le cache : il faut observer
    que la clé en dépend, donc que la requête est réellement rejouée.
    """
    from instantane import rafraichir

    lecture = _lecture()
    avant = _instantane_pret(lecture)["rafraichi_le"]

    sonde = "select clock_timestamp() as instant"
    premiere = lecture.interroger(sonde)["instant"][0]
    seconde = lecture.interroger(sonde)["instant"][0]
    assert premiere == seconde, (
        "deux lectures identiques ont rendu des valeurs différentes : le cache ne sert pas, "
        "et l'invalidation ne peut donc pas être éprouvée"
    )

    reussite, message = rafraichir.rafraichir()
    assert reussite, message

    apres = lecture.etat()["rafraichi_le"]
    assert apres > avant, (
        f"l'horodatage n'a pas avancé après un rafraîchissement : {avant} puis {apres}"
    )

    troisieme = lecture.interroger(sonde)["instant"][0]
    assert troisieme != premiere, (
        "la même valeur est rendue après un rafraîchissement : la clé de cache ne dépend pas de "
        "l'horodatage, et un état périmé resterait affiché"
    )


def test_la_date_de_reference_est_celle_des_donnees() -> None:
    """La date affichée vient de la table d'état, elle-même égale à la dernière extraction
    chargée, mesurée indépendamment sur la couche source."""
    lecture = _lecture()
    portee = _instantane_pret(lecture)["date_reference"]

    import psycopg

    from ingestion import appliquer_ddl

    variables = appliquer_ddl.charger_environnement()
    conn = psycopg.connect(
        host=variables["POSTGRES_HOST"],
        port=variables["POSTGRES_PORT"],
        dbname=variables["POSTGRES_DB"],
        user=variables["POSTGRES_USER"],
        password=variables.get("POSTGRES_PASSWORD", ""),
    )
    try:
        with conn.cursor() as curseur:
            curseur.execute(
                "select table_name from information_schema.columns "
                "where table_schema = 'source' and column_name = 'date_extraction'"
            )
            tables = [ligne[0] for ligne in curseur.fetchall()]
            union = " union all ".join(
                f"select max(to_date(date_extraction, 'MM/DD/YYYY')) as d from source.{table}"
                for table in tables
            )
            curseur.execute(f"select max(d) from ({union}) as toutes")
            attendue = curseur.fetchone()[0]
    finally:
        conn.close()

    assert portee == attendue, (
        f"date de référence affichée {portee}, dernière extraction chargée {attendue}"
    )
