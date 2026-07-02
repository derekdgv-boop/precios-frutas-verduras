"""Scraper genérico para tiendas basadas en VTEX (Chedraui, HEB)."""
import unicodedata
import requests

PAGE_SIZE = 50

# Subcategorías consideradas "natural, no procesado": solo fruta y verdura
# fresca. Fuera: ensaladas/cocteles, jugos, salsas, a granel (nueces/semillas),
# cortes listos para comer, desinfectantes, vegetales en bolsa/pre-cortados.
SUBCATEGORIAS_PERMITIDAS = {"frutas", "verduras"}
CATEGORIA_BLOQUEADA = ("ensalada", "coctel", "jugo", "salsa", "topping", "guacamole", "desinfect")
NOMBRE_BLOQUEADO = ("ensalada", "coctel", "salsa", "topping", "guacamole", "desinfect", "jugo")


def _norm(text):
    nfkd = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def _es_natural(categories, nombre):
    """True si el producto cuelga de una subcategoría .../Frutas/... o
    .../Verduras/... y no cae en categoría/nombre de producto procesado
    (ensaladas, cocteles, jugos, salsas, etc.)."""
    if any(w in _norm(nombre) for w in NOMBRE_BLOQUEADO):
        return False

    tiene_permitida = False
    for path in categories or []:
        partes = [_norm(p) for p in path.split("/") if p]
        if any(w in p for p in partes for w in CATEGORIA_BLOQUEADA):
            return False
        if any(p in SUBCATEGORIAS_PERMITIDAS for p in partes):
            tiene_permitida = True
    return tiene_permitida


def fetch_products(base_url, category_path, store_name, max_pages=10):
    """Descarga todos los productos naturales (fruta/verdura fresca) de una
    categoría VTEX, paginando de 50 en 50."""
    products = []
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    for page in range(max_pages):
        start = page * PAGE_SIZE
        end = start + PAGE_SIZE - 1
        url = f"{base_url}/api/catalog_system/pub/products/search/{category_path}?_from={start}&_to={end}"
        resp = session.get(url, timeout=30)
        if resp.status_code not in (200, 206):
            break
        try:
            batch = resp.json()
        except ValueError:
            break
        if not batch:
            break

        for item in batch:
            if not _es_natural(item.get("categories"), item.get("productName")):
                continue
            try:
                sku = item["items"][0]
                offer = sku["sellers"][0]["commertialOffer"]
                price = offer.get("Price")
                if not price:
                    continue
                products.append({
                    "tienda": store_name,
                    "nombre": item.get("productName", "").strip(),
                    "precio": round(float(price), 2),
                    "unidad": sku.get("measurementUnit", ""),
                })
            except (KeyError, IndexError, TypeError):
                continue

        if len(batch) < PAGE_SIZE:
            break

    return products
