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
    """Toute page déclarée existe au registre et possède son fichier.

    Le sens réciproque — toute page du registre est déclarée — n'est pas asserté ici : il ne
    pourra l'être qu'une fois les sept pages écrites, et l'asserter maintenant reviendrait à
    exiger la déclaration de pages sans fichier, qui échoueraient à l'affichage.
    """
    declarees = _pages_declarees()
    connues = set(_registre()["pages"])

    assert declarees, "le point d'entrée ne déclare aucune page"
    assert len(declarees) == len(set(declarees)), f"pages déclarées en double : {declarees}"

    inconnues = sorted(set(declarees) - connues)
    assert not inconnues, f"pages déclarées mais absentes du registre : {inconnues}"

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


def test_une_page_sans_indicateur_filtrable_ne_porte_pas_de_filtre() -> None:
    """La troisième branche du mécanisme, éprouvée sur les deux cas qui existent.

    Aucune page écrite n'a aujourd'hui tous ses indicateurs hors filtre ; la fonction est donc
    éprouvée sur ce que le registre porte — au moins une page mixte et aucune page entièrement
    hors filtre — plutôt que sur un cas construit qui ne prouverait rien du registre réel.
    """
    from dashboard import rendu

    for page in pages_ecrites():
        valeurs = {entree["filtrabilite"] for entree in rendu.indicateurs_de(page)}
        attendu = valeurs != {"non"}
        assert rendu.page_porte_un_filtre(page) is attendu, (
            f"page {page} : filtre {'attendu' if attendu else 'non attendu'} "
            f"pour des filtrabilités {sorted(valeurs)}"
        )

    mixtes = [
        page
        for page in pages_ecrites()
        if len({entree["filtrabilite"] for entree in rendu.indicateurs_de(page)}) > 1
    ]
    assert mixtes, (
        "aucune page écrite ne mêle des indicateurs filtrables et non filtrables : le mécanisme "
        "de marquage n'est éprouvé sur aucun cas réel"
    )


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
