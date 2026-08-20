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
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
REPORT = RACINE / "report"
CHAPITRES = REPORT / "chapitres"
PRINCIPAL = REPORT / "rapport.tex"
BIBLIO = REPORT / "biblio.bib"
MARQUEURS = REPORT / "marqueurs.tex"
SOURCES = RACINE / "docs" / "sources" / "sources.yml"

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


def etat_du_document() -> str | None:
    actif = partie_active(MARQUEURS.read_text(encoding="utf-8"))
    trouve = _ETAT.search(actif)
    return None if trouve is None else trouve.group(1).strip().lower()


def fichiers_de_chapitre() -> list[Path]:
    return sorted(CHAPITRES.glob("*.tex"))


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
