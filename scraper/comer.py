"""Scraper de La Comer (tienda 'Comer'), sucursal La Comer Altaria Aguascalientes."""
import requests

NOMBRE_BLOQUEADO = ("ensalada", "coctel", "salsa", "topping", "guacamole", "desinfect", "jugo")

API_URL = "https://www.lacomer.com.mx/lacomer-api/api/v1/public/articulopasillo/articulospasillord"
SUCC_ID = 430  # La Comer Altaria Aguascalientes
PAS_ID = 13    # Pasillo "Frutas y Verduras"

# Subcategorías (padreId) dentro del pasillo Frutas y Verduras.
# Fuera a propósito: Ensaladas y Aderezos Refrigerados (procesado),
# Frutas y Verduras Empacadas (cortes/bolsas semi-procesadas),
# Semillas, Cereales y Frutos Secos (no es fruta/verdura fresca).
SUBCATEGORIAS = {
    14: "Frutas",
    15: "Frutas Cítricas",
    18: "Legumbres",
    16: "Tallos y Hongos",
    19: "Tubérculos y Raíces",
    17: "Verduras, Hortalizas y Manojos",
    20: "Frutas y Verduras Orgánicas",
}


def fetch_products(store_name="Comer"):
    products = []
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    for padre_id, subcat_name in SUBCATEGORIAS.items():
        # La API ignora noPagina/numResultados y siempre regresa el
        # subcatálogo completo en una sola respuesta.
        params = dict(
            agruVirtual=0, filtroSeleccionado=0, idPromocion=0, marca="",
            noPagina=1, numResultados=500, orden=-1, padreId=padre_id,
            parmInt=1, pasId=PAS_ID, pasiPort=0, precio="", succId=SUCC_ID,
        )
        resp = session.get(API_URL, params=params, timeout=30)
        if resp.status_code != 200:
            continue
        data = resp.json()
        items = data.get("vecArticulo") or []

        for a in items:
            nombre = (a.get("artDes") or "").strip()
            precio = a.get("artPrven")
            if not nombre or not precio:
                continue
            if any(w in nombre.lower() for w in NOMBRE_BLOQUEADO):
                continue
            products.append({
                "tienda": store_name,
                "nombre": nombre,
                "precio": round(float(precio), 2),
                "unidad": (a.get("artTun") or "").strip(),
                "subcategoria": subcat_name,
            })

    return products
