"""
MÓDULO: broll_pexels.py
========================
Descarga clips de b-roll de Pexels basándose en keywords
extraídas dinámicamente de la noticia por GPT.

- Keywords específicas por noticia (no siempre las mismas)
- Rotación aleatoria para no repetir clips
- Clips en vertical (9:16) o recortados automáticamente
- Integración con ffmpeg para intercalar con tu vídeo

INSTALACIÓN:
    pip install requests openai python-dotenv

REQUISITOS:
    - API key de Pexels (gratis): https://www.pexels.com/api/
    - Añadir al .env: PEXELS_API_KEY=...
    - OPENAI_API_KEY ya lo tienes

USO:
    from broll_pexels import get_broll_clips
    clips = get_broll_clips(article_text, num_clips=3, duration=7)
"""

import os
import re
import json
import random
import requests
import subprocess
import tempfile
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client         = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

REEL_WIDTH  = 1080
REEL_HEIGHT = 1920

# Caché local para no repetir clips entre vídeos
USED_CLIPS_FILE = "used_clips_cache.json"


# ─────────────────────────────────────────────
# PASO 1: GPT extrae keywords específicas
# ─────────────────────────────────────────────
def extract_keywords(article_text: str) -> list[str]:
    """
    GPT analiza la noticia y devuelve keywords visuales específicas
    en inglés para buscar en Pexels.
    Evita términos genéricos como 'artificial intelligence' o 'technology'.
    """
    print("  🔍 Extrayendo keywords visuales con GPT...")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """Eres un director de vídeo. Tu tarea es extraer keywords
                visuales específicas para buscar clips de b-roll en Pexels.

                REGLAS:
                - Devuelve SOLO un JSON array con 6 keywords en inglés
                - Sé MUY específico: no uses "technology" o "artificial intelligence"
                - Usa términos visuales concretos: "robot arm factory", "server room cables",
                  "person typing laptop", "stock market screen", "satellite space", etc.
                - Piensa en qué imágenes aparecerían en un telediario sobre esta noticia
                - Varía entre primer plano, plano general y plano detalle

                Responde SOLO con JSON, sin backticks:
                ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6"]"""
            },
            {
                "role": "user",
                "content": f"Extrae keywords visuales para esta noticia:\n\n{article_text[:500]}"
            }
        ],
        temperature=0.8,  # Alta temperatura para más variedad
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"```json|```", "", raw).strip()
    keywords = json.loads(raw)

    print(f"  ✅ Keywords: {keywords}")
    return keywords


# ─────────────────────────────────────────────
# PASO 2: Busca clips en Pexels
# ─────────────────────────────────────────────
def search_pexels_clips(keyword: str, per_page: int = 10) -> list[dict]:
    """
    Busca vídeos en Pexels por keyword.
    Devuelve lista de clips con id, url de descarga y dimensiones.
    """
    headers = {"Authorization": PEXELS_API_KEY}
    params  = {
        "query":    keyword,
        "per_page": per_page,
        "orientation": "portrait",  # Preferimos vertical para Reels
        "size": "medium"
    }

    response = requests.get(
        "https://api.pexels.com/videos/search",
        headers=headers,
        params=params,
        timeout=15
    )

    if response.status_code != 200:
        print(f"  ⚠️  Pexels error para '{keyword}': {response.status_code}")
        return []

    data   = response.json()
    clips  = []

    for video in data.get("videos", []):
        # Buscar el archivo de mejor calidad disponible
        best_file = None
        for f in video.get("video_files", []):
            if f.get("width", 0) >= 720:
                if best_file is None or f.get("width", 0) < best_file.get("width", 9999):
                    best_file = f

        if best_file:
            clips.append({
                "id":       video["id"],
                "url":      best_file["link"],
                "width":    best_file.get("width", 0),
                "height":   best_file.get("height", 0),
                "duration": video.get("duration", 10),
            })

    return clips


# ─────────────────────────────────────────────
# PASO 3: Filtra clips ya usados
# ─────────────────────────────────────────────
def load_used_clips() -> set:
    if os.path.exists(USED_CLIPS_FILE):
        with open(USED_CLIPS_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_used_clips(used: set):
    # Mantiene solo los últimos 200 para no crecer indefinidamente
    ids_list = list(used)[-200:]
    with open(USED_CLIPS_FILE, "w") as f:
        json.dump(ids_list, f)


# ─────────────────────────────────────────────
# PASO 4: Descarga y recorta el clip a 9:16
# ─────────────────────────────────────────────
def download_and_crop_clip(clip: dict, output_path: str, duration: int = 7) -> bool:
    """
    Descarga el clip de Pexels y lo recorta a formato 9:16 y duración exacta.
    Devuelve True si tiene éxito.
    """
    try:
        # Descargar el clip
        response = requests.get(clip["url"], timeout=30, stream=True)
        if response.status_code != 200:
            return False

        raw_path = output_path.replace(".mp4", "_raw.mp4")
        with open(raw_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Recortar a 9:16 y duración exacta con ffmpeg
        crop_filter = (
            f"crop=ih*{REEL_WIDTH}/{REEL_HEIGHT}:ih,"  # Crop a ratio 9:16
            f"scale={REEL_WIDTH}:{REEL_HEIGHT}"         # Escalar a resolución Reel
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", raw_path,
            "-t", str(duration),          # Duración exacta
            "-vf", crop_filter,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            output_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        os.remove(raw_path)
        return True

    except Exception as e:
        print(f"  ⚠️  Error descargando clip: {e}")
        return False


# ─────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────
def get_broll_clips(article_text: str, num_clips: int = 4, duration: int = 7) -> list[str]:
    """
    Función principal. Recibe el texto de la noticia y devuelve
    una lista de rutas a clips de b-roll listos para usar en ffmpeg.

    Args:
        article_text: Texto de la noticia
        num_clips:    Cuántos clips necesitas (default 4)
        duration:     Duración de cada clip en segundos (default 7)

    Returns:
        Lista de rutas a archivos .mp4 descargados y recortados
    """
    work_dir  = Path(tempfile.mkdtemp())
    used_ids  = load_used_clips()
    keywords  = extract_keywords(article_text)

    # Mezclar keywords para más variedad
    random.shuffle(keywords)

    downloaded_clips = []

    for keyword in keywords:
        if len(downloaded_clips) >= num_clips:
            break

        print(f"  🎥 Buscando clips para: '{keyword}'...")
        candidates = search_pexels_clips(keyword, per_page=15)

        # Filtrar los ya usados y mezclar aleatoriamente
        fresh = [c for c in candidates if c["id"] not in used_ids]
        if not fresh:
            # Si todos están usados, resetear caché para esta keyword
            fresh = candidates
        random.shuffle(fresh)

        for clip in fresh:
            if len(downloaded_clips) >= num_clips:
                break

            output_path = str(work_dir / f"broll_{len(downloaded_clips)}.mp4")
            print(f"  ⬇️  Descargando clip {clip['id']}...")

            if download_and_crop_clip(clip, output_path, duration):
                downloaded_clips.append(output_path)
                used_ids.add(clip["id"])
                print(f"  ✅ Clip listo: {output_path}")
                break  # Un clip por keyword para máxima variedad

    save_used_clips(used_ids)
    print(f"\n  ✅ {len(downloaded_clips)} clips de b-roll listos")
    return downloaded_clips


# ─────────────────────────────────────────────
# TEST RÁPIDO
# Ejecuta: python broll_pexels.py
# ─────────────────────────────────────────────
if __name__ == "__main__":
    test_article = """
    OpenAI ha lanzado GPT-5, su modelo de inteligencia artificial más avanzado.
    El nuevo modelo supera a sus predecesores en razonamiento y codificación.
    Según la compañía, GPT-5 es capaz de resolver problemas matemáticos complejos.
    """

    clips = get_broll_clips(test_article, num_clips=3, duration=7)

    print(f"\n🎬 Clips generados:")
    for clip in clips:
        print(f"   - {clip}")