"""Scraper genérico para tiendas basadas en VTEX (Chedraui, HEB)."""
import requests

PAGE_SIZE = 50


def fetch_products(base_url, category_path, store_name, max_pages=10):
    """Descarga todos los productos de una categoría VTEX, paginando de 50 en 50."""
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
