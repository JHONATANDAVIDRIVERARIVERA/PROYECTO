# 🚀 Guía de Instalación de Docker

## Windows

### Paso 1: Descargar Docker Desktop
1. Ve a [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Descarga **Docker Desktop for Windows**
3. Ejecuta el instalador y sigue las instrucciones

### Paso 2: Configuración del Sistema
- **Windows 10/11**: Asegúrate de tener WSL 2 habilitado
- El instalador te pedirá reiniciar el sistema

### Paso 3: Verificar Instalación
Abre PowerShell y ejecuta:
```powershell
docker --version
docker-compose --version
```

### Paso 4: Configurar Recursos (Recomendado)
1. Abre Docker Desktop
2. Ve a **Settings** → **Resources**
3. Asigna al menos:
   - **CPU**: 2 cores
   - **Memory**: 4 GB
   - **Swap**: 1 GB

---

## Linux (Ubuntu/Debian)

```bash
# Actualizar paquetes
sudo apt-get update

# Instalar dependencias
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Agregar clave GPG oficial de Docker
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Configurar repositorio
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Agregar usuario al grupo docker (evita usar sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verificar instalación
docker --version
docker compose version
```

---

## macOS

### Opción 1: Docker Desktop (Recomendado)
1. Ve a [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Descarga **Docker Desktop for Mac**
3. Arrastra Docker.app a Applications
4. Ejecuta Docker desde Applications

### Opción 2: Homebrew
```bash
brew install --cask docker
```

### Verificar Instalación
```bash
docker --version
docker-compose --version
```

---

## 🧪 Probar Docker

Una vez instalado, prueba con:

```bash
# Test simple
docker run hello-world

# Si funciona, verás un mensaje de confirmación
```

---

## 🔧 Siguientes Pasos

Una vez Docker esté instalado:

1. **Navega al proyecto**:
   ```bash
   cd C:\Users\Lenovo\Documents\GitHub\PROYECTO
   ```

2. **Construye y ejecuta la aplicación**:
   ```bash
   # Opción fácil: usa el script helper (Windows)
   .\docker-helper.ps1
   
   # O manualmente
   docker-compose up -d
   ```

3. **Accede a la aplicación**:
   - Abre tu navegador en: http://localhost:5000

4. **Para acceso desde otros dispositivos**:
   ```powershell
   # En PowerShell, obtén tu IP local
   ipconfig
   
   # Desde otro dispositivo en la misma red, accede a:
   # http://<TU_IP>:5000
   ```

---

## ❓ Problemas Comunes

### Windows: "WSL 2 installation is incomplete"
1. Abre PowerShell como Administrador
2. Ejecuta:
   ```powershell
   wsl --install
   wsl --set-default-version 2
   ```
3. Reinicia el sistema

### "Docker daemon is not running"
- Asegúrate de que Docker Desktop esté ejecutándose
- Revisa la bandeja del sistema (system tray)

### Permiso denegado (Linux)
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Puerto 5000 en uso
```bash
# Cambiar el puerto en docker-compose.yml
# De: "5000:5000"
# A:  "8080:5000"
```

---

## 📚 Recursos Adicionales

- [Documentación oficial de Docker](https://docs.docker.com/)
- [Docker Desktop troubleshooting](https://docs.docker.com/desktop/troubleshoot/overview/)
- [WSL 2 installation guide](https://docs.microsoft.com/en-us/windows/wsl/install)

---

**¿Listo?** Una vez instalado Docker, vuelve a `DOCKER_README.md` para construir y ejecutar la aplicación. 🐳
