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


def match_basket(products, patterns):
    """Para cada producto canónico, regresa el primer artículo que haga match."""
    compiled = {k: re.compile(p) for k, p in patterns.items()}
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

    patterns = json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))

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
        basket[store_name] = match_basket(products, patterns)

    # data/latest.json: snapshot de hoy, pivotado por producto
    latest = {"fecha": today, "productos": {}}
    for canon in patterns:
        latest["productos"][canon] = {}
        for store_name in stores:
            match = basket[store_name].get(canon)
            if match:
                latest["productos"][canon][store_name] = {
                    "precio": match["precio"],
                    "nombre": match["nombre"],
                    "unidad": match.get("unidad", ""),
                }
    (DATA_DIR / "latest.json").write_text(
        json.dumps(latest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # data/history.csv: una fila por producto/tienda/día, para graficar tendencia
    history_file = DATA_DIR / "history.csv"
    is_new = not history_file.exists()
    with open(history_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["fecha", "producto", "tienda", "precio", "nombre_original", "unidad"])
        for canon in patterns:
            for store_name in stores:
                match = basket[store_name].get(canon)
                if match:
                    writer.writerow([today, canon, store_name, match["precio"], match["nombre"], match.get("unidad", "")])

    print("Listo.")


if __name__ == "__main__":
    main()
