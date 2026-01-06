# Wybieramy lekką wersję Pythona
FROM python:3.11-slim

# Ustawiamy katalog roboczy wewnątrz kontenera
WORKDIR /app

# Kopiujemy plik z listą bibliotek
COPY requirements.txt .

# Instalujemy biblioteki
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy kod aplikacji
COPY . .

# Informujemy, na jakim porcie działa aplikacja
EXPOSE 8000

# Komenda uruchamiająca serwer
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]