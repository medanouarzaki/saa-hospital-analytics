"""Aucun nombre du rapport n'est tapé : chacun vient du registre des chiffres, par son identifiant.

Le motif est mesuré. Cinq valeurs ont circulé dans les documents de ce projet sans être rattachées
à une commande, et les cinq étaient fausses ou périmées : un total de lignes décrivant une
génération écrasée, un décompte de personnes confondu avec un décompte d'identifiants, un mot
recouvrant deux grandeurs différentes, un décompte de paramètres dépassé, et un taux d'occupation
qu'aucun artefact ne portait.

LES SÉRIES SUIVENT LA MÊME RÈGLE. Un graphique ou un tableau dont les données seraient tapées dans
la source de composition serait exactement ce que ce registre existe pour empêcher. Une série est
donc une commande, son résultat est un fichier de données, et le rapport l'appelle par son
identifiant. CE FICHIER EST CONFRONTÉ ICI À L'EMPREINTE DU REGISTRE : c'est le lien qui interdit de
retoucher une donnée à la main après coup. L'autre lien — que l'empreinte du registre soit bien
celle que la COMMANDE produit — relève de `docs/chiffres/mesurer.py --verifier`, qui ouvre la base.
Aucun des deux codes ne vérifie le lien de l'autre.

CE CONTRÔLE N'OUVRE AUCUNE BASE. Il vérifie la correspondance entre le registre et le rapport ; que
les valeurs consignées soient celles que les commandes rendent aujourd'hui relève de
`docs/chiffres/mesurer.py --verifier`, qui ne peut s'exécuter que sur la période entière.

PAR QUELLE VOIE CHAQUE PROPRIÉTÉ SERAIT-ELLE VRAIE MÊME SI LE CODE ÉTAIT FAUX ? La question est
posée pour chacune ci-dessous, et la mutation qui ferme la voie est nommée. C'est la leçon de
quatre mutations successives qui ont révélé un contrôle défectueux plutôt qu'un code correct.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
REGISTRE = RACINE / "docs" / "chiffres" / "registre_chiffres.yml"
CHAPITRES = RACINE / "report" / "chapitres"
RENDU = RACINE / "report" / "chiffres.tex"
# Les fichiers de données des séries sont désignés au registre par un chemin relatif au répertoire
# de composition, qui est celui que `\addplot table` reçoit tel quel.
RACINE_SERIES = RACINE / "report"

# Les deux séparateurs de colonnes admis, repris du rendu qui écrit ces fichiers. Le nom est
# déclaré au registre ; l'écrire ici en clair plutôt que le lire ferait diverger le contrôle du
# rendu au premier séparateur ajouté, et c'est pourquoi la table est confrontée par mutation.
SEPARATEURS = {"virgule": ",", "tabulation": "\t"}

# Un commentaire LaTeX s'ouvre sur un pourcentage non échappé.
_COMMENTAIRE = re.compile(r"(?<!\\)(?:\\\\)*%")

# L'appel d'un chiffre : la commande, suivie immédiatement de l'accolade. La garde de fin interdit
# de confondre `\chiffre` avec une commande dont le nom commence par les mêmes lettres.
_APPEL = re.compile(r"\\chiffre\{([a-z0-9-]+)\}")

# L'appel d'une série, de même forme et de même garde de fin.
_APPEL_SERIE = re.compile(r"\\serie\{([a-z0-9-]+)\}")

# La définition rendue, du côté du fichier produit.
_DEFINITION = re.compile(r"\\csname chiffre@([a-z0-9-]+)\\endcsname\{")
_DEFINITION_SERIE = re.compile(r"\\csname serie@([a-z0-9-]+)\\endcsname\{([^}]*)\}")


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


def series() -> list[dict]:
    return registre().get("series", [])


def identifiants_des_series() -> set[str]:
    return {s["id"] for s in series()}


def appels_de_serie(source: str) -> set[str]:
    return set(_APPEL_SERIE.findall(partie_active(source)))


def appels_de_serie_du_rapport() -> dict[str, set[str]]:
    return {c.name: appels_de_serie(c.read_text(encoding="utf-8")) for c in fichiers_de_chapitre()}


def memes_nombres(rendue: str, consignee: str) -> bool:
    """Deux écritures d'un même nombre, comparées comme des nombres et non comme des chaînes.

    Les conventions du rendu sont dépouillées avant la comparaison, et elles sont trois :
    l'espace fine insécable des milliers, la virgule décimale, et le signe moins composé en mode
    mathématique. Une convention ajoutée au rendu sans être dépouillée ici ferait rougir ce
    contrôle, ce qui est le comportement voulu — il ne doit pas ignorer une écriture qu'il ne
    comprend pas.

    La comparaison précédente dépouillait les zéros de fin des DEUX côtés avant de les confronter :
    elle rendait « 30 » sur l'entier 30 et « 3 » sur le décimal 30.0, et déclarait donc un écart là
    où il n'y en avait aucun. Mesuré sur deux entrées dont la valeur consignée finit par un zéro
    après la virgule. Un identifiant qui n'est pas un nombre — une date, par exemple — se compare
    toujours caractère à caractère.
    """
    try:
        return float(rendue) == float(consignee)
    except ValueError:
        return rendue == consignee


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
        rendue = trouve.group(1).replace("\\,", "").replace("$-$", "-").replace(",", ".")
        consignee = str(entree["valeur"])
        if not memes_nombres(rendue, consignee):
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


# --------------------------------------------------------------------------------------------
# Les séries. Témoins d'abord, dans les deux sens, puis les quatre propriétés.
# --------------------------------------------------------------------------------------------

TEMOINS_POSITIFS_SERIE = (
    ("appel simple", r"\addplot table {\serie{flux-mensuel}};", {"flux-mensuel"}),
    (
        "deux appels sur une ligne",
        r"\serie{flux-horaire} et \serie{completude-champs}",
        {"flux-horaire", "completude-champs"},
    ),
    (
        "appel dans un argument entre accolades",
        r"\pgfplotstabletypeset[col sep=comma]{\serie{urgences-par-niveau}}",
        {"urgences-par-niveau"},
    ),
)

TEMOINS_NEGATIFS_SERIE = (
    ("appel dans un commentaire", r"% ancien \serie{flux-mensuel}", set()),
    (
        "texte actif puis commentaire",
        r"\serie{flux-mensuel} % \serie{flux-mensuel-faux}",
        {"flux-mensuel"},
    ),
    ("commande homographe", r"\series{flux-mensuel}", set()),
    ("identifiant en majuscules", r"\serie{FLUX-MENSUEL}", set()),
    ("la chaîne hors de toute commande", r"la serie flux-mensuel se trace", set()),
    (
        "un chiffre n'est pas une série",
        r"\chiffre{flux-mensuel}",
        set(),
    ),
)


def test_le_motif_de_serie_reconnait_chaque_forme_d_appel() -> None:
    for nom, source, attendu in TEMOINS_POSITIFS_SERIE:
        assert appels_de_serie(source) == attendu, f"témoin positif « {nom} » : {source!r}"


def test_le_motif_de_serie_ne_reconnait_pas_ce_qui_n_est_pas_un_appel() -> None:
    for nom, source, attendu in TEMOINS_NEGATIFS_SERIE:
        assert appels_de_serie(source) == attendu, f"témoin négatif « {nom} » : {source!r}"


def test_tout_identifiant_de_serie_appele_existe_au_registre() -> None:
    """Voie par laquelle elle serait vraie à tort : si aucun chapitre n'appelait de série, la
    propriété passerait sur l'ensemble vide — exactement la voie déjà rencontrée sur les scalaires.
    Les deux gardes ci-dessous la ferment, côté registre et côté rapport.
    """
    connus = identifiants_des_series()
    assert connus, "le registre ne porte aucune série : la propriété ne vérifierait rien"
    appels = appels_de_serie_du_rapport()
    tous = set().union(*appels.values()) if appels else set()
    assert tous, "aucun chapitre n'appelle de série : la propriété ne vérifierait rien"

    inconnus = [
        f"{fichier} appelle la série « {identifiant} », absente du registre"
        for fichier, ids in sorted(appels.items())
        for identifiant in sorted(ids)
        if identifiant not in connus
    ]
    assert not inconnus, "appels de série sans cible :\n  " + "\n  ".join(inconnus)


def test_toute_serie_est_employee_ou_declaree_non_employee() -> None:
    """Le second sens. Voie par laquelle elle serait vraie à tort : un motif vide passerait un
    contrôle de présence de clé, et tout le registre pourrait être déclaré non employé sans qu'un
    seul graphique lise quoi que ce soit. Le motif est donc exigé non vide.
    """
    appels = appels_de_serie_du_rapport()
    employees = set().union(*appels.values()) if appels else set()

    orphelines = []
    sans_motif = []
    for serie in series():
        identifiant = serie["id"]
        if identifiant in employees:
            continue
        if "motif_non_emploi" not in serie:
            orphelines.append(
                f"{identifiant} ({serie['lignes']} lignes) : aucun chapitre ne l'appelle et le "
                "registre ne la déclare pas non employée"
            )
        elif not (serie.get("motif_non_emploi") or "").strip():
            sans_motif.append(f"{identifiant} est déclarée non employée sans motif")

    assert not orphelines, f"{len(orphelines)} série(s) sans emploi ni motif :\n  " + "\n  ".join(
        orphelines
    )
    assert not sans_motif, "déclarations sans motif :\n  " + "\n  ".join(sans_motif)


def test_le_fichier_de_donnees_est_celui_que_la_commande_produit() -> None:
    """LA PROPRIÉTÉ QUI DONNE SON SENS À L'APPAREIL DES SÉRIES.

    Voie par laquelle elle serait vraie même si le code était faux : l'empreinte pourrait avoir été
    calculée SUR LE FICHIER plutôt que sur ce que la commande rend, et une retouche à la main
    passerait alors les deux contrôles. Cette voie est fermée ailleurs, et il faut le dire ici :
    `docs/chiffres/mesurer.py --verifier` recalcule l'empreinte À PARTIR DE LA COMMANDE, sur la base
    complète, avant toute publication. Le présent contrôle ferme l'autre moitié du chemin — que le
    fichier LU soit bien celui dont le registre porte l'empreinte — et les deux moitiés ne sont
    jamais vérifiées par le même code.

    L'en-tête et le nombre de lignes sont confrontés en plus de l'empreinte : une empreinte seule
    dirait « ce n'est pas le bon fichier » sans jamais dire en quoi.
    """
    assert series(), "le registre ne porte aucune série : la propriété ne vérifierait rien"
    fautes = []
    for serie in series():
        chemin = RACINE_SERIES / serie["fichier"]
        if not chemin.is_file():
            fautes.append(f"{serie['id']} : {serie['fichier']} n'existe pas")
            continue
        texte = chemin.read_text(encoding="utf-8")
        lignes = texte.rstrip("\n").split("\n")
        entete = lignes[0].split(SEPARATEURS[serie.get("separateur", "virgule")])
        if entete != list(serie["colonnes"]):
            fautes.append(
                f"{serie['id']} : l'en-tête du fichier est {entete}, "
                f"{list(serie['colonnes'])} déclarées au registre"
            )
        if len(lignes) - 1 != serie["lignes"]:
            fautes.append(
                f"{serie['id']} : le fichier porte {len(lignes) - 1} ligne(s) de données, "
                f"{serie['lignes']} déclarées au registre"
            )
        obtenue = hashlib.sha256(texte.encode("utf-8")).hexdigest()
        if obtenue != serie["empreinte"]:
            fautes.append(
                f"{serie['id']} : le fichier lu a pour empreinte {obtenue}, le registre consigne "
                f"{serie['empreinte']} — le fichier n'est plus celui que la commande a produit"
            )
    assert not fautes, "fichiers de série divergents :\n  " + "\n  ".join(fautes)


def test_toute_serie_porte_une_commande_et_un_fichier() -> None:
    """Voie par laquelle elle serait vraie à tort : une commande réduite à un espace, ou une liste
    de colonnes vide, passeraient un contrôle de présence de clé. Le contrôle porte donc sur les
    valeurs dépouillées, et il exige aussi que le type soit l'un des deux connus.
    """
    fautes = []
    for serie in series():
        if not (serie.get("commande") or "").strip():
            fautes.append(f"{serie['id']} : commande vide")
        if serie.get("type") not in {"sql", "python"}:
            fautes.append(f"{serie['id']} : type « {serie.get('type')} » inconnu")
        if not (serie.get("fichier") or "").strip():
            fautes.append(f"{serie['id']} : fichier vide")
        if not serie.get("colonnes"):
            fautes.append(f"{serie['id']} : aucune colonne déclarée")
        if not (serie.get("empreinte") or "").strip():
            fautes.append(f"{serie['id']} : empreinte vide")
    assert not fautes, "séries incomplètes :\n  " + "\n  ".join(fautes)


def test_le_rendu_porte_exactement_les_series_du_registre() -> None:
    """Comme pour les scalaires, la correspondance est vérifiée DANS LES DEUX SENS, et les chemins
    rendus sont confrontés aux chemins consignés.
    """
    rendu = RENDU.read_text(encoding="utf-8")
    definies = dict(_DEFINITION_SERIE.findall(rendu))
    attendues = identifiants_des_series()

    manquantes = sorted(attendues - set(definies))
    en_trop = sorted(set(definies) - attendues)
    assert not manquantes, "séries du registre absentes du rendu : " + ", ".join(manquantes)
    assert not en_trop, "séries du rendu absentes du registre : " + ", ".join(en_trop)

    ecarts = [
        f"{serie['id']} : registre {serie['fichier']}, rendu {definies[serie['id']]}"
        for serie in series()
        if definies[serie["id"]] != serie["fichier"]
    ]
    assert not ecarts, "chemins rendus divergents :\n  " + "\n  ".join(ecarts)


def test_chaque_chapitre_declare_les_series_qu_il_appelle() -> None:
    """La cinquième étiquette de l'en-tête, au même titre que les quatre autres."""
    _SER = re.compile(r"^\s*%\s*SER\s*:\s*(.*)$")
    desaccords = []
    for chemin in fichiers_de_chapitre():
        source = chemin.read_text(encoding="utf-8")
        declarees: set[str] = set()
        vue = False
        for ligne in source.splitlines():
            correspondance = _SER.match(ligne)
            if correspondance is None:
                continue
            vue = True
            valeur = correspondance.group(1).strip()
            if valeur.lower() not in {"(aucun)", "(aucune)", ""}:
                declarees |= {m.strip() for m in valeur.split(",") if m.strip()}
        portees = appels_de_serie(source)
        if not vue:
            desaccords.append(f"{chemin.name} : aucune ligne « SER: » en tête")
            continue
        for absent in sorted(portees - declarees):
            desaccords.append(f"{chemin.name} appelle la série « {absent} » sans la déclarer")
        for inutile in sorted(declarees - portees):
            desaccords.append(f"{chemin.name} déclare la série « {inutile} » sans l'appeler")
    assert not desaccords, "déclarations de séries divergentes :\n  " + "\n  ".join(desaccords)
