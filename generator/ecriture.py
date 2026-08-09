"""Écrit les tables du générateur en CSV et en copie colonne, avec manifeste.

Ce module ne valide aucune valeur métier : la couche source est
intégralement en texte et sans contrainte, et le générateur peut et doit
produire des valeurs mal formées — c'est la matière de la quarantaine et du
rapprochement traités ailleurs. La mise en forme convertit ce qu'on lui
donne selon le `type_metier` de la colonne ; elle ne juge jamais si la
valeur est correcte.
"""

import csv
import hashlib
from collections import defaultdict
from datetime import date as date_cls
from pathlib import Path

import pandas as pd
import yaml

from generator import config, registre

POLITIQUES_GUILLEMETS = {
    "minimal": csv.QUOTE_MINIMAL,
    "all": csv.QUOTE_ALL,
    "non_numeric": csv.QUOTE_NONNUMERIC,
    "none": csv.QUOTE_NONE,
}


def _entrees_format() -> dict[str, dict]:
    return {e["nom"]: e for e in config.charger_entrees()}


def mettre_en_forme(valeur, type_metier: str, format_config: dict[str, dict]) -> str:
    if valeur is None:
        return format_config["valeur_manquante"]["valeur"]

    if type_metier in ("texte", "code"):
        return str(valeur)
    if type_metier == "entier":
        return str(valeur)
    if type_metier == "decimal":
        decimales = format_config["nombre_decimales"]["valeur"]
        separateur = format_config["separateur_decimal"]["valeur"]
        return f"{valeur:.{decimales}f}".replace(".", separateur)
    if type_metier == "booleen":
        representation = format_config["representation_booleen"]["valeur"]
        return representation["vrai"] if valeur else representation["faux"]
    if type_metier == "date":
        gabarit = format_config["format_date"]["valeur"]
        return valeur.strftime(gabarit)
    if type_metier == "horodatage":
        gabarit = format_config["format_horodatage"]["valeur"]
        return valeur.strftime(gabarit)

    raise ValueError(f"type_metier sans règle de mise en forme : {type_metier!r}")


def _valider_colonnes(table: str, ligne: dict, colonnes: list[str]) -> None:
    cles_ligne = set(ligne.keys())
    colonnes_attendues = set(colonnes)

    manquantes = colonnes_attendues - cles_ligne
    if manquantes:
        raise ValueError(f"{table} : colonnes manquantes dans la ligne : {sorted(manquantes)}")

    en_trop = cles_ligne - colonnes_attendues
    if en_trop:
        raise ValueError(f"{table} : colonnes en trop dans la ligne : {sorted(en_trop)}")


def _valider_bornage_periode(
    table: str, ligne: dict, date_debut: date_cls, date_fin: date_cls
) -> None:
    valeur_date = ligne["date_extraction"]
    if valeur_date < date_debut or valeur_date > date_fin:
        raise ValueError(
            f"{table} : date_extraction {valeur_date.isoformat()} hors de la période "
            f"[{date_debut.isoformat()}, {date_fin.isoformat()}] pour la ligne {ligne!r}"
        )


def _empreinte(chemin: Path) -> str:
    return hashlib.sha256(chemin.read_bytes()).hexdigest()


def _chemin_partition(
    racine: Path, gabarit: str, scenario: str, table: str, date_extraction: str
) -> Path:
    relatif = gabarit.format(scenario=scenario, table=table, date_extraction=date_extraction)
    return racine / relatif


class Execution:
    def __init__(self, racine: Path, scenario: str, graine: int, date_debut: str, date_fin: str):
        self.racine = Path(racine)
        self.scenario = scenario
        self.graine = graine
        self.date_debut = date_debut
        self.date_fin = date_fin
        self.decompte_lignes: dict[str, int] = {}
        self.partitions: dict[str, list[str]] = {}
        self.empreintes: dict[str, str] = {}

    def ecrire_table(self, table: str, lignes: list[dict]) -> None:
        colonnes = registre.colonnes_table(table)
        if not colonnes:
            raise KeyError(f"table inconnue du registre : {table}")

        format_config = _entrees_format()
        gabarit = format_config["gabarit_arborescence"]["valeur"]
        encodage = format_config["encodage"]["valeur"]
        separateur = ","
        politique = POLITIQUES_GUILLEMETS[format_config["politique_guillemets_csv"]["valeur"]]
        fin_de_ligne = format_config["fin_de_ligne"]["valeur"]
        types_colonnes = {colonne: registre.type_metier(table, colonne) for colonne in colonnes}

        date_debut_periode = date_cls.fromisoformat(self.date_debut)
        date_fin_periode = date_cls.fromisoformat(self.date_fin)

        par_date: dict[str, list[dict]] = defaultdict(list)
        for ligne in lignes:
            _valider_colonnes(table, ligne, colonnes)
            _valider_bornage_periode(table, ligne, date_debut_periode, date_fin_periode)
            valeur_date = ligne["date_extraction"]
            cle_date = valeur_date.isoformat()
            par_date[cle_date].append(ligne)

        nom_court = table.split(".")[-1]
        partitions_table = self.partitions.setdefault(table, [])

        for cle_date, lignes_du_jour in par_date.items():
            lignes_formattees = [
                {
                    colonne: mettre_en_forme(ligne[colonne], types_colonnes[colonne], format_config)
                    for colonne in colonnes
                }
                for ligne in lignes_du_jour
            ]

            dossier = _chemin_partition(self.racine, gabarit, self.scenario, table, cle_date)
            dossier.mkdir(parents=True, exist_ok=True)

            df = pd.DataFrame(lignes_formattees, columns=colonnes)

            chemin_csv = dossier / f"{nom_court}.csv"
            df.to_csv(
                chemin_csv,
                index=False,
                sep=separateur,
                lineterminator=fin_de_ligne,
                encoding=encodage,
                quoting=politique,
            )

            chemin_parquet = dossier / f"{nom_court}.parquet"
            df.to_parquet(chemin_parquet, engine="pyarrow", index=False)

            for chemin in (chemin_csv, chemin_parquet):
                relatif = str(chemin.relative_to(self.racine))
                partitions_table.append(relatif)
                self.empreintes[relatif] = _empreinte(chemin)

        self.decompte_lignes[table] = self.decompte_lignes.get(table, 0) + len(lignes)

    def ecrire_manifeste(self) -> Path:
        manifeste = {
            "scenario": self.scenario,
            "graine": self.graine,
            "periode": {"debut": self.date_debut, "fin": self.date_fin},
            "decompte_lignes": self.decompte_lignes,
            "partitions": self.partitions,
            "empreintes": self.empreintes,
        }
        chemin = self.racine / "manifeste.yml"
        with chemin.open("w", encoding="utf-8") as f:
            yaml.safe_dump(manifeste, f, allow_unicode=True, sort_keys=True)
        return chemin
