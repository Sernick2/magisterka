import os, time, requests, pika
from fastapi import FastAPI, HTTPException
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

# Konfiguracja z docker-compose
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@order_db:5432/orders_db")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8000")

# Funkcja Retry - kluczowa w chmurze
def get_engine():
    temp_engine = create_engine(DATABASE_URL)
    for i in range(10):  # 10 prób
        try:
            temp_engine.connect()
            print("Połączono z bazą danych Order DB!")
            return temp_engine
        except OperationalError:
            print(f"Próba {i+1}/10: Czekam na bazę danych Order DB...")
            time.sleep(3)
    return temp_engine

def send_to_queue(message):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
        channel = connection.channel()
        channel.queue_declare(queue='order_notifications')
        channel.basic_publish(exchange='', routing_key='order_notifications', body=message)
        connection.close()
    except Exception as e:
        print(f"Błąd kolejki: {e}")

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class OrderModel(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer)
    status = Column(String, default="CREATED")

# Tworzenie tabeli
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Order Service",
    root_path="/order-service"
)

@app.get("/")
def health():
    return {"status": "Order Service is healthy"}

@app.post("/orders/{product_id}")
def create_order(product_id: int):
    # 1. Sprawdź czy produkt istnieje w Product Service (REST API Call)
    try:
        response = requests.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}", timeout=5)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Produkt nie istnieje!")
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Katalog produktów (Product Service) jest chwilowo niedostępny")

    # 2. Jeśli OK, zapisz zamówienie
    db = SessionLocal()
    try:
        new_order = OrderModel(product_id=product_id)
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        send_to_queue(f"Zamówienie nr {new_order.id} na produkt {product_id}")
        return {"message": "Zamówienie złożone!", "order": new_order}
    finally:
        db.close()