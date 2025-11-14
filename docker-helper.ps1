# Script de ayuda para Docker - Clasificador de Residuos
# Ejecutar en PowerShell

Write-Host "=== Clasificador de Residuos - Docker Helper ===" -ForegroundColor Cyan
Write-Host ""

function Show-Menu {
    Write-Host "Selecciona una opción:" -ForegroundColor Yellow
    Write-Host "1. Construir imagen Docker"
    Write-Host "2. Ejecutar con docker-compose (recomendado)"
    Write-Host "3. Ejecutar con docker run"
    Write-Host "4. Ver logs"
    Write-Host "5. Detener aplicación"
    Write-Host "6. Ver estado del modelo"
    Write-Host "7. Verificar IP local (para acceso desde otros dispositivos)"
    Write-Host "8. Limpiar contenedores y reiniciar"
    Write-Host "0. Salir"
    Write-Host ""
}

function Build-Image {
    Write-Host "Construyendo imagen Docker..." -ForegroundColor Green
    docker build -t garbage-classifier .
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Imagen construida exitosamente" -ForegroundColor Green
    } else {
        Write-Host "✗ Error al construir la imagen" -ForegroundColor Red
    }
}

function Start-WithCompose {
    Write-Host "Iniciando con docker-compose..." -ForegroundColor Green
    docker-compose up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Aplicación iniciada" -ForegroundColor Green
        Write-Host "Accede a: http://localhost:5000" -ForegroundColor Cyan
    } else {
        Write-Host "✗ Error al iniciar" -ForegroundColor Red
    }
}

function Start-WithDocker {
    Write-Host "Iniciando con docker run..." -ForegroundColor Green
    docker run -d -p 5000:5000 --name garbage-classifier-app garbage-classifier
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Aplicación iniciada" -ForegroundColor Green
        Write-Host "Accede a: http://localhost:5000" -ForegroundColor Cyan
    } else {
        Write-Host "✗ Error al iniciar" -ForegroundColor Red
    }
}

function Show-Logs {
    Write-Host "Mostrando logs (Ctrl+C para salir)..." -ForegroundColor Green
    $container = docker ps -q -f name=garbage-classifier
    if ($container) {
        docker logs -f $container
    } else {
        Write-Host "✗ Contenedor no encontrado" -ForegroundColor Red
    }
}

function Stop-App {
    Write-Host "Deteniendo aplicación..." -ForegroundColor Yellow
    docker-compose down
    docker stop garbage-classifier-app 2>$null
    docker rm garbage-classifier-app 2>$null
    Write-Host "✓ Aplicación detenida" -ForegroundColor Green
}

function Check-ModelStatus {
    Write-Host "Verificando estado del modelo..." -ForegroundColor Green
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:5000/public_model_status" -TimeoutSec 5
        $response | ConvertTo-Json -Depth 5
    } catch {
        Write-Host "✗ No se pudo conectar. ¿Está la aplicación corriendo?" -ForegroundColor Red
    }
}

function Show-LocalIP {
    Write-Host "Tu dirección IP local:" -ForegroundColor Green
    Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike "127.*"} | Select-Object IPAddress, InterfaceAlias | Format-Table
    Write-Host "Para acceder desde otro dispositivo, usa: http://<IP>:5000" -ForegroundColor Cyan
}

function Clean-AndRestart {
    Write-Host "Limpiando y reiniciando..." -ForegroundColor Yellow
    docker-compose down
    docker stop garbage-classifier-app 2>$null
    docker rm garbage-classifier-app 2>$null
    Write-Host "Reconstruyendo imagen..." -ForegroundColor Green
    docker build -t garbage-classifier .
    Write-Host "Iniciando aplicación..." -ForegroundColor Green
    docker-compose up -d
    Write-Host "✓ Aplicación reiniciada" -ForegroundColor Green
}

# Menú principal
do {
    Show-Menu
    $option = Read-Host "Opción"
    
    switch ($option) {
        1 { Build-Image }
        2 { Start-WithCompose }
        3 { Start-WithDocker }
        4 { Show-Logs }
        5 { Stop-App }
        6 { Check-ModelStatus }
        7 { Show-LocalIP }
        8 { Clean-AndRestart }
        0 { Write-Host "Saliendo..." -ForegroundColor Cyan; break }
        default { Write-Host "Opción inválida" -ForegroundColor Red }
    }
    
    if ($option -ne 0) {
        Write-Host ""
        Read-Host "Presiona Enter para continuar"
        Clear-Host
    }
} while ($option -ne 0)
