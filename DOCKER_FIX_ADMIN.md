# 🔧 Cómo arreglar Docker Desktop más tarde

Este archivo tiene los pasos para cuando tengas acceso de administrador y quieras usar Docker.

---

## ⚠️ Problema Actual

Docker Desktop no puede iniciar porque WSL (Windows Subsystem for Linux) necesita actualización, pero el comando `wsl --update` requiere permisos de administrador.

---

## ✅ Solución - Pasos a seguir

### 1. Abrir PowerShell como Administrador

**Opción A - Menú Inicio**:
1. Presiona tecla Windows
2. Escribe "PowerShell"
3. Clic derecho en "Windows PowerShell"
4. Selecciona "Ejecutar como administrador"

**Opción B - Atajo de teclado**:
1. Presiona `Win + X`
2. Selecciona "Windows PowerShell (Administrador)" o "Terminal (Administrador)"

### 2. Actualizar WSL

En la ventana de PowerShell con permisos de administrador, ejecuta:

```powershell
wsl --update
```

Espera a que termine (puede tomar 2-5 minutos). Verás algo como:
```
Comprobando si hay actualizaciones...
Descargando actualizaciones...
Instalando actualizaciones...
```

### 3. Verificar WSL actualizado

```powershell
wsl --version
```

Deberías ver la versión actualizada, algo como:
```
Versión de WSL: 2.x.x.x
Versión de kernel: 5.x.x.x
```

### 4. Reiniciar Docker Desktop

1. Cierra Docker Desktop completamente (clic derecho en el ícono de la bandeja → Quit Docker Desktop)
2. Espera 10 segundos
3. Vuelve a abrir Docker Desktop desde el menú inicio

### 5. Verificar que Docker funciona

Abre una nueva ventana de PowerShell (normal, no requiere admin) y ejecuta:

```powershell
docker info
```

Si ves información del servidor sin errores, ¡Docker está funcionando! ✅

### 6. Construir y ejecutar tu aplicación

```powershell
# Navega al proyecto
cd C:\Users\Lenovo\Documents\GitHub\PROYECTO

# Construir y ejecutar
docker-compose up -d --build

# Ver logs
docker-compose logs -f
```

### 7. Acceder a la aplicación

- **En tu PC**: http://localhost:5000
- **Desde otros dispositivos**: 
  1. Obtén tu IP: `ipconfig`
  2. Comparte: `http://TU_IP:5000`

---

## 🐛 Si siguen habiendo problemas

### Error: "This computer doesn't have VT-X/AMD-v enabled"

1. Reinicia tu PC
2. Entra al BIOS/UEFI (usualmente presionando F2, F10, Del o Esc al iniciar)
3. Busca opciones de virtualización:
   - Intel: "Intel VT-x", "Intel Virtualization Technology"
   - AMD: "AMD-V", "SVM Mode"
4. Habilítalo (Enabled)
5. Guarda y sal (Save and Exit)

### Error: "Docker Desktop requires Windows 10 Pro/Enterprise"

Si tienes Windows 10 Home:
- Docker Desktop funciona con WSL 2 en Windows 10 Home (versión 2004 o superior)
- Asegúrate de tener las actualizaciones más recientes de Windows

### Error persistente después de actualizar WSL

1. Desinstala Docker Desktop
2. Reinicia el PC
3. Descarga la última versión desde https://www.docker.com/products/docker-desktop
4. Vuelve a instalar

---

## 📊 Verificación rápida - Checklist

Antes de intentar usar Docker, verifica:

- [ ] Windows 10 versión 2004+ o Windows 11
- [ ] WSL 2 instalado y actualizado
- [ ] Virtualización habilitada en BIOS
- [ ] Docker Desktop instalado
- [ ] Permisos de administrador disponibles (para actualizar WSL)

---

## 💡 Mientras tanto...

Usa las alternativas sin Docker:

**Opción recomendada**: Render (ya configurado)
- Ve a https://render.com
- Redeploy tu servicio
- Comparte la URL

**Opción rápida**: ngrok
```powershell
.\start-with-ngrok.ps1
```

**Documentación completa**: Lee `COMPARTIR_SIN_DOCKER.md`

---

## 📝 Resumen

1. ✅ Archivos Docker ya creados (`Dockerfile`, `docker-compose.yml`, etc.)
2. ⏳ Pendiente: Actualizar WSL con permisos admin
3. ⏳ Pendiente: Reiniciar Docker Desktop
4. ⏳ Pendiente: Probar `docker-compose up -d`

**Cuando tengas permisos de admin**, sigue esta guía y Docker funcionará. 🐳

---

¿Dudas? Consulta la documentación oficial:
- Docker Desktop: https://docs.docker.com/desktop/
- WSL 2: https://docs.microsoft.com/en-us/windows/wsl/
