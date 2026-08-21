"""Chaque chapitre déclare ce sur quoi il repose, et la déclaration coïncide avec ce qu'il porte.

L'entrepôt étiquette chaque colonne par sa provenance et bloque si une colonne n'en porte pas. La
prose n'avait aucun équivalent : une affirmation pouvait s'écrire sans que rien ne dise d'où elle
venait, et une citation pouvait pointer vers une clé absente sans que rien ne le signale avant la
compilation — qui, elle, se contente d'un point d'interrogation dans le texte.

Trois étiquettes, les mêmes que celles des colonnes :

    DOC  une entrée du registre des sources l'étaye — elle se cite par une commande de citation ;
    OBS  un relevé d'observation l'étaye — aucune source publiée ne la porte ;
    HYP  ni l'une ni l'autre : une convention posée, déclarée comme telle.

LA CORRESPONDANCE EST VÉRIFIÉE DANS LES DEUX SENS. Une clé citée et non déclarée est une source
employée en douce ; une clé déclarée et non citée est une déclaration qui a cessé d'être vraie, et
c'est le cas qui arrive quand un paragraphe est supprimé. Une seule direction ne prouve pas
l'égalité des deux ensembles.

CE CONTRÔLE LIT LES SOURCES, JAMAIS LE PDF : il ne compile rien et ne dépend d'aucune distribution
typographique.

SA PORTÉE COUVRE LES FICHIERS DE CHAPITRE ET LES FICHIERS D'ANNEXE. Elle a été étendue le jour où
les tableaux de relevé exhaustifs sont descendus du corps du rapport vers une annexe : quand une
matière se déplace, c'est la portée du contrôle qui suit la matière, jamais la matière qui reste où
le contrôle sait déjà regarder. Sans cette extension, cinquante-six champs relevés — onglets,
menus, filtres, colonnes de résultat — seraient sortis de toute couverture d'un seul déplacement de
fichier, et le contrôle serait resté vert.

LA PORTÉE EST DÉCLARATIVE, PAS DEVINÉE. Les fichiers d'annexe examinés sont énumérés dans
`ANNEXES`, et cette liste est confrontée aux inclusions de `report/annexes.tex` DANS LES DEUX SENS.
Découvrir les fichiers par une convention de répertoire aurait fait entrer n'importe quel fichier
déposé là sans que personne ne l'ait décidé ; se contenter d'une liste sans la confronter aurait
laissé passer l'inverse.

PAR QUELLE VOIE CE CONTRÔLE SERAIT-IL VERT ALORS QU'UN CHAMP AURAIT PERDU SA PROVENANCE ? Quatre
voies ont été cherchées avant d'écrire l'extension, et les quatre sont fermées.

  1. Un fichier d'annexe ajouté et absent de `ANNEXES`. Ses identifiants ne seraient pas comptés,
     et les champs correspondants tomberaient en orphelins : le contrôle ROUGIT. La voie est
     fermée par construction, et `test_la_liste_des_annexes_coincide_avec_les_inclusions` la
     nomme explicitement.
  2. Un fichier resté dans `ANNEXES` mais que `report/annexes.tex` n'inclut plus. C'est la voie
     dangereuse : le fichier ne serait plus composé, ses champs auraient disparu du document, et
     le contrôle continuerait de compter leurs identifiants. Fermée par la confrontation dans le
     second sens.
  3. `report/annexes.tex` lui-même retiré du fichier principal. Toutes les annexes sortiraient du
     document composé sans qu'aucune liste ne bouge. Fermée par
     `test_les_annexes_sont_incluses_par_le_document`.
  4. Un identifiant porté par une annexe sans être déclaré en tête de celle-ci, ou déclaré sans y
     être porté. Fermée par la correspondance dans les deux sens, qui s'applique désormais aux
     annexes comme aux chapitres.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
REPORT = RACINE / "report"
CHAPITRES = REPORT / "chapitres"
PRINCIPAL = REPORT / "rapport.tex"
ANNEXES_PRINCIPAL = REPORT / "annexes.tex"

# Les fichiers d'annexe que ce contrôle examine, au même titre que les fichiers de chapitre. La
# liste est DÉCLARÉE ici et confrontée aux inclusions de `report/annexes.tex` dans les deux sens :
# un fichier ajouté à l'un sans l'autre fait rougir un contrôle.
#
# `dictionnaire_donnees.tex` n'y figure pas, et c'est délibéré : il est produit mécaniquement
# depuis le registre des champs, ne porte aucune déclaration de provenance et n'a pas à en porter
# — `tests/test_provenance.py` le compare au registre dont il dérive. L'écarter ici est donc une
# décision, pas un oubli, et `EXCLUS` la rend visible plutôt que silencieuse.
ANNEXES = ("releve_des_ecrans.tex",)
EXCLUS = ("dictionnaire_donnees.tex",)
BIBLIO = REPORT / "biblio.bib"
MARQUEURS = REPORT / "marqueurs.tex"
SOURCES = RACINE / "docs" / "sources" / "sources.yml"
RELEVE = RACINE / "docs" / "observation" / "releve_champs.yml"
REGISTRE_CHAMPS = RACINE / "docs" / "champs" / "registre_champs.yml"

ETIQUETTES = ("DOC", "OBS", "HYP")

# Un commentaire LaTeX s'ouvre sur un caractère de pourcentage non échappé. Un pourcentage précédé
# d'un nombre PAIR de contre-obliques est bien un ouvrant ; précédé d'un nombre impair, il est
# échappé et ne commente rien.
_COMMENTAIRE = re.compile(r"(?<!\\)(?:\\\\)*%")

_DECLARATION = re.compile(r"^\s*%\s*(DOC|OBS|HYP)\s*:\s*(.*)$")
_NON_EMPLOYEE = re.compile(r"^\s*%\s*NON-EMPLOYEE\s*:\s*(\S+)\s*—\s*(.+)$")

# La commande de citation, et elle seule : le mot « cite » doit être suivi immédiatement de
# l'accolade ouvrante, sans quoi \citeauthor et ses variantes seraient prises pour elle.
_CITE = re.compile(r"\\cite\{([^}]*)\}")
_RELEVE = re.compile(r"\\releve\{([^}]*)\}")
_CONVENTION = re.compile(r"\\convention\{([^}]*)\}")
_A_REDIGER = re.compile(r"\\aRediger\{([^}]*)\}")

# L'identifiant d'un champ relevé, tel que le relevé et le registre des champs l'écrivent :
# REL-XXX.YNN. La garde finale interdit d'accepter le préfixe d'un identifiant plus long — sans
# elle, `REL-PAT.D100` livrerait `REL-PAT.D10`, qui existe et désigne un autre champ.
_CHAMP_RELEVE = re.compile(r"REL-[A-Z]{3}\.[A-Z][0-9]{2}(?![0-9])")

_SECTIONS_DECLAREES = re.compile(r"^\s*%\s*SECTIONS\s*:\s*([0-9]+)\s*$")
_SECTION = re.compile(r"^\\section\{", re.MULTILINE)

_CLE_BIB = re.compile(r"@misc\{([^,]+),")
_ETAT = re.compile(r"^\s*\\newcommand\{\\etatDuDocument\}\{([^}]*)\}", re.MULTILINE)

AUCUN = {"(aucun)", "(aucune)", ""}


def sans_commentaire(ligne: str) -> str:
    """La partie active d'une ligne : ce qui précède le premier pourcentage non échappé."""
    trouve = _COMMENTAIRE.search(ligne)
    return ligne if trouve is None else ligne[: trouve.end() - 1]


def partie_active(source: str) -> str:
    return "\n".join(sans_commentaire(ligne) for ligne in source.splitlines())


def _liste(valeur: str) -> set[str]:
    if valeur.strip().lower() in AUCUN:
        return set()
    return {morceau.strip() for morceau in valeur.split(",") if morceau.strip()}


def declarations(source: str) -> dict[str, set[str]]:
    """Ce que l'en-tête d'un fichier déclare, par étiquette.

    L'en-tête est fait de commentaires : il se lit sur les lignes BRUTES, pas sur la partie active.
    """
    trouvees: dict[str, set[str]] = {}
    for ligne in source.splitlines():
        correspondance = _DECLARATION.match(ligne)
        if correspondance is None:
            continue
        etiquette, valeur = correspondance.group(1), correspondance.group(2)
        trouvees.setdefault(etiquette, set()).update(_liste(valeur))
    return {etiquette: trouvees.get(etiquette, set()) for etiquette in ETIQUETTES}


def portees(source: str) -> dict[str, set[str]]:
    """Ce qu'un fichier porte réellement, par étiquette, commentaires exclus."""
    actif = partie_active(source)
    doc: set[str] = set()
    for groupe in _CITE.findall(actif):
        doc.update(_liste(groupe))
    obs = set(_RELEVE.findall(actif)) | set(_A_REDIGER.findall(actif))
    # Un tableau de relevé porte les identifiants en clair, sans commande de citation : ils
    # comptent comme cités au même titre.
    obs |= set(_CHAMP_RELEVE.findall(actif))
    hyp = set(_CONVENTION.findall(actif))
    return {"DOC": doc, "OBS": obs, "HYP": hyp}


def cles_bibliographiques() -> set[str]:
    return set(_CLE_BIB.findall(BIBLIO.read_text(encoding="utf-8")))


def registre() -> list[dict]:
    with open(SOURCES, encoding="utf-8") as fichier:
        return yaml.safe_load(fichier)


def cle_de(identifiant: str) -> str:
    return identifiant.lower().replace("-", "")


def non_citables() -> dict[str, str]:
    """Les entrées du registre qui n'entrent pas au fichier bibliographique, par clé attendue."""
    return {
        cle_de(entree["id"]): entree["id"]
        for entree in registre()
        if entree["verification"] == "introuvable"
    }


def citables() -> dict[str, str]:
    return {
        cle_de(entree["id"]): entree["id"]
        for entree in registre()
        if entree["verification"] != "introuvable"
    }


def champs_du_releve() -> dict[str, dict]:
    with open(RELEVE, encoding="utf-8") as fichier:
        donnees = yaml.safe_load(fichier)
    return {champ["id"]: champ for ecran in donnees["ecrans"] for champ in ecran["champs"]}


def non_emplois_declares() -> dict[str, str]:
    """Les champs que le relevé déclare inemployés, avec le motif de leur groupe."""
    with open(RELEVE, encoding="utf-8") as fichier:
        donnees = yaml.safe_load(fichier)
    declares: dict[str, str] = {}
    for groupe in donnees.get("champs_non_employes", []):
        motif = (groupe.get("motif") or "").strip()
        for identifiant in groupe.get("champs", []):
            declares[identifiant] = motif
    return declares


def champs_invoques_par_le_registre() -> set[str]:
    with open(REGISTRE_CHAMPS, encoding="utf-8") as fichier:
        registre = yaml.safe_load(fichier)
    return {entree["preuve"] for entree in registre if entree["provenance"] == "OBS"}


def etat_du_document() -> str | None:
    actif = partie_active(MARQUEURS.read_text(encoding="utf-8"))
    trouve = _ETAT.search(actif)
    return None if trouve is None else trouve.group(1).strip().lower()


def fichiers_de_chapitre() -> list[Path]:
    """Les fichiers de chapitre ET les fichiers d'annexe déclarés.

    Le nom reste celui d'origine parce que la propriété qu'ils partagent est la même : ce sont les
    fichiers de PROSE du rapport, ceux qui portent des citations, des relevés et des conventions,
    et dont la déclaration de tête doit coïncider avec le contenu.
    """
    return sorted(CHAPITRES.glob("*.tex")) + [REPORT / nom for nom in ANNEXES]


_INPUT = re.compile(r"\\input\{([a-z0-9_-]+)\}")


def inclusions_des_annexes() -> set[str]:
    """Les fichiers que `report/annexes.tex` inclut, nom de fichier compris."""
    actif = partie_active(ANNEXES_PRINCIPAL.read_text(encoding="utf-8"))
    return {f"{nom}.tex" for nom in _INPUT.findall(actif)}


def non_employees_declarees() -> dict[str, str]:
    trouvees = {}
    for ligne in PRINCIPAL.read_text(encoding="utf-8").splitlines():
        correspondance = _NON_EMPLOYEE.match(ligne)
        if correspondance is not None:
            trouvees[correspondance.group(1).strip()] = correspondance.group(2).strip()
    return trouvees


# --------------------------------------------------------------------------------------------
# Témoins du motif d'extraction : la règle des deux sens, forme par forme.
# --------------------------------------------------------------------------------------------

TEMOINS_POSITIFS = (
    ("citation simple", r"texte \cite{s30} suite", {"s30"}),
    ("citation multiple", r"texte \cite{s01,s29} suite", {"s01", "s29"}),
    ("citation multiple espacée", r"texte \cite{ s01 , s29 } suite", {"s01", "s29"}),
    ("deux citations séparées", r"\cite{s05} et \cite{s20}", {"s05", "s20"}),
    ("citation en fin de ligne", r"fin de phrase \cite{s12}", {"s12"}),
)

TEMOINS_NEGATIFS = (
    ("clé dans un commentaire", r"% ancienne citation \cite{s99}", set()),
    ("clé après du texte puis commentaire", r"texte \cite{s30} % \cite{s99}", {"s30"}),
    ("pourcentage échappé : la ligne reste active", r"100\% des cas \cite{s30}", {"s30"}),
    ("clé préfixe d'une autre", r"\cite{s301}", {"s301"}),
    ("la chaîne hors de toute commande de citation", r"la clé s30 est mentionnée", set()),
    ("commande homographe", r"\citeauthor{s30}", set()),
)


def test_le_motif_reconnait_chaque_forme_de_citation() -> None:
    for nom, source, attendu in TEMOINS_POSITIFS:
        assert portees(source)["DOC"] == attendu, f"témoin positif « {nom} » : {source!r}"


def test_le_motif_ne_reconnait_pas_ce_qui_n_est_pas_une_citation() -> None:
    for nom, source, attendu in TEMOINS_NEGATIFS:
        assert portees(source)["DOC"] == attendu, f"témoin négatif « {nom} » : {source!r}"


def test_le_motif_reconnait_les_deux_autres_etiquettes() -> None:
    source = r"une valeur\convention{pyramide} et un relevé\releve{equipe}"
    assert portees(source)["HYP"] == {"pyramide"}
    assert portees(source)["OBS"] == {"equipe"}
    assert portees("% " + source)["HYP"] == set(), "un commentaire ne porte rien"
    assert portees("% " + source)["OBS"] == set(), "un commentaire ne porte rien"


def test_la_declaration_se_lit_sur_les_commentaires_d_entete() -> None:
    entete = "%   DOC: s01, s29\n%   OBS: (aucun)\n%   HYP: pyramide\n\\chapter{X}"
    lues = declarations(entete)
    assert lues["DOC"] == {"s01", "s29"}
    assert lues["OBS"] == set(), "« (aucun) » déclare l'ensemble vide, pas un identifiant"
    assert lues["HYP"] == {"pyramide"}


# --------------------------------------------------------------------------------------------
# Les quatre propriétés.
# --------------------------------------------------------------------------------------------


def test_toute_cle_citee_existe_au_fichier_bibliographique() -> None:
    connues = cles_bibliographiques()
    manquantes = []
    for chemin in fichiers_de_chapitre():
        for cle in sorted(portees(chemin.read_text(encoding="utf-8"))["DOC"]):
            if cle not in connues:
                manquantes.append(f"{chemin.name} cite « {cle} », absente de report/biblio.bib")
    assert not manquantes, "citations sans cible :\n  " + "\n  ".join(manquantes)


def test_la_declaration_coincide_avec_ce_que_le_fichier_porte() -> None:
    desaccords = []
    for chemin in fichiers_de_chapitre():
        source = chemin.read_text(encoding="utf-8")
        declare, porte = declarations(source), portees(source)
        for etiquette in ETIQUETTES:
            for absent in sorted(porte[etiquette] - declare[etiquette]):
                desaccords.append(
                    f"{chemin.name} porte {etiquette} « {absent} » sans le déclarer en tête"
                )
            for inutile in sorted(declare[etiquette] - porte[etiquette]):
                desaccords.append(
                    f"{chemin.name} déclare {etiquette} « {inutile} » et ne le porte nulle part"
                )
    assert not desaccords, "déclarations et contenus divergent :\n  " + "\n  ".join(desaccords)


def test_une_entree_non_citable_du_registre_n_est_pas_citee() -> None:
    interdites = non_citables()
    assert interdites, (
        "le registre ne porte aucune entrée non citable : cette propriété ne vérifierait rien"
    )
    fautes = []
    for chemin in fichiers_de_chapitre():
        for cle in sorted(portees(chemin.read_text(encoding="utf-8"))["DOC"]):
            if cle in interdites:
                fautes.append(
                    f"{chemin.name} cite « {cle} », entrée {interdites[cle]} du registre : sa "
                    "vérification vaut « introuvable », elle n'entre pas au fichier "
                    "bibliographique et ne peut donc pas être citée"
                )
    assert not fautes, "entrées non citables citées :\n  " + "\n  ".join(fautes)


def test_toute_entree_citable_est_citee_ou_declaree_non_employee() -> None:
    etat = etat_du_document()
    if etat != "remise":
        # Abstention explicite, et motivée : la propriété n'a de sens que sur un rapport rédigé.
        # En état de brouillon, la plupart des chapitres sont vides et la quasi-totalité du
        # registre serait signalée à chaque exécution.
        return
    citees: set[str] = set()
    for chemin in fichiers_de_chapitre():
        citees |= portees(chemin.read_text(encoding="utf-8"))["DOC"]
    declarees = non_employees_declarees()
    orphelines = [
        f"{identifiant} ({cle}) n'est citée par aucun chapitre et ne figure pas parmi les "
        "sources déclarées non employées"
        for cle, identifiant in sorted(citables().items())
        if cle not in citees and cle not in declarees
    ]
    assert not orphelines, (
        f"état « remise » : {len(orphelines)} entrée(s) du registre sans emploi ni motif :\n  "
        + "\n  ".join(orphelines)
    )


def test_aucun_paragraphe_ne_reste_a_rediger() -> None:
    etat = etat_du_document()
    restants = []
    for chemin in fichiers_de_chapitre():
        actif = partie_active(chemin.read_text(encoding="utf-8"))
        for identifiant in sorted(_A_REDIGER.findall(actif)):
            restants.append(f"{chemin.name} : « {identifiant} »")
    if etat != "remise":
        # Abstention explicite : en brouillon, un paragraphe non encore écrit est normal, et la
        # marque est visible à la compilation pour que personne ne l'oublie.
        return
    assert not restants, "état « remise » : des paragraphes restent à rédiger :\n  " + "\n  ".join(
        restants
    )


def test_la_liste_des_annexes_coincide_avec_les_inclusions() -> None:
    """La portée déclarée et la portée réelle, dans les deux sens.

    Premier sens : un fichier d'annexe inclus par le document et absent de `ANNEXES` échapperait à
    l'examen. Second sens : un fichier resté dans `ANNEXES` mais que le document n'inclut plus
    verrait ses identifiants comptés alors qu'ils ne figurent plus nulle part — c'est la voie par
    laquelle ce contrôle serait vert sur des champs disparus, et c'est celle-ci qui la ferme.

    `EXCLUS` porte les fichiers volontairement hors examen. Un fichier inclus qui n'est ni dans
    `ANNEXES` ni dans `EXCLUS` est un oubli, et il est rouge.
    """
    inclus = inclusions_des_annexes()
    declares, exclus = set(ANNEXES), set(EXCLUS)

    non_examines = sorted(inclus - declares - exclus)
    assert not non_examines, (
        f"fichiers inclus par {ANNEXES_PRINCIPAL.name} et hors de toute liste : {non_examines} — "
        "ajoutez-les à ANNEXES pour qu'ils soient examinés, ou à EXCLUS avec le motif"
    )

    fantomes = sorted(declares - inclus)
    assert not fantomes, (
        f"fichiers déclarés dans ANNEXES et que {ANNEXES_PRINCIPAL.name} n'inclut plus : "
        f"{fantomes} — leurs identifiants seraient comptés alors qu'ils ne sont plus composés"
    )

    exclus_absents = sorted(exclus - inclus)
    assert not exclus_absents, (
        f"fichiers déclarés dans EXCLUS et non inclus : {exclus_absents} — une exclusion qui ne "
        "porte sur rien masque une décision qui n'a plus d'objet"
    )


def test_les_annexes_sont_incluses_par_le_document() -> None:
    """Sans cette propriété, retirer les annexes du fichier principal ne rougirait nulle part.

    Les identifiants continueraient d'être comptés par le contrôle, et les champs
    correspondants auraient pourtant quitté le document composé.
    """
    actif = partie_active(PRINCIPAL.read_text(encoding="utf-8"))
    assert "\\input{annexes}" in actif, (
        f"{PRINCIPAL.name} n'inclut plus {ANNEXES_PRINCIPAL.name} : les fichiers d'annexe ne sont "
        "plus composés, et les identifiants qu'ils portent ne sont plus dans le document"
    )


def test_chaque_fichier_examine_existe() -> None:
    """Un nom mal orthographié dans `ANNEXES` lèverait à la lecture ; il doit rougir avant."""
    absents = [chemin.name for chemin in fichiers_de_chapitre() if not chemin.is_file()]
    assert not absents, f"fichiers déclarés et absents du disque : {absents}"


def test_chaque_chapitre_declare_les_trois_etiquettes() -> None:
    """Une déclaration absente n'est pas une déclaration vide.

    Sans cette propriété, un fichier sans en-tête passerait les deux sens de la correspondance par
    accident : ensemble déclaré vide contre ensemble porté vide. C'est la déclaration explicite qui
    engage, et son absence doit se voir.
    """
    incompletes = []
    for chemin in fichiers_de_chapitre():
        lignes = chemin.read_text(encoding="utf-8").splitlines()
        presentes = {
            correspondance.group(1)
            for ligne in lignes
            if (correspondance := _DECLARATION.match(ligne)) is not None
        }
        for etiquette in ETIQUETTES:
            if etiquette not in presentes:
                incompletes.append(f"{chemin.name} : aucune ligne « {etiquette}: » en tête")
    assert not incompletes, "en-têtes de provenance incomplets :\n  " + "\n  ".join(incompletes)


# --------------------------------------------------------------------------------------------
# Le relevé de champs, troisième étiquette de l'appareil.
# --------------------------------------------------------------------------------------------

TEMOINS_CHAMP_POSITIFS = (
    (
        "identifiant dans un tableau",
        r"\texttt{REL-DEM.I01} & Identification & texte \\",
        {"REL-DEM.I01"},
    ),
    ("identifiant nu dans la prose", r"le champ REL-RDV.C02 horodate la création", {"REL-RDV.C02"}),
    ("identifiant cité par la commande", r"un relevé\releve{REL-IPP.O03} atteste", {"REL-IPP.O03"}),
    (
        "deux identifiants sur une ligne",
        r"REL-PAT.D09 et REL-PAT.D11",
        {"REL-PAT.D09", "REL-PAT.D11"},
    ),
)

TEMOINS_CHAMP_NEGATIFS = (
    ("identifiant dans un commentaire", r"% ancien tableau REL-DEM.I01", set()),
    ("texte actif puis commentaire", r"REL-DEM.I01 & site % REL-DEM.I02", {"REL-DEM.I01"}),
    ("pourcentage échappé : la ligne reste active", r"100\% des cas, REL-DEM.I02", {"REL-DEM.I02"}),
    ("préfixe d'un identifiant plus long", r"REL-PAT.D100", set()),
    ("bloc sans numéro de champ", r"le bloc REL-PAT est dense", set()),
    ("écran à trois lettres mais séparateur absent", r"REL-PAT-D09", set()),
)


def test_le_motif_reconnait_chaque_forme_d_identifiant_de_champ() -> None:
    for nom, source, attendu in TEMOINS_CHAMP_POSITIFS:
        assert portees(source)["OBS"] == attendu, f"témoin positif « {nom} » : {source!r}"


def test_le_motif_ne_reconnait_pas_ce_qui_n_est_pas_un_identifiant_de_champ() -> None:
    for nom, source, attendu in TEMOINS_CHAMP_NEGATIFS:
        assert portees(source)["OBS"] == attendu, f"témoin négatif « {nom} » : {source!r}"


def test_tout_identifiant_de_champ_cite_existe_au_releve() -> None:
    connus = champs_du_releve()
    assert connus, "le relevé ne porte aucun champ : cette propriété ne vérifierait rien"
    inconnus = []
    for chemin in fichiers_de_chapitre():
        for identifiant in sorted(portees(chemin.read_text(encoding="utf-8"))["OBS"]):
            if _CHAMP_RELEVE.fullmatch(identifiant) and identifiant not in connus:
                inconnus.append(
                    f"{chemin.name} cite le champ « {identifiant} », absent du relevé de champs"
                )
    assert not inconnus, "identifiants de champ sans cible :\n  " + "\n  ".join(inconnus)


def test_tout_champ_du_releve_est_employe_ou_declare_non_employe() -> None:
    """Le sens que le contrôle de provenance des colonnes ne vérifiait pas.

    `tests/test_provenance.py::test_coherence_preuves` vérifie que toute preuve OBS du registre
    des champs pointe vers un champ du relevé. Rien ne vérifiait l'inverse : un champ vu à
    l'écran, jamais porté au registre ni cité par le rapport, disparaissait du modèle sans qu'un
    contrôle ne bronche. Trois voies d'emploi, et un motif écrit quand aucune ne s'applique.
    """
    champs = champs_du_releve()
    par_le_registre = champs_invoques_par_le_registre()
    declares = non_emplois_declares()

    cites: set[str] = set()
    for chemin in fichiers_de_chapitre():
        cites |= portees(chemin.read_text(encoding="utf-8"))["OBS"]

    orphelins = []
    sans_motif = []
    for identifiant in sorted(champs):
        if identifiant in par_le_registre or identifiant in cites:
            continue
        if identifiant not in declares:
            orphelins.append(
                f"{identifiant} « {champs[identifiant]['libelle']} » : aucune entrée du registre "
                "des champs ne l'invoque, aucun chapitre ne le cite, et le relevé ne le déclare "
                "pas non employé"
            )
        elif not declares[identifiant]:
            sans_motif.append(f"{identifiant} est déclaré non employé sans motif")

    assert not orphelins, (
        f"{len(orphelins)} champ(s) relevé(s) sans emploi ni motif :\n  " + "\n  ".join(orphelins)
    )
    assert not sans_motif, "déclarations de non-emploi sans motif :\n  " + "\n  ".join(sans_motif)


def test_aucun_champ_declare_non_employe_n_est_inconnu_du_releve() -> None:
    """L'autre sens de la déclaration : on ne déclare pas inemployé ce qui n'existe pas."""
    champs = champs_du_releve()
    fantomes = sorted(i for i in non_emplois_declares() if i not in champs)
    assert not fantomes, "champs déclarés non employés et absents du relevé : " + ", ".join(
        fantomes
    )


def sections_declarees(source: str) -> int | None:
    for ligne in source.splitlines():
        correspondance = _SECTIONS_DECLAREES.match(ligne)
        if correspondance is not None:
            return int(correspondance.group(1))
    return None


def sections_portees(source: str) -> int:
    return len(_SECTION.findall(partie_active(source)))


def test_le_motif_compte_les_sections_et_ignore_ce_qui_n_en_est_pas() -> None:
    """Témoins des deux sens du décompte de sections."""
    positifs = (
        ("une section", "\\section{A}\n", 1),
        ("deux sections", "\\section{A}\ntexte\n\\section{B}\n", 2),
        ("aucune section", "\\chapter*{Introduction}\n", 0),
    )
    negatifs = (
        ("section commentée", "% \\section{A}\n", 0),
        ("sous-section", "\\subsection{A}\n", 0),
        ("section non en début de ligne", "voir \\section{A} plus haut\n", 0),
        ("commande homographe", "\\sectionmark{A}\n", 0),
    )
    for nom, source, attendu in positifs:
        assert sections_portees(source) == attendu, f"témoin positif « {nom} »"
    for nom, source, attendu in negatifs:
        assert sections_portees(source) == attendu, f"témoin négatif « {nom} »"
    assert sections_declarees("%   SECTIONS: 8\n") == 8
    assert sections_declarees("\\section{A}\n") is None, "aucune déclaration n'est pas zéro"


def test_chaque_chapitre_declare_son_nombre_de_sections() -> None:
    """Le retrait d'une section à l'intérieur d'un chapitre ne se voyait nulle part.

    La correspondance entre déclaration et contenu ne le détecte que si la section retirée
    portait au moins une source ou un champ qu'aucune autre ne porte — mesuré : sur les huit
    sections du chapitre du système d'information, six sont ainsi détectées et deux ne le sont
    pas, parce qu'elles ne citent que des identifiants déjà cités ailleurs. Le décompte déclaré
    ferme cet angle mort.
    """
    ecarts = []
    for chemin in fichiers_de_chapitre():
        source = chemin.read_text(encoding="utf-8")
        declare, porte = sections_declarees(source), sections_portees(source)
        if declare is None:
            ecarts.append(f"{chemin.name} : aucune ligne « SECTIONS: » en tête")
        elif declare != porte:
            ecarts.append(f"{chemin.name} déclare {declare} section(s) et en porte {porte}")
    assert not ecarts, "décomptes de sections divergents :\n  " + "\n  ".join(ecarts)
