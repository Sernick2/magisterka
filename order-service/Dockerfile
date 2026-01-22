# Używamy tej samej bazy co w product-service dla spójności
FROM python:3.11-slim

WORKDIR /app

# Kopiujemy i instalujemy zależności
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy kod serwisu
COPY . .

# Order Service będzie działał wewnątrz kontenera na porcie 8000
EXPOSE 8000

# Komenda startowa
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]