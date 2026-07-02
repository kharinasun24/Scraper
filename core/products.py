# core/products.py
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Product:
    markt: str
    name: str
    preis: float
    url: str = ""
    kategorie: str = ""   # hilfreich für Filter