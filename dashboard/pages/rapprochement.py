"""Page de rapprochement : les cinq indicateurs que le registre déclare pour elle.

**Aucun de ses indicateurs ne répond au filtre de période**, et la page n'en porte donc pas : elle
affiche le motif que le registre donne. Aucun n'est recalculé depuis les tables de faits, et chacun
l'affiche.

Le seuil de décision n'est jamais écrit ici : il est **lu dans les données**, dans la colonne que
les grappes portent à cet effet. Un seuil écrit dans la page pourrait diverger de celui qui a
réellement servi à former les grappes affichées à côté.

L'apport du rapprochement **compare deux méthodes l'une à l'autre**, et non une méthode à une
vérité : les paires que le rapprochement probabiliste regroupe, contre celles que la collision
exacte réunit. Les deux ensembles se dérivent de l'instantané seul. C'est ce que la décision servie
demande — faut-il lancer une campagne de fusion, et sur quelle règle — et cela tiendrait à
l'identique dans un établissement où aucune correspondance n'est connue d'avance.

Les grandeurs de précision et de rappel, elles, viennent d'une évaluation menée en amont ; l'écran
les présente comme telles, sans reconstruire ce sur quoi elles ont été établies.
"""

from __future__ import annotations

import streamlit as st

from dashboard import lecture, rendu

PAGE = "rapprochement"

CRITERES_LISIBLES = {
    "nom_date_naissance": "Nom et date de naissance identiques",
    "piece_identite": "Pièce d'identité identique",
}

REQUETES = {
    "rapprochement_collisions_exactes": """
        select critere,
               patients_examines,
               nombre_groupes,
               patients_concernes,
               taille_plus_grand_groupe,
               taille_mediane_groupes
        from agg_doublons_identite
        order by critere
    """,
    # La distribution des tailles est plus informative que le seul nombre de grappes : elle dit si
    # le rapprochement fusionne par paires ou forme de grandes grappes, ce que le total masque.
    # Le décompte porte sur les GRAPPES, non sur les lignes : la table porte une ligne par
    # enregistrement rapproché, si bien que compter les lignes multiplierait chaque grappe par sa
    # taille. La distinction se voit à la confrontation et non à la lecture.
    "rapprochement_grappes": """
        select taille_grappe,
               count(distinct grappe_id) as grappes,
               count(*) as enregistrements
        from grappes_identite
        group by taille_grappe
        order by taille_grappe
    """,
    "rapprochement_courbe": """
        select seuil, precision_valeur, rappel, f_mesure
        from evaluation
        order by seuil
    """,
    # Le seuil vient des données : c'est celui que portent les grappes elles-mêmes.
    "rapprochement_seuil": """
        select (select distinct seuil from grappes_identite) as seuil_applique,
               e.precision_valeur, e.rappel, e.f_mesure
        from evaluation e
        where e.seuil = (select distinct seuil from grappes_identite)
    """,
    # L'apport croise DEUX MÉTHODES : les paires que les grappes réunissent, et celles que
    # chacun des deux critères de collision exacte réunit sur les patients de version courante.
    # Les critères sont ceux du modèle qui produit l'agrégat des doublons, lus et non supposés.
    # Une jointure externe complète donne les trois effectifs en une passe ; aucune sous-requête
    # corrélée n'y figure.
    "rapprochement_apport": """
        with courants as (
            select n_ipp, nom, nom_famille_1, date_naissance,
                   type_piece_identite, n_piece_identite
            from dim_patient where est_courante
        ),
        probabiliste as (
            select a.n_ipp as gauche, b.n_ipp as droite
            from grappes_identite a
            join grappes_identite b
              on a.grappe_id = b.grappe_id and a.n_ipp < b.n_ipp
        ),
        collision as (
            select a.n_ipp as gauche, b.n_ipp as droite
            from courants a
            join courants b on a.n_ipp < b.n_ipp
               and a.nom = b.nom and a.nom_famille_1 = b.nom_famille_1
               and a.date_naissance = b.date_naissance
            where a.nom <> '' and a.nom_famille_1 <> '' and a.date_naissance is not null
            union
            select a.n_ipp, b.n_ipp
            from courants a
            join courants b on a.n_ipp < b.n_ipp
               and a.type_piece_identite = b.type_piece_identite
               and a.n_piece_identite = b.n_piece_identite
            where a.type_piece_identite <> '' and a.n_piece_identite <> ''
        )
        select
            count(*) filter (where p.gauche is not null and c.gauche is not null)
                as paires_communes,
            count(*) filter (where p.gauche is not null and c.gauche is null)
                as regroupees_par_le_probabiliste_seul,
            count(*) filter (where p.gauche is null and c.gauche is not null)
                as reunies_par_la_collision_seule,
            count(*) as paires_distinctes
        from probabiliste p
        full outer join collision c on p.gauche = c.gauche and p.droite = c.droite
    """,
}


def _pourcentage(valeur) -> str:
    return f"{100 * float(valeur):.2f} %".replace(".", ",")


def rendre() -> None:
    rendu.en_tete("Rapprochement d'identités")
    rendu.filtre_de_page(PAGE)

    rendu.titre_indicateur("rapprochement_seuil")
    seuil = lecture.interroger(REQUETES["rapprochement_seuil"]).iloc[0]
    colonnes = st.columns(4)
    with colonnes[0]:
        st.metric("Seuil appliqué", f"{float(seuil['seuil_applique']):.2f}".replace(".", ","))
    with colonnes[1]:
        st.metric("Précision", _pourcentage(seuil["precision_valeur"]))
    with colonnes[2]:
        st.metric("Rappel", _pourcentage(seuil["rappel"]))
    with colonnes[3]:
        st.metric("F-mesure", f"{float(seuil['f_mesure']):.4f}".replace(".", ","))
    st.caption(
        "Le seuil affiché est celui que portent les grappes elles-mêmes, lu dans les données et "
        "non écrit dans la page. Précision, rappel et F-mesure proviennent de l'évaluation du "
        "modèle de rapprochement, menée en amont lors de son calage ; ce sont des grandeurs de "
        "réglage du modèle, non des mesures de l'activité."
    )

    rendu.titre_indicateur("rapprochement_apport")
    apport = lecture.interroger(REQUETES["rapprochement_apport"]).iloc[0]
    communes = int(apport["paires_communes"])
    probabiliste_seul = int(apport["regroupees_par_le_probabiliste_seul"])
    collision_seule = int(apport["reunies_par_la_collision_seule"])
    st.caption(
        "Les deux méthodes sont comparées l'une à l'autre, et non à un appariement connu d'avance. "
        "Une paire est comptée dès que deux dossiers de patients y sont réunis par l'une ou "
        "l'autre : par une grappe pour le rapprochement probabiliste, par l'égalité exacte du nom "
        "et de la date de naissance ou du numéro de pièce d'identité pour la collision."
    )
    colonnes = st.columns(3)
    with colonnes[0]:
        st.metric("Réunies par les deux", f"{communes}")
    with colonnes[1]:
        st.metric("Par le rapprochement seul", f"{probabiliste_seul}")
    with colonnes[2]:
        st.metric("Par la collision seule", f"{collision_seule}")
    st.caption(
        f"{probabiliste_seul} paires que la collision exacte ne réunit pas, et {collision_seule} "
        f"que le rapprochement ne regroupe pas : les deux méthodes ne se recouvrent pas, et "
        f"{communes} paires sur {communes + probabiliste_seul + collision_seule} sont trouvées "
        "par les deux. Ce que l'une trouve seule mesure ce qu'abandonnerait celui qui y "
        "renoncerait."
    )

    rendu.titre_indicateur("rapprochement_courbe")
    courbe = lecture.interroger(REQUETES["rapprochement_courbe"])
    seuil_applique = float(seuil["seuil_applique"])
    seuil_lisible = f"{seuil_applique:.2f}".replace(".", ",")

    # Précision contre rappel, et non les trois grandeurs contre le seuil. Portée en abscisse, la
    # valeur du seuil écrase le tracé : le balayage est logarithmique aux deux extrémités, si bien
    # que la plupart des points se pressent contre les bords du cadre et que le segment central,
    # à une précision et un rappel de 1, se confond avec la bordure supérieure.
    plan = rendu.en_nombres(courbe, "precision_valeur", "rappel").assign(
        repere=lambda t: [
            f"Seuil retenu ({seuil_lisible})"
            if valeur == seuil_applique
            else "Autres seuils balayés"
            for valeur in t["seuil"]
        ]
    )
    # Le point du seuil retenu est tracé en dernier pour n'être caché par aucun autre : les
    # marques sont dessinées dans l'ordre des lignes, et il partage sa position avec beaucoup.
    plan = plan.sort_values("repere", ascending=False, kind="stable")

    positions_distinctes = len(
        plan.groupby([plan["rappel"].round(6), plan["precision_valeur"].round(6)])
    )
    parfaits = int(((plan["rappel"] == 1.0) & (plan["precision_valeur"] == 1.0)).sum())

    st.scatter_chart(
        plan,
        x="rappel",
        y="precision_valeur",
        color="repere",
        x_label="Rappel",
        y_label="Précision",
    )
    st.caption(
        f"Un point par seuil balayé, {len(courbe)} au total, dont {parfaits} atteignent à la fois "
        f"une précision et un rappel de 1 et se superposent donc au coin supérieur droit — "
        f"{positions_distinctes} positions distinctes seulement. **C'est un résultat et non un "
        "défaut d'affichage** : le modèle sépare les deux populations si nettement que déplacer le "
        f"seuil ne change rien au résultat sur presque tout son domaine. Le seuil retenu, "
        f"{seuil_lisible}, est repéré par sa couleur et nommé en légende."
    )
    st.caption(
        "Le tableau ci-dessous ne porte **qu'une seule ligne**, celle du seuil retenu : les "
        f"{len(courbe)} seuils balayés sont dans le graphique, pas dans ce tableau."
    )
    st.dataframe(
        courbe[courbe["seuil"] == seuil["seuil_applique"]],
        hide_index=True,
        height="content",
    )

    rendu.titre_indicateur("rapprochement_grappes")
    grappes = lecture.interroger(REQUETES["rapprochement_grappes"])
    gauche, droite = st.columns(2)
    with gauche:
        st.metric("Grappes formées", f"{int(grappes['grappes'].sum())}")
    with droite:
        st.metric("Enregistrements rapprochés", f"{int(grappes['enregistrements'].sum())}")
    st.caption(
        "La distribution des tailles dit ce que le total masque : un rapprochement qui fusionne "
        "par paires et un rapprochement qui forme de grandes grappes donnent le même nombre "
        "d'enregistrements et n'ont pas le même effet."
    )
    st.dataframe(grappes, hide_index=True)

    rendu.titre_indicateur("rapprochement_collisions_exactes")
    collisions = lecture.interroger(REQUETES["rapprochement_collisions_exactes"])
    collisions = collisions.assign(
        critere=collisions["critere"].map(lambda code: CRITERES_LISIBLES.get(code, code))
    )
    # `height="content"` et non la valeur par défaut : la documentation de la version installée dit
    # que `"auto"` dimensionne le cadre pour « au plus dix lignes », d'après une hauteur de ligne
    # nominale. Les libellés de critère et les en-têtes de colonne de ce tableau se replient sur
    # deux lignes, si bien que ses deux lignes réelles dépassent ce cadre et que la seconde
    # n'apparaît qu'après défilement. `"content"` fait épouser au cadre la hauteur de son contenu.
    st.dataframe(collisions, hide_index=True, height="content")


rendre()
