import os
import io
import time
import shutil
from pathlib import Path
from PIL import Image
from google import genai
from google.genai import types

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
# Pega tu API Key de Gemini si no usas variables de entorno
API_KEY = ""  # Ej: "AIzaSy..."

CATEGORIAS = [
    "documentos",
    "personas",
    "capturas",
    "tensura",
    "otros"
]
# ==============================================================================

api_key_final = API_KEY.strip() or os.environ.get("GEMINI_API_KEY")

if not api_key_final:
    print("❌ ERROR: No se encontró una API Key válida.")
    exit(1)

client = genai.Client(api_key=api_key_final)

def comprimir_imagen_para_ia(ruta_imagen, max_dimension=512):
    with Image.open(ruta_imagen) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        img.thumbnail((max_dimension, max_dimension))
        
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=70)
        return buffer.getvalue()

def clasificar_imagen_con_retry(bytes_imagen, max_reintentos=3):
    """Envía la miniatura a Gemini y maneja el error 429 de Rate Limit automáticamente."""
    prompt = f"""
    Analiza esta imagen y clasifícala estrictamente en UNA de las siguientes categorías:
    {', '.join(CATEGORIAS)}.

    Reglas de clasificación:
    - 'documentos': Textos, hojas escaneadas, facturas, recibos, carnets, PDFs renderizados.
    - 'personas': Fotos reales de personas o grupos de personas, o mascotas.
    - 'capturas': Capturas de pantalla (screenshots) de celular o computador.
    - 'tensura': Imágenes, fanarts, cuadros de anime o manga relacionados específicamente con Tensei Shitara Slime Datta Ken (Rimuru, etc.).
    - 'otros': Si no encaja con ninguna de las anteriores.

    Responde ÚNICAMENTE con el nombre de la categoría elegida, en minúsculas.
    """

    for intento in range(max_reintentos):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(data=bytes_imagen, mime_type='image/jpeg'),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    temperature=0.1
                )
            )
            
            resultado = response.text.strip().lower()
            if resultado in CATEGORIAS:
                return resultado
            return "otros"

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                tiempo_espera = 15
                print(f"⏳ Límite de peticiones alcanzado (Rate Limit). Esperando {tiempo_espera}s antes de reintentar... (Intento {intento + 1}/{max_reintentos})")
                time.sleep(tiempo_espera)
            else:
                print(f"❌ Error inesperado consultando la IA: {e}")
                return "otros"
                
    print("❌ Se superaron los reintentos para esta imagen. Se enviará a 'otros'.")
    return "otros"

def organizar_por_ia(ruta_objetivo):
    ruta_base = Path(ruta_objetivo)
    extensiones_fotos = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.heic'}
    
    archivos_procesados = 0

    for archivo in ruta_base.iterdir():
        if archivo.is_file() and archivo.suffix.lower() in extensiones_fotos:
            print(f"🤖 Analizando: {archivo.name}...")
            
            try:
                bytes_ligeros = comprimir_imagen_para_ia(archivo)
                categoria = clasificar_imagen_con_retry(bytes_ligeros)
                
                carpeta_destino = ruta_base / categoria
                carpeta_destino.mkdir(exist_ok=True)
                
                destino_final = carpeta_destino / archivo.name
                
                if destino_final.exists():
                    print(f"⚠️ [Duplicado] {archivo.name} ya existe en {categoria}/. Omitiendo.")
                    continue
                    
                shutil.move(str(archivo), str(destino_final))
                print(f"📁 Clasificado en [{categoria}]: {archivo.name}")
                archivos_procesados += 1
                
                # Pausa preventiva para mantenerse dentro de las 5 peticiones por minuto
                time.sleep(12)
                
            except Exception as e:
                print(f"❌ Error procesando {archivo.name}: {e}")

    print(f"\n🎉 ¡Clasificación por IA terminada! Se movieron {archivos_procesados} imágenes.")

if __name__ == "__main__":
    RUTA_DE_PRUEBA = "/home/camper/Escritorio/img"  
    
    if os.path.exists(RUTA_DE_PRUEBA):
        print(f"Iniciando clasificación por IA en: {RUTA_DE_PRUEBA}\n")
        organizar_por_ia(RUTA_DE_PRUEBA)
    else:
        print(f"❌ La ruta '{RUTA_DE_PRUEBA}' no existe. Verifícala.")

