"""Contrôle de qualité journalier : cumule les rejets d'une date d'extraction sur les onze
tables et compare ce cumul au même seuil que celui du chargeur de fichier — jamais un seuil
propre à ce module (`ingestion/controles.yml`, `seuil_quarantaine`, lu via
`ingestion.controles.charger_config()`, comme `ingestion/chargeur.py`).

Le chargeur garde chaque fichier individuellement : un défaut systémique qui dépose peu de
lignes mauvaises dans chacune des onze tables, chaque fichier restant sous le seuil, échappe à
une garde qui raisonne fichier par fichier. Ce contrôle observe le cumul de la journée entière,
ce que le chargeur, structurellement, ne peut pas voir (docs/decisions/
0040-controle-qualite-taux-rejet-cumule.md).

`source` porte la date au format d'affichage du système observé (`date_extraction`,
MM/DD/YYYY) ; `quarantaine` porte la même date au format ISO (`rejet_partition`, YYYY-MM-DD) —
les deux tables ne portent pas la date de la même façon. Ne modifie rien en base : lecture
seule.
"""

import argparse
import sys
from datetime import datetime

from ingestion import chargeur, controles

_FORMAT_DATE = "%m/%d/%Y"


def _date_us(date_iso: str) -> str:
    return datetime.strptime(date_iso, "%Y-%m-%d").strftime(_FORMAT_DATE)


def decompte_journee(date_iso: str) -> dict[str, dict[str, int]]:
    """Lignes chargées et rejetées de `date_iso`, par table, sur les onze tables du registre."""
    date_us = _date_us(date_iso)
    decomptes: dict[str, dict[str, int]] = {}
    with chargeur.connexion() as conn, conn.cursor() as cur:
        for table in chargeur._tables():
            cur.execute(
                f"select count(*) from source.{table} where date_extraction = %s", (date_us,)
            )
            charges = cur.fetchone()[0]
            cur.execute(
                f"select count(*) from quarantaine.{table} where rejet_partition = %s",
                (date_iso,),
            )
            rejetes = cur.fetchone()[0]
            decomptes[table] = {"charges": charges, "rejetes": rejetes}
    return decomptes


def _ventilation(decomptes: dict[str, dict[str, int]]) -> str:
    return "\n".join(
        f"  {table}: charges={d['charges']} rejetes={d['rejetes']}"
        for table, d in sorted(decomptes.items())
    )


def evaluer(date_iso: str) -> tuple[bool, str]:
    """Renvoie (reussite, message). Ne lève jamais pour un jour sans aucune ligne : le taux y
    est indéfini (0/0), détecté avant toute division, traité comme une réussite explicite —
    aucun rejet ne peut dépasser un seuil sur une population vide."""
    decomptes = decompte_journee(date_iso)
    total_charges = sum(d["charges"] for d in decomptes.values())
    total_rejetes = sum(d["rejetes"] for d in decomptes.values())
    total_lignes = total_charges + total_rejetes
    ventilation = _ventilation(decomptes)

    if total_lignes == 0:
        return True, (
            f"controle de qualite pour {date_iso} : aucune ligne rencontree ce jour, taux non "
            f"calculable\n{ventilation}"
        )

    taux = total_rejetes / total_lignes
    seuil = controles.charger_config()["seuil_quarantaine"]["valeur"]

    if taux > seuil:
        return False, (
            f"controle de qualite pour {date_iso} : ECHEC - taux de rejet cumule {taux:.4f} "
            f"depasse le seuil {seuil:.4f} (rejetes={total_rejetes}, lignes={total_lignes})\n"
            f"{ventilation}"
        )

    return True, (
        f"controle de qualite pour {date_iso} : OK - taux de rejet cumule {taux:.4f} sous le "
        f"seuil {seuil:.4f} (rejetes={total_rejetes}, lignes={total_lignes})\n{ventilation}"
    )


def main() -> None:
    analyseur = argparse.ArgumentParser(
        description="Controle de qualite journalier : taux de rejet cumule d'une date "
        "d'extraction sur les onze tables, compare au seuil du chargeur."
    )
    analyseur.add_argument("date_extraction", help="Date d'extraction, format AAAA-MM-JJ")
    arguments = analyseur.parse_args()

    reussite, message = evaluer(arguments.date_extraction)
    print(message)
    if not reussite:
        sys.exit(1)


if __name__ == "__main__":
    main()
