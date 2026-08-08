"""Contrôles bloquants sur le registre des sources (docs/sources/sources.yml).

Deux tests distincts :
  - test_completude_sources vérifie hors ligne la structure du fichier ;
  - test_urls_vivantes vérifie que les URL répondent encore.

Asymétrie volontaire du contrôle HTTP : le test échoue si et seulement si un
code 404 ou 410 est obtenu. Un 404/410 signifie que le document a disparu et
invalide la source. Un 403 ou 429, un délai dépassé, ou une erreur de
connexion signifient qu'un serveur bloque ou throttle un client automatisé,
ce qui ne dit rien sur l'existence du document. Confondre les deux rendrait
ce test rouge sur un registre par ailleurs correct, et il finirait par être
désactivé — ce que ce test existe précisément pour éviter.
"""

import importlib.util
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
SOURCES = RACINE / "docs" / "sources" / "sources.yml"
CONVERTISSEUR = RACINE / "docs" / "sources" / "to_bibtex.py"
BIBLIOGRAPHIE = RACINE / "report" / "biblio.bib"

FIABILITE_AUTORISEES = {"officielle", "academique", "presse", "secondaire"}
VERIFICATION_AUTORISEES = {
    "contenu_lu",
    "accessible_non_extractible",
    "non_verifiable_par_outil",
    "introuvable",
}

CHAMPS_OBLIGATOIRES = [
    "id",
    "titre",
    "auteur",
    "type",
    "url",
    "date_publication",
    "date_consultation",
    "fiabilite",
    "verification",
    "utilise_pour",
]


def charger_sources() -> list[dict]:
    with open(SOURCES, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_completude_sources() -> None:
    sources = charger_sources()

    identifiants = [s.get("id") for s in sources]
    doublons = {i for i in identifiants if identifiants.count(i) > 1}
    assert not doublons, f"Identifiants dupliqués : {sorted(doublons)}"

    identifiants_valides = set(identifiants)

    for source in sources:
        ident = source.get("id", "<sans id>")

        for champ in CHAMPS_OBLIGATOIRES:
            assert champ in source, f"{ident} : champ obligatoire manquant '{champ}'"
            valeur = source[champ]
            assert isinstance(valeur, str) and valeur.strip(), (
                f"{ident} : champ '{champ}' vide"
            )

        assert source["fiabilite"] in FIABILITE_AUTORISEES, (
            f"{ident} : fiabilite '{source['fiabilite']}' hors ensemble autorisé"
        )
        assert source["verification"] in VERIFICATION_AUTORISEES, (
            f"{ident} : verification '{source['verification']}' hors ensemble autorisé"
        )

        if source["url"] == "sans_url":
            assert source["verification"] == "introuvable", (
                f"{ident} : url 'sans_url' n'est admise que si verification vaut "
                f"'introuvable' (ici '{source['verification']}')"
            )

        if source["verification"] == "introuvable":
            note = source.get("note", "")
            assert isinstance(note, str) and note.strip(), (
                f"{ident} : verification 'introuvable' exige une note non vide"
            )

        for champ_reference in ("doublon_de", "remplace_par"):
            if champ_reference in source:
                cible = source[champ_reference]
                assert cible in identifiants_valides, (
                    f"{ident} : {champ_reference}='{cible}' ne désigne aucun "
                    f"identifiant existant"
                )


def code_http(url: str, delai_max: int = 15) -> str:
    """Retourne le code HTTP obtenu en suivant les redirections, sans
    télécharger le corps de la réponse (-o /dev/null), borné en temps
    (-m). Retourne 'TIMEOUT' ou 'ERREUR_CONNEXION' si curl échoue avant
    d'obtenir une réponse."""
    resultat = subprocess.run(
        [
            "curl",
            "-s",
            "-L",
            "-o",
            "/dev/null",
            "-w",
            "%{http_code}",
            "-m",
            str(delai_max),
            url,
        ],
        capture_output=True,
        text=True,
    )
    if resultat.returncode == 28:
        return "TIMEOUT"
    if resultat.returncode != 0:
        return "ERREUR_CONNEXION"
    return resultat.stdout.strip()


def test_urls_vivantes() -> None:
    """Contrôle bidirectionnel.

    La propriété exploitée n'est pas « toutes les URL vivent » — un registre
    contient légitimement des sources mortes, documentées comme telles
    (verification=introuvable). La propriété exploitée est que l'ÉTAT DÉCLARÉ
    par chaque entrée reste vrai : une entrée introuvable doit rester morte,
    une entrée vivante doit rester vivante. Un contrôle à sens unique (qui ne
    vérifierait que l'absence de 404 sur les entrées vivantes) laisserait le
    registre vieillir sans le dire : une source aujourd'hui vivante qui
    disparaît demain resterait marquée verification=contenu_lu indéfiniment,
    car rien ne la ferait rougir. Le sens retour (une entrée introuvable qui
    redeviendrait accessible) est tout aussi réel : le registre doit être mis
    à jour, pas rester silencieusement obsolète dans l'autre sens.

    Asymétrie conservée sur la nature des codes qui comptent comme preuve :
    404 et 410 sont les seuls codes qui distinguent la disparition d'un blocage
    de robot. 403, 429, les délais dépassés et les erreurs de connexion sont
    consignés mais ne tranchent ni dans un sens ni dans l'autre — ils ne disent
    rien sur l'existence du document, seulement qu'un serveur a refusé ou
    throttlé un client automatisé. Les traiter comme une preuve, dans un sens
    ou dans l'autre, rendrait ce test rouge sur un registre correct.

    S-02 est un contrôle positif permanent : c'est une URL réellement morte
    (verification=introuvable), présente à demeure dans le jeu de données réel
    — pas une mutation temporaire — qui vérifie à chaque exécution que ce test
    mesure effectivement quelque chose plutôt que d'être vert par vacuité.
    """
    sources = charger_sources()
    a_controler = [s for s in sources if s.get("url") and s["url"] != "sans_url"]
    ignorees_sans_url = [s for s in sources if s.get("url") == "sans_url"]

    NI_PREUVE_NI_CONTRE_PREUVE = {"403", "429", "TIMEOUT", "ERREUR_CONNEXION"}

    echecs = []
    for source in a_controler:
        code = code_http(source["url"])
        morte_attendue = source["verification"] == "introuvable"
        attendu = "mort" if morte_attendue else "vivant"
        print(f"{source['id']} : {code} : attendu={attendu} : {source['url']}")

        if code in NI_PREUVE_NI_CONTRE_PREUVE:
            continue

        est_morte = code in ("404", "410")
        if morte_attendue and not est_morte:
            echecs.append(
                f"{source['id']} : déclarée morte (introuvable) mais répond {code}"
            )
        elif not morte_attendue and est_morte:
            echecs.append(
                f"{source['id']} : déclarée vivante mais répond {code}"
            )

    print(f"URL interrogées : {len(a_controler)} sur {len(sources)} entrées")
    print(f"entrées ignorées (url=sans_url) : {len(ignorees_sans_url)}")

    assert not echecs, "État déclaré non conforme à l'état mesuré : " + " | ".join(echecs)


def test_biblio_synchronisee() -> None:
    """report/biblio.bib est un fichier produit et committé : rien ne garantit
    qu'il reste synchrone avec sources.yml après une modification manuelle de
    l'un sans régénération de l'autre. Ce test régénère la bibliographie dans
    un répertoire temporaire hors du dépôt (jamais dans report/), et compare
    octet à octet au fichier committé. Il ne réécrit jamais report/biblio.bib :
    un test qui corrige ce qu'il contrôle ne contrôle rien.
    """
    spec = importlib.util.spec_from_file_location("to_bibtex", CONVERTISSEUR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    with tempfile.TemporaryDirectory() as tmp:
        destination_temporaire = Path(tmp) / "biblio_regenere.bib"
        module.SOURCE = SOURCES
        module.DESTINATION = destination_temporaire
        module.main()
        contenu_regenere = destination_temporaire.read_bytes()

    contenu_committe = BIBLIOGRAPHIE.read_bytes()

    assert contenu_regenere == contenu_committe, (
        "report/biblio.bib n'est plus synchrone avec docs/sources/sources.yml : "
        "régénérer avec `uv run python3 docs/sources/to_bibtex.py`"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v", "-s"]))
