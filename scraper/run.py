"""Orquestador: junta precios de Chedraui, HEB y Comer, arma la canasta
comparativa y guarda resultados en data/."""
import csv
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import vtex_store
import comer

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PRODUCTS_FILE = Path(__file__).parent / "products.json"

TZ_MX = timezone(timedelta(hours=-6))


def strip_accents(text):
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize(text):
    return strip_accents(text or "").lower()


def match_basket(products, catalogo):
    """Para cada producto canónico, regresa el primer artículo que haga match."""
    compiled = {k: re.compile(v["patron"]) for k, v in catalogo.items()}
    found = {}
    for prod in products:
        norm_name = normalize(prod["nombre"])
        for canon, rx in compiled.items():
            if canon in found:
                continue
            if rx.search(norm_name):
                found[canon] = prod
    return found


def main():
    today = datetime.now(TZ_MX).date().isoformat()
    print(f"Scrapeando precios para {today}...")

    catalogo = json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))

    stores = {}

    print("- Chedraui...")
    stores["Chedraui"] = vtex_store.fetch_products(
        "https://www.chedraui.com.mx", "supermercado/frutas-y-verduras", "Chedraui"
    )
    print(f"  {len(stores['Chedraui'])} productos")

    print("- HEB...")
    stores["HEB"] = vtex_store.fetch_products(
        "https://www.heb.com.mx", "frutas-y-verduras", "HEB"
    )
    print(f"  {len(stores['HEB'])} productos")

    print("- Comer...")
    stores["Comer"] = comer.fetch_products("Comer")
    print(f"  {len(stores['Comer'])} productos")

    # Guarda el catálogo crudo del día (auditoría / futuras canastas)
    day_dir = RAW_DIR / today
    day_dir.mkdir(parents=True, exist_ok=True)
    for store_name, products in stores.items():
        (day_dir / f"{store_name.lower()}.json").write_text(
            json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # Arma la canasta comparativa
    basket = {}
    for store_name, products in stores.items():
        basket[store_name] = match_basket(products, catalogo)

    # data/latest.json: snapshot de hoy, pivotado por producto (canasta) +
    # catálogo completo por tienda (todo fruta/verdura natural, sin procesados)
    latest = {"fecha": today, "productos": {}, "catalogos": {}}
    for canon, info in catalogo.items():
        latest["productos"][canon] = {"nombre_producto": info["nombre"]}
        for store_name in stores:
            match = basket[store_name].get(canon)
            if match:
                latest["productos"][canon][store_name] = {
                    "precio": match["precio"],
                    "nombre": match["nombre"],
                    "unidad": match.get("unidad", ""),
                }

    for store_name, products in stores.items():
        ordenados = sorted(products, key=lambda p: normalize(p["nombre"]))
        latest["catalogos"][store_name] = [
            {"nombre": p["nombre"], "precio": p["precio"], "unidad": p.get("unidad", "")}
            for p in ordenados
        ]

    (DATA_DIR / "latest.json").write_text(
        json.dumps(latest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # data/history.csv: una fila por producto/tienda/día, para graficar tendencia.
    # Si ya corrió hoy (re-ejecución manual), reemplaza las filas de hoy en vez
    # de duplicarlas.
    history_file = DATA_DIR / "history.csv"
    fieldnames = ["fecha", "producto", "tienda", "precio", "nombre_original", "unidad"]
    filas_previas = []
    if history_file.exists():
        with open(history_file, newline="", encoding="utf-8") as f:
            filas_previas = [r for r in csv.DictReader(f) if r["fecha"] != today]

    filas_hoy = []
    for canon in catalogo:
        for store_name in stores:
            match = basket[store_name].get(canon)
            if match:
                filas_hoy.append({
                    "fecha": today, "producto": canon, "tienda": store_name,
                    "precio": match["precio"], "nombre_original": match["nombre"],
                    "unidad": match.get("unidad", ""),
                })

    with open(history_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filas_previas + filas_hoy)

    print("Listo.")


if __name__ == "__main__":
    main()
