# Cocina 360 - Guía de Instalación

Sigue estos pasos para ejecutar **Cocina 360** correctamente en tu equipo.

---

## Requisitos previos

Antes de comenzar, asegúrate de tener instalado lo siguiente:

- **Python 3.12 o superior**  
  Descárgalo desde el sitio oficial:  
  [https://www.python.org/downloads/](https://www.python.org/downloads/](https://www.python.org/downloads/release/python-3128/)

- **pip** (el instalador de paquetes de Python)  
  Normalmente viene incluido con Python. Puedes verificarlo ejecutando `pip --version` en la terminal.

---

## Pasos de instalación

### 1. Descargar el proyecto

- Accede al repositorio de GitHub de **Cocina 360**  
  *https://github.com/cadiazh/Cocina360*  
- Haz clic en el botón verde **"Code"** y selecciona **"Download ZIP"**.  
- Extrae el contenido en una carpeta de tu preferencia.

---

### 2. Preparar el directorio del proyecto

- (Opcional pero recomendado) Crea una carpeta llamada `cocina360` en tu escritorio y mueve dentro la carpeta extraída.  
- Abre una terminal o consola y navega hasta la carpeta del proyecto.  
- Copia la ruta completa de la carpeta.

Ejemplo en Windows:

```bash
cd C:\Users\tu_usuario\Desktop\cocina360\Cocina360
```
## 🚀 Instrucciones de instalación y ejecución

### 3. Instalar las dependencias
Instala los paquetes necesarios con:

```bash
pip install -r requirements.txt
```

### 4. Aplicar las migraciones de la base de datos
Configura la base de datos ejecutando:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Ejecutar el servidor de desarrollo
Inicia el servidor de Django con:

```bash
python manage.py runserver
```

### 6. Abrir la aplicación web
Abre tu navegador y visita:

```bash
http://localhost:8000/
```
