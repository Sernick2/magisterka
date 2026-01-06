from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Product Service API")

# Model danych
class Product(BaseModel):
    id: int
    name: str
    description: str
    price: float

# Dane testowe (Mock)
products_db = [
    {"id": 1, "name": "Laptop Pro", "description": "Mocny sprzęt do pracy", "price": 4500.0},
    {"id": 2, "name": "Mysz Bezprzewodowa", "description": "Cicha i precyzyjna", "price": 120.0},
    {"id": 3, "name": "Monitor 4K", "description": "Matryca IPS 27 cali", "price": 1800.0},
]

@app.get("/")
def read_root():
    return {"message": "Product Service is running"}

@app.get("/products", response_model=List[Product])
def get_products():
    return products_db

@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    product = next((p for p in products_db if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product