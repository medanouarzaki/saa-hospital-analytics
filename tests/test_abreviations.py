"""Les abréviations du rapport : un registre, une liste produite, et un développé à la première.

QUATRE PROPRIÉTÉS, et chacune ferme une voie distincte.

(a1) Tout sigle de la prose est au registre des abréviations ou dans ses exceptions, et tout
     sigle du registre est employé ou porte le motif de son non-emploi. Les deux sens : un sigle
     ajouté au texte sans entrée manquerait à la liste, une entrée sans emploi y figurerait pour
     rien.
(a2) `report/liminaires/abreviations.tex` est, octet à octet, le rendu du générateur : la liste ne
     se retouche pas à la main.
(a3) La liste produite est triée selon la clé du générateur, sans doublon de sigle.
(a4) La première occurrence de chaque sigle dans le corps — à partir de l'introduction, dans l'ordre
     d'inclusion du document — est dans la PROSE et dans la même phrase que son développé. Une
     cellule de tableau, un titre d'objet ou un libellé d'écran reproduit ne compte pas : le
     développé n'y entre pas. Le résumé et l'abstract précèdent la liste et en sont exemptés.

UN SIGLE est un jeton qui commence par une capitale et en porte au moins deux, chiffres et tirets
admis. Ce que la prose ne compose pas comme texte courant n'est pas cherché : les arguments des
commandes que `tests/test_aucun_nombre_tape.py` retire déjà, et ceux de `\\texttt`, `\\cite`,
`\\ref`, `\\label`, `\\chiffre`, `\\serie`, `\\releve`, `\\convention`, des annonces du plan, de
`\\pageref`, `\\url` et `\\href` ; les environnements de tracé ; les commentaires ; les fichiers
produits. Aucun accès à la base.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
REPORT = RACINE / "report"
REGISTRE = RACINE / "docs" / "abreviations" / "abreviations.yml"
GENERATEUR = RACINE / "docs" / "abreviations" / "to_tex.py"
LISTE = REPORT / "liminaires" / "abreviations.tex"

_SIGLE = re.compile(r"(?<![\w\\-])[A-ZÀ-Ý][A-ZÀ-Ý0-9-]*[A-ZÀ-Ý0-9](?![\w-])")
_COMMANDES_PROPRES = (
    "texttt",
    "cite",
    "ref",
    "label",
    "chiffre",
    "serie",
    "releve",
    "convention",
    "annonceChapitre",
    "annoncePartie",
    "pageref",
    "url",
    "href",
)
# Ce qui n'est pas de la prose courante pour la règle de première occurrence : les objets, leurs
# titres et leurs cellules.
_OBJET = re.compile(r"\\begin\{(figure|table|longtable|tabular)\*?\}.*?\\end\{\1\*?\}", re.S)
_ITEM = re.compile(r"\\item\[([^\]]*)\]")
_EXEMPTS = {"resume.tex", "page-de-garde.tex", "remerciements.tex"}


def _nombres_tapes():
    import test_aucun_nombre_tape

    return test_aucun_nombre_tape


def _generateur():
    spec = importlib.util.spec_from_file_location("abreviations_to_tex", GENERATEUR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def registre() -> dict:
    import yaml

    return yaml.safe_load(REGISTRE.read_text(encoding="utf-8"))


def depouiller(source: str, prose_seule: bool = False) -> str:
    """La partie composée comme texte, une ligne ; sans les objets si `prose_seule`."""
    t = _nombres_tapes()
    texte = t.partie_active(source)
    if prose_seule:
        texte = _OBJET.sub(" ", texte)
    for motif in (t._ENV_TRACE, t._PGF, t._TABULAIRE, t._DEFINITION):
        texte = motif.sub(" ", texte)
    for commande in tuple(t.COMMANDES_A_ARGUMENT) + _COMMANDES_PROPRES:
        texte = re.sub(r"\\" + commande + r"\*?(\[[^\]]*\])*(\{[^{}]*\})*", " ", texte)
    texte = re.sub(r"\\[a-zA-Z@]+\*?", " ", texte)
    texte = texte.replace("{", " ").replace("}", " ")
    return " ".join(texte.split())


def sigles(texte: str) -> list[str]:
    return [m for m in _SIGLE.findall(texte) if sum(c.isupper() for c in m) >= 2]


def phrases(texte: str) -> list[str]:
    """Les phrases : une fin sur . ! ? suivie d'un blanc et d'une capitale, hors abréviations."""
    morceaux, debut = [], 0
    for m in re.finditer(r"[.!?](?=\s+[A-ZÀ-Ý«(])", texte):
        if re.search(
            r"(?:\bcf|\bp|\bn°|\bart|\bvol|\bet al)\.$", texte[max(0, m.start() - 6) : m.end()]
        ):
            continue
        morceaux.append(texte[debut : m.end()])
        debut = m.end()
    morceaux.append(texte[debut:])
    return [" ".join(m.split()) for m in morceaux if m.strip()]


def fichiers_dans_l_ordre() -> list[Path]:
    """Les sources de prose, dans l'ordre d'inclusion du document ; fichiers produits exclus."""
    principal = (REPORT / "rapport.tex").read_text(encoding="utf-8")
    actif = "\n".join(_nombres_tapes().partie_active(ligne) for ligne in principal.splitlines())
    noms = re.findall(r"\\input\{((?:liminaires|chapitres)/[^}]+|annexes)\}", actif)
    return [REPORT / f"{n}.tex" for n in noms if REPORT / f"{n}.tex" != LISTE]


# --- témoins du motif -----------------------------------------------------------------------

TEMOINS_VUS = (
    ("sigle courant", "Le SAA accueille les patients.", ["SAA"]),
    ("sigle coupé par un retour à la ligne", "le\nMPI coupé", ["MPI"]),
    ("fragment d'un nom de produit", "le progiciel Hosix.NET", ["NET"]),
)
TEMOINS_NON_VUS = (
    ("clé de source dans une citation", r"voir \cite{S-22} ici"),
    ("libellé en chasse fixe", r"le champ \texttt{IPP} seul"),
    ("mot à une capitale", "Structured Query Language"),
    ("nom de produit en casse mixte", "SQLFluff et Ruff"),
    ("commentaire", "% le SAA en commentaire"),
)


def test_le_motif_voit_chaque_forme_de_sigle() -> None:
    for nom, source, attendu in TEMOINS_VUS:
        assert sigles(depouiller(source)) == attendu, f"témoin « {nom} »"


def test_le_motif_ne_prend_pas_pour_un_sigle_ce_qui_n_en_est_pas() -> None:
    for nom, source in TEMOINS_NON_VUS:
        assert not sigles(depouiller(source)), f"témoin négatif « {nom} »"


def test_une_cellule_de_tableau_n_est_pas_une_premiere_occurrence() -> None:
    source = (
        "\\begin{table}\\caption{Le MPI}\\begin{tabular}{ll} Chercher MPI & onglet \\\\"
        "\\end{tabular}\\end{table} Puis l'index maître des patients (MPI) est nommé."
    )
    premieres = [p for p in phrases(depouiller(source, prose_seule=True)) if "MPI" in sigles(p)]
    assert premieres and "index maître des patients" in premieres[0], premieres


# --- les quatre propriétés ------------------------------------------------------------------


def test_tout_sigle_de_la_prose_est_au_registre_et_tout_sigle_du_registre_est_employe() -> None:
    reg = registre()
    declares = {e["sigle"] for e in reg["abreviations"]}
    exceptions = {e["jeton"] for e in reg.get("exceptions", [])}
    fichiers = fichiers_dans_l_ordre()
    assert any(f.name == "introduction.tex" for f in fichiers), "aucun chapitre lu"
    employes = {s for f in fichiers for s in sigles(depouiller(f.read_text(encoding="utf-8")))}
    assert employes, "aucun sigle trouvé dans la prose : la propriété ne vérifierait rien"
    inconnus = sorted(employes - declares - exceptions)
    assert not inconnus, f"sigles employés absents du registre et de ses exceptions : {inconnus}"
    sans_emploi = sorted(
        e["sigle"]
        for e in reg["abreviations"]
        if e["sigle"] not in employes and not e.get("non_employe")
    )
    assert not sans_emploi, f"sigles du registre jamais employés, sans motif : {sans_emploi}"


def test_la_liste_est_le_rendu_du_generateur() -> None:
    generateur = _generateur()
    attendu = generateur.rendre(generateur.charger())
    assert LISTE.read_text(encoding="utf-8") == attendu, (
        "report/liminaires/abreviations.tex diffère du rendu de docs/abreviations/to_tex.py : "
        "régénérer, ne pas retoucher"
    )


def test_la_liste_est_triee_et_sans_doublon() -> None:
    generateur = _generateur()
    produits = _ITEM.findall(LISTE.read_text(encoding="utf-8"))
    assert produits, "la liste produite ne porte aucune entrée"
    assert len(produits) == len(set(produits)), f"doublons dans la liste : {produits}"
    assert produits == sorted(produits, key=generateur.cle_de_tri), f"ordre rompu : {produits}"


def test_la_premiere_occurrence_de_chaque_sigle_porte_son_developpe() -> None:
    reg = registre()
    developpes = {e["sigle"]: e["developpe"] for e in reg["abreviations"]}
    fichiers = fichiers_dans_l_ordre()
    noms = [f.name for f in fichiers]
    corps = [f for f in fichiers[noms.index("introduction.tex") :] if f.name not in _EXEMPTS]
    unites = [
        p
        for f in corps
        for p in phrases(depouiller(f.read_text(encoding="utf-8"), prose_seule=True))
    ]
    fautes, vus = [], set()
    for phrase in unites:
        for sigle in sigles(phrase):
            if sigle in vus or sigle not in developpes:
                continue
            vus.add(sigle)
            if developpes[sigle].casefold() not in phrase.casefold():
                fautes.append(f"{sigle} : « {phrase[:140]} »")
    assert vus, "aucun sigle du registre dans la prose du corps : la propriété ne vérifierait rien"
    # Un sigle employé seulement dans une cellule ou un titre n'a pas de première occurrence en
    # prose : il manque son développé. Un sigle employé nulle part relève de (a1), non d'ici.
    employes = {
        s
        for f in corps
        for s in sigles(depouiller(f.read_text(encoding="utf-8")))
        if s in developpes
    }
    manquants = sorted(employes - vus)
    assert not manquants, f"sigles employés hors de toute prose du corps : {manquants}"
    assert not fautes, "première occurrence sans son développé :\n  " + "\n  ".join(fautes)
