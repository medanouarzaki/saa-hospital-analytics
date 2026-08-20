"""Le rendu Markdown du relevé de champs est bien celui que son générateur produit.

Le fichier porte en tête « produit mécaniquement : ne pas modifier à la main », et rien ne le
vérifiait. Mesuré : une clé ajoutée au relevé — les champs déclarés non employés — n'a pas été
rendue pendant tout un cycle de travail, le générateur ne la lisant pas. Le rendu était donc
incomplet au regard de sa source, silencieusement, et la seule façon de s'en apercevoir était de
lire les deux fichiers côte à côte.

CE CONTRÔLE NE COMPILE RIEN ET N'OUVRE AUCUNE BASE : il régénère dans un répertoire temporaire et
compare octet pour octet. Le générateur n'est pas modifié pour être testable — sa cible est une
constante de module, et le test la remplace le temps de l'exécution.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
GENERATEUR = RACINE / "docs" / "observation" / "generer_releve_md.py"
RENDU = RACINE / "docs" / "observation" / "releve_champs.md"

TITRE_NON_EMPLOYES = "## Champs non employés"


def charger_module(chemin: Path):
    spec = importlib.util.spec_from_file_location(chemin.stem, chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_le_rendu_markdown_du_releve_est_a_jour(tmp_path: Path) -> None:
    module = charger_module(GENERATEUR)
    cible = tmp_path / "releve_champs.md"
    module.CIBLE = cible
    module.main()

    assert cible.exists(), "le générateur n'a rien produit"
    attendu = cible.read_bytes()
    obtenu = RENDU.read_bytes()
    assert obtenu == attendu, (
        "docs/observation/releve_champs.md diffère de ce que son générateur produit : "
        f"{len(obtenu)} octets commis contre {len(attendu)} régénérés. "
        "Relancer docs/observation/generer_releve_md.py."
    )


def test_le_rendu_porte_les_champs_non_employes(tmp_path: Path) -> None:
    """La section que le générateur ne rendait pas est bien celle qui manquait.

    Sans cette propriété, la précédente resterait verte si le générateur cessait de rendre la
    section ET que le fichier commis cessait de la porter : deux régressions symétriques
    s'annulent, et c'est exactement le défaut que ce contrôle existe pour empêcher.
    """
    import yaml

    with (RACINE / "docs" / "observation" / "releve_champs.yml").open(encoding="utf-8") as f:
        donnees = yaml.safe_load(f)
    groupes = donnees.get("champs_non_employes", [])
    assert groupes, "le relevé ne déclare aucun champ non employé : la propriété ne vérifie rien"

    rendu = RENDU.read_text(encoding="utf-8")

    # Chercher les identifiants ne suffit pas : ils figurent tous au tableau de leur écran, que la
    # section soit rendue ou non. Mesuré — une mutation qui supprimait la section entière laissait
    # cette propriété verte. Ce sont le titre de section et les motifs qui n'existent nulle part
    # ailleurs.
    assert TITRE_NON_EMPLOYES in rendu, (
        f"le rendu ne porte pas la section « {TITRE_NON_EMPLOYES} » : le générateur ne rend pas "
        "les champs déclarés non employés"
    )

    manquants = [
        " ".join(groupe["motif"].split())[:60]
        for groupe in groupes
        if " ".join(groupe["motif"].split()) not in rendu
    ]
    assert not manquants, "motifs de non-emploi absents du rendu Markdown : " + " | ".join(
        manquants
    )
