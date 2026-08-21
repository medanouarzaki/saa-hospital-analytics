"""La correspondance entre les relations injectées et les conclusions du chapitre d'analyse.

C'EST UNE DETTE OUVERTE DU PROJET, ET CE CONTRÔLE LA TIENT FERMÉE. Le registre des relations
injectées déclare, pour chaque relation, que toute conclusion qui repose dessus doit être présentée
comme un paramètre affiché et non comme une découverte. Rien ne vérifiait jusqu'ici que le rapport
le fasse, ni surtout qu'il le fasse POUR CHACUNE — une relation oubliée passait inaperçue, et une
conclusion sans origine déclarée aussi.

LE PRINCIPE EST BIDIRECTIONNEL, et il vaut pour toute référence croisée de ce dépôt :

  - toute relation du registre est reprise par une conclusion du chapitre, ou déclarée non reprise
    avec son motif ;
  - toute conclusion du chapitre renvoie à une relation, ou est déclarée comme n'en venant pas.

Une seule des deux directions laisserait passer la moitié des défauts : la première seule tolère
une conclusion tombée du ciel, la seconde seule tolère une relation jamais confrontée.

CE CONTRÔLE N'OUVRE AUCUNE BASE et ne compile rien. Il lit deux fichiers.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent

# DEUX FICHIERS, ET LA PORTÉE SUIT LA MATIÈRE. Les marques de conclusion vivent dans la prose du
# chapitre ; les lignes de correspondance vivent en annexe depuis que le tableau y est descendu.
# Le contrôle lit les deux, et les deux sont écrits ici en clair : sans le second, toute relation
# du registre serait déclarée non reprise et le contrôle rougirait à tort ; sans le premier,
# aucune conclusion ne serait vue.
CHAPITRE = RACINE / "report" / "chapitres" / "analyse-de-l-activite.tex"
CORRESPONDANCE = RACINE / "report" / "correspondance_relations.tex"
FICHIERS = (CHAPITRE, CORRESPONDANCE)
REGISTRE = RACINE / "docs" / "relations_injectees.yml"

# Un commentaire LaTeX s'ouvre sur un pourcentage non échappé.
_COMMENTAIRE = re.compile(r"(?<!\\)(?:\\\\)*%")

# Les trois commandes de la correspondance, et la marque d'une conclusion dans la prose. Chaque
# motif exige l'accolade immédiatement après le nom, sans quoi une commande dont le nom commence
# par les mêmes lettres serait prise pour elle.
_CONCLUSION = re.compile(r"\\conclusion\{(C-[0-9]{2})\}")
_REPRISE = re.compile(r"\\relreprise\{(R-[0-9]{2})\}\{([^}]*)\}")
_NON_REPRISE = re.compile(r"\\relnonreprise\{(R-[0-9]{2})\}\{([^}]*)\}")
_HORS = re.compile(r"\\conclusionhors\{(C-[0-9]{2})\}\{([^}]*)\}")

_REFERENCE = re.compile(r"C-[0-9]{2}")


def sans_commentaire(ligne: str) -> str:
    trouve = _COMMENTAIRE.search(ligne)
    return ligne if trouve is None else ligne[: trouve.end() - 1]


def partie_active(source: str) -> str:
    return "\n".join(sans_commentaire(ligne) for ligne in source.splitlines())


def source() -> str:
    return "\n".join(partie_active(f.read_text(encoding="utf-8")) for f in FICHIERS)


def test_les_deux_fichiers_de_la_correspondance_existent() -> None:
    """Un nom mal orthographié dans la liste lèverait à la lecture ; il doit rougir avant."""
    absents = [f.relative_to(RACINE).as_posix() for f in FICHIERS if not f.is_file()]
    assert not absents, f"fichiers déclarés et absents du disque : {absents}"


def relations() -> list[dict]:
    with REGISTRE.open(encoding="utf-8") as fichier:
        return yaml.safe_load(fichier)


def conclusions_de_la_prose() -> list[str]:
    return _CONCLUSION.findall(source())


def reprises() -> dict[str, list[str]]:
    return {r: _REFERENCE.findall(c) for r, c in _REPRISE.findall(source())}


def non_reprises() -> dict[str, str]:
    return {r: motif.strip() for r, motif in _NON_REPRISE.findall(source())}


def hors_relation() -> dict[str, str]:
    return {c: motif.strip() for c, motif in _HORS.findall(source())}


# --------------------------------------------------------------------------------------------
# Témoins des quatre motifs, dans les deux sens.
# --------------------------------------------------------------------------------------------

TEMOINS_POSITIFS = (
    ("conclusion simple", r"\conclusion{C-07} Le taux vaut", ["C-07"]),
    ("deux conclusions", r"\conclusion{C-01} et \conclusion{C-22}", ["C-01", "C-22"]),
)

TEMOINS_NEGATIFS = (
    ("dans un commentaire", r"% ancienne \conclusion{C-07}", []),
    ("texte actif puis commentaire", r"\conclusion{C-01} % \conclusion{C-02}", ["C-01"]),
    ("commande homographe", r"\conclusions{C-07}", []),
    ("identifiant mal formé", r"\conclusion{C-7}", []),
    ("la chaîne hors de toute commande", r"la conclusion C-07 dit que", []),
)


def test_le_motif_de_conclusion_reconnait_chaque_forme() -> None:
    for nom, texte, attendu in TEMOINS_POSITIFS:
        assert _CONCLUSION.findall(partie_active(texte)) == attendu, f"témoin positif « {nom} »"


def test_le_motif_de_conclusion_ne_reconnait_pas_ce_qui_n_en_est_pas_une() -> None:
    for nom, texte, attendu in TEMOINS_NEGATIFS:
        assert _CONCLUSION.findall(partie_active(texte)) == attendu, f"témoin négatif « {nom} »"


def test_les_motifs_de_correspondance_lisent_leurs_deux_arguments() -> None:
    """Témoin positif des trois commandes de tableau, et témoin négatif de leur confusion."""
    ligne = r"\relreprise{R-04}{C-02, C-13}{injectée}{mesurée}"
    assert _REPRISE.findall(partie_active(ligne)) == [("R-04", "C-02, C-13")]
    assert _NON_REPRISE.findall(partie_active(ligne)) == []

    ligne = r"\relnonreprise{R-08}{aucune grandeur ne la porte}"
    assert _NON_REPRISE.findall(partie_active(ligne)) == [("R-08", "aucune grandeur ne la porte")]
    assert _REPRISE.findall(partie_active(ligne)) == []

    ligne = r"\conclusionhors{C-01}{effet des paramètres de volumétrie}"
    assert _HORS.findall(partie_active(ligne)) == [("C-01", "effet des paramètres de volumétrie")]


# --------------------------------------------------------------------------------------------
# Premier sens : toute relation injectée est reprise ou déclarée non reprise.
# --------------------------------------------------------------------------------------------


def test_toute_relation_injectee_figure_a_la_correspondance() -> None:
    """Voie par laquelle elle serait vraie même si le chapitre était faux : si le registre des
    relations était vide, ou si le chapitre ne portait aucune ligne de correspondance, la
    propriété passerait sur l'ensemble vide. Les deux gardes ci-dessous la ferment.

    La confrontation se fait contre le REGISTRE lu à chaque exécution, jamais contre une liste
    recopiée ici : une relation ajoutée au registre fait rougir ce contrôle tant qu'aucune ligne
    de correspondance ne la prend en charge.
    """
    attendues = {relation["id"] for relation in relations()}
    assert attendues, "le registre des relations injectées est vide : rien ne serait vérifié"
    couvertes = set(reprises()) | set(non_reprises())
    assert couvertes, "le chapitre ne porte aucune ligne de correspondance"

    orphelines = sorted(attendues - couvertes)
    inconnues = sorted(couvertes - attendues)
    assert not orphelines, (
        "relations injectées sans ligne de correspondance : "
        + ", ".join(orphelines)
        + " — chacune doit être reprise par une conclusion ou déclarée non reprise avec son motif"
    )
    assert not inconnues, "lignes de correspondance sans relation au registre : " + ", ".join(
        inconnues
    )


def test_une_relation_est_reprise_ou_motivee_mais_jamais_les_deux() -> None:
    """Voie par laquelle elle serait vraie à tort : une relation pourrait figurer aux deux
    tableaux et paraître couverte deux fois, ce qui reviendrait à la déclarer non reprise tout en
    la reprenant. La garde ferme cette voie.
    """
    doubles = sorted(set(reprises()) & set(non_reprises()))
    assert not doubles, "relations à la fois reprises et déclarées non reprises : " + ", ".join(
        doubles
    )


def test_toute_non_reprise_porte_un_motif_non_vide() -> None:
    """Voie par laquelle elle serait vraie à tort : un motif réduit à un espace passerait un
    contrôle de présence d'argument. Le contrôle porte donc sur la valeur dépouillée, et il exige
    un motif d'une longueur qui interdit la formule creuse.
    """
    fautes = [
        f"{relation} : motif « {motif} » trop court pour dire pourquoi elle n'est pas reprise"
        for relation, motif in sorted(non_reprises().items())
        if len(motif) < 40
    ]
    assert not fautes, "motifs de non-reprise insuffisants :\n  " + "\n  ".join(fautes)


# --------------------------------------------------------------------------------------------
# Second sens : toute conclusion du chapitre a une origine déclarée.
# --------------------------------------------------------------------------------------------


def test_toute_conclusion_de_la_prose_a_une_origine_declaree() -> None:
    """LE SENS QUE CE PROJET A DÛ AJOUTER APRÈS COUP SUR TROIS AUTRES APPAREILS.

    Voie par laquelle elle serait vraie même si le chapitre était faux : si la prose ne marquait
    aucune conclusion, la propriété passerait sur l'ensemble vide, et le chapitre pourrait affirmer
    ce qu'il veut sans jamais dire d'où cela vient. La garde ferme cette voie.
    """
    dans_la_prose = conclusions_de_la_prose()
    assert dans_la_prose, "la prose du chapitre ne marque aucune conclusion"

    reprises_par_relation = {c for cibles in reprises().values() for c in cibles}
    declarees_hors = set(hors_relation())

    sans_origine = sorted(
        c for c in set(dans_la_prose) if c not in reprises_par_relation and c not in declarees_hors
    )
    assert not sans_origine, (
        "conclusions sans origine déclarée : "
        + ", ".join(sans_origine)
        + " — chacune doit être nommée par une ligne de reprise ou déclarée comme ne venant "
        "d'aucune relation"
    )

    inexistantes = sorted((reprises_par_relation | declarees_hors) - set(dans_la_prose))
    assert not inexistantes, (
        "la correspondance nomme des conclusions absentes de la prose : " + ", ".join(inexistantes)
    )


def test_une_conclusion_vient_d_une_relation_ou_d_aucune_mais_jamais_des_deux() -> None:
    """Voie par laquelle elle serait vraie à tort : une conclusion pourrait être à la fois nommée
    par une relation et déclarée n'en venir d'aucune, ce qui est une contradiction.
    """
    reprises_par_relation = {c for cibles in reprises().values() for c in cibles}
    doubles = sorted(reprises_par_relation & set(hors_relation()))
    assert not doubles, (
        "conclusions à la fois reprises par une relation et déclarées sans relation : "
        + ", ".join(doubles)
    )


def test_chaque_conclusion_est_marquee_une_seule_fois_et_les_numeros_se_suivent() -> None:
    """Sans quoi deux paragraphes pourraient porter le même numéro, et la correspondance
    désignerait deux endroits à la fois. La continuité des numéros ferme l'autre moitié : une
    conclusion retirée de la prose sans être retirée du tableau laisserait un trou.
    """
    dans_la_prose = conclusions_de_la_prose()
    doublons = sorted({c for c in dans_la_prose if dans_la_prose.count(c) > 1})
    assert not doublons, "conclusions marquées plusieurs fois : " + ", ".join(doublons)

    numeros = sorted(int(c.split("-")[1]) for c in dans_la_prose)
    attendus = list(range(1, len(numeros) + 1))
    assert numeros == attendus, (
        f"les numéros de conclusion ne se suivent pas : {numeros} au lieu de {attendus}"
    )


def test_toute_declaration_sans_relation_porte_un_motif_non_vide() -> None:
    """Même garde que du côté des non-reprises, et pour la même raison."""
    fautes = [
        f"{conclusion} : motif « {motif} » trop court pour dire d'où la conclusion vient"
        for conclusion, motif in sorted(hors_relation().items())
        if len(motif) < 40
    ]
    assert not fautes, "motifs sans relation insuffisants :\n  " + "\n  ".join(fautes)
