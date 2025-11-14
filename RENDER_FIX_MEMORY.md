# 🔧 Solución a Worker Timeout y Out-of-Memory en Render

## ❌ Problema
Los logs mostraban:
```
[CRITICAL] WORKER TIMEOUT (pid:XX)
[ERROR] Worker (pid:XX) was sent SIGKILL! Perhaps out of memory?
```

Esto ocurre porque **cada worker de Gunicorn carga TensorFlow y el modelo independientemente**, excediendo los 512MB de RAM del tier gratuito de Render.

## ✅ Cambios Realizados

### 1. **Procfile Optimizado**
```bash
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 1 --timeout 120 --preload --max-requests 1000 --max-requests-jitter 50
```

**Mejoras:**
- `--preload`: Carga el modelo UNA sola vez antes de crear workers (comparten memoria)
- `--threads 1`: Reduce overhead de threads
- `--timeout 120`: Timeout de 2 minutos (suficiente para cargar TensorFlow)
- `--max-requests 1000`: Recicla workers para prevenir memory leaks

### 2. **requirements.txt - tensorflow-cpu**
```
tensorflow-cpu==2.15.0
```
**Beneficio:** Reduce uso de memoria de ~400MB a ~200MB (50% menos)

### 3. **Variables de Entorno TensorFlow**
Añadidas a `app.py`:
```python
_os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force CPU
_os.environ['OMP_NUM_THREADS'] = '1'
_os.environ['TF_NUM_INTEROP_THREADS'] = '1'
_os.environ['TF_NUM_INTRAOP_THREADS'] = '1'
```
**Beneficio:** Limita threads y fuerza uso de CPU (no GPU)

## 📋 Pasos para Desplegar

### Opción A: Desde la UI de Render
1. Ve a tu servicio en Render Dashboard
2. Haz clic en **"Manual Deploy"** → **"Clear build cache & deploy"**
3. Espera ~3-5 minutos (primera carga de TensorFlow es lenta)
4. Verifica en los logs que veas:
   ```
   [INFO] TensorFlow configurado con límites de memoria
   [INFO] Modelo recargado desde garbage_model.h5
   ```

### Opción B: Push a Git (automático)
```bash
git add .
git commit -m "Fix: Optimizado para Render (preload + tensorflow-cpu)"
git push origin main
```

## 🔍 Verificación Post-Deploy

### Logs Saludables
Deberías ver esto SIN timeouts:
```
[INFO] Booting worker with pid: XX
[INFO] TensorFlow configurado con límites de memoria
[INFO] Modelo recargado desde garbage_model.h5
```

### Logs Problemáticos (si continúan)
Si aún ves `WORKER TIMEOUT`, considera:

1. **Upgrade a plan pagado** (512MB → 2GB RAM)
2. **Usar modelo más ligero**:
   ```bash
   # En tu máquina local, reduce el modelo
   python
   >>> from tensorflow import keras
   >>> model = keras.models.load_model('garbage_model.h5')
   >>> model.save('garbage_model_lite.h5', include_optimizer=False)
   ```
   Edita `app.py`:
   ```python
   MODEL_PATH = 'garbage_model_lite.h5'
   ```

## 🚀 Monitoreo

### Ver logs en tiempo real:
```bash
# Desde terminal (necesitas Render CLI)
render logs -t <service-name>
```

### Desde la web:
https://dashboard.render.com → Tu servicio → Logs

## 💡 Consideraciones Adicionales

### Si el modelo es muy grande (>50MB):
Considera usar **Render Disks** para almacenar el modelo:
1. Crea un Render Disk en el dashboard
2. Monta en `/opt/render/project/models`
3. Actualiza `MODEL_PATH` en `app.py`

### Para mejorar velocidad de arranque:
Añade a `.slugignore` (si usas Heroku-style buildpack):
```
dataset/
*.md
test_*.py
```

## ⚠️ Limitaciones del Free Tier
- **512MB RAM**: Suficiente para tensorflow-cpu + modelo pequeño (<30MB)
- **Cold starts**: Si no hay tráfico por 15 min, el servicio se duerme
- **Spin-up time**: Primera petición puede tardar 30-60s

## 📊 Uso de Memoria Estimado
| Componente | Memoria |
|------------|---------|
| Python runtime | ~50MB |
| Flask + deps | ~30MB |
| TensorFlow-CPU | ~180MB |
| Modelo .h5 | ~20-50MB |
| **Total** | **~280-310MB** ✅ |

Con margen de seguridad en 512MB del free tier.

---

**Última actualización:** 2025-11-14  
**Versión TensorFlow:** 2.15.0 (CPU)  
**Gunicorn:** 21.2.0
