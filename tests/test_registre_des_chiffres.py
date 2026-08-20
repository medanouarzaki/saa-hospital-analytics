"""Aucun nombre du rapport n'est tapé : chacun vient du registre des chiffres, par son identifiant.

Le motif est mesuré. Cinq valeurs ont circulé dans les documents de ce projet sans être rattachées
à une commande, et les cinq étaient fausses ou périmées : un total de lignes décrivant une
génération écrasée, un décompte de personnes confondu avec un décompte d'identifiants, un mot
recouvrant deux grandeurs différentes, un décompte de paramètres dépassé, et un taux d'occupation
qu'aucun artefact ne portait.

CE CONTRÔLE N'OUVRE AUCUNE BASE. Il vérifie la correspondance entre le registre et le rapport ; que
les valeurs consignées soient celles que les commandes rendent aujourd'hui relève de
`docs/chiffres/mesurer.py --verifier`, qui ne peut s'exécuter que sur la période entière.

PAR QUELLE VOIE CHAQUE PROPRIÉTÉ SERAIT-ELLE VRAIE MÊME SI LE CODE ÉTAIT FAUX ? La question est
posée pour chacune ci-dessous, et la mutation qui ferme la voie est nommée. C'est la leçon de
quatre mutations successives qui ont révélé un contrôle défectueux plutôt qu'un code correct.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
REGISTRE = RACINE / "docs" / "chiffres" / "registre_chiffres.yml"
CHAPITRES = RACINE / "report" / "chapitres"
RENDU = RACINE / "report" / "chiffres.tex"

# Un commentaire LaTeX s'ouvre sur un pourcentage non échappé.
_COMMENTAIRE = re.compile(r"(?<!\\)(?:\\\\)*%")

# L'appel d'un chiffre : la commande, suivie immédiatement de l'accolade. La garde de fin interdit
# de confondre `\chiffre` avec une commande dont le nom commence par les mêmes lettres.
_APPEL = re.compile(r"\\chiffre\{([a-z0-9-]+)\}")

# La définition rendue, du côté du fichier produit.
_DEFINITION = re.compile(r"\\csname chiffre@([a-z0-9-]+)\\endcsname\{")


def sans_commentaire(ligne: str) -> str:
    trouve = _COMMENTAIRE.search(ligne)
    return ligne if trouve is None else ligne[: trouve.end() - 1]


def partie_active(source: str) -> str:
    return "\n".join(sans_commentaire(ligne) for ligne in source.splitlines())


def registre() -> dict:
    with REGISTRE.open(encoding="utf-8") as fichier:
        return yaml.safe_load(fichier)


def entrees() -> list[dict]:
    return registre()["chiffres"]


def identifiants_du_registre() -> set[str]:
    return {e["id"] for e in entrees()}


def fichiers_de_chapitre() -> list[Path]:
    return sorted(CHAPITRES.glob("*.tex"))


def appels(source: str) -> set[str]:
    return set(_APPEL.findall(partie_active(source)))


def appels_du_rapport() -> dict[str, set[str]]:
    return {c.name: appels(c.read_text(encoding="utf-8")) for c in fichiers_de_chapitre()}


def non_emplois_declares() -> dict[str, str]:
    return {
        e["id"]: (e.get("motif_non_emploi") or "").strip()
        for e in entrees()
        if "motif_non_emploi" in e
    }


# --------------------------------------------------------------------------------------------
# Témoins du motif d'appel, dans les deux sens.
# --------------------------------------------------------------------------------------------

TEMOINS_POSITIFS = (
    ("appel simple", r"il y a \chiffre{source-patients-lignes} fiches", {"source-patients-lignes"}),
    (
        "deux appels sur une ligne",
        r"\chiffre{colonnes-marts} et \chiffre{colonnes-intermediate}",
        {"colonnes-marts", "colonnes-intermediate"},
    ),
    ("appel collé à une unité", r"\chiffre{tom-publie}~\%", {"tom-publie"}),
    ("appel en début de ligne", r"\chiffre{periode-jours} jours", {"periode-jours"}),
)

TEMOINS_NEGATIFS = (
    ("appel dans un commentaire", r"% ancien \chiffre{source-patients-lignes}", set()),
    (
        "texte actif puis commentaire",
        r"\chiffre{colonnes-marts} % \chiffre{colonnes-marts-faux}",
        {"colonnes-marts"},
    ),
    (
        "pourcentage échappé : la ligne reste active",
        r"100\% de \chiffre{tom-publie}",
        {"tom-publie"},
    ),
    ("commande homographe", r"\chiffres{source-patients-lignes}", set()),
    ("identifiant en majuscules", r"\chiffre{SOURCE-PATIENTS-LIGNES}", set()),
    ("la chaîne hors de toute commande", r"le chiffre source-patients-lignes vaut", set()),
)


def test_le_motif_reconnait_chaque_forme_d_appel() -> None:
    for nom, source, attendu in TEMOINS_POSITIFS:
        assert appels(source) == attendu, f"témoin positif « {nom} » : {source!r}"


def test_le_motif_ne_reconnait_pas_ce_qui_n_est_pas_un_appel() -> None:
    for nom, source, attendu in TEMOINS_NEGATIFS:
        assert appels(source) == attendu, f"témoin négatif « {nom} » : {source!r}"


# --------------------------------------------------------------------------------------------
# Les quatre propriétés.
# --------------------------------------------------------------------------------------------


def test_tout_identifiant_appele_existe_au_registre() -> None:
    """Voie par laquelle elle serait vraie à tort : si aucun chapitre n'appelait de chiffre, la
    propriété passerait sur l'ensemble vide. La garde ci-dessous ferme cette voie.
    """
    connus = identifiants_du_registre()
    assert connus, "le registre ne porte aucune entrée : la propriété ne vérifierait rien"
    tous = set().union(*appels_du_rapport().values()) if appels_du_rapport() else set()
    assert tous, "aucun chapitre n'appelle de chiffre : la propriété ne vérifierait rien"

    inconnus = [
        f"{fichier} appelle « {identifiant} », absent du registre des chiffres"
        for fichier, ids in sorted(appels_du_rapport().items())
        for identifiant in sorted(ids)
        if identifiant not in connus
    ]
    assert not inconnus, "appels sans cible :\n  " + "\n  ".join(inconnus)


def test_toute_entree_est_employee_ou_declaree_non_employee() -> None:
    """Le second sens — celui que ce projet a dû ajouter deux fois après coup.

    Voie par laquelle elle serait vraie à tort : si tout le registre était déclaré non employé,
    elle passerait sans qu'aucun chiffre serve. Le motif est donc exigé non vide, et la mutation
    qui vide un motif rougit.
    """
    employes = set().union(*appels_du_rapport().values()) if appels_du_rapport() else set()
    declares = non_emplois_declares()

    orphelins = []
    sans_motif = []
    for entree in entrees():
        identifiant = entree["id"]
        if identifiant in employes:
            continue
        if identifiant not in declares:
            orphelins.append(
                f"{identifiant} ({entree['valeur']} {entree['unite']}) : aucun chapitre ne "
                "l'appelle et le registre ne le déclare pas non employé"
            )
        elif not declares[identifiant]:
            sans_motif.append(f"{identifiant} est déclaré non employé sans motif")

    assert not orphelins, f"{len(orphelins)} chiffre(s) sans emploi ni motif :\n  " + "\n  ".join(
        orphelins
    )
    assert not sans_motif, "déclarations sans motif :\n  " + "\n  ".join(sans_motif)


def test_toute_entree_porte_une_commande_non_vide() -> None:
    """Voie par laquelle elle serait vraie à tort : une commande réduite à un espace passerait un
    contrôle de présence de clé. Le contrôle porte donc sur la valeur dépouillée, et il exige aussi
    que le type soit l'un des deux connus — une commande sans type n'est pas exécutable.
    """
    fautes = []
    for entree in entrees():
        commande = (entree.get("commande") or "").strip()
        if not commande:
            fautes.append(f"{entree['id']} : commande vide")
        if entree.get("type") not in {"sql", "python"}:
            fautes.append(f"{entree['id']} : type « {entree.get('type')} » inconnu")
        if not (entree.get("unite") or "").strip():
            fautes.append(f"{entree['id']} : unité vide")
    assert not fautes, "entrées incomplètes :\n  " + "\n  ".join(fautes)


def test_le_rendu_porte_exactement_les_entrees_du_registre() -> None:
    """Voie par laquelle elle serait vraie à tort : le rendu pourrait porter les définitions et le
    registre avoir changé depuis. La correspondance est donc vérifiée DANS LES DEUX SENS, et les
    valeurs rendues sont confrontées aux valeurs consignées, chiffre à chiffre.
    """
    rendu = RENDU.read_text(encoding="utf-8")
    definis = set(_DEFINITION.findall(rendu))
    attendus = identifiants_du_registre()

    manquants = sorted(attendus - definis)
    en_trop = sorted(definis - attendus)
    assert not manquants, "entrées du registre absentes du rendu : " + ", ".join(manquants)
    assert not en_trop, "définitions du rendu absentes du registre : " + ", ".join(en_trop)

    ecarts = []
    for entree in entrees():
        motif = re.compile(
            r"\\csname chiffre@" + re.escape(entree["id"]) + r"\\endcsname\{([^}]*)\}"
        )
        trouve = motif.search(rendu)
        rendue = trouve.group(1).replace("\\,", "").replace(",", ".")
        consignee = str(entree["valeur"])
        if (
            rendue.rstrip("0").rstrip(".") != consignee.rstrip("0").rstrip(".")
            and rendue != consignee
        ):
            ecarts.append(f"{entree['id']} : registre {consignee}, rendu {trouve.group(1)}")
    assert not ecarts, "valeurs rendues divergentes :\n  " + "\n  ".join(ecarts)


def test_chaque_chapitre_declare_les_chiffres_qu_il_appelle() -> None:
    """La quatrième étiquette de l'en-tête, au même titre que les trois autres."""
    _CHI = re.compile(r"^\s*%\s*CHI\s*:\s*(.*)$")
    desaccords = []
    for chemin in fichiers_de_chapitre():
        source = chemin.read_text(encoding="utf-8")
        declares: set[str] = set()
        vue = False
        for ligne in source.splitlines():
            correspondance = _CHI.match(ligne)
            if correspondance is None:
                continue
            vue = True
            valeur = correspondance.group(1).strip()
            if valeur.lower() not in {"(aucun)", "(aucune)", ""}:
                declares |= {m.strip() for m in valeur.split(",") if m.strip()}
        portes = appels(source)
        if not vue:
            desaccords.append(f"{chemin.name} : aucune ligne « CHI: » en tête")
            continue
        for absent in sorted(portes - declares):
            desaccords.append(f"{chemin.name} appelle « {absent} » sans le déclarer en tête")
        for inutile in sorted(declares - portes):
            desaccords.append(f"{chemin.name} déclare « {inutile} » et ne l'appelle nulle part")
    assert not desaccords, "déclarations de chiffres divergentes :\n  " + "\n  ".join(desaccords)
