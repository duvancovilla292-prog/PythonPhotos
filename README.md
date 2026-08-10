# 📸 Suite de Organización de Fotos y Videos

Herramienta automatizada en Python para extraer, centralizar y clasificar de forma limpia tus archivos multimedia (fotos y videos) en subcarpetas estructuradas por **Año/Mes/Día**.

---

## 🛠️ Archivos de la Suite

La suite se compone de dos scripts complementarios:

1. **`extractor.py`**:
   - Recorre recursivamente todas las subcarpetas existentes dentro de la ruta especificada.
   - Extrae únicamente fotos y videos sueltos y los centraliza en la raíz de la carpeta base.
   - Resuelve conflictos de nombres duplicados automáticamente añadiendo un sufijo numérico (`_1`, `_2`, etc.).

2. **`organizador_fotos.py`**:
   - Escanea la carpeta raíz y organiza de forma jerárquica cada elemento multimedia en la estructura: `CarpetaBase/Año/Mes/Día`.
   - **Manejo inteligente de fechas (Jerarquía de Prioridad):**
     1. **Nombre del archivo:** Detecta fechas en formato `AAAAMMDD` (típicas de descargas de WhatsApp como `IMG-20241024-WA0047.jpg` o `VID-20240711-WA0071.mp4`).
     2. **Metadatos EXIF:** Lee la fecha real de captura guardada en la cabecera de las fotos tomadas con cámara.
     3. **Fecha del sistema:** Usa la fecha de modificación/creación del archivo como respaldo si las anteriores no están disponibles.

---

## 📋 Requisitos Previos

- Tener instalado **Python 3.8+**.
- Tener la librería **Pillow** para lectura de metadatos de imágenes.

---

## 🚀 Paso a Paso de Uso

### Paso 1: Preparación del Entorno
Abre tu terminal y ubícate en el directorio donde guardaste los scripts y/o la carpeta de fotos que deseas procesar.

Instala la librería requerida ejecutando:
```bash
pip install Pillow
```

### Paso 2: Configurar las Rutas de Trabajo
Abre cada uno de los archivos Python con tu editor de código preferido y ajusta la variable con la ruta de la carpeta objetivo:

- En `extractor.py`: Modifica la variable `RUTA_OBJETIVO` (línea final dentro del bloque `__main__`).
- En `organizador_fotos.py`: Modifica la variable `RUTA_DE_PRUEBA` (alrededor de la línea 113).

*Ejemplo de ruta en Linux / macOS:* `/home/usuario/Imágenes/MiCarpetaDeFotos`  
*Ejemplo de ruta en Windows:* `C:/Usuarios/Usuario/Fotos/MiCarpetaDeFotos`

---

### Paso 3: Extracción de Subcarpetas (Paso Opcional pero Recomendado)
Si tus fotos están dispersas en múltiples subcarpetas desordenadas, ejecuta primero `extractor.py`. Este comando extraerá todo a la raíz de la carpeta sin perder ningún archivo.

### Paso 4: Organización por Fechas
Una vez centralizados los archivos en la raíz, ejecuta `organizador_fotos.py` para crear las subcarpetas por **Año**, **Mes** (en español) y **Día**, moviendo cada archivo a su ubicación final.

---

## 💻 Resumen de Comandos (En Orden de Ejecución)

```bash
# 1. Instalación de dependencias
pip install Pillow

# 2. Extraer fotos/videos de subcarpetas hacia la raíz
python extractor.py

# 3. Clasificar y organizar todo por Año/Mes/Día
python organizador_fotos.py
```
