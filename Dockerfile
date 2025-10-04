FROM python:3.11-slim

# Nastavení pracovního adresáře
WORKDIR /app

# Instalace systémových závislostí
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Kopírování requirements.txt a instalace Python závislostí
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopírování celého projektu
COPY . .

# Vytvoření adresářů pro databázi a logy
RUN mkdir -p database logs

# Kopírování entrypoint scriptu
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Nastavení práv pro ostatní skripty (pokud existují)
RUN chmod +x start_app.sh stop_app.sh install_and_run.sh 2>/dev/null || true

# Exponování portu
EXPOSE 8080

# Nastavení proměnných prostředí
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=8080
ENV PYTHONUNBUFFERED=1

# Spuštění aplikace pomocí start_all.sh nebo pomocí Bash scriptu pro start obou služeb
ENTRYPOINT ["/docker-entrypoint.sh"]