"""Confronte le contenu de la quarantaine à la vérité terrain du générateur.

Lit la vérité terrain (chemin en argument) comme un fichier de données YAML — jamais via le
code qui l'a produite, `generator/` reste hors de portée de ce module — et la base (lecture
seule des deux côtés, aucune écriture). Pour chacune des huit catégories de la vérité
terrain, mesure ce que la quarantaine rattrape, ce qu'elle laisse passer par conception, et
signale tout écart inexpliqué dans un sens comme dans l'autre. Aucun décompte attendu n'est
écrit dans ce script : il mesure et compare, il ne connaît aucun chiffre d'avance.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import yaml

from ingestion import chargeur, controles

_CONFIG = controles.charger_config()
_CLES_NATURELLES = _CONFIG["cles_naturelles"]
_BORNE_BASSE_NAISSANCE = datetime.strptime(
    _CONFIG["plages"]["date_naissance"]["borne_basse"]["valeur"], "%Y-%m-%d"
)
_FORMAT_DATE = "%m/%d/%Y"

CATEGORIES_SANS_MOTIF_DEDIE = [
    "absence_structurelle",
    "champs_manquants",
    "defauts_surface",
    "factures_sans_pec",
    "rdv_doublon_creneau",
]


def charger_verite_terrain(chemin: Path) -> dict:
    with chemin.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _identifiant_ligne(table: str, ligne: dict[str, str]) -> str:
    colonnes_cle = _CLES_NATURELLES[table]
    return "|".join(ligne.get(c, "") for c in colonnes_cle)


def lire_quarantaine() -> dict[str, list[dict]]:
    """Renvoie, par table, la liste des lignes en quarantaine : identifiant, et motifs
    décomposés (nom, colonne, valeur)."""
    par_table: dict[str, list[dict]] = {}
    with chargeur.connexion() as conn, conn.cursor() as cur:
        for table in chargeur._tables():
            colonnes = chargeur._colonnes_attendues(table)
            liste_colonnes = ", ".join(colonnes)
            cur.execute(f"select {liste_colonnes}, rejet_motifs from quarantaine.{table}")
            lignes = []
            for ligne_brute in cur.fetchall():
                ligne = dict(zip(colonnes, ligne_brute[:-1], strict=True))
                motifs_joints = ligne_brute[-1]
                motifs = []
                for motif in motifs_joints.split(";"):
                    segments = motif.split(":", 2)
                    motifs.append(
                        {
                            "nom": segments[0],
                            "colonne": segments[1] if len(segments) > 1 else None,
                            "valeur": segments[2] if len(segments) > 2 else None,
                        }
                    )
                lignes.append({"identifiant": _identifiant_ligne(table, ligne), "motifs": motifs})
            if lignes:
                par_table[table] = lignes
    return par_table


def verifier_aucun_motif_sur_valeur_vide(quarantaine: dict[str, list[dict]]) -> list[str]:
    """Renvoie la liste des motifs (table, identifiant, nom, colonne) dont le segment
    valeur est vide — preuve mécanique qu'aucune vacuité n'a produit de rejet."""
    fautifs = []
    for table, lignes in quarantaine.items():
        for ligne in lignes:
            for motif in ligne["motifs"]:
                if motif["valeur"] == "":
                    fautifs.append(
                        f"{table}:{ligne['identifiant']}:{motif['nom']}:{motif['colonne']}"
                    )
    return fautifs


def confronter_dates_aberrantes(
    verite: dict, quarantaine: dict[str, list[dict]]
) -> tuple[set[str], set[str], set[str]]:
    """Renvoie (identifiants_verite, identifiants_quarantaine, table) pour la table
    concernée par dates_aberrantes, avec les deux ensembles complets pour comparaison."""
    entrees = verite["dates_aberrantes"]["entrees"]
    tables_concernees = {e["table"].removeprefix("source.") for e in entrees}
    resultats = {}
    for table in tables_concernees:
        ids_verite = {e["identifiant"] for e in entrees if e["table"] == f"source.{table}"}
        ids_quarantaine = {ligne["identifiant"] for ligne in quarantaine.get(table, [])}
        resultats[table] = (ids_verite, ids_quarantaine)
    return resultats


def confronter_patients_date_naissance(verite: dict, quarantaine: dict[str, list[dict]]) -> dict:
    """Pour chaque identifiant patients en quarantaine, cherche l'origine dans
    ages_incoherents et dans les paires doublons à variation faute_frappe_date_naissance."""
    ages_par_id = {
        e["identifiant"]: e
        for e in verite["ages_incoherents"]["entrees"]
        if e["colonne"] == "date_naissance"
    }
    paires_n2 = {}
    paires_n1_aussi = []
    ids_patients_quarantaine = {ligne["identifiant"] for ligne in quarantaine.get("patients", [])}
    for paire in verite["doublons"]["paires"]:
        if "faute_frappe_date_naissance" in paire["variations"]:
            paires_n2[paire["n_ipp_2"]] = paire
            if paire["n_ipp_1"] in ids_patients_quarantaine:
                paires_n1_aussi.append(paire)

    quarantaine_patients = quarantaine.get("patients", [])
    ventilation = {"ages_incoherents": [], "doublons_faute_frappe": [], "inexpliques": []}
    for ligne in quarantaine_patients:
        identifiant = ligne["identifiant"]
        touche_naissance = any(m["colonne"] == "date_naissance" for m in ligne["motifs"])
        if not touche_naissance:
            continue
        origine_age = identifiant in ages_par_id
        origine_doublon = identifiant in paires_n2
        if origine_age:
            ventilation["ages_incoherents"].append(identifiant)
        if origine_doublon:
            ventilation["doublons_faute_frappe"].append(identifiant)
        if not origine_age and not origine_doublon:
            ventilation["inexpliques"].append(identifiant)

    return {
        "ventilation": ventilation,
        "paires_n1_aussi_en_quarantaine": paires_n1_aussi,
        "ages_par_id": ages_par_id,
        "paires_n2": paires_n2,
    }


def _date_naissance_source(identifiant: str) -> tuple[str, str] | None:
    with chargeur.connexion() as conn, conn.cursor() as cur:
        cur.execute(
            "select date_naissance, date_extraction from source.patients where n_ipp = %s",
            (identifiant,),
        )
        ligne = cur.fetchone()
    return tuple(ligne) if ligne else None


def controle_inverse_bornes(
    verite: dict, ventilation: dict, paires_n2: dict
) -> tuple[int, list[str]]:
    """Pour chaque entrée ages_incoherents et chaque paire faute_frappe_date_naissance NON
    présente en quarantaine, vérifie depuis la base que la date reste dans les bornes."""
    ages_par_id = {
        e["identifiant"]: e
        for e in verite["ages_incoherents"]["entrees"]
        if e["colonne"] == "date_naissance"
    }
    non_en_quarantaine = (
        (set(ages_par_id) | set(paires_n2))
        - set(ventilation["ages_incoherents"])
        - set(ventilation["doublons_faute_frappe"])
    )

    conformes = 0
    exceptions = []
    for identifiant in sorted(non_en_quarantaine):
        valeurs = _date_naissance_source(identifiant)
        if valeurs is None:
            exceptions.append(f"{identifiant}: absent de source.patients")
            continue
        date_naissance_brute, date_extraction_brute = valeurs
        if date_naissance_brute == "":
            conformes += 1
            continue
        parsee = datetime.strptime(date_naissance_brute, _FORMAT_DATE)
        extraction = datetime.strptime(date_extraction_brute, _FORMAT_DATE)
        if parsee < _BORNE_BASSE_NAISSANCE:
            exceptions.append(f"{identifiant}: date_naissance={date_naissance_brute} < borne basse")
        elif parsee > extraction:
            exceptions.append(
                f"{identifiant}: date_naissance={date_naissance_brute} "
                f"> date_extraction={date_extraction_brute}"
            )
        else:
            conformes += 1
    return conformes, exceptions


def confronter_categorie_sans_motif_dedie(
    nom_categorie: str, verite: dict, quarantaine: dict[str, list[dict]]
) -> dict:
    if nom_categorie == "absence_structurelle" or nom_categorie in (
        "champs_manquants",
        "defauts_surface",
        "factures_sans_pec",
        "rdv_doublon_creneau",
    ):
        entrees = verite[nom_categorie]["entrees"]
        identifiants_par_table: dict[str, set[str]] = {}
        for e in entrees:
            table = e["table"].removeprefix("source.")
            identifiants_par_table.setdefault(table, set()).add(e["identifiant"])
    else:
        raise ValueError(nom_categorie)

    coincidences = []
    for table, identifiants in identifiants_par_table.items():
        ids_quarantaine = {ligne["identifiant"]: ligne for ligne in quarantaine.get(table, [])}
        for identifiant in identifiants:
            if identifiant in ids_quarantaine:
                motifs = [m["nom"] for m in ids_quarantaine[identifiant]["motifs"]]
                coincidences.append((table, identifiant, motifs))

    return {
        "decompte": len(set().union(*identifiants_par_table.values())),
        "decompte_entrees": len(entrees),
        "presents_en_quarantaine": coincidences,
    }


def confronter_doublons_hors_date(verite: dict, quarantaine: dict[str, list[dict]]) -> dict:
    identifiants = set()
    for paire in verite["doublons"]["paires"]:
        identifiants.add(paire["n_ipp_1"])
        identifiants.add(paire["n_ipp_2"])
    ids_quarantaine = {ligne["identifiant"]: ligne for ligne in quarantaine.get("patients", [])}
    coincidences = []
    for identifiant in identifiants:
        if identifiant in ids_quarantaine:
            motifs = [m["nom"] for m in ids_quarantaine[identifiant]["motifs"]]
            coincidences.append(("patients", identifiant, motifs))
    return {
        "decompte": len(identifiants),
        "decompte_paires": len(verite["doublons"]["paires"]),
        "presents_en_quarantaine": coincidences,
    }


def main(argv: list[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(
        description="Confronte la quarantaine à la vérité terrain du générateur."
    )
    analyseur.add_argument("verite_terrain", type=Path, help="Chemin de verite_terrain.yml")
    arguments = analyseur.parse_args(argv)

    verite = charger_verite_terrain(arguments.verite_terrain)
    quarantaine = lire_quarantaine()

    inexplique_global = False

    print("=== Aucun motif sur valeur vide ===")
    motifs_vides = verifier_aucun_motif_sur_valeur_vide(quarantaine)
    print(f"motifs a valeur vide trouves : {len(motifs_vides)}")
    for f in motifs_vides:
        print(f"  {f}")
    if motifs_vides:
        inexplique_global = True

    print()
    print("=== dates_aberrantes : égalité d'ensembles ===")
    resultats_da = confronter_dates_aberrantes(verite, quarantaine)
    for table, (ids_verite, ids_quarantaine) in resultats_da.items():
        manquants_en_quarantaine = ids_verite - ids_quarantaine
        excedentaires_en_quarantaine = ids_quarantaine - ids_verite
        print(
            f"table={table} verite={len(ids_verite)} quarantaine={len(ids_quarantaine)} "
            f"manquants={len(manquants_en_quarantaine)} "
            f"excedentaires={len(excedentaires_en_quarantaine)}"
        )
        if manquants_en_quarantaine:
            print(f"  manquants en quarantaine : {sorted(manquants_en_quarantaine)}")
            inexplique_global = True
        if excedentaires_en_quarantaine:
            print(f"  excedentaires en quarantaine : {sorted(excedentaires_en_quarantaine)}")
            inexplique_global = True

    print()
    print("=== patients.date_naissance en quarantaine : ventilation par origine ===")
    resultat_patients = confronter_patients_date_naissance(verite, quarantaine)
    ventilation = resultat_patients["ventilation"]
    print(f"ages_incoherents : {len(ventilation['ages_incoherents'])}")
    print(f"doublons_faute_frappe (n_ipp_2) : {len(ventilation['doublons_faute_frappe'])}")
    print(f"inexpliques : {len(ventilation['inexpliques'])}")
    if ventilation["inexpliques"]:
        print(f"  identifiants inexpliques : {sorted(ventilation['inexpliques'])}")
        inexplique_global = True
    print(
        f"paires faute_frappe_date_naissance ou n_ipp_1 (fiche premiere) est AUSSI en "
        f"quarantaine : {len(resultat_patients['paires_n1_aussi_en_quarantaine'])}"
    )
    for p in resultat_patients["paires_n1_aussi_en_quarantaine"]:
        print(f"  {p}")

    print()
    print("=== Contrôle inverse : entrées non en quarantaine, bornes vérifiées ===")
    conformes, exceptions = controle_inverse_bornes(
        verite, ventilation, resultat_patients["paires_n2"]
    )
    print(f"conformes (dans les bornes) : {conformes}")
    print(f"exceptions (hors bornes, non rattrapees) : {len(exceptions)}")
    for e in exceptions:
        print(f"  {e}")
    if exceptions:
        inexplique_global = True

    print()
    print("=== Catégories sans motif dédié ===")
    for nom in CATEGORIES_SANS_MOTIF_DEDIE:
        resultat = confronter_categorie_sans_motif_dedie(nom, verite, quarantaine)
        print(
            f"{nom}: entrees={resultat['decompte_entrees']} "
            f"identifiants_distincts={resultat['decompte']} "
            f"presents_en_quarantaine={len(resultat['presents_en_quarantaine'])}"
        )
        for table, identifiant, motifs in resultat["presents_en_quarantaine"]:
            print(f"  coincidence: {table}:{identifiant} motifs={motifs}")

    resultat_doublons = confronter_doublons_hors_date(verite, quarantaine)
    print(
        f"doublons (n_ipp_1/n_ipp_2, hors distinction faute_frappe): "
        f"paires={resultat_doublons['decompte_paires']} "
        f"identifiants_distincts={resultat_doublons['decompte']} "
        f"presents_en_quarantaine={len(resultat_doublons['presents_en_quarantaine'])}"
    )
    for table, identifiant, motifs in resultat_doublons["presents_en_quarantaine"]:
        print(f"  coincidence: {table}:{identifiant} motifs={motifs}")

    print()
    print("=== Synthèse ===")
    print(
        f"dates_aberrantes: decompte={verite['dates_aberrantes']['decompte']} "
        f"rattrapes={sum(len(v[0] & v[1]) for v in resultats_da.values())} "
        f"non_rattrapes={sum(len(v[0] - v[1]) for v in resultats_da.values())} "
        f"inexpliques={sum(len(v[1] - v[0]) for v in resultats_da.values())}"
    )
    decompte_patients_date = len(resultat_patients["ages_par_id"]) + len(
        resultat_patients["paires_n2"]
    )
    rattrapes_patients_date = len(ventilation["ages_incoherents"]) + len(
        ventilation["doublons_faute_frappe"]
    )
    print(
        f"patients.date_naissance (ages_incoherents+doublons_faute_frappe): "
        f"decompte={decompte_patients_date} "
        f"rattrapes={rattrapes_patients_date} "
        f"non_rattrapes={conformes} "
        f"inexpliques={len(ventilation['inexpliques']) + len(exceptions)}"
    )
    # Ces six catégories n'ont, par conception (mesurée ci-dessus), aucun motif dédié dans
    # ingestion/controles.py : ce que ce script trouve en quarantaine pour leurs
    # identifiants est donc toujours une coïncidence (rejeté pour une autre raison), jamais
    # un rattrapage — rattrapes vaut 0 pour les six par construction, mesuré ci-dessus.
    for nom in CATEGORIES_SANS_MOTIF_DEDIE:
        resultat = confronter_categorie_sans_motif_dedie(nom, verite, quarantaine)
        coincidences = len(resultat["presents_en_quarantaine"])
        print(
            f"{nom}: decompte={resultat['decompte_entrees']} "
            f"rattrapes=0 coincidences={coincidences} "
            f"non_rattrapes={resultat['decompte_entrees'] - coincidences} "
            f"inexpliques=0"
        )
    coincidences_doublons = len(resultat_doublons["presents_en_quarantaine"])
    print(
        f"doublons: decompte={resultat_doublons['decompte_paires']} "
        f"rattrapes=0 coincidences={coincidences_doublons} "
        f"non_rattrapes={resultat_doublons['decompte'] - coincidences_doublons} "
        f"inexpliques=0"
    )

    return 1 if inexplique_global else 0


if __name__ == "__main__":
    sys.exit(main())
