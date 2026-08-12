"""Contrôles d'entrée de l'ingestion : typage, plage et unicité, sur une ligne ou un fichier.

Lit le registre des champs (`docs/champs/registre_champs.yml`) en lecture seule pour
connaître les colonnes et le `type_metier` de chaque table, et sa propre configuration
déclarée (`ingestion/controles.yml`) pour les formats, les plages, les clés naturelles et
le domaine booléen. N'importe rien de `generator/` : les deux chaînes ne partagent que le
registre, ce qui est ce qui donne un sens à une réconciliation ultérieure entre elles.

La vacuité passe tout : une valeur vide (`valeur == ""`, jamais un test de fausseté — `0`
et `0.00` sont des valeurs légitimes) n'est soumise à aucun contrôle de typage, de plage ou
de domaine.
"""

import decimal
from datetime import datetime
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
REGISTRE = RACINE / "docs" / "champs" / "registre_champs.yml"
CONFIG = RACINE / "ingestion" / "controles.yml"


def charger_registre() -> list[dict]:
    with REGISTRE.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def charger_config() -> dict:
    with CONFIG.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _colonnes_par_table(registre: list[dict]) -> dict[str, list[dict]]:
    par_table: dict[str, list[dict]] = {}
    for entree in registre:
        table = entree["table"].removeprefix("source.")
        par_table.setdefault(table, []).append(entree)
    return par_table


_REGISTRE = charger_registre()
_CONFIG = charger_config()
_COLONNES_PAR_TABLE = _colonnes_par_table(_REGISTRE)

_FORMAT_DATE = _CONFIG["formats"]["date"]["motif"]
_FORMAT_HORODATAGE = _CONFIG["formats"]["horodatage"]["motif"]
_BORNE_BASSE_EVENEMENT = datetime.strptime(
    _CONFIG["plages"]["borne_basse_evenement"]["valeur"], "%Y-%m-%d"
)
_BORNE_BASSE_NAISSANCE = datetime.strptime(
    _CONFIG["plages"]["date_naissance"]["borne_basse"]["valeur"], "%Y-%m-%d"
)
_DOMAINE_BOOLEEN = {str(v) for v in _CONFIG["booleens"]["domaine"]}
_CLES_NATURELLES = _CONFIG["cles_naturelles"]


def _parser(valeur: str, type_metier: str) -> datetime | None:
    motif = _FORMAT_DATE if type_metier == "date" else _FORMAT_HORODATAGE
    try:
        return datetime.strptime(valeur, motif)
    except ValueError:
        return None


def controler_ligne(table: str, ligne: dict[str, str]) -> list[str]:
    """Contrôle une ligne (dict colonne -> valeur brute) pour une table donnée.

    Renvoie la liste des motifs de rejet, vide si la ligne passe.
    """
    motifs: list[str] = []
    colonnes = _COLONNES_PAR_TABLE.get(table, [])

    date_extraction_parsee = None
    valeur_date_extraction = ligne.get("date_extraction", "")
    if valeur_date_extraction != "":
        date_extraction_parsee = _parser(valeur_date_extraction, "date")

    for entree in colonnes:
        colonne = entree["colonne"]
        type_metier = entree["type_metier"]
        valeur = ligne.get(colonne, "")

        if valeur == "":
            continue

        if type_metier in ("date", "horodatage"):
            parsee = _parser(valeur, type_metier)
            if parsee is None:
                motifs.append(f"typage_{type_metier}:{colonne}:{valeur}")
                continue

            if colonne == "date_naissance":
                if parsee < _BORNE_BASSE_NAISSANCE:
                    motifs.append(f"plage_basse:{colonne}:{valeur}")
                if date_extraction_parsee is not None and parsee > date_extraction_parsee:
                    motifs.append(f"naissance_future:{colonne}:{valeur}")
            elif parsee < _BORNE_BASSE_EVENEMENT:
                motifs.append(f"plage_basse:{colonne}:{valeur}")

        elif type_metier == "decimal":
            try:
                decimal.Decimal(valeur)
            except decimal.InvalidOperation:
                motifs.append(f"typage_decimal:{colonne}:{valeur}")

        elif type_metier == "entier":
            try:
                int(valeur)
            except ValueError:
                motifs.append(f"typage_entier:{colonne}:{valeur}")

        elif type_metier == "booleen":
            if valeur not in _DOMAINE_BOOLEEN:
                motifs.append(f"domaine_booleen:{colonne}:{valeur}")

    return motifs


def controler_unicite(table: str, lignes: list[dict[str, str]]) -> list[list[str]]:
    """Contrôle l'unicité de la clé naturelle sur l'ensemble des lignes d'un fichier.

    Renvoie une liste de motifs par ligne, alignée sur `lignes` (une liste vide pour une
    ligne indemne). Une clé naturelle vide ne participe pas au contrôle d'unicité mais
    reçoit son propre motif.
    """
    colonnes_cle = _CLES_NATURELLES[table]
    nom_cle = ",".join(colonnes_cle)

    motifs_par_ligne: list[list[str]] = [[] for _ in lignes]
    vues: set[tuple[str, ...]] = set()

    for indice, ligne in enumerate(lignes):
        valeurs = tuple(ligne.get(colonne, "") for colonne in colonnes_cle)

        if any(v == "" for v in valeurs):
            motifs_par_ligne[indice].append(f"cle_vide:{nom_cle}")
            continue

        if valeurs in vues:
            valeur_affichee = "|".join(valeurs)
            motifs_par_ligne[indice].append(f"unicite:{nom_cle}:{valeur_affichee}")
        else:
            vues.add(valeurs)

    return motifs_par_ligne
