"""Rend docs/observation/releve_champs.yml en Markdown."""

from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent
SOURCE = RACINE / "releve_champs.yml"
CIBLE = RACINE / "releve_champs.md"


def formater_valeurs(valeurs_observees: str | list[str]) -> str:
    if valeurs_observees == "aucune_valeur_observee":
        return "aucune valeur observée"
    return ", ".join(f"`{v}`" for v in valeurs_observees)


def rendre_bloc(champs_du_bloc: list[dict]) -> list[str]:
    lignes = [
        "| id | libelle | type_apparent | saisie | valeurs_observees |",
        "|---|---|---|---|---|",
    ]
    for champ in champs_du_bloc:
        lignes.append(
            f"| {champ['id']} | {champ['libelle']} | {champ['type_apparent']} | "
            f"{champ['saisie']} | {formater_valeurs(champ['valeurs_observees'])} |"
        )

    notes = [champ for champ in champs_du_bloc if champ.get("note")]
    if notes:
        lignes.append("")
        for champ in notes:
            lignes.append(f"- `{champ['id']}` : {champ['note']}")

    return lignes


def rendre_ecran(ecran: dict) -> list[str]:
    lignes = [f"## {ecran['code']} — {ecran['libelle']}", ""]
    champs_par_bloc: dict[str, list[dict]] = {bloc["code"]: [] for bloc in ecran["blocs"]}
    for champ in ecran["champs"]:
        champs_par_bloc[champ["bloc"]].append(champ)

    for bloc in ecran["blocs"]:
        lignes.append(f"### {bloc['code']} — {bloc['libelle']}")
        lignes.append("")
        lignes.extend(rendre_bloc(champs_par_bloc[bloc["code"]]))
        lignes.append("")

    return lignes


def rendre_non_employes(groupes: list[dict]) -> list[str]:
    """Les champs relevés que rien n'emploie, et le motif de leur non-emploi.

    Sans cette section, le rendu serait incomplet au regard de sa source : la clé existe dans le
    relevé depuis que le sens manquant de la traçabilité a été écrit, et le rendu ne la portait pas.
    """
    lignes = ["## Champs non employés", ""]
    total = sum(len(groupe["champs"]) for groupe in groupes)
    lignes.append(
        f"{total} champ(s) qu'aucune entrée du registre des champs n'invoque et qu'aucun chapitre "
        "du rapport ne cite. Chacun porte le motif de son groupe."
    )
    lignes.append("")
    for groupe in groupes:
        lignes.append(f"**Motif.** {' '.join(groupe['motif'].split())}")
        lignes.append("")
        lignes.append("| id |")
        lignes.append("|---|")
        for identifiant in groupe["champs"]:
            lignes.append(f"| {identifiant} |")
        lignes.append("")
    return lignes


def main() -> None:
    with SOURCE.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    lignes = [
        "<!-- Fichier produit mécaniquement : ne pas modifier à la main. -->",
        "",
        f"# Relevé de champs — {data['profil_observe']}",
        "",
        f"Observation du {data['date_observation']}.",
        "",
    ]
    for ecran in data["ecrans"]:
        lignes.extend(rendre_ecran(ecran))

    groupes = data.get("champs_non_employes")
    if groupes:
        lignes.extend(rendre_non_employes(groupes))

    CIBLE.write_text("\n".join(lignes).rstrip("\n") + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
