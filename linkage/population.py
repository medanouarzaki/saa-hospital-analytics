"""Extraction de la population de rapprochement depuis marts.dim_patient.

Les paramètres de connexion sont lus dans l'environnement du processus, avec
des valeurs par défaut non secrètes pour le port, la base et l'utilisateur
(les valeurs publiées par le projet en développement local) et pour le mot
de passe (chaîne vide, une valeur légitime pour ce champ). L'hôte n'a
délibérément pas de valeur par défaut : contrairement au port, à la base, à
l'utilisateur ou au mot de passe, aucune valeur ne convient de façon sûre
dans tous les contextes d'exécution (poste local, conteneur, CI) — son
absence est donc une erreur de configuration signalée par son nom, pas une
valeur silencieusement devinée.

La colonne d'identifiant du rapprochement est n_ipp. La bibliothèque splink
attend par défaut une colonne nommée "unique_id"
(`splink.SettingsCreator.__init__`, paramètre
`unique_id_column_name: str = 'unique_id'`) mais ce nom est configurable :
ce module conserve donc le nom n_ipp dans les données extraites, sans le
renommer, et tout usage de splink en aval doit passer
`unique_id_column_name="n_ipp"` à SettingsCreator.
"""

import os

import psycopg

from linkage.champs import CHAMPS_COMPARES, Normalisation
from linkage.normalisation import v1, v2

CLES_AVEC_DEFAUT_NON_SECRET = {
    "POSTGRES_PORT": "5433",
    "POSTGRES_DB": "saa",
    "POSTGRES_USER": "saa",
    "POSTGRES_PASSWORD": "",
}


class ParametreConnexionManquant(ValueError):
    """Levée quand une variable de connexion obligatoire (sans valeur par
    défaut sûre) est absente de l'environnement."""


def parametres_connexion(environ: dict[str, str] | None = None) -> dict[str, str]:
    """Résout les paramètres de connexion depuis l'environnement.

    `environ` permet d'injecter un environnement de test ; par défaut,
    os.environ est utilisé. POSTGRES_HOST n'a pas de valeur par défaut :
    son absence lève ParametreConnexionManquant en nommant la clé. Les
    autres clés ont une valeur par défaut non secrète ; POSTGRES_PASSWORD
    en particulier peut légitimement valoir une chaîne vide, ce qui n'est
    jamais traité comme une absence.
    """
    source = os.environ if environ is None else environ

    if "POSTGRES_HOST" not in source:
        raise ParametreConnexionManquant("variable de connexion manquante : POSTGRES_HOST")
    hote = source["POSTGRES_HOST"]

    parametres = {"POSTGRES_HOST": hote}
    for cle, defaut in CLES_AVEC_DEFAUT_NON_SECRET.items():
        parametres[cle] = source.get(cle, defaut)
    return parametres


def _connexion(environ: dict[str, str] | None = None) -> psycopg.Connection:
    p = parametres_connexion(environ)
    return psycopg.connect(
        host=p["POSTGRES_HOST"],
        port=p["POSTGRES_PORT"],
        dbname=p["POSTGRES_DB"],
        user=p["POSTGRES_USER"],
        password=p["POSTGRES_PASSWORD"],
    )


def _colonnes_select() -> str:
    colonnes = ["n_ipp"]
    for nom_champ in CHAMPS_COMPARES:
        colonnes.append(nom_champ)
    return ", ".join(colonnes)


def extraire_population(environ: dict[str, str] | None = None) -> list[dict]:
    """Retourne la population de rapprochement : une ligne par n_ipp en
    version courante de marts.dim_patient, portant n_ipp, les champs bruts
    du registre et leurs versions normalisées selon la variante déclarée
    (les champs déclarés sans normalisation n'ont pas de colonne normalisée
    additionnelle).
    """
    colonnes = _colonnes_select()
    requete = f"""
        SELECT {colonnes}
        FROM marts.dim_patient
        WHERE est_courante
    """
    with _connexion(environ) as connexion, connexion.cursor() as curseur:
        curseur.execute(requete)
        noms = [d.name for d in curseur.description]
        lignes = curseur.fetchall()

    resultat = []
    for ligne in lignes:
        enregistrement = dict(zip(noms, ligne, strict=True))
        for nom_champ, champ in CHAMPS_COMPARES.items():
            if champ.normalisation is Normalisation.AUCUNE:
                continue
            valeur_brute = enregistrement[nom_champ]
            if champ.normalisation is Normalisation.V1:
                enregistrement[f"{nom_champ}_norm"] = v1(valeur_brute)
            elif champ.normalisation is Normalisation.V2:
                enregistrement[f"{nom_champ}_norm"] = v2(valeur_brute)
        resultat.append(enregistrement)
    return resultat
