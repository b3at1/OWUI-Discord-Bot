FROM ghcr.io/astral-sh/uv:0.11.2-python3.14-trixie

WORKDIR /app
COPY . /app/

RUN uv sync --no-dev
RUN patch -p1 < patch/tamu_ai.patch

CMD ["uv", "run", "python", "-m", "bot"]