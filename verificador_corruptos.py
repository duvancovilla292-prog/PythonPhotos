import os
import sys
import time
import zipfile
import concurrent.futures
from pathlib import Path
from PIL import Image

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
# Pon aquí la ruta a revisar o déjala vacía "" para ingresar por terminal.
RUTA_A_REVISAR = ""
# ==============================================================================

# Extensiones conocidas por categorías
EXT_IMAGENES = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff', '.ico'}
EXT_ZIP_BASED = {'.zip', '.docx', '.xlsx', '.pptx', '.jar', '.apk', '.epub', '.odt', '.ods'}
EXT_VIDEOS_AUDIO = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mp3', '.wav', '.flac', '.ogg', '.m4a'}

def verificar_integridad_archivo(ruta_str):
    """
    Verifica un archivo buscando errores de lectura en disco (I/O)
    y realizando validaciones de estructura según su formato.
    Retorna (es_corrupto, ruta, motivo).
    """
    path = Path(ruta_str)
    
    # 1. Verificar si el archivo está vacío (0 bytes)
    try:
        tamano = path.stat().st_size
        if tamano == 0:
            return True, str(path), "Archivo vacío (0 bytes)"
    except Exception as e:
        return True, str(path), f"Error de acceso/permisos: {e}"

    ext = path.suffix.lower()

    # 2. Validación específica por formato
    try:
        # A. Imágenes (PIL)
        if ext in EXT_IMAGENES:
            with Image.open(path) as img:
                img.verify()  # Verifica la estructura física del encabezado
            # Reabrir para probar la decodificación completa de píxeles
            with Image.open(path) as img:
                img.load()
            return False, str(path), None

        # B. Archivos comprimidos y documentos Office (.docx, .xlsx, .zip, etc.)
        elif ext in EXT_ZIP_BASED:
            with zipfile.ZipFile(path, 'r') as zf:
                primer_error = zf.testzip()
                if primer_error is not None:
                    return True, str(path), f"Estructura ZIP/Doc dañada (archivo interno corrupto: {primer_error})"
            return False, str(path), None

        # C. Documentos PDF (Encabezado y pie)
        elif ext == '.pdf':
            with open(path, 'rb') as f:
                header = f.read(1024)
                if not header.startswith(b'%PDF-'):
                    return True, str(path), "Encabezado PDF inválido"
                f.seek(-1024, os.SEEK_END)
                tail = f.read(1024)
                if b'%%EOF' not in tail:
                    return True, str(path), "Fin de archivo PDF incompleto o truncado"
            return False, str(path), None

        # D. Archivos multimedia y lecturas generales de I/O a alta velocidad
        else:
            # Lectura por bloques de 4 MB para saturar la RAM/CPU y detectar sectores defectuosos
            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(4 * 1024 * 1024)
                    if not chunk:
                        break
            
            # Verificación básica de cabecera en videos conocidos
            if ext in {'.mp4', '.m4v', '.mov'}:
                with open(path, 'rb') as f:
                    cabecera = f.read(32)
                    if b'ftyp' not in cabecera:
                        return True, str(path), "Cabecera MP4/MOV dañada (falta átomo ftyp)"
            elif ext in {'.mkv', '.webm'}:
                with open(path, 'rb') as f:
                    cabecera = f.read(10)
                    if not cabecera.startswith(b'\x1a\x45\xdf\xa3'):
                        return True, str(path), "Cabecera MKV/WebM dañada"

            return False, str(path), None

    except (zipfile.BadZipFile, zipfile.LargeZipFile) as e:
        return True, str(path), f"Archivo ZIP/Office corrupto: {e}"
    except SyntaxError as e:
        return True, str(path), f"Estructura de imagen dañada: {e}"
    except OSError as e:
        return True, str(path), f"Error de lectura I/O / Datos truncados: {e}"
    except Exception as e:
        return True, str(path), f"Error de integridad: {e}"

def escanear_carpeta_multiprocesos(ruta_base_str):
    ruta_base = Path(ruta_base_str).expanduser().resolve()
    
    if not ruta_base.exists():
        print(f"❌ La ruta '{ruta_base}' no existe.")
        return

    print(f"🔍 Recolectando lista de archivos en: {ruta_base} ...")
    
    # Recopilar todos los archivos recursivamente
    todos_los_archivos = []
    for raiz, _, archivos in os.walk(ruta_base):
        for f in archivos:
            todos_los_archivos.append(os.path.join(raiz, f))

    total = len(todos_los_archivos)
    if total == 0:
        print("⚠️ No se encontraron archivos para analizar.")
        return

    # Utilizar todos los núcleos lógicos del procesador
    num_procesadores = os.cpu_count() or 4
    print(f"⚡ Iniciando escaneo ultra rápido ({total} archivos) usando {num_procesadores} núcleos de CPU...\n")
    print("="*80)

    corruptos = []
    revisados = 0
    t_inicio = time.time()

    # Procesamiento en paralelo mediante ProcessPoolExecutor
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_procesadores) as executor:
        futuro_a_ruta = {executor.submit(verificar_integridad_archivo, ruta): ruta for ruta in todos_los_archivos}

        for futuro in concurrent.futures.as_completed(futuro_a_ruta):
            revisados += 1
            es_corrupto, ruta_archivo, motivo = futuro.result()

            if es_corrupto:
                corruptos.append((ruta_archivo, motivo))
                # Imprime en tiempo real en la terminal apenas encuentra uno defectuoso
                sys.stdout.write(f"\r❌ [CORRUPTO DETECTADO]\n  📍 Ruta: {ruta_archivo}\n  ⚠️ Motivo: {motivo}\n\n")
                sys.stdout.flush()

            # Progreso
            pct = (revisados / total) * 100
            sys.stdout.write(f"\r📊 Analizando: [{revisados}/{total}] ({pct:.1f}%) | Corruptos encontrados: {len(corruptos)}")
            sys.stdout.flush()

    t_total = time.time() - t_inicio

    print("\n" + "="*80)
    print(f"🎉 Escaneo completado en {t_total:.2f} segundos.")
    print(f"📁 Total de archivos revisados: {total}")
    print(f"🚨 Total de archivos corruptos : {len(corruptos)}")
    print("="*80)

    if corruptos:
        print("\n📋 RESUMEN DE ARCHIVOS CORRUPTOS ENCONTRADOS:")
        for idx, (p, m) in enumerate(corruptos, 1):
            print(f" {idx}. {p}\n    └─ Motivo: {m}")
    else:
        print("\n✅ ¡Excelente! No se encontró ningún archivo corrupto.")

if __name__ == "__main__":
    ruta = RUTA_A_REVISAR.strip()
    if not ruta:
        ruta = input("👉 Ingresa la ruta de la carpeta a revisar: ").strip().strip("'\"")
    
    escanear_carpeta_multiprocesos(ruta)