import os
import time
from fastapi import FastAPI
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

# Pobieramy adres bazy
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/products_db")

# Funkcja tworząca połączenie z bazą z prostym mechanizmem ponawiania (retry)
# Chmura/Kontenery potrzebują sekundy na "rozruch" bazy danych
def get_engine():
    engine = create_engine(DATABASE_URL)
    for _ in range(5):
        try:
            engine.connect()
            return engine
        except OperationalError:
            print("Czekam na bazę danych...")
            time.sleep(2)
    return engine

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Model bazy danych
class ProductModel(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Float)

# Tworzymy tabele
Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/products")
def get_products():
    db = SessionLocal()
    try:
        # Jeśli baza pusta, dodajmy rekordy testowe
        if not db.query(ProductModel).first():
            db.add(ProductModel(name="Laptop z Bazy", price=4999.99))
            db.add(ProductModel(name="Myszka z Bazy", price=150.0))
            db.commit()
        
        products = db.query(ProductModel).all()
        return products
    finally:
        db.close()

@app.get("/")
def health_check():
    return {"status": "ok", "database": "connected"}