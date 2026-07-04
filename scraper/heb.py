"""Scraper de HEB. Ya no usa la API clásica de VTEX (catalog_system/pub) —
HEB migró su sitio a un frontend propio en Next.js con su propia API
'/api/categories/...'. Sigue corriendo sobre catálogo VTEX por debajo
(imágenes en vteximg.com.br), pero la búsqueda pública cambió de forma.
Esta API nueva es inestable bajo varias páginas seguidas (a veces corta
la paginación a medias), así que cada página reintenta antes de rendirse."""
import time
import requests

from vtex_store import _es_natural

API_URL = "https://www.heb.com.mx/api/categories/frutas-y-verduras"
STORE_ID = "hebmx002959"  # unico storeId que expone el sitio (catalogo nacional)
HITS_PER_PAGE = 100
INTENTOS_POR_PAGINA = 4
PAUSA_ENTRE_PAGINAS = 1.5


def _pedir_pagina(session, page):
    params = {"storeId": STORE_ID, "page": page, "hitsPerPage": HITS_PER_PAGE}
    for intento in range(INTENTOS_POR_PAGINA):
        try:
            resp = session.get(API_URL, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("products"):
                    return data
        except (requests.RequestException, ValueError):
            pass
        time.sleep(2 * (intento + 1))
    return None


def fetch_products(store_name="HEB"):
    products = []
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    page = 1
    total_pages = None
    while total_pages is None or page <= total_pages:
        data = _pedir_pagina(session, page)
        if data is None:
            break  # esta página no respondió tras varios intentos; nos quedamos con lo ya juntado

        total_pages = data.get("totalPages", page)
        for item in data.get("products") or []:
            breadcrumb = [item.get("breadCrumb") or ""]
            if not _es_natural(breadcrumb, item.get("name")):
                continue
            precio = (item.get("price") or {}).get("basePrice")
            if not precio:
                continue
            products.append({
                "tienda": store_name,
                "nombre": (item.get("name") or "").strip(),
                "precio": round(float(precio), 2),
                "unidad": item.get("measurementUnit", ""),
            })

        page += 1
        time.sleep(PAUSA_ENTRE_PAGINAS)

    return products
