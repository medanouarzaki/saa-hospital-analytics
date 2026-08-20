"""L'index des enregistrements de décision, tenu par un contrôle plutôt que par la discipline.

`docs/decisions/README.md` liste un enregistrement par ligne. Un index tenu à la main diverge : un
enregistrement ajouté sans sa ligne reste invisible, une ligne dont le fichier a été renommé pointe
dans le vide, et un titre corrigé d'un seul côté fait dire à l'index autre chose que ce que
l'enregistrement décide.

LA CORRESPONDANCE EST VÉRIFIÉE DANS LES DEUX SENS, et ce n'est pas une précaution de style : une
seule direction ne prouve pas une propriété bidirectionnelle. Tout fichier d'enregistrement a sa
ligne ; toute ligne a son fichier ; et les titres concordent, caractère pour caractère.

LA VACANCE DE NUMÉRO EST DÉCLARÉE, PAS DÉCOUVERTE. Le numéro 0009 n'a jamais été porté par aucun
fichier. Le contrôle exige que l'index le déclare, et n'admet aucun autre trou : un numéro sauté par
inadvertance se distingue ainsi d'une vacance assumée.

Aucun accès à la base, aucune dépendance à un volume de données : ce fichier se collecte et
s'exécute sur un clone frais.
"""

from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DECISIONS = RACINE / "docs" / "decisions"
INDEX = DECISIONS / "README.md"

# Un fichier d'enregistrement : quatre chiffres, un tiret, un intitulé. L'index lui-même porte un
# nom qui ne suit pas cette forme, et se trouve donc exclu sans avoir à être nommé.
MOTIF_FICHIER = re.compile(r"^(\d{4})-.+\.md$")
# Une ligne d'index : | [NNNN](fichier.md) | phrase |
MOTIF_LIGNE = re.compile(r"^\|\s*\[(\d{4})\]\(([^)]+)\)\s*\|\s*(.+?)\s*\|$")
# Le titre d'un enregistrement : « # ADR NNNN — phrase ». Le tiret est un tiret cadratin.
MOTIF_TITRE = re.compile(r"^#\s*ADR\s+(\d{4})\s*—\s*(.+?)\s*$")

# La vacance, déclarée dans l'index sous cette forme. Le contrôle lit le numéro dans le texte plutôt
# que de le porter lui-même : combler la vacance sans retirer la phrase ferait rougir le contrôle.
MOTIF_VACANCE = re.compile(r"\*\*Le numéro (\d{4}) est vacant\.\*\*")


def _enregistrements() -> dict[str, tuple[str, str]]:
    """Numéro -> (nom de fichier, phrase du titre), lus sur le disque."""
    trouves: dict[str, tuple[str, str]] = {}
    for chemin in sorted(DECISIONS.glob("*.md")):
        correspondance = MOTIF_FICHIER.match(chemin.name)
        if not correspondance:
            continue
        titre = next(
            (
                ligne
                for ligne in chemin.read_text(encoding="utf-8").splitlines()
                if ligne.startswith("# ")
            ),
            "",
        )
        entete = MOTIF_TITRE.match(titre)
        assert entete, f"{chemin.name} : titre « {titre} » hors du gabarit « # ADR NNNN — … »"
        assert entete.group(1) == correspondance.group(1), (
            f"{chemin.name} : le titre porte le numéro {entete.group(1)}, le nom de fichier "
            f"{correspondance.group(1)}"
        )
        trouves[correspondance.group(1)] = (chemin.name, entete.group(2))
    return trouves


def _lignes_de_l_index() -> dict[str, tuple[str, str]]:
    """Numéro -> (fichier cité, phrase citée), lus dans l'index."""
    lignes: dict[str, tuple[str, str]] = {}
    for ligne in INDEX.read_text(encoding="utf-8").splitlines():
        correspondance = MOTIF_LIGNE.match(ligne.strip())
        if not correspondance:
            continue
        numero, fichier, phrase = correspondance.groups()
        assert numero not in lignes, f"le numéro {numero} figure deux fois à l'index"
        lignes[numero] = (fichier, phrase)
    return lignes


def test_tout_enregistrement_a_sa_ligne_d_index() -> None:
    """Premier sens : rien sur le disque qui manque à l'index."""
    manquants = sorted(set(_enregistrements()) - set(_lignes_de_l_index()))
    assert not manquants, (
        f"enregistrements sans ligne d'index : {manquants} — ajoutez-les à {INDEX.name}"
    )


def test_toute_ligne_d_index_a_son_enregistrement() -> None:
    """Second sens : rien à l'index qui manque sur le disque."""
    enregistrements = _enregistrements()
    orphelines = []
    for numero, (fichier, _) in sorted(_lignes_de_l_index().items()):
        if numero not in enregistrements:
            orphelines.append(f"{numero} (cité comme {fichier})")
        elif enregistrements[numero][0] != fichier:
            orphelines.append(
                f"{numero} : l'index cite {fichier}, le disque porte {enregistrements[numero][0]}"
            )
    assert not orphelines, f"lignes d'index sans enregistrement correspondant : {orphelines}"


def test_les_titres_concordent_entre_l_index_et_les_enregistrements() -> None:
    """Un titre corrigé d'un seul côté fait dire à l'index autre chose que la décision."""
    enregistrements = _enregistrements()
    index = _lignes_de_l_index()
    ecarts = []
    for numero in sorted(set(enregistrements) & set(index)):
        _, attendue = enregistrements[numero]
        _, citee = index[numero]
        if citee != attendue:
            ecarts.append(f"{numero} : index « {citee} » contre titre « {attendue} »")
    assert not ecarts, "titres divergents entre l'index et les enregistrements :\n" + "\n".join(
        ecarts
    )


def test_la_numerotation_est_sans_trou_hors_la_vacance_declaree() -> None:
    """Un numéro sauté par inadvertance se distingue d'une vacance assumée."""
    texte = INDEX.read_text(encoding="utf-8")
    declarees = {m.group(1) for m in MOTIF_VACANCE.finditer(texte)}

    numeros = sorted(int(n) for n in _enregistrements())
    assert numeros, "aucun enregistrement trouvé"
    attendus = set(range(numeros[0], numeros[-1] + 1))
    absents = {f"{n:04d}" for n in attendus - set(numeros)}

    non_declarees = sorted(absents - declarees)
    assert not non_declarees, f"numéros absents et non déclarés vacants à l'index : {non_declarees}"

    declarees_a_tort = sorted(declarees - absents)
    assert not declarees_a_tort, (
        f"numéros déclarés vacants à l'index mais portés par un fichier : {declarees_a_tort} — "
        "retirez la phrase de vacance"
    )
