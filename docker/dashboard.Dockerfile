FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.10.0 /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY dashboard/app.py dashboard/app.py

EXPOSE 8501

CMD ["uv", "run", "--frozen", "streamlit", "run", "dashboard/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
