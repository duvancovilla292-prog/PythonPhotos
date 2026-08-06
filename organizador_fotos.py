import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS

# 1. Diccionario para renombrar los meses a español
MESES_ESPAÑOL = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

def extraer_fecha_de_nombre(nombre_archivo):
    """
    Busca patrones de fecha tipo YYYYMMDD en el nombre del archivo
    (común en fotos de WhatsApp como IMG-20241024-WA0047.jpg o VID-20240711-WA0071.mp4).
    """
    # Expresión regular para secuencias de 8 dígitos (Año: 1990-2099, Mes: 01-12, Día: 01-31)
    patron = r'(19[9\d]|20[0-9]\d)(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])'
    coincidencia = re.search(patron, nombre_archivo)
    
    if coincidencia:
        ano_str, mes_str, dia_str = coincidencia.groups()
        try:
            return datetime(int(ano_str), int(mes_str), int(dia_str))
        except ValueError:
            pass
            
    # Patrón alternativo con separadores (ej: 2024-10-24 o 2024_10_24)
    patron_separado = r'(19[9\d]|20[0-9]\d)[-_\.](0[1-9]|1[0-2])[-_\.](0[1-9]|[12]\d|3[01])'
    coincidencia_sep = re.search(patron_separado, nombre_archivo)
    if coincidencia_sep:
        ano_str, mes_str, dia_str = coincidencia_sep.groups()
        try:
            return datetime(int(ano_str), int(mes_str), int(dia_str))
        except ValueError:
            pass

    return None

def obtener_fecha_archivo(ruta_archivo):
    """
    Jerarquía de extracción de fecha:
    1. Nombre del archivo (WhatsApp, capturas, etc.)
    2. Metadatos EXIF
    3. Fecha de modificación del sistema
    """
    # 1. Primer intento: verificar el nombre del archivo
    fecha_nombre = extraer_fecha_de_nombre(ruta_archivo.name)
    if fecha_nombre:
        return fecha_nombre

    # 2. Segundo intento: metadatos EXIF (imágenes)
    try:
        imagen = Image.open(ruta_archivo)
        info_exif = imagen._getexif()
        
        if info_exif:
            for etiqueta, valor in info_exif.items():
                nombre_etiqueta = TAGS.get(etiqueta, etiqueta)
                if nombre_etiqueta == 'DateTimeOriginal':
                    return datetime.strptime(valor, '%Y:%m:%d %H:%M:%S')
    except Exception:
        pass
    
    # 3. Tercer intento: fecha de modificación del sistema
    timestamp = os.path.getmtime(ruta_archivo)
    return datetime.fromtimestamp(timestamp)

def organizar_carpeta(ruta_objetivo):
    ruta_base = Path(ruta_objetivo)
    
    extensiones_fotos = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.heic', '.raw'}
    extensiones_videos = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.mts'}
    
    extensiones_validas = extensiones_fotos.union(extensiones_videos)
    
    archivos_movidos = 0

    for archivo in ruta_base.iterdir():
        if archivo.is_file() and archivo.suffix.lower() in extensiones_validas:
            
            # Extraer fecha con el nuevo orden de prioridades
            fecha = obtener_fecha_archivo(archivo)
            
            ano = str(fecha.year)
            mes = MESES_ESPAÑOL[fecha.month]
            dia = str(fecha.day)
            
            carpeta_destino = ruta_base / ano / mes / dia
            carpeta_destino.mkdir(parents=True, exist_ok=True)
            
            destino_final = carpeta_destino / archivo.name
            
            if destino_final.exists():
                print(f"[⚠️ Duplicado] El archivo {archivo.name} ya existe en el destino. Se omitió.")
                continue
                
            shutil.move(str(archivo), str(destino_final))
            
            es_video = archivo.suffix.lower() in extensiones_videos
            emoji = "📹 Video" if es_video else "📸 Foto"
            
            print(f"{emoji} movido: {archivo.name} -> {ano}/{mes}/{dia}/")
            archivos_movidos += 1

    print(f"\n🎉 ¡Proceso terminado! Se organizaron {archivos_movidos} archivos.")

if __name__ == "__main__":
    RUTA_DE_PRUEBA = "/home/camper/Escritorio/cumple nono 2026" 
    
    if os.path.exists(RUTA_DE_PRUEBA):
        print(f"Iniciando organización en: {RUTA_DE_PRUEBA}\n")
        organizar_carpeta(RUTA_DE_PRUEBA)
    else:
        print(f"❌ La ruta '{RUTA_DE_PRUEBA}' no existe. Por favor verifícala.")