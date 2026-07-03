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


def _es_mejor_match(candidato, actual):
    """Prefiere precio por kg (unidad comparable estándar de fruta/verdura);
    solo compara precio numérico dentro del mismo "nivel" de unidad, para no
    confundir un paquete de 250g más barato en pesos con un kg más caro."""
    cand_kg = normalize(candidato.get("unidad", "")) == "kg"
    act_kg = normalize(actual.get("unidad", "")) == "kg"
    if cand_kg != act_kg:
        return cand_kg  # el que sea "kg" gana, sin importar precio
    return candidato["precio"] < actual["precio"]


def match_basket(products, catalogo):
    """Para cada producto canónico, regresa el artículo que haga match
    priorizando precio por kg (determinista y comparable); si ninguna
    coincidencia es por kg, gana la más barata entre las que hay."""
    compiled = {k: re.compile(v["patron"]) for k, v in catalogo.items()}
    found = {}
    for prod in products:
        norm_name = normalize(prod["nombre"])
        for canon, rx in compiled.items():
            if not rx.search(norm_name):
                continue
            if canon not in found or _es_mejor_match(prod, found[canon]):
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

    # Lee el historial previo (antes de sobreescribirlo) para poder comparar
    # el precio de hoy contra el último precio conocido de cada producto/tienda.
    history_file = DATA_DIR / "history.csv"
    fieldnames = ["fecha", "producto", "tienda", "precio", "nombre_original", "unidad"]
    filas_previas = []
    if history_file.exists():
        with open(history_file, newline="", encoding="utf-8") as f:
            filas_previas = [r for r in csv.DictReader(f) if r["fecha"] != today]

    ultimo_previo = {}
    for r in filas_previas:
        key = (r["producto"], r["tienda"])
        if key not in ultimo_previo or r["fecha"] > ultimo_previo[key]["fecha"]:
            ultimo_previo[key] = r

    filas_hoy = []
    cambios = []
    for canon in catalogo:
        for store_name in stores:
            match = basket[store_name].get(canon)
            if not match:
                continue
            filas_hoy.append({
                "fecha": today, "producto": canon, "tienda": store_name,
                "precio": match["precio"], "nombre_original": match["nombre"],
                "unidad": match.get("unidad", ""),
            })

            prev = ultimo_previo.get((canon, store_name))
            if not prev:
                continue
            precio_prev = float(prev["precio"])
            precio_hoy = match["precio"]
            if abs(precio_hoy - precio_prev) < 0.01:
                continue
            cambios.append({
                "producto": canon,
                "nombre_producto": catalogo[canon]["nombre"],
                "tienda": store_name,
                "precio_anterior": round(precio_prev, 2),
                "precio_nuevo": precio_hoy,
                "diferencia": round(precio_hoy - precio_prev, 2),
                "porcentaje": round((precio_hoy - precio_prev) / precio_prev * 100, 1),
                "fecha_anterior": prev["fecha"],
            })

    cambios.sort(key=lambda c: abs(c["porcentaje"]), reverse=True)

    # data/latest.json: snapshot de hoy, pivotado por producto (canasta) +
    # catálogo completo por tienda (todo fruta/verdura natural, sin procesados)
    # + cambios de precio respecto al último dato conocido.
    latest = {"fecha": today, "productos": {}, "catalogos": {}, "cambios": cambios}
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
    with open(history_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filas_previas + filas_hoy)

    print(f"Listo. {len(cambios)} cambios de precio detectados.")


if __name__ == "__main__":
    main()
