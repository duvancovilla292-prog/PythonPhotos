import os
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

def obtener_fecha_archivo(ruta_archivo):
    """
    Intenta obtener la fecha EXIF si es una imagen;
    si no tiene EXIF o es un video, usa la fecha de modificación del archivo.
    """
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
    
    # Si es video o imagen sin EXIF, usamos la fecha de modificación del sistema
    timestamp = os.path.getmtime(ruta_archivo)
    return datetime.fromtimestamp(timestamp)

def organizar_carpeta(ruta_objetivo):
    ruta_base = Path(ruta_objetivo)
    
    # 2. Definir extensiones de fotos y videos
    extensiones_fotos = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.heic', '.raw'}
    extensiones_videos = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.mts'}
    
    # Unimos ambos conjuntos (solo fotos y videos)
    extensiones_validas = extensiones_fotos.union(extensiones_videos)
    
    archivos_movidos = 0

    # Iterar SOLO sobre los archivos que están en la raíz de la carpeta
    for archivo in ruta_base.iterdir():
        # Verifica que sea un archivo y que su extensión esté en las permitidas
        if archivo.is_file() and archivo.suffix.lower() in extensiones_validas:
            
            # Obtener la fecha del archivo
            fecha = obtener_fecha_archivo(archivo)
            
            ano = str(fecha.year)
            mes = MESES_ESPAÑOL[fecha.month]
            dia = str(fecha.day)
            
            # Crear la estructura de la ruta: CarpetaBase/Año/Mes/Día
            carpeta_destino = ruta_base / ano / mes / dia
            
            # Crear las subcarpetas si no existen
            carpeta_destino.mkdir(parents=True, exist_ok=True)
            
            # Definir la ruta final del archivo
            destino_final = carpeta_destino / archivo.name
            
            # Control de duplicados
            if destino_final.exists():
                print(f"[⚠️ Duplicado] El archivo {archivo.name} ya existe en el destino. Se omitió.")
                continue
                
            # Mover el archivo
            shutil.move(str(archivo), str(destino_final))
            
            # Identificar visualmente en la consola si fue foto o video
            es_video = archivo.suffix.lower() in extensiones_videos
            emoji = "📹 Video" if es_video else "📸 Foto"
            
            print(f"{emoji} movido: {archivo.name} -> {ano}/{mes}/{dia}/")
            archivos_movidos += 1

    print(f"\n🎉 ¡Proceso terminado! Se organizaron {archivos_movidos} archivos (fotos y videos).")

if __name__ == "__main__":
    # Ajusta aquí la ruta de tu carpeta
    RUTA_DE_PRUEBA = "/home/camper/Documentos/WAStatusSaver" 
    
    if os.path.exists(RUTA_DE_PRUEBA):
        print(f"Iniciando organización en: {RUTA_DE_PRUEBA}\n")
        organizar_carpeta(RUTA_DE_PRUEBA)
    else:
        print(f"❌ La ruta '{RUTA_DE_PRUEBA}' no existe. Por favor verifícala.")