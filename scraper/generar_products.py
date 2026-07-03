"""Script de una sola vez: genera products.json a partir de la lista oficial
de claves de artículo que dio el usuario. Regex usa lookaheads (?=.*\\bXXX\\b)
para exigir todas las palabras clave, en cualquier orden, sobre el nombre
normalizado (sin acentos, minúsculas) del producto de cada tienda."""
import json

# (id, nombre para mostrar, [palabras clave requeridas])
ITEMS = [
    ("acelga", "Acelga", ["acelga"]),
    ("aguacate", "Aguacate Hass", ["aguacate", "!hoja"]),
    ("ajo", "Ajo", ["ajo"]),
    ("alcachofa", "Alcachofa", ["alcachofa"]),
    ("alfalfa", "Alfalfa", ["alfalfa", "!germen", "!germinado", "!germimax", "!aderezo"]),
    ("apio", "Apio", ["apio"]),
    ("arugula", "Arúgula", ["arugul"]),
    ("berenjena", "Berenjena", ["berenjena"]),
    ("betabel", "Betabel", ["betabel"]),
    ("blueberry", "Blueberry / Arándano", ["arandano|blueberry"]),
    ("brocoli", "Brócoli", ["brocoli"]),
    ("calabaza_italiana", "Calabaza Italiana", ["calabaza", "italian"]),
    ("camote", "Camote", ["camote"]),
    ("cana_azucar", "Caña de Azúcar", ["cana"]),
    ("cebolla_blanca", "Cebolla Blanca", ["cebolla", "blanca"]),
    ("cebolla_cambray", "Cebolla de Cambray", ["cebolla", "cambray"]),
    ("cebolla_morada", "Cebolla Morada", ["cebolla", "morada"]),
    ("cebollin", "Cebollín", ["cebollin"]),
    ("cereza", "Cereza", ["cereza"]),
    ("champinon", "Champiñón", ["champin"]),
    ("chayote", "Chayote", ["chayote"]),
    ("chicharo", "Chícharo", ["chicharo"]),
    ("chile_caribe", "Chile Caribe", ["chile", "caribe"]),
    ("chile_chilaca", "Chile Chilaca", ["chilaca"]),
    ("chile_arbol", "Chile de Árbol", ["chile", "arbol"]),
    ("chile_guajillo", "Chile Guajillo", ["chile", "guajillo"]),
    ("chile_guero", "Chile Güero / Húngaro", ["chile", "guero|hungaro"]),
    ("chile_habanero", "Chile Habanero", ["chile", "habanero"]),
    ("chile_jalapeno", "Chile Jalapeño", ["chile", "jalape"]),
    ("chile_poblano", "Chile Poblano", ["chile", "poblano"]),
    ("chile_serrano", "Chile Serrano", ["chile", "serrano"]),
    ("cilantro", "Cilantro", ["cilantro"]),
    ("ciruela_moscatel", "Ciruela Moscatel", ["ciruela", "moscatel"]),
    ("ciruela_roja", "Ciruela Roja", ["ciruela", "!moscatel"]),
    ("col_blanca", "Col Blanca", ["col", "blanca"]),
    ("coliflor", "Coliflor", ["coliflor"]),
    ("durazno_amarillo", "Durazno Amarillo", ["durazno", "amarillo"]),
    ("durazno_prisco", "Durazno Prisco", ["durazno", "prisco"]),
    ("durazno_rojo", "Durazno Rojo", ["durazno", "rojo"]),
    ("ejote", "Ejote", ["ejote"]),
    ("elote", "Elote", ["elote"]),
    ("epazote", "Epazote", ["epazote"]),
    ("esparrago", "Espárrago", ["esparrago"]),
    ("espinaca", "Espinaca", ["espinaca"]),
    ("frambuesa", "Frambuesa", ["frambuesa"]),
    ("fresa", "Fresa", ["fresa"]),
    ("germen_soya", "Germen de Soya", ["germen", "soya"]),
    ("guanabana", "Guanábana", ["guanabana"]),
    ("guayaba", "Guayaba", ["guayaba"]),
    ("hierbabuena", "Hierbabuena", ["hierbabuena"]),
    ("jamaica", "Jamaica", ["jamaica", "!mezcla", "!hidrolizada"]),
    ("jengibre", "Jengibre", ["jengibre"]),
    ("jicama", "Jícama", ["jicama"]),
    ("jitomate_saladet", "Jitomate Saladet", ["jitomate|tomate", "saladet"]),
    ("jitomate_bola", "Jitomate / Tomate Bola", ["jitomate|tomate", "bola"]),
    ("kiwi", "Kiwi", ["kiwi"]),
    ("lechuga_italiana", "Lechuga Italiana", ["lechuga", "italian"]),
    ("lechuga_orejona", "Lechuga Orejona / Larga / Lisa", ["lechuga", "orejona|larga|lisa"]),
    ("lechuga_romana", "Lechuga Romana", ["lechuga", "romana"]),
    ("lechuga_sangria", "Lechuga Sangría", ["lechuga", "sangria"]),
    ("lichi", "Lichi", ["lichi"]),
    ("limon", "Limón", ["limon"]),
    ("mamey", "Mamey", ["mamey"]),
    ("mandarina", "Mandarina", ["mandarina"]),
    ("mango_ataulfo", "Mango Ataulfo", ["mango", "ataulfo"]),
    ("mango_manila", "Mango Manila", ["mango", "manila"]),
    ("mango_paraiso", "Mango Paraíso", ["mango", "paraiso"]),
    ("manzana_golden", "Manzana Golden", ["manzana", "golden"]),
    ("manzana_granny", "Manzana Granny Smith", ["manzana", "granny"]),
    ("manzana_roja", "Manzana Roja", ["manzana", "roja"]),
    ("manzana_royal_gala", "Manzana Royal Gala", ["manzana", "gala"]),
    ("mejorana", "Mejorana", ["mejorana"]),
    ("melon_amarillo", "Melón Amarillo", ["melon", "amarillo"]),
    ("melon_chino", "Melón Chino", ["melon", "chino"]),
    ("naranja", "Naranja", ["naranja"]),
    ("nopal_entero", "Nopal Entero", ["nopal", "!picado"]),
    ("nopal_picado", "Nopal Picado", ["nopal", "picado"]),
    ("papa_blanca", "Papa Blanca", ["papa", "blanca"]),
    ("papa_cambray", "Papa Cambray", ["papa", "cambray"]),
    ("papaya", "Papaya Maradol", ["papaya"]),
    ("pepino", "Pepino", ["pepino"]),
    ("pera_danjou", "Pera D'Anjou", ["pera", "anjou"]),
    ("pera_mantequilla", "Pera Mantequilla", ["pera", "mantequilla"]),
    ("perejil", "Perejil", ["perejil"]),
    ("pimiento_amarillo", "Pimiento Amarillo", ["pimiento", "amarillo"]),
    ("pimiento_naranja", "Pimiento Naranja", ["pimiento", "naranja"]),
    ("pimiento_rojo", "Pimiento Rojo", ["pimiento", "rojo"]),
    ("pimiento_verde", "Pimiento Verde", ["pimiento", "verde"]),
    ("pina", "Piña", ["pina"]),
    ("pitahaya", "Pitahaya", ["pitahaya"]),
    ("platano_chiapas", "Plátano", ["platano"]),
    ("platano_macho", "Plátano Macho", ["platano", "macho"]),
    ("rabano", "Rábano", ["rabano"]),
    ("repollo", "Repollo (Col Blanca)", ["repollo"]),
    ("sandia", "Sandía", ["sandia"]),
    ("te_limon", "Té Limón", ["te", "limon"]),
    ("tomate_huaje", "Tomate Huaje", ["tomate", "huaje"]),
    ("tomate_cherry", "Tomate Cherry", ["tomate", "cherry"]),
    ("tomate_verde", "Tomate Verde", ["tomate", "verde"]),
    ("tomillo", "Tomillo", ["tomillo"]),
    ("toronja", "Toronja", ["toronja"]),
    ("uva_blanca", "Uva Blanca", ["uva", "blanca"]),
    ("uva_globo", "Uva Globo", ["uva", "globo"]),
    ("uva_roja", "Uva Roja", ["uva", "roja"]),
    ("uva_verde", "Uva Verde", ["uva", "verde"]),
    ("verdolaga", "Verdolaga", ["verdolaga"]),
    ("yaca", "Yaca", ["yaca"]),
    ("yuca", "Yuca", ["yuca"]),
    ("zanahoria", "Zanahoria", ["zanahoria"]),
    ("zarzamora", "Zarzamora", ["zarzamora"]),
]


def build_pattern(keywords):
    """Sufijo 's?' (no '\\w*'): solo permite plural, no cualquier palabra que
    empiece igual (evita que "cana" matchee "canario", etc.).
    Ancla con '^' porque son puros lookaheads de ancho cero: sin ancla,
    re.search prueba posiciones posteriores y un '(?!...)' negativo puede
    "esquivar" la palabra prohibida buscando después de que ya apareció."""
    parts = ["^"]
    for kw in keywords:
        if kw.startswith("!"):
            parts.append(f"(?!.*\\b({kw[1:]})s?\\b)")
        else:
            parts.append(f"(?=.*\\b({kw})s?\\b)")
    return "".join(parts)


out = {}
for id_, nombre, keywords in ITEMS:
    out[id_] = {"nombre": nombre, "patron": build_pattern(keywords)}

with open("products.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print(f"{len(out)} productos escritos en products.json")
