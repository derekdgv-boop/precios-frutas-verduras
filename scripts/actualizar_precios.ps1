# Corre el scraper completo (Chedraui, HEB, Comer) desde esta compu -
# HEB y Comer bloquean las IPs de GitHub Actions, pero no la de este equipo.
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

    git pull --quiet 2>&1 | Out-File -Append -Encoding utf8 $log

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
