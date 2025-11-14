# 🐳 Docker - Clasificador de Residuos

Esta guía te ayudará a ejecutar la aplicación usando Docker en cualquier computador o dispositivo.

## 📋 Requisitos

- **Docker** instalado ([Descargar Docker Desktop](https://www.docker.com/products/docker-desktop))
- **Docker Compose** (incluido en Docker Desktop)
- Al menos **2GB de RAM** disponible para el contenedor

## 🚀 Inicio Rápido

### Opción 1: Usar Docker Compose (Recomendado)

```bash
# 1. Clonar el repositorio (si aún no lo tienes)
git clone https://github.com/JHONATANDAVIDRIVERARIVERA/PROYECTO.git
cd PROYECTO

# 2. Construir y ejecutar
docker-compose up -d

# 3. Ver logs (opcional)
docker-compose logs -f

# 4. Acceder a la aplicación
# Abre tu navegador en: http://localhost:5000
```

### Opción 2: Usar Docker directamente

```bash
# 1. Construir la imagen
docker build -t garbage-classifier .

# 2. Ejecutar el contenedor
docker run -d \
  -p 5000:5000 \
  --name garbage-classifier-app \
  garbage-classifier

# 3. Ver logs
docker logs -f garbage-classifier-app
```

## 🔧 Comandos Útiles

### Detener la aplicación
```bash
# Con docker-compose
docker-compose down

# Con docker
docker stop garbage-classifier-app
```

### Reiniciar la aplicación
```bash
# Con docker-compose
docker-compose restart

# Con docker
docker restart garbage-classifier-app
```

### Ver estado del modelo
```bash
# Verificar que el modelo se cargó correctamente
curl http://localhost:5000/public_model_status

# O en PowerShell
Invoke-RestMethod -Uri "http://localhost:5000/public_model_status"
```

### Acceder al contenedor (debugging)
```bash
# Abrir shell dentro del contenedor
docker exec -it garbage-classifier-app bash
```

### Ver uso de recursos
```bash
# Monitorear CPU y memoria
docker stats garbage-classifier-app
```

## 🌐 Acceso desde Otros Dispositivos

Para acceder desde otros dispositivos en la misma red:

1. Encuentra la IP de tu computador:
   ```bash
   # Windows (PowerShell)
   ipconfig
   
   # Linux/Mac
   ifconfig
   ```

2. Desde otro dispositivo, abre el navegador y accede a:
   ```
   http://<IP_DE_TU_COMPUTADOR>:5000
   ```

**Ejemplo:** Si tu IP es `192.168.1.100`, accede a `http://192.168.1.100:5000`

## 📦 Personalización

### Cambiar el puerto

Edita `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # Cambia 8080 por el puerto que prefieras
```

### Ajustar workers de Gunicorn

Edita `Dockerfile`, línea CMD:
```dockerfile
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "2", ...]
```

### Limitar memoria del contenedor

```bash
docker run -d \
  -p 5000:5000 \
  --memory="2g" \
  --name garbage-classifier-app \
  garbage-classifier
```

## 🐛 Troubleshooting

### El contenedor no arranca
```bash
# Ver logs detallados
docker logs garbage-classifier-app

# Verificar si el puerto está en uso
# Windows
netstat -ano | findstr :5000

# Linux/Mac
lsof -i :5000
```

### Error de memoria (OOM)
- Aumenta la memoria asignada a Docker Desktop (Configuración → Resources → Memory)
- Reduce el número de workers en el Dockerfile

### Modelo no se carga
```bash
# Verificar que los archivos del modelo están en la imagen
docker exec -it garbage-classifier-app ls -lh garbage_model.h5 class_indices.json

# Forzar recarga del modelo
curl http://localhost:5000/reload_model
```

### No puedo acceder desde otro dispositivo
- Verifica que el firewall permita conexiones al puerto 5000
- Confirma que ambos dispositivos están en la misma red
- En Windows, ejecuta como Administrador:
  ```powershell
  New-NetFirewallRule -DisplayName "Flask App" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
  ```

## 📊 Monitoreo y Mantenimiento

### Ver estado de salud
```bash
docker inspect --format='{{json .State.Health}}' garbage-classifier-app | python -m json.tool
```

### Limpiar recursos no usados
```bash
# Eliminar contenedores detenidos
docker container prune

# Eliminar imágenes sin usar
docker image prune

# Limpieza completa (cuidado!)
docker system prune -a
```

## 🔐 Producción

Para desplegar en producción:

1. **Usa HTTPS** con un reverse proxy (nginx, Traefik)
2. **Variables de entorno** para configuración sensible
3. **Volúmenes persistentes** para uploads y logs
4. **Límites de recursos** para evitar saturar el servidor
5. **Backup regular** del modelo y configuración

### Ejemplo con nginx reverse proxy

```yaml
# Agregar a docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - garbage-classifier
```

## 📝 Notas

- El primer arranque puede tardar 30-60 segundos mientras TensorFlow carga el modelo
- El healthcheck verifica cada 30s que la app responde
- Los logs se muestran en stdout/stderr para facilitar debugging
- El contenedor usa un usuario no-root por seguridad

## 🆘 Soporte

Si encuentras problemas:
1. Revisa los logs: `docker-compose logs -f`
2. Verifica el estado del modelo: `/public_model_status`
3. Prueba el endpoint de diagnóstico: `/whoami`
4. Consulta los issues en GitHub

---

**¿Listo para usar?** Ejecuta `docker-compose up -d` y abre http://localhost:5000 🚀
