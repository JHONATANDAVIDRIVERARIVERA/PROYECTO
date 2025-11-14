# Multi-stage build para optimizar tamaño de imagen
FROM python:3.11-slim as builder

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema necesarias para TensorFlow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements y instalar dependencias
COPY requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt

# Etapa final - imagen ligera
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH \
    PORT=5000

# Instalar dependencias mínimas del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad (opcional pero recomendado)
RUN useradd -m -u 1000 appuser

# Crear directorio de trabajo
WORKDIR /app

# Copiar dependencias de Python desde builder
COPY --from=builder /root/.local /root/.local

# Copiar código de la aplicación
COPY --chown=appuser:appuser . .

# Crear directorio para uploads si no existe
RUN mkdir -p static/uploads && chown -R appuser:appuser static/uploads

# Cambiar a usuario no-root
USER appuser

# Exponer puerto
EXPOSE 5000

# Healthcheck para verificar que la app está funcionando
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/public_model_status')" || exit 1

# Comando de inicio con gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "2", "--timeout", "300", "--preload", "--access-logfile", "-", "--error-logfile", "-"]
