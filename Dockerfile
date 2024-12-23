# Aggiungi la creazione di un ambiente virtuale Python
FROM python:3.11-slim

WORKDIR /app

# Clona il repository
RUN git clone https://github.com/firo/lucasbacktesting.git .

# Installa dipendenze di sistema per creare l'ambiente virtuale
RUN apt-get update && apt-get install -y python3-venv

# Crea e attiva un ambiente virtuale
RUN python3 -m venv /env
ENV PATH="/env/bin:$PATH"

# Installa i pacchetti Python nell'ambiente virtuale
RUN pip install --no-cache-dir backtrader yfinance streamlit pandas matplotlib

# Comando di default per eseguire il container
CMD ["streamlit", "run", "app.py"]
