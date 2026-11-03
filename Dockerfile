FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends stockfish ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python -m unittest discover -s tests -v && python -m compileall -q app.py clocks.py \
    && useradd --create-home --uid 10001 chessuser
USER chessuser
EXPOSE 10000
CMD ["sh", "start.sh"]
