# Corre el scraper completo (Chedraui, HEB, Comer) desde esta compu.
#
# Rol en el esquema hibrido: GitHub Actions ya refresca Chedraui y HEB a
# diario sin depender de nadie. Esta PC aporta lo unico que Actions no puede:
# COMER, cuya API esta tras Cloudflare y bloquea IPs de datacenter pero no la
# residencial de este equipo. Por eso corre run.py completo (las 3 tiendas):
# Comer queda fresco cada vez que la compu esta encendida; si esta apagada,
# el sitio sigue vivo con Chedraui/HEB frescos y Comer en su ultimo precio.
# Registrado en el Programador de Tareas de Windows para correr a diario.

$ErrorActionPreference = "Stop"
$repo = "C:\Users\famil\precios-frutas-verduras"
$log = Join-Path $repo "scripts\ultima_corrida.log"

function Log($msg) {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg" | Out-File -Append -Encoding utf8 $log
}

try {
    Set-Location $repo
    Log "--- Iniciando actualizacion ---"

    # --rebase --autostash: Actions pudo pushear Chedraui/HEB desde la ultima
    # corrida local; reintegra encima sin chocar.
    git pull --rebase --autostash --quiet 2>&1 | Out-File -Append -Encoding utf8 $log

    & "$repo\venv\Scripts\python.exe" "$repo\scraper\run.py" 2>&1 | Out-File -Append -Encoding utf8 $log

    git add data/ 2>&1 | Out-File -Append -Encoding utf8 $log
    $fecha = Get-Date -Format "yyyy-MM-dd"
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        git commit -m "Actualiza precios $fecha (local)" 2>&1 | Out-File -Append -Encoding utf8 $log
        git push 2>&1 | Out-File -Append -Encoding utf8 $log
        Log "Cambios subidos."
    } else {
        Log "Sin cambios que subir."
    }
    Log "--- Listo ---"
} catch {
    Log "ERROR: $_"
}
