"""Contrôle de l'échantillon de données versé au dépôt.

POURQUOI CE FICHIER EXISTE.

Ce répertoire est le seul du dépôt à porter des lignes de données. Le projet repose sur une décision
de cadrage — aucune donnée réelle ne sort du service — et verser des lignes dans un dépôt public,
même synthétiques, exige que rien ne puisse être pris pour du réel. La protection tient à une
mention portée par chaque ligne de chaque fichier ; ce fichier vérifie qu'elle y est, partout, et
que l'échantillon n'a pas divergé de ce dont il est extrait.

CE QU'IL VÉRIFIE, une fonction par propriété :

  1. chaque ligne de l'échantillon existe dans la table dont elle est extraite, et les colonnes sont
     celles de la table — une égalité entre deux mesures ;
  2. chaque fichier porte sa mention sur chacune de ses lignes, et aucun fichier n'en est dépourvu ;
  3. réengendrer l'échantillon rend le même contenu ;
  4. la paire de fiches en double est présente, les deux, et leurs différences sont visibles ;
  5. le volume est conforme à ce que le module déclare, sans littéral.

CE QU'IL NE VÉRIFIE PAS : que les données soient synthétiques. Cela ne se vérifie pas depuis un
fichier ; cela se garantit par la chaîne qui les produit, et se déclare au lecteur — ce que la
mention fait.

Aucun travail au niveau du module : ni connexion, ni lecture de variable d'environnement, ni
chargement de fichier à l'import.

Aucun littéral de volumétrie : les décomptes attendus sont lus dans la configuration du module
d'engendrement, jamais recopiés ici.
"""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path

import psycopg
import pytest

RACINE = Path(__file__).resolve().parent.parent


def _module():
    """Le module d'engendrement, importé à l'appel et jamais à l'import."""
    import sys  # noqa: PLC0415

    if str(RACINE) not in sys.path:
        sys.path.insert(0, str(RACINE))
    from extraction import echantillon  # noqa: PLC0415

    return echantillon


def _fichiers_suivis() -> list[str]:
    """Les fichiers de l'échantillon RÉELLEMENT SUIVIS, et non le contenu du répertoire.

    Même mécanisme que le contrôle qui interdit les images : une règle d'exclusion qui rendrait ces
    fichiers invisibles à la publication serait un défaut, et partir du répertoire ne l'attraperait
    pas.
    """
    sortie = subprocess.run(
        ["git", "-C", str(RACINE), "ls-files", "-z", "echantillon"],
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    return sorted(chemin for chemin in sortie.split("\0") if chemin.endswith(".csv"))


def _lire(chemin: Path) -> tuple[list[str], list[dict]]:
    with chemin.open(encoding="utf-8-sig", newline="") as fichier:
        lecteur = csv.DictReader(fichier)
        lignes = list(lecteur)
        return list(lecteur.fieldnames or []), lignes


def _connexion(schema: str):
    module = _module()
    try:
        return module._connexion(schema)
    except psycopg.OperationalError as exc:
        pytest.fail(
            f"connexion impossible à la base ({exc}) : l'échantillon se vérifie contre les tables "
            "dont il est extrait, qui doivent être chargées"
        )


def _fenetre_complete_ou_abstention() -> None:
    """GARDE D'APPLICABILITÉ des deux propriétés qui interrogent la base.

    L'échantillon versé est extrait du jeu COMPLET. Les deux tâches d'intégration qui portent une
    base chargent, elles, une fenêtre réduite à trois mois : mesuré, 20 248 des fiches patient de la
    base complète sont postérieures à cette fenêtre, si bien que les clés versées n'y existeraient
    pas et que la propriété rougirait sur une donnée juste. Le test s'abstient donc, avec un motif
    explicite, lorsque la date de prise maximale ne coïncide pas avec la date de fin de période lue
    dans la configuration — même mécanisme que la garde des indicateurs de séjour, une égalité
    mesurée en base et en configuration, jamais une marge arbitraire.

    Les trois autres propriétés — la mention, la paire en double, le volume — n'interrogent aucune
    base et s'exécutent partout. **C'est la mention qui protège la publication, et elle n'est jamais
    dispensée.**
    """
    from datetime import date  # noqa: PLC0415

    from generator import config  # noqa: PLC0415

    conn = _connexion("instantane")
    try:
        with conn.cursor() as curseur:
            curseur.execute("select max(date_prise) from fct_rendez_vous")
            (jour_max,) = curseur.fetchone()
    finally:
        conn.close()

    date_fin = date.fromisoformat(config.valeur("date_fin"))
    if jour_max != date_fin:
        pytest.skip(
            f"fenêtre chargée partielle : date de prise maximale ({jour_max}) != date de fin de "
            f"période configurée ({date_fin}) — l'échantillon versé est extrait du jeu complet, et "
            "ses clés n'existent pas dans une fenêtre réduite"
        )


def test_chaque_ligne_de_l_echantillon_existe_dans_sa_table() -> None:
    """Égalité entre deux mesures : les clés de l'échantillon et celles de la table.

    La vérification porte sur la CLÉ de chaque ligne, relue en base : une ligne recopiée à la main,
    ou conservée après suppression en base, n'y serait pas retrouvée. Les colonnes sont comparées de
    la même façon — celles du fichier, moins la colonne de mention, contre celles du catalogue.
    """
    module = _module()
    _fenetre_complete_ou_abstention()
    suivis = _fichiers_suivis()
    assert suivis, "aucun fichier d'échantillon n'est suivi par le dépôt"

    fautifs: list[str] = []
    for schema in ("source", "instantane"):
        tables = module.TABLES_SOURCE if schema == "source" else module.TABLES_ANALYTIQUES
        conn = _connexion(schema)
        try:
            with conn.cursor() as curseur:
                for table, ordre in tables.items():
                    chemin = RACINE / "echantillon" / f"{table}.csv"
                    if chemin.as_posix().replace(f"{RACINE.as_posix()}/", "") not in suivis:
                        fautifs.append(f"{table} : fichier non suivi")
                        continue
                    colonnes_fichier, lignes = _lire(chemin)
                    assert lignes, f"{table} : le fichier ne porte aucune ligne"

                    curseur.execute(
                        "select column_name from information_schema.columns "
                        "where table_schema = current_schema() and table_name = %s "
                        "order by ordinal_position",
                        (table,),
                    )
                    colonnes_table = [nom for (nom,) in curseur.fetchall()]
                    attendues = [module.COLONNE_MENTION] + colonnes_table
                    if colonnes_fichier != attendues:
                        fautifs.append(
                            f"{table} : colonnes du fichier différentes de celles de la table — "
                            f"{len(colonnes_fichier)} contre {len(attendues)}"
                        )
                        continue

                    cle = ordre.split(",")[0].strip()
                    valeurs = [ligne[cle] for ligne in lignes]
                    curseur.execute(
                        f"select {cle}::text from {table} where {cle}::text = any(%s)", (valeurs,)
                    )
                    presentes = {valeur for (valeur,) in curseur.fetchall()}
                    absentes = sorted(set(valeurs) - presentes)
                    if absentes:
                        fautifs.append(
                            f"{table} : {len(absentes)} clé(s) de l'échantillon absente(s) de la "
                            f"table — {', '.join(absentes[:4])}"
                        )
        finally:
            conn.close()

    assert not fautifs, "l'échantillon a divergé des tables : " + " | ".join(fautifs)


def test_chaque_fichier_porte_sa_mention_sur_chaque_ligne() -> None:
    """Dans les deux sens : aucun fichier sans mention, aucune ligne sans mention.

    C'est la propriété qui protège la publication. Elle porte sur les fichiers SUIVIS : un fichier
    présent sur le disque mais non suivi ne serait pas publié, et un fichier suivi sans mention le
    serait.
    """
    module = _module()
    suivis = _fichiers_suivis()
    assert suivis, "aucun fichier d'échantillon n'est suivi par le dépôt"

    sans_colonne: list[str] = []
    sans_mention: list[str] = []
    for chemin_relatif in suivis:
        chemin = RACINE / chemin_relatif
        colonnes, lignes = _lire(chemin)
        if not colonnes or colonnes[0] != module.COLONNE_MENTION:
            sans_colonne.append(f"{chemin_relatif} : première colonne {colonnes[:1]}")
            continue
        fautives = [
            numero
            for numero, ligne in enumerate(lignes, start=2)
            if ligne.get(module.COLONNE_MENTION) != module.MENTION
        ]
        if fautives:
            sans_mention.append(
                f"{chemin_relatif} : {len(fautives)} ligne(s) sans la mention, dont la ligne "
                f"{fautives[0]}"
            )

    assert not sans_colonne, "fichiers sans colonne de mention : " + " | ".join(sans_colonne)
    assert not sans_mention, "lignes sans mention : " + " | ".join(sans_mention)

    assert module.MENTION.strip(), "la mention est vide"
    for mot in ("synth", "aucun patient"):
        assert mot.lower() in module.MENTION.lower(), (
            f"la mention ne dit pas l'essentiel : « {mot} » absent de « {module.MENTION} »"
        )


def test_reengendrer_l_echantillon_rend_le_meme_contenu(tmp_path: Path) -> None:
    """Reproductibilité, comparée sur le CONTENU et non sur les octets.

    POURQUOI PAS LES OCTETS. Le fichier écrit dépend du format de rendu textuel des valeurs par le
    pilote de base — un horodatage, un décimal ou une valeur absente peuvent se rendre autrement
    d'une version à l'autre sans que la ligne extraite change. Comparer les octets ferait rougir ce
    contrôle sur une montée de version qui n'aurait rien changé à l'échantillon. La comparaison
    porte donc sur les lignes lues, champ par champ, ce qui est la propriété visée : le même extrait
    des mêmes tables.
    """
    module = _module()
    _fenetre_complete_ou_abstention()

    module.produire(tmp_path)
    produits = sorted(chemin.name for chemin in tmp_path.glob("*.csv"))
    verses = sorted(Path(chemin).name for chemin in _fichiers_suivis())
    assert produits == verses, (
        f"le réengendrement produit {len(produits)} fichiers, le dépôt en porte {len(verses)}"
    )

    ecarts: list[str] = []
    for nom in produits:
        colonnes_neuves, lignes_neuves = _lire(tmp_path / nom)
        colonnes_versees, lignes_versees = _lire(RACINE / "echantillon" / nom)
        if colonnes_neuves != colonnes_versees:
            ecarts.append(f"{nom} : colonnes différentes")
        elif lignes_neuves != lignes_versees:
            differentes = sum(
                1 for a, b in zip(lignes_neuves, lignes_versees, strict=False) if a != b
            )
            ecarts.append(
                f"{nom} : {len(lignes_neuves)} lignes réengendrées contre {len(lignes_versees)} "
                f"versées, {differentes} différentes"
            )

    assert not ecarts, "le réengendrement ne rend pas le même contenu : " + " | ".join(ecarts)


def test_la_paire_de_fiches_en_double_est_presente_et_ses_differences_visibles() -> None:
    """Les deux fiches, et au moins une colonne qui les distingue.

    Sans les deux, l'échantillon ne montrerait pas ce que le rapprochement a à rapprocher ; sans
    différence visible, il montrerait deux lignes identiques, ce qui n'apprendrait rien non plus.
    """
    module = _module()
    _colonnes, lignes = _lire(RACINE / "echantillon" / "patients.csv")
    par_ipp = {ligne["n_ipp"]: ligne for ligne in lignes}

    assert len(module.PAIRE_DOUBLON) == 2, (
        f"la paire déclarée par le module n'en est pas une : {module.PAIRE_DOUBLON}"
    )
    manquantes = [ipp for ipp in module.PAIRE_DOUBLON if ipp not in par_ipp]
    assert not manquantes, (
        f"fiches de la paire en double absentes de l'échantillon : {manquantes} — "
        "l'échantillon ne montre plus ce que le rapprochement a à rapprocher"
    )

    gauche, droite = (par_ipp[ipp] for ipp in module.PAIRE_DOUBLON)
    differentes = sorted(
        nom
        for nom in gauche
        if nom not in (module.COLONNE_MENTION, "n_ipp") and gauche[nom] != droite[nom]
    )
    assert differentes, (
        "les deux fiches de la paire sont identiques colonne pour colonne : leurs différences ne "
        "sont pas visibles"
    )
    communes = sorted(
        nom
        for nom in gauche
        if nom not in (module.COLONNE_MENTION, "n_ipp") and gauche[nom] == droite[nom]
    )
    assert communes, (
        "les deux fiches ne partagent aucune valeur : rien ne suggère qu'elles désignent la même "
        "personne"
    )


def test_le_volume_verse_est_celui_que_le_module_declare() -> None:
    """Le décompte attendu se dérive de la configuration du module, jamais d'un littéral."""
    module = _module()
    suivis = _fichiers_suivis()
    attendues = set(module.TABLES_SOURCE) | set(module.TABLES_ANALYTIQUES)

    presentes = {Path(chemin).stem for chemin in suivis}
    manquantes = sorted(attendues - presentes)
    en_trop = sorted(presentes - attendues)
    assert not manquantes, f"tables déclarées par le module et non versées : {manquantes}"
    assert not en_trop, f"fichiers versés et non déclarés par le module : {en_trop}"

    fautifs: list[str] = []
    for chemin_relatif in suivis:
        table = Path(chemin_relatif).stem
        plafond = (
            module.LIGNES_SOURCE if table in module.TABLES_SOURCE else module.LIGNES_ANALYTIQUE
        )
        if table == "patients":
            plafond += len(module.PAIRE_DOUBLON)
        _colonnes, lignes = _lire(RACINE / chemin_relatif)
        if len(lignes) > plafond:
            fautifs.append(f"{table} : {len(lignes)} lignes versées pour un plafond de {plafond}")
        if not lignes:
            fautifs.append(f"{table} : aucune ligne versée")

    assert not fautifs, "volume non conforme à ce que le module déclare : " + " | ".join(fautifs)
