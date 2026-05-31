# Usamos una imagen liviana de Python
FROM python:3.9-slim

# Directorio de trabajo
WORKDIR /app

# Copiamos e instalamos dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY . .

# Comando para ejecutar la app
CMD ["python", "main.py"]
# ... tus pasos anteriores (FROM python, COPY requirements, etc.) ...

# Asegúrate de que gunicorn esté en tu requirements.txt o instálalo aquí
RUN pip install gunicorn

# Cambiamos el comando de ejecución:
# --workers 4: Permite atender a 4 jueces/dispositivos en simultáneo total
# --timeout 120: Da tiempo extra si una imagen es muy pesada
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "--timeout", "120", "main:app"]
