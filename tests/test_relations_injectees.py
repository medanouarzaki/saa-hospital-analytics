"""Contrôles bloquants sur la correspondance entre `docs/relations_injectees.yml` (le
registre des relations injectées) et la configuration du générateur.

Ne recopie aucun nom de paramètre ni aucun décompte : lit le registre et la configuration à
chaque exécution, pour qu'une relation ajoutée ou renommée sans paramètre correspondant
fasse rougir ce fichier plutôt que de passer inaperçue.
"""

import re
from collections import Counter
from pathlib import Path

import yaml

from generator import config

RACINE = Path(__file__).resolve().parent.parent
CHEMIN_REGISTRE = RACINE / "docs" / "relations_injectees.yml"
CHEMIN_INDICATEURS = RACINE / "dashboard" / "indicateurs.yml"

# La valeur que porte `page_tableau_de_bord` quand AUCUNE page n'affiche la relation. Une relation
# injectée sans être affichée est légitime — le générateur la produit, le tableau de bord ne la
# montre pas — mais elle doit le DÉCLARER, faute de quoi le registre affirme une visibilité qu'il
# n'a pas. C'est exactement ce qui a laissé trois entrées pointer vers une page supprimée.
AUCUNE_PAGE = "aucune"


def _charger_registre() -> list[dict]:
    with CHEMIN_REGISTRE.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _pages_du_tableau_de_bord() -> set[str]:
    """Les pages déclarées, DÉRIVÉES du registre des indicateurs et jamais recopiées ici.

    Deux sources possibles existaient : la liste `pages` de l'en-tête du registre des indicateurs,
    et les pages effectivement portées par ses entrées. La seconde est retenue — une page déclarée
    à l'en-tête mais sans aucun indicateur n'afficherait rien — et les deux sont confrontées, de
    sorte qu'une divergence entre elles fasse rougir ici plutôt que de passer pour une page valide.
    """
    with CHEMIN_INDICATEURS.open(encoding="utf-8") as f:
        registre = yaml.safe_load(f)
    declarees = set(registre["pages"])
    portees = {entree["page"] for entree in registre["indicateurs"]}
    assert declarees == portees, (
        "les pages déclarées à l'en-tête du registre des indicateurs et celles portées par ses "
        f"entrées divergent : {sorted(declarees ^ portees)}"
    )
    return portees


def _noms_par_relation(relations: list[dict]) -> dict[str, list[str]]:
    return {r["id"]: [n.strip() for n in r["parametre"].split(",")] for r in relations}


def test_chaque_nom_de_parametre_existe_dans_la_configuration() -> None:
    relations = _charger_registre()
    noms_par_relation = _noms_par_relation(relations)
    entrees = {e["nom"] for e in config.charger_entrees()}

    manquants = []
    for id_relation, noms in noms_par_relation.items():
        for nom in noms:
            if nom not in entrees:
                manquants.append((id_relation, nom))
    assert not manquants, manquants


def test_decompte_relations_et_noms_distincts() -> None:
    relations = _charger_registre()
    assert len(relations) == 21

    noms_par_relation = _noms_par_relation(relations)

    # deux calculs independants du nombre de noms distincts, sur les memes donnees source :
    # un aplatissement par comprehension de liste puis un ensemble, et un comptage par
    # Counter dont on prend le nombre de cles -- une divergence entre les deux signalerait
    # une erreur de decoupage plutot qu'une simple faute de frappe dans un seul calcul.
    tous_les_noms = [nom for noms in noms_par_relation.values() for nom in noms]
    n_distincts_ensemble = len(set(tous_les_noms))
    n_distincts_compteur = len(Counter(tous_les_noms))
    assert n_distincts_ensemble == n_distincts_compteur
    assert n_distincts_ensemble > 0


def test_aucune_relation_orpheline() -> None:
    relations = _charger_registre()
    for relation in relations:
        noms = [n.strip() for n in relation["parametre"].split(",")]
        assert all(noms), relation
        assert len(noms) >= 1, relation


def test_chaque_relation_nomme_une_page_existante_ou_declare_n_en_avoir_aucune() -> None:
    """La page de destination d'une relation existe, ou l'entrée déclare qu'aucune ne l'affiche.

    Le registre annonce, pour chaque relation injectée, où le lecteur la retrouvera. Rien ne
    vérifiait cette annonce : trois entrées ont renvoyé pendant tout un bloc à une page que la
    composition du tableau de bord ne comporte pas. Une relation peut légitimement n'être affichée
    nulle part ; ce qui ne se peut pas, c'est qu'elle annonce une page qui n'existe pas.
    """
    pages = _pages_du_tableau_de_bord()
    fautives = []
    for relation in _charger_registre():
        page = relation.get("page_tableau_de_bord")
        if page is None:
            fautives.append(f"{relation['id']} : clé 'page_tableau_de_bord' absente")
        elif page != AUCUNE_PAGE and page not in pages:
            fautives.append(
                f"{relation['id']} : page '{page}' inconnue du tableau de bord "
                f"(pages existantes : {sorted(pages)})"
            )
    assert not fautives, "pages de destination invalides : " + " | ".join(fautives)


def test_une_relation_sans_page_le_dit_dans_sa_prose() -> None:
    """Une entrée qui déclare n'être affichée nulle part l'écrit aussi en toutes lettres.

    Le champ contrôlé par la propriété précédente est une valeur ; la prose qui l'accompagne est ce
    qu'un relecteur lit. Les deux doivent dire la même chose, faute de quoi le registre resterait
    trompeur à la lecture tout en étant vert au contrôle.

    Le motif est éprouvé contre un cas positif construit avant que son silence ne soit cru.
    """
    motif = re.compile(r"aucune page", re.IGNORECASE)
    assert motif.search("Aucune page du tableau de bord."), (
        "le motif ne reconnaît pas un cas positif"
    )
    assert not motif.search("Tableau de bord, page Urgences."), "le motif reconnaît un cas négatif"

    fautives = [
        relation["id"]
        for relation in _charger_registre()
        if relation.get("page_tableau_de_bord") == AUCUNE_PAGE
        and not motif.search(str(relation.get("ou_apparait", "")))
    ]
    assert not fautives, (
        "relations déclarées sans page mais dont la prose ne le dit pas : " + ", ".join(fautives)
    )


def test_tout_indicateur_cite_existe_et_siege_sur_la_page_declaree() -> None:
    """Quand une entrée nomme un indicateur, celui-ci existe et siège sur la page déclarée.

    Cette propriété attrape la faute SYMÉTRIQUE de la précédente : une relation qui se déclare
    affichée nulle part alors qu'elle nomme un indicateur bien vivant, ou qui nomme un indicateur
    d'une autre page que celle qu'elle annonce.

    Sa portée est limitée et le dire vaut mieux que le laisser croire : elle ne peut rien pour une
    entrée dont la prose ne nomme aucun indicateur. Une relation affichée sous un intitulé qu'elle
    ne cite pas resterait donc déclarable « aucune page » sans que rien ne rougisse. Relier
    systématiquement un paramètre du générateur à l'indicateur qui le donne à voir demanderait un
    chaînage que le registre ne porte pas aujourd'hui.
    """
    with CHEMIN_INDICATEURS.open(encoding="utf-8") as f:
        registre_indicateurs = yaml.safe_load(f)
    page_par_indicateur = {
        entree["identifiant"]: entree["page"] for entree in registre_indicateurs["indicateurs"]
    }

    # Le motif est éprouvé contre un cas positif construit avant que son silence ne soit cru.
    motif = re.compile(r"\b([a-z]+(?:_[a-z]+)+)\b")
    temoin = "indicateur rendez_vous_delai_et_absence_intra_activite. Chapitre 7."
    assert motif.findall(temoin), "le motif ne reconnaît pas un identifiant pourtant présent"

    fautives = []
    for relation in _charger_registre():
        prose = str(relation.get("ou_apparait", ""))
        cites = [nom for nom in motif.findall(prose) if nom in page_par_indicateur]
        for nom in cites:
            page_declaree = relation.get("page_tableau_de_bord")
            if page_declaree == AUCUNE_PAGE:
                fautives.append(
                    f"{relation['id']} : se déclare affichée nulle part mais nomme "
                    f"l'indicateur '{nom}', qui existe page '{page_par_indicateur[nom]}'"
                )
            elif page_par_indicateur[nom] != page_declaree:
                fautives.append(
                    f"{relation['id']} : nomme l'indicateur '{nom}' de la page "
                    f"'{page_par_indicateur[nom]}' mais déclare la page '{page_declaree}'"
                )
    assert not fautives, "indicateurs cités incohérents : " + " | ".join(fautives)
