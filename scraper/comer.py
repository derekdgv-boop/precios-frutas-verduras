"""Scraper de La Comer (tienda 'Comer'), sucursal La Comer Altaria Aguascalientes."""
import requests

API_URL = "https://www.lacomer.com.mx/lacomer-api/api/v1/public/articulopasillo/articulospasillord"
SUCC_ID = 430  # La Comer Altaria Aguascalientes
PAS_ID = 13    # Pasillo "Frutas y Verduras"

# Subcategorías (padreId) dentro del pasillo Frutas y Verduras
SUBCATEGORIAS = {
    14: "Frutas",
    15: "Frutas Cítricas",
    18: "Legumbres",
    16: "Tallos y Hongos",
}


def fetch_products(store_name="Comer"):
    products = []
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    for padre_id, subcat_name in SUBCATEGORIAS.items():
        page = 1
        while True:
            params = dict(
                agruVirtual=0, filtroSeleccionado=0, idPromocion=0, marca="",
                noPagina=page, numResultados=100, orden=-1, padreId=padre_id,
                parmInt=1, pasId=PAS_ID, pasiPort=0, precio="", succId=SUCC_ID,
            )
            resp = session.get(API_URL, params=params, timeout=30)
            if resp.status_code != 200:
                break
            data = resp.json()
            items = data.get("vecArticulo") or []
            if not items:
                break

            for a in items:
                nombre = (a.get("artDes") or "").strip()
                precio = a.get("artPrven")
                if not nombre or not precio:
                    continue
                products.append({
                    "tienda": store_name,
                    "nombre": nombre,
                    "precio": round(float(precio), 2),
                    "unidad": (a.get("artTun") or "").strip(),
                    "subcategoria": subcat_name,
                })

            if len(items) < 100:
                break
            page += 1

    return products
