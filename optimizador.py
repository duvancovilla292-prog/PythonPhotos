import os
import re
import sys
import time
import shutil
import subprocess
from pathlib import Path
from PIL import Image

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
# Puedes dejar la ruta configurada o dejarla vacía "" para ingresarla por consola
RUTA_A_OPTIMIZAR = "/media/camper/CIEL3/Box/Ciel0/fotos/familia/Rolón Florez/Primos/heidy/2026/Mayo"

# Calidad de imágenes (82-85 es el punto óptimo sin pérdida visual)
CALIDAD_JPEG = 82
CALIDAD_WEBP = 85

# Calidad y velocidad de video FFmpeg
CRF_VIDEO = 26
PRESET_VIDEO = 'ultrafast'  # Máxima velocidad de codificación en móviles

EXT_IMAGENES = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
EXT_VIDEOS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.mts'}
# ==============================================================================

def formatear_tamano(bytes_num):
    """Convierte bytes a formato legible (KB, MB, GB)."""
    for unidad in ['B', 'KB', 'MB', 'GB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.2f} {unidad}"
        bytes_num /= 1024.0
    return f"{bytes_num:.2f} TB"

def dibujar_barra(porcentaje, longitud=20):
    """Genera una barra visual de progreso [████████░░░░]"""
    porcentaje = min(100.0, max(0.0, porcentaje))
    llenos = int(longitud * porcentaje // 100)
    barra = '█' * llenos + '░' * (longitud - llenos)
    return f"[{barra}] {porcentaje:.1f}%"

def verificar_ffmpeg():
    """Verifica si FFmpeg está instalado de forma nativa en el sistema."""
    return shutil.which('ffmpeg') is not None

def obtener_duracion_video(ruta_path):
    """Obtiene la duración total del video en segundos mediante FFmpeg."""
    comando = ['ffmpeg', '-i', str(ruta_path)]
    try:
        res = subprocess.run(comando, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, errors='ignore')
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", res.stderr)
        if match:
            h, m, s, ms = match.groups()
            return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 100.0
    except Exception:
        pass
    return None

def mostrar_lista_detallada(archivos_imgs, archivos_vids):
    """
    Muestra la lista decorada de archivos ordenados de mayor a menor peso,
    separando categorías con barras visibles y sumatorias independientes.
    """
    # Ordenar de mayor a menor tamaño
    imgs_ordenadas = sorted(archivos_imgs, key=lambda p: p.stat().st_size, reverse=True)
    vids_ordenados = sorted(archivos_vids, key=lambda p: p.stat().st_size, reverse=True)

    peso_imgs = sum(p.stat().st_size for p in imgs_ordenadas)
    peso_vids = sum(p.stat().st_size for p in vids_ordenados)
    peso_total_global = peso_imgs + peso_vids

    print("\n" + "═"*85)
    print("📋 LISTADO DETALLADO DE ARCHIVOS (ORDENADOS DE MAYOR A MENOR TAMAÑO)")
    print("═"*85)

    # SECCIÓN 1: IMÁGENES
    print(f"\n🖼️  SECCIÓN IMÁGENES ({len(imgs_ordenadas)} archivos encontradas)")
    print("─"*85)
    if imgs_ordenadas:
        for idx, p in enumerate(imgs_ordenadas, 1):
            tamano_str = formatear_tamano(p.stat().st_size)
            print(f" {idx:3d}. {p.name:<55} │ Peso: {tamano_str:>10}")
    else:
        print(" (No se encontraron imágenes en esta ubicación)")
    print("─"*85)
    print(f" 📊 SUMA TOTAL SOLO IMÁGENES : {formatear_tamano(peso_imgs)}")

    # LÍNEA VISIBLE DE SEPARACIÓN ENTRE IMÁGENES Y VIDEOS
    print("\n" + "█"*85)
    print("█" * 35 + " 🎥  SECCIÓN VIDEOS " + "█" * 30)
    print("█"*85)

    # SECCIÓN 2: VIDEOS
    print(f"\n🎥  SECCIÓN VIDEOS ({len(vids_ordenados)} archivos encontrados)")
    print("─"*85)
    if vids_ordenados:
        for idx, p in enumerate(vids_ordenados, 1):
            tamano_str = formatear_tamano(p.stat().st_size)
            print(f" {idx:3d}. {p.name:<55} │ Peso: {tamano_str:>10}")
    else:
        print(" (No se encontraron videos en esta ubicación)")
    print("─"*85)
    print(f" 📊 SUMA TOTAL SOLO VIDEOS   : {formatear_tamano(peso_vids)}")

    # RESUMEN GLOBAL FINAL
    print("\n" + "═"*85)
    print(f"📦 SUMATORIA GENERAL ACUMULADA (IMÁGENES + VIDEOS): {formatear_tamano(peso_total_global)}")
    print("═"*85 + "\n")

def optimizar_imagen(ruta_path):
    """Optimiza una imagen manteniendo su ubicación, resolución y nombre exacto."""
    tamano_original = ruta_path.stat().st_size
    temp_path = ruta_path.with_suffix(f".tmp_{time.time_ns()}{ruta_path.suffix}")
    ext = ruta_path.suffix.lower()

    try:
        with Image.open(ruta_path) as img:
            exif_data = img.info.get('exif')
            kwargs = {}
            if exif_data:
                kwargs['exif'] = exif_data

            if ext in {'.jpg', '.jpeg'}:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(temp_path, format="JPEG", quality=CALIDAD_JPEG, optimize=True, progressive=True, **kwargs)
            elif ext == '.png':
                img.save(temp_path, format="PNG", optimize=True, **kwargs)
            elif ext == '.webp':
                img.save(temp_path, format="WEBP", quality=CALIDAD_WEBP, method=6, **kwargs)
            else:
                return None

        tamano_nuevo = temp_path.stat().st_size

        if tamano_nuevo < tamano_original:
            temp_path.replace(ruta_path)
            ahorro_bytes = tamano_original - tamano_nuevo
            pct_ahorro = (ahorro_bytes / tamano_original) * 100
            return (tamano_original, tamano_nuevo, pct_ahorro)
        else:
            if temp_path.exists():
                temp_path.unlink()
            return (tamano_original, tamano_original, 0.0)

    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        print(f"\n  ❌ Error procesando imagen {ruta_path.name}: {e}")
        return None

def optimizar_video(ruta_path):
    """
    Optimiza un video utilizando FFmpeg a alta velocidad (ultrafast + multihilo).
    """
    tamano_original = ruta_path.stat().st_size
    temp_mkv = ruta_path.with_suffix(f".tmp_{time.time_ns()}.mkv")
    duracion_total = obtener_duracion_video(ruta_path)
    
    comando = [
        'ffmpeg', '-y',
        '-threads', '0',               # Multihilo activo (100% CPU)
        '-i', str(ruta_path),
        '-vcodec', 'libx264',
        '-crf', str(CRF_VIDEO),
        '-preset', PRESET_VIDEO,        # Velocidad ultrafast
        '-acodec', 'aac',
        '-b:a', '128k',
        '-progress', 'pipe:1',
        '-nostats',
        str(temp_mkv)
    ]

    try:
        proc = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        t_inicio_vid = time.time()
        
        while True:
            linea = proc.stdout.readline()
            if not linea and proc.poll() is not None:
                break
            
            if "out_time_us=" in linea:
                try:
                    us_str = linea.split("=")[1].strip()
                    if us_str.isdigit():
                        seg_actuales = int(us_str) / 1_000_000.0
                        
                        pct_progreso = (seg_actuales / duracion_total * 100) if duracion_total else 0.0
                        t_transcurrido = time.time() - t_inicio_vid
                        peso_actual = temp_mkv.stat().st_size if temp_mkv.exists() else 0
                        vel_bytes_sec = (peso_actual / t_transcurrido) if t_transcurrido > 0 else 0
                        
                        barra_str = dibujar_barra(pct_progreso, longitud=18)
                        vel_str = formatear_tamano(vel_bytes_sec)
                        peso_str = formatear_tamano(peso_actual)
                        orig_str = formatear_tamano(tamano_original)
                        
                        sys.stdout.write(f"\r   └─ ⚡ {barra_str} | Vel: {vel_str}/s | Prog: {peso_str} / {orig_str}   ")
                        sys.stdout.flush()
                except Exception:
                    pass

        proc.wait()
        sys.stdout.write("\n")
        sys.stdout.flush()

        if proc.returncode != 0 or not temp_mkv.exists():
            if temp_mkv.exists():
                temp_mkv.unlink()
            return None

        tamano_nuevo = temp_mkv.stat().st_size

        if tamano_nuevo < tamano_original:
            destino_final = ruta_path.with_suffix('.mkv')
            
            if ruta_path != destino_final and ruta_path.exists():
                ruta_path.unlink()

            temp_mkv.replace(destino_final)
            ahorro_bytes = tamano_original - tamano_nuevo
            pct_ahorro = (ahorro_bytes / tamano_original) * 100
            return (tamano_original, tamano_nuevo, pct_ahorro)
        else:
            if temp_mkv.exists():
                temp_mkv.unlink()
            return (tamano_original, tamano_original, 0.0)

    except Exception as e:
        if temp_mkv.exists():
            temp_mkv.unlink()
        print(f"\n  ❌ Error procesando video {ruta_path.name}: {e}")
        return None

def procesar_directorio(ruta_base_str):
    ruta_base = Path(ruta_base_str).expanduser().resolve()

    if not ruta_base.exists():
        print(f"❌ La ruta '{ruta_base}' no existe. Revisa los permisos en Termux.")
        return

    print(f"\n🔍 Fase 1: Escaneando archivos en '{ruta_base}'...")
    
    archivos_imagenes = []
    archivos_videos = []

    for raiz, _, archivos in os.walk(ruta_base):
        for nombre in archivos:
            p = Path(raiz) / nombre
            ext = p.suffix.lower()
            if ext in EXT_IMAGENES:
                archivos_imagenes.append(p)
            elif ext in EXT_VIDEOS:
                archivos_videos.append(p)

    peso_imgs_inicial_bruto = sum(p.stat().st_size for p in archivos_imagenes)
    peso_vids_inicial_bruto = sum(p.stat().st_size for p in archivos_videos)

    total_imgs_bruto = len(archivos_imagenes)
    total_vids_bruto = len(archivos_videos)

    if total_imgs_bruto == 0 and total_vids_bruto == 0:
        print("⚠️ No se encontraron imágenes ni videos para procesar.")
        return

    # Bucle del Menú Principal
    while True:
        print("\n" + "="*80)
        print("📊 RESUMEN DEL PRE-ESCANEO:")
        print(f" • Imágenes encontradas : {total_imgs_bruto} archivos ({formatear_tamano(peso_imgs_inicial_bruto)})")
        print(f" • Videos encontrados   : {total_vids_bruto} archivos ({formatear_tamano(peso_vids_inicial_bruto)})")
        print("="*80)
        print("👉 MENÚ PRINCIPAL:")
        print(" [1] Solo Imágenes")
        print(" [2] Solo Videos")
        print(" [3] Ambos (Imágenes y Videos)")
        print(" [4] Ver lista detallada de archivos (Ordenados por peso + Sumas)")
        print(" [0] 🛑 CANCELAR Y SALIR")
        
        opcion_tipo = input("\nElige una opción (0, 1, 2, 3 o 4): ").strip()

        if opcion_tipo == '0':
            print("\n🚫 Operación cancelada por el usuario. Saliendo sin modificar nada.")
            return

        if opcion_tipo == '4':
            mostrar_lista_detallada(archivos_imagenes, archivos_videos)
            continue

        procesar_imgs = opcion_tipo in {'1', '3'}
        procesar_vids = opcion_tipo in {'2', '3'}

        if procesar_imgs or procesar_vids:
            break
        else:
            print("❌ Opción inválida. Intenta nuevamente.")

    # Menú 2: Filtro por peso
    while True:
        print("\n👉 ¿Deseas filtrar por peso de archivo?")
        print(" [1] Procesar TODOS los archivos")
        print(" [2] Procesar solo archivos MAYORES a cierto peso (en MB)")
        print(" [0] 🛑 CANCELAR Y SALIR")
        
        opcion_filtro = input("\nElige una opción (0, 1 o 2): ").strip()

        if opcion_filtro == '0':
            print("\n🚫 Operación cancelada por el usuario. Saliendo sin modificar nada.")
            return

        umbral_bytes = 0
        if opcion_filtro == '2':
            try:
                mb_min = float(input("\n👉 Ingresa el peso mínimo en MB (ej: 5 o 10.5): ").strip())
                umbral_bytes = mb_min * 1024 * 1024
                break
            except ValueError:
                print("❌ Entrada numérica no válida. Intenta de nuevo.")
        elif opcion_filtro == '1':
            break
        else:
            print("❌ Opción inválida. Intenta de nuevo.")

    # Aplicar filtros por peso
    imgs_filtradas = [p for p in archivos_imagenes if p.stat().st_size >= umbral_bytes] if procesar_imgs else []
    vids_filtrados = [p for p in archivos_videos if p.stat().st_size >= umbral_bytes] if procesar_vids else []

    total_imgs = len(imgs_filtradas)
    total_vids = len(vids_filtrados)
    peso_imgs_inicial = sum(p.stat().st_size for p in imgs_filtradas)
    peso_vids_inicial = sum(p.stat().st_size for p in vids_filtrados)

    print("\n" + "="*80)
    print(f"📊 SELECCIÓN FINAL A PROCESAR (Mayores a {umbral_bytes / (1024*1024):.2f} MB):")
    print(f" • Imágenes a procesar : {total_imgs} archivos ({formatear_tamano(peso_imgs_inicial)})")
    print(f" • Videos a procesar   : {total_vids} archivos ({formatear_tamano(peso_vids_inicial)})")
    print("="*80 + "\n")

    if total_imgs == 0 and total_vids == 0:
        print("⚠️ No hay archivos que cumplan con los criterios seleccionados.")
        return

    if procesar_vids and total_vids > 0:
        if not verificar_ffmpeg():
            print("\n❌ ERROR: FFmpeg no está instalado en Termux.")
            print("👉 Ejecuta en la consola: pkg install ffmpeg -y")
            return

    t_inicio = time.time()
    
    bytes_ahorrados_imgs = 0
    peso_imgs_final = 0
    bytes_ahorrados_vids = 0
    peso_vids_final = 0

    # --------------------------------------------------------------------------
    # PROCESAR IMÁGENES
    # --------------------------------------------------------------------------
    if total_imgs > 0:
        print("🖼️ --- OPTIMIZANDO IMÁGENES ---")
        for idx, img_path in enumerate(imgs_filtradas, 1):
            pct = (idx / total_imgs) * 100
            res = optimizar_imagen(img_path)
            if res:
                t_orig, t_nuevo, pct_arch = res
                peso_imgs_final += t_nuevo
                if pct_arch > 0:
                    bytes_ahorrados_imgs += (t_orig - t_nuevo)
                    print(f"[{idx}/{total_imgs}] ({pct:.1f}%) 🖼️ {img_path.name} | {formatear_tamano(t_orig)} ➔ {formatear_tamano(t_nuevo)} (-{pct_arch:.1f}%)")
                else:
                    print(f"[{idx}/{total_imgs}] ({pct:.1f}%) ℹ️ {img_path.name} | Ya optimizado ({formatear_tamano(t_orig)})")

    # --------------------------------------------------------------------------
    # PROCESAR VIDEOS
    # --------------------------------------------------------------------------
    if total_vids > 0:
        print("\n🎥 --- OPTIMIZANDO VIDEOS (MODO ALTA VELOCIDAD) ---")
        for idx, vid_path in enumerate(vids_filtrados, 1):
            pct = (idx / total_vids) * 100
            print(f"[{idx}/{total_vids}] ({pct:.1f}%) ⏳ Procesando: {vid_path.name}")
            res = optimizar_video(vid_path)
            if res:
                t_orig, t_nuevo, pct_arch = res
                peso_vids_final += t_nuevo
                if pct_arch > 0:
                    bytes_ahorrados_vids += (t_orig - t_nuevo)
                    print(f"   └─ 🎥 ¡Optimizado!: {vid_path.stem}.mkv | {formatear_tamano(t_orig)} ➔ {formatear_tamano(t_nuevo)} (-{pct_arch:.1f}%)")
                else:
                    print(f"   └─ ℹ️ Sin cambios: {vid_path.name} | El video comprimido no era más liviano.")

    t_duracion = time.time() - t_inicio

    # --------------------------------------------------------------------------
    # REPORTE FINAL CONSOLIDADO
    # --------------------------------------------------------------------------
    print("\n" + "="*80)
    print("🎉 ¡PROCESO FINALIZADO CON ÉXITO!")
    print(f"⏱️ Tiempo total de ejecución : {t_duracion:.1f} segundos")
    print("="*80)

    if total_imgs > 0:
        pct_ahorro_imgs = (bytes_ahorrados_imgs / peso_imgs_inicial * 100) if peso_imgs_inicial > 0 else 0
        print("🖼️ IMÁGENES:")
        print(f" • Procesadas               : {total_imgs} archivos")
        print(f" • Peso inicial real        : {formatear_tamano(peso_imgs_inicial)}")
        print(f" • Peso final real          : {formatear_tamano(peso_imgs_final)}")
        print(f" • Reducción total          : -{pct_ahorro_imgs:.2f}% ({formatear_tamano(bytes_ahorrados_imgs)} ahorrados)")
        print("-" * 80)

    if total_vids > 0:
        pct_ahorro_vids = (bytes_ahorrados_vids / peso_vids_inicial * 100) if peso_vids_inicial > 0 else 0
        print("🎥 VIDEOS:")
        print(f" • Procesados               : {total_vids} archivos")
        print(f" • Peso inicial real        : {formatear_tamano(peso_vids_inicial)}")
        print(f" • Peso final real          : {formatear_tamano(peso_vids_final)}")
        print(f" • Reducción total          : -{pct_ahorro_vids:.2f}% ({formatear_tamano(bytes_ahorrados_vids)} ahorrados)")
        print("-" * 80)

    total_ahorrado_global = bytes_ahorrados_imgs + bytes_ahorrados_vids
    peso_global_inicial = peso_imgs_inicial + peso_vids_inicial
    peso_global_final = peso_imgs_final + peso_vids_final
    pct_global = (total_ahorrado_global / peso_global_inicial * 100) if peso_global_inicial > 0 else 0

    print(f"📦 AHORRO GLOBAL TOTAL: {formatear_tamano(peso_global_inicial)} ➔ {formatear_tamano(peso_global_final)} (-{pct_global:.2f}%)")
    print("="*80)

if __name__ == "__main__":
    ruta = RUTA_A_OPTIMIZAR.strip()
    if not ruta:
        ruta = input("👉 Ingresa la ruta de la carpeta a optimizar: ").strip().strip("'\"")
    
    procesar_directorio(ruta)
