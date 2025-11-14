FROM tensorflow/tensorflow:2.20.0

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH \
    PORT=5000

WORKDIR /app

# Copiar requirements (sin tensorflow) e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Crear usuario no-root y dar permisos a uploads
RUN useradd -m -u 1000 appuser \
    && mkdir -p static/uploads \
    && chown -R appuser:appuser /app/static/uploads

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/public_model_status')" || exit 1

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "2", "--timeout", "300", "--preload", "--access-logfile", "-", "--error-logfile", "-"]
