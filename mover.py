import os
import shutil
import time
import sys
from pathlib import Path

# ==============================================================================
# CONFIGURACIÓN DE RUTAS
# ==============================================================================
# Deja las rutas entre comillas o déjalas vacías "" para ingresarlas por terminal.
RUTA_ORIGEN = ""   # Ej: "/home/usuario/Descargas/MiCarpeta" o "/home/usuario/video.mp4"
RUTA_DESTINO = ""  # Ej: "/media/usuario/MI_USB/Fotos"
# ==============================================================================

CHUNK_SIZE = 2 * 1024 * 1024  # Bloques de 2 MB para medir con precisión física

def formatear_tamano(bytes_num):
    """Convierte bytes a formato legible (KB, MB, GB)."""
    for unidad in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.2f} {unidad}"
        bytes_num /= 1024.0
    return f"{bytes_num:.2f} PB"

def dibujar_barra(porcentaje, longitud=20):
    """Genera una barra de progreso visual [████████░░░░]"""
    porcentaje = min(100.0, max(0.0, porcentaje))
    llenos = int(longitud * porcentaje // 100)
    barra = '█' * llenos + '░' * (longitud - llenos)
    return f"[{barra}] {porcentaje:.1f}%"

def obtener_lista_archivos(origen_path):
    """Retorna lista de tuplas (path_absoluto, path_relativo_destino, tamano)"""
    archivos = []
    if origen_path.is_file():
        archivos.append((origen_path, origen_path.name, origen_path.stat().st_size))
    elif origen_path.is_dir():
        for raiz, _, filenames in os.walk(origen_path):
            for filename in filenames:
                p_abs = Path(raiz) / filename
                p_rel = p_abs.relative_to(origen_path.parent)
                archivos.append((p_abs, p_rel, p_abs.stat().st_size))
    return archivos

def mover_con_progreso_real(origen_str, destino_str):
    origen_path = Path(origen_str).expanduser().resolve()
    destino_path = Path(destino_str).expanduser().resolve()

    if not origen_path.exists():
        print(f"❌ Error: La ruta de origen '{origen_path}' no existe.")
        return

    destino_path.mkdir(parents=True, exist_ok=True)

    print("🔍 Escaneando archivos y calculando pesos...")
    archivos = obtener_lista_archivos(origen_path)

    if not archivos:
        print("⚠️ No se encontraron archivos para mover.")
        return

    total_archivos = len(archivos)
    total_bytes_global = sum(size for _, _, size in archivos)
    bytes_ram_global = 0
    bytes_disco_global = 0

    print("\n" + "="*75)
    print(f"📦 RESUMEN DE LA OPERACIÓN (CONTROL DE RAM + ESCRITURA FÍSICA USB)")
    print(f" • Archivos a mover : {total_archivos}")
    print(f" • Peso total       : {formatear_tamano(total_bytes_global)}")
    print(f" • Origen           : {origen_path}")
    print(f" • Destino          : {destino_path}")
    print("="*75 + "\n")

    tiempo_inicio_global = time.time()

    for idx, (f_abs, f_rel, f_size) in enumerate(archivos, 1):
        f_destino = destino_path / f_rel if origen_path.is_dir() else destino_path / f_abs.name
        f_destino.parent.mkdir(parents=True, exist_ok=True)

        print(f"📄 [{idx}/{total_archivos}] Moviendo: {f_abs.name} ({formatear_tamano(f_size)})")

        bytes_ram_archivo = 0
        bytes_disco_archivo = 0
        
        t_inicio_archivo = time.time()

        with open(f_abs, 'rb') as f_src, open(f_destino, 'wb') as f_dst:
            fd_dst = f_dst.fileno()

            while True:
                chunk = f_src.read(CHUNK_SIZE)
                if not chunk:
                    break
                
                # 1. Escritura en Buffer RAM (Caché de Linux)
                f_dst.write(chunk)
                f_dst.flush()
                
                bytes_chunk = len(chunk)
                bytes_ram_archivo += bytes_chunk
                bytes_ram_global += bytes_chunk

                pct_ram = (bytes_ram_archivo / f_size * 100) if f_size > 0 else 100
                t_actual = time.time() - t_inicio_archivo
                vel_ram = (bytes_ram_archivo / t_actual) if t_actual > 0 else 0

                # Renderizar fila de RAM
                sys.stdout.write(
                    f"\r  ├── 🧠 RAM (Caché):  {dibujar_barra(pct_ram)} | Vel: {formatear_tamano(vel_ram)}/s ({formatear_tamano(bytes_ram_archivo)}/{formatear_tamano(f_size)})\n"
                )

                # 2. Forzar volcado físico al Hardware mediante os.fsync
                os.fsync(fd_dst)
                
                bytes_disco_archivo += bytes_chunk
                bytes_disco_global += bytes_chunk

                pct_disco = (bytes_disco_archivo / f_size * 100) if f_size > 0 else 100
                t_actual_disco = time.time() - t_inicio_archivo
                vel_real_disco = (bytes_disco_archivo / t_actual_disco) if t_actual_disco > 0 else 0

                # Renderizar fila de Escritura Física
                sys.stdout.write(
                    f"  └── 💾 REAL (USB):   {dibujar_barra(pct_disco)} | Vel Real: {formatear_tamano(vel_real_disco)}/s ({formatear_tamano(bytes_disco_archivo)}/{formatear_tamano(f_size)})"
                )
                
                # Reposicionar el cursor para sobreescribir dinámicamente ambas barras
                sys.stdout.write("\033[F")
                sys.stdout.flush()

        sys.stdout.write("\n\n")
        sys.stdout.flush()

        # Eliminar archivo original solo tras confirmar la escritura física en disco
        f_abs.unlink()

    if origen_path.is_dir():
        shutil.rmtree(origen_path, ignore_errors=True)

    tiempo_total = time.time() - tiempo_inicio_global
    vel_real_promedio = (total_bytes_global / tiempo_total) if tiempo_total > 0 else 0

    print("="*75)
    print(f"🎉 ¡Listo! Archivos movidos y confirmados físicamente en el almacenamiento.")
    print(f"⏱️ Tiempo total real   : {tiempo_total:.1f} segundos")
    print(f"🚀 Velocidad real media: {formatear_tamano(vel_real_promedio)}/s")
    print(f"📊 Archivos procesados : {total_archivos}/{total_archivos} ({formatear_tamano(total_bytes_global)})")
    print("="*75)

if __name__ == "__main__":
    orig = RUTA_ORIGEN.strip()
    dest = RUTA_DESTINO.strip()

    if not orig:
        orig = input("👉 Ingresa la ruta de ORIGEN (archivo o carpeta): ").strip().strip("'\"")
    if not dest:
        dest = input("👉 Ingresa la ruta de DESTINO (carpeta): ").strip().strip("'\"")

    mover_con_progreso_real(orig, dest)