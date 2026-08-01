import os
import shutil
from pathlib import Path

def extraer_archivos(ruta_origen):
    ruta_base = Path(ruta_origen).resolve()
    
    # Extensiones de fotos y videos permitidos
    extensiones_fotos = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.heic', '.raw'}
    extensiones_videos = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.mts'}
    extensiones_validas = extensiones_fotos.union(extensiones_videos)
    
    archivos_extraidos = 0
    
    # Recorrer la carpeta base y TODAS sus subcarpetas
    for raiz, subcarpetas, archivos in os.walk(ruta_base):
        for nombre_archivo in archivos:
            path_archivo = Path(raiz) / nombre_archivo
            
            # Si el archivo ya está directamente en la raíz, lo dejamos intacto
            if path_archivo.parent == ruta_base:
                continue
                
            # Verificar si es una foto o video válido
            if path_archivo.suffix.lower() in extensiones_validas:
                destino_final = ruta_base / nombre_archivo
                
                # Manejo de duplicados al mover a la raíz (agrega _1, _2, etc.)
                contador = 1
                while destino_final.exists():
                    nombre_sin_ext = path_archivo.stem
                    extension = path_archivo.suffix
                    destino_final = ruta_base / f"{nombre_sin_ext}_{contador}{extension}"
                    contador += 1
                
                # Mover el archivo a la carpeta raíz
                shutil.move(str(path_archivo), str(destino_final))
                
                es_video = path_archivo.suffix.lower() in extensiones_videos
                tipo = "📹 Video" if es_video else "📸 Foto"
                
                print(f"{tipo} extraído: {path_archivo.relative_to(ruta_base)} -> {destino_final.name}")
                archivos_extraidos += 1
                
    print(f"\n🎉 ¡Extracción completada! Se sacaron {archivos_extraidos} fotos y videos a la raíz.")

if __name__ == "__main__":
    # Ajusta esta ruta a la carpeta donde quieras hacer la extracción
    RUTA_OBJETIVO = "/home/camper/Escritorio/mom" 
    
    if os.path.exists(RUTA_OBJETIVO):
        print(f"Iniciando extracción en: {RUTA_OBJETIVO}\n")
        extraer_archivos(RUTA_OBJETIVO)
    else:
        print(f"❌ La ruta '{RUTA_OBJETIVO}' no existe. Por favor verifícala.")