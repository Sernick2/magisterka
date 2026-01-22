import os, time, json, redis
from fastapi import FastAPI, HTTPException
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

# Pobieramy adres bazy
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/products_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
cache = redis.from_url(REDIS_URL, decode_responses=True)

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

def init_db():
    db = SessionLocal()
    try:
        if not db.query(ProductModel).first():
            print("Inicjalizacja bazy danych produktami...")
            db.add(ProductModel(name="Laptop z Bazy", price=4999.99))
            db.add(ProductModel(name="Myszka z Bazy", price=150.0))
            db.commit()
    finally:
        db.close()

# Model bazy danych
class ProductModel(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Float)

# Tworzymy tabele
Base.metadata.create_all(bind=engine)
init_db

app = FastAPI(title="Product Service")

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

@app.get("/products/{product_id}")
def get_product(product_id: int):
    # 1. Próba pobrania z Cache
    cached_product = cache.get(f"product:{product_id}")
    if cached_product:
        print("--- CACHE HIT! Pobrano z Redis ---")
        return json.loads(cached_product)

    # 2. Jeśli nie ma w cache, idziemy do bazy
    db = SessionLocal()
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    db.close()

    if not product:
        raise HTTPException(status_code=404, detail="Produkt nie znaleziony")

    # 3. Zapisujemy do cache na 60 sekund (aby dane nie były wiecznie nieaktualne)
    product_data = {"id": product.id, "name": product.name, "price": product.price}
    cache.setex(f"product:{product_id}", 60, json.dumps(product_data))
    
    print("--- CACHE MISS! Pobrano z Bazy i zapisano do Redis ---")
    return product_data

@app.get("/")
def health_check():
    return {"status": "ok", "database": "connected"}