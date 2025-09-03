DEFAULT_KEYWORD_MAP = {
    # comida
    "comida": "Comida",
    "pan": "Comida",
    "galleta": "Comida",
    "galletas": "Comida",
    "pastel": "Comida",
    "pasteles": "Comida",
    "torta": "Comida",
    "snack": "Comida",
    "snacks": "Comida",
    "fruta": "Comida",
    "frutas": "Comida",
    "dulce": "Comida",
    "dulces": "Comida",
    "café": "Comida",
    "cafe": "Comida",
    "bebida": "Comida",
    "papas": "Comida",
    "papa": "Comida",
    "guayaba": "Comida",
    "arepa": "Comida",
    "empanada": "Comida",
    "jugos": "Comida",
    "jugo": "Comida",
    # ropa
    "ropa": "Ropa",
    "camisa": "Ropa",
    "camiseta": "Ropa",
    "jeans": "Ropa",
    "pantalón": "Ropa",
    "pantalon": "Ropa",
    "abrigo": "Ropa",
    "zapato": "Ropa",
    "zapatos": "Ropa",
    # tecnología
    "tecnologia": "Tecnología",
    "tecnología": "Tecnología",
    "smartphone": "Tecnología",
    "celular": "Tecnología",
    "laptop": "Tecnología",
    "pc": "Tecnología",
    "computador": "Tecnología",
    "audifonos": "Tecnología",
    "audífonos": "Tecnología",
    "smartwatch": "Tecnología",
}

def recommend_categories_from_text(text: str, keyword_map: dict | None = None) -> list[str]:
    if not text:
        return []
    mapping = keyword_map or DEFAULT_KEYWORD_MAP
    lowered = text.lower()
    categories: set[str] = set()
    for keyword, category in mapping.items():
        if keyword in lowered:
            categories.add(category)
    return sorted(categories)

