# Imagen base
FROM python:3.10-slim

# Evita que Python genere archivos .pyc
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Crea el directorio del proyecto
WORKDIR /app

# Instala dependencias del sistema necesarias para reportlab y pillow
RUN apt-get update && apt-get install -y \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia el requirements
COPY requirements.txt /app/

# Instala dependencias Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copia todo el proyecto
COPY . /app/

# Expone el puerto
EXPOSE 8080

# Comando por defecto
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
