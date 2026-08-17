FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.10.0 /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Le repertoire d'affichage entier, registre compris, et le module d'ingestion dont le
# tableau de bord tire son chemin de connexion — il n'en ouvre pas un second.
COPY dashboard/ dashboard/
COPY ingestion/ ingestion/

EXPOSE 8501

# `python -m streamlit`, et non l'executable `streamlit` : la forme `-m` place le repertoire de
# travail — ici /app, la racine du depot dans l'image — en tete du chemin d'import, ce que
# l'executable ne fait pas. La bibliotheque d'affichage n'y ajoute, elle, que le repertoire du
# script principal (/app/dashboard) ; sans le repertoire de travail, `from dashboard import ...`
# en tete de chaque page reste introuvable et aucune page ne rend.
#
# C'est le mecanisme deja employe par toutes les taches du graphe quotidien : repertoire de
# travail fixe a la racine du depot, invocation par `uv run python -m <module>`. Le projet
# declare `package = false` et n'est installe nulle part ; la racine du depot en tete du chemin
# d'import est donc la seule chose qui le rende importable, ici comme ailleurs.
CMD ["uv", "run", "--frozen", "python", "-m", "streamlit", "run", "dashboard/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
