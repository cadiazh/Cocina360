# Usa una imagen base de Python ligera basada en Debian Bullseye (estable)
FROM python:3.11-slim-bullseye

# Instala dependencias del sistema necesarias para reportlab y xhtml2pdf (para renderizado de PDFs)
RUN apt-get update && apt-get install -y \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo de requisitos y instala dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código del proyecto
COPY . .

# Expone el puerto 8000 (puerto por defecto de Django)
EXPOSE 8080

# Comando para ejecutar el servidor (para desarrollo; en producción usa Gunicorn)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]