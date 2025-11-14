# Script para ejecutar la app y compartirla con ngrok
# Ejecutar en PowerShell

Write-Host "=== Iniciando Clasificador de Residuos ===" -ForegroundColor Cyan
Write-Host ""

# Verificar si Python está disponible
try {
    $pythonVersion = py --version 2>&1
    Write-Host "✓ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python no encontrado. Instala Python primero." -ForegroundColor Red
    exit 1
}

# Verificar si ngrok está instalado
$ngrokInstalled = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrokInstalled) {
    Write-Host "ngrok no está instalado. Descargándolo..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Opción 1: Descargar manualmente desde https://ngrok.com/download" -ForegroundColor Cyan
    Write-Host "Opción 2: Instalar con winget (si tienes Windows 11):" -ForegroundColor Cyan
    Write-Host "  winget install ngrok.ngrok" -ForegroundColor White
    Write-Host ""
    $install = Read-Host "¿Quieres intentar instalarlo con winget ahora? (s/n)"
    if ($install -eq 's') {
        winget install ngrok.ngrok
        if ($LASTEXITCODE -ne 0) {
            Write-Host "No se pudo instalar automáticamente. Descarga desde https://ngrok.com/download" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Por favor instala ngrok y vuelve a ejecutar este script." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "=== Iniciando aplicación Flask ===" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; py app.py" -WindowStyle Normal

Write-Host "Esperando a que la aplicación inicie..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "=== Iniciando túnel ngrok ===" -ForegroundColor Green
Write-Host "Presiona Ctrl+C para detener el túnel cuando termines" -ForegroundColor Yellow
Write-Host ""

# Iniciar ngrok en el puerto 5000
ngrok http 5000
