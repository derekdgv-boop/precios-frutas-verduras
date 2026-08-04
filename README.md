# Precios Frutas y Verduras — Aguascalientes

Comparador diario de precios de frutas y verduras frescas en Aguascalientes,
tomados del **catálogo público en línea** de tres cadenas: **Chedraui**, **HEB**
y **La Comer**. Frontend estático (GitHub Pages) + scraper en Python.

- **Sitio:** publicado con GitHub Pages desde este repo (`index.html`).
- **Datos:** `data/latest.json` (snapshot de hoy) y `data/history.csv` (serie histórica).

## Qué hace

1. `scraper/run.py` baja el catálogo de fruta/verdura **natural** de cada tienda
   (filtra ensaladas, jugos, salsas, cortes procesados).
2. Arma una **canasta comparativa**: para ~110 productos canónicos, empareja el
   artículo de cada tienda por regex, priorizando precio por **kg** (unidad
   comparable).
3. Detecta **cambios de precio** vs. el último dato conocido.
4. Escribe:
   - `data/latest.json` — canasta pivoteada + catálogo completo por tienda +
     cambios del día + `fuentes` (estado/frescura por tienda).
   - `data/history.csv` — una fila por producto/tienda/día (podada a los últimos
     180 días) para la gráfica de tendencia.
   - `data/raw/<fecha>/<tienda>.json` — catálogo crudo del día (auditoría).
5. `index.html` (sin dependencias, sin build) lee esos archivos y muestra la
   canasta, el catálogo por tienda, los cambios del día, avisos de frescura y
   una gráfica de tendencia por producto (toca un renglón de la canasta).

## Estructura

```
index.html                 Frontend (vanilla JS, sin build ni CDN)
requirements.txt           Dependencia del scraper: requests
scraper/
  run.py                   Orquestador: scrapea, arma canasta, escribe data/
  vtex_store.py            Scraper genérico VTEX (Chedraui)
  heb.py                   Scraper HEB (API Next.js propia)
  comer.py                 Scraper La Comer (API lacomer-api)
  products.json            Catálogo canónico: {id: {nombre, patron regex}}
  generar_products.py      Genera products.json desde la lista ITEMS
  test_matching.py         Tests de emparejamiento (regex + canasta)
scripts/
  actualizar_precios.ps1   Corrida diaria local (Task Scheduler de Windows)
.github/workflows/scrape.yml  Corrida manual (solo Chedraui; ver nota)
data/                      Salida del scraper (JSON + CSV)
```

## Correr local

Requiere Python 3.12+.

```bash
python -m venv venv
venv\Scripts\activate            # Windows;  en Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
python scraper/run.py
```

Abre `index.html` con cualquier servidor estático (por `fetch` de los JSON):

```bash
python -m http.server 8000
# luego abre http://localhost:8000
```

### Tests

```bash
python -m unittest discover -s scraper -p "test_*.py"
```

### Regenerar el catálogo de productos

`scraper/products.json` es **generado**. Edita la lista `ITEMS` en
`scraper/generar_products.py` y regenera:

```bash
python scraper/generar_products.py
```

Cada entrada de `ITEMS` es `(id, "Nombre a mostrar", [palabras clave])`.
Las palabras clave se exigen **todas** (en cualquier orden); prefija con `!`
para excluir (p. ej. `["ciruela", "!moscatel"]`), y usa `|` para alternativas
(`["arandano|blueberry"]`).

## Actualización automática

La corrida diaria **real** ocurre **local** vía el Programador de Tareas de
Windows, ejecutando `scripts/actualizar_precios.ps1` (hace `git pull`, corre el
scraper y hace `commit`/`push` de `data/`).

> **Por qué no GitHub Actions:** HEB y La Comer bloquean las IPs de GitHub
> Actions (anti-bot Incapsula/Cloudflare), así que desde ahí salen en 0. El
> workflow `.github/workflows/scrape.yml` queda solo para pruebas manuales
> (`workflow_dispatch`) y trae Chedraui bien; HEB/Comer saldrán vacías.
>
> Si una tienda scrapea 0, `run.py` **conserva su último dato bueno** y lo marca
> como `stale` en `latest.json`; la UI muestra un aviso en vez de borrar precios.

## Notas de datos

- Precio por **kilogramo** salvo que se indique otra unidad (`/pza`, `/un`…).
- El "precio más bajo del día" solo se resalta cuando las tiendas comparten
  **la misma unidad** (comparar $/kg contra $/pza sería engañoso).
- No incluye Mega Comercial Mexicana (sin tienda en línea).
- Sucursales: Chedraui/HEB catálogo nacional; La Comer Altaria Aguascalientes.
  Constantes de tienda (`SUCC_ID`, `STORE_ID`) documentadas en cada scraper.
