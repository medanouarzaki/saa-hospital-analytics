"""Point d'entrée du tableau de bord : configuration et navigation à deux sections.

La navigation est DÉCLARATIVE — les pages sont énumérées ici — et non découverte par convention de
répertoire. Les deux mécanismes existent dans la version installée ; celui-ci est retenu parce
qu'il rend la composition des pages lisible dans un fichier, donc vérifiable par un contrôle plutôt
que par une inspection de répertoire. L'ordre d'affichage est celui de cette liste, et non l'ordre
alphabétique des noms de fichiers.

**Les pages sont groupées en deux sections nommées par leur public**, et non par leur sujet. Le
mécanisme est celui de la bibliothèque, dont la signature accepte les deux formes :
`navigation(pages: 'Sequence[PageType] | Mapping[SectionHeader, Sequence[PageType]]', ...)` ; passer
un dictionnaire fait de chaque clé l'intitulé d'une section. Le partage suit une règle unique, et
la section déclarée par chaque indicateur au registre en découle : un indicateur reste opérationnel
si sa valeur peut changer une décision du service ; il passe en méthode s'il décrit la chaîne — sa
performance, sa provenance, ses paramètres — et non l'activité.

Grouper une page ne déplace pas son adresse : `url_path` est fixé explicitement sur chacune, si bien
qu'un lien noté avant la réorganisation continue de fonctionner.

Les pages déclarées ici et les pages déclarées au registre des indicateurs doivent coïncider, et les
sections aussi : un contrôle le vérifie dans les deux sens.
"""

import streamlit as st

st.set_page_config(
    page_title="Service d'accueil et d'admission",
    layout="wide",
)

# Les deux intitulés nomment le PUBLIC, non le sujet. « Qualité » ou « Technique » désigneraient un
# domaine et laisseraient un responsable de service se demander si la seconde section le concerne ;
# ces deux-là répondent à la question avant qu'elle ne se pose.
SECTION_PILOTAGE = "Pilotage du service"
SECTION_METHODE = "Évaluation de la chaîne"

PAGES = {
    SECTION_PILOTAGE: [
        st.Page("pages/activite.py", title="Activité", url_path="activite", default=True),
        st.Page("pages/rendez_vous.py", title="Rendez-vous", url_path="rendez-vous"),
        st.Page("pages/urgences.py", title="Urgences", url_path="urgences"),
        st.Page("pages/sejours.py", title="Séjours", url_path="sejours"),
        st.Page("pages/facturation.py", title="Facturation", url_path="facturation"),
        st.Page("pages/qualite.py", title="Qualité des données", url_path="qualite"),
        st.Page("pages/donnees.py", title="Données", url_path="donnees"),
    ],
    SECTION_METHODE: [
        st.Page(
            "pages/rapprochement.py", title="Rapprochement d'identités", url_path="rapprochement"
        ),
        st.Page(
            "pages/provenance_et_parametres.py",
            title="Provenance et paramètres",
            url_path="provenance-et-parametres",
        ),
    ],
}

st.navigation(PAGES).run()
