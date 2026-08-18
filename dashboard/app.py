"""Point d'entrée du tableau de bord : configuration et navigation.

La navigation est DÉCLARATIVE — les pages sont énumérées ici — et non découverte par convention de
répertoire. Les deux mécanismes existent dans la version installée ; celui-ci est retenu parce
qu'il rend la composition des pages lisible dans un fichier, donc vérifiable par un contrôle plutôt
que par une inspection de répertoire. L'ordre d'affichage est celui de cette liste, et non l'ordre
alphabétique des noms de fichiers.

Les pages déclarées ici et les pages déclarées au registre des indicateurs doivent coïncider : un
contrôle le vérifie dans les deux sens.
"""

import streamlit as st

st.set_page_config(
    page_title="Service d'accueil et d'admission",
    layout="wide",
)

PAGES = [
    st.Page("pages/activite.py", title="Activité", url_path="activite", default=True),
    st.Page("pages/rendez_vous.py", title="Rendez-vous", url_path="rendez-vous"),
    st.Page("pages/urgences.py", title="Urgences", url_path="urgences"),
    st.Page("pages/sejours.py", title="Séjours", url_path="sejours"),
    st.Page("pages/facturation.py", title="Facturation", url_path="facturation"),
    st.Page("pages/qualite.py", title="Qualité des données", url_path="qualite"),
    st.Page("pages/rapprochement.py", title="Rapprochement d'identités", url_path="rapprochement"),
    st.Page("pages/donnees.py", title="Données", url_path="donnees"),
]

st.navigation(PAGES).run()
