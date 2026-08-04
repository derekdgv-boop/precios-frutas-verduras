"""Scraper de La Comer (tienda 'Comer'), sucursal La Comer Altaria Aguascalientes.

La API está detrás de Cloudflare (bot management): un requests normal recibe
403 desde IPs de datacenter (GitHub Actions). cloudscraper resuelve el reto JS
de Cloudflare e imita un navegador, así que corre serverless sin proxy.
"""
import time
import cloudscraper

NOMBRE_BLOQUEADO = ("ensalada", "coctel", "salsa", "topping", "guacamole", "desinfect", "jugo")

API_URL = "https://www.lacomer.com.mx/lacomer-api/api/v1/public/articulopasillo/articulospasillord"
SUCC_ID = 430  # La Comer Altaria Aguascalientes
PAS_ID = 13    # Pasillo "Frutas y Verduras"
# Si cambian de sucursal/pasillo: navegar el pasillo en lacomer.com.mx,
# DevTools > Network > "articulospasillord" y leer succId/pasId del query.

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


HOME_URL = "https://www.lacomer.com.mx/lacomer/"
PAUSA_ENTRE_SUBCAT = 1.5
INTENTOS_POR_SUBCAT = 3


def _pedir_subcat(session, padre_id):
    """Pide una subcategoría con reintentos. Cloudflare a veces re-reta a media
    corrida; reintentar (recreando la sesión) recupera la cookie cf_clearance."""
    params = dict(
        agruVirtual=0, filtroSeleccionado=0, idPromocion=0, marca="",
        noPagina=1, numResultados=500, orden=-1, padreId=padre_id,
        parmInt=1, pasId=PAS_ID, pasiPort=0, precio="", succId=SUCC_ID,
    )
    for intento in range(INTENTOS_POR_SUBCAT):
        try:
            resp = session.get(API_URL, params=params, timeout=40)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        # Re-templar: home nueva para renovar el reto de Cloudflare.
        time.sleep(2 * (intento + 1))
        try:
            session = cloudscraper.create_scraper()
            session.get(HOME_URL, timeout=40)
        except Exception:
            pass
    return None


def fetch_products(store_name="Comer"):
    products = []
    session = cloudscraper.create_scraper()  # sesión que pasa el reto de Cloudflare
    # Warm-up: visita la home para obtener la cookie cf_clearance antes de la API.
    try:
        session.get(HOME_URL, timeout=40)
    except Exception:
        pass

    for padre_id, subcat_name in SUBCATEGORIAS.items():
        data = _pedir_subcat(session, padre_id)
        if data is None:
            continue
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

        time.sleep(PAUSA_ENTRE_SUBCAT)  # no martillar Cloudflare entre subcats

    return products
