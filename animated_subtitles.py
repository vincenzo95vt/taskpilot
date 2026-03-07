"""
SUBTÍTULOS ANIMADOS — Reemplaza image_audio_to_clip en reel_generator.py
=========================================================================
Cambios respecto a la versión anterior:
- Whisper API extrae timestamps por palabra del audio de ElevenLabs
- FFmpeg pinta cada palabra en su momento exacto
- Estilo: amarillo con borde negro, centrado, tamaño grande

INSTALACIÓN (nada nuevo si ya tienes openai instalado):
    pip install openai python-dotenv

USO:
    Sustituye la función image_audio_to_clip en tu reel_generator.py
    por las dos funciones de este archivo:
      - get_word_timestamps()
      - image_audio_to_clip()
"""

import os
import subprocess
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

REEL_WIDTH  = 1080
REEL_HEIGHT = 1920


# ─────────────────────────────────────────────
# PASO 1: Whisper extrae timestamps por palabra
# ─────────────────────────────────────────────
def get_word_timestamps(audio_path: str) -> list[dict]:
    """
    Llama a Whisper API y devuelve lista de palabras con tiempos:
    [{"word": "La", "start": 0.0, "end": 0.18}, ...]

    Coste: ~$0.006/minuto → menos de 1€/mes para 3 videos/día
    """
    print("  ⏱️  Extrayendo timestamps con Whisper...")

    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",       # Activa datos detallados
            timestamp_granularities=["word"],      # Timestamps por palabra
            language="es"                          # Fuerza español para mayor precisión
        )

    words = []
    for w in response.words:
        words.append({
            "word":  w.word.strip(),
            "start": round(w.start, 3),
            "end":   round(w.end, 3)
        })

    print(f"  ✅ {len(words)} palabras con timestamps extraídas")
    return words


# ─────────────────────────────────────────────
# PASO 2: Construye el filtro drawtext de FFmpeg
# ─────────────────────────────────────────────
def build_subtitle_filter(words: list[dict]) -> str:
    """
    Genera una cadena de filtros drawtext para FFmpeg.
    Cada palabra aparece en su momento exacto en amarillo con borde negro.

    Estrategia: muestra grupos de 3 palabras a la vez para que sea
    más legible (como los subtítulos de TikTok/Reels profesionales).
    """

    def escape(text: str) -> str:
        """Escapa caracteres especiales para FFmpeg drawtext."""
        return (text
                .replace("\\", "")
                .replace("'",  "")
                .replace(":",  "\\:")
                .replace("%",  "\\%")
                .replace("[",  "\\[")
                .replace("]",  "\\]"))

    filters = []

    # Agrupa las palabras en chunks de 3
    chunk_size = 3
    chunks = []
    for i in range(0, len(words), chunk_size):
        group = words[i:i + chunk_size]
        text  = " ".join(w["word"] for w in group)
        start = group[0]["start"]
        end   = group[-1]["end"]
        chunks.append({"text": text, "start": start, "end": end})

    for chunk in chunks:
        text_escaped = escape(chunk["text"])
        t_start      = chunk["start"]
        t_end        = chunk["end"] - 0.08   # pequeño margen para que no desaparezca muy rápido

        filter_str = (
            f"drawtext="
            f"text='{text_escaped}':"
            f"fontsize=72:"
            f"fontcolor=yellow:"
            f"font=Arial:"
            f"borderw=4:"
            f"bordercolor=black:"
            f"x=(w-text_w)/2:"
            f"y=(h*0.75):"
            f"fix_bounds=true:"
            f"enable='between(t,{t_start},{t_end})'"
        )
        filters.append(filter_str)

    # FFmpeg necesita los filtros encadenados con comas
    return ",".join(filters)

def video_audio_to_clip(video_path: str, audio_path: str, output_path: str, narration: str = ""):
    """
    Como image_audio_to_clip pero para vídeos de Pexels.
    Sin -loop 1 y sin Ken Burns (el vídeo ya tiene movimiento).
    """
    print(f"  🎬 Generando clip b-roll con subtítulos...")

    words = get_word_timestamps(audio_path)
    subtitle_filter = build_subtitle_filter(words)

    # Solo escalar a 9:16, sin zoompan (el vídeo ya tiene movimiento)
    scale_filter = f"scale={REEL_WIDTH}:{REEL_HEIGHT}:force_original_aspect_ratio=decrease,pad={REEL_WIDTH}:{REEL_HEIGHT}:(ow-iw)/2:(oh-ih)/2"

    full_filter = f"{scale_filter},{subtitle_filter}"

    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",    # ← loop infinito del vídeo
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-map", "0:v",           # ← vídeo del clip Pexels
        "-map", "1:a",           # ← audio de ElevenLabs
        "-shortest",             # ← ahora corta cuando termina el audio
        "-vf", full_filter,
        "-preset", "fast",
        output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"  ✅ Clip b-roll listo: {output_path}")
# ─────────────────────────────────────────────
# PASO 3: Genera el clip con subtítulos animados
# — Reemplaza image_audio_to_clip en reel_generator.py
# ─────────────────────────────────────────────
def image_audio_to_clip(image_path: str, audio_path: str, output_path: str, narration: str = ""):
    """
    Crea un clip de vídeo con:
    - Efecto Ken Burns (zoom lento)
    - Subtítulos palabra por palabra en amarillo con borde negro
    - Sincronizados exactamente con el audio de ElevenLabs

    Reemplaza directamente la función image_audio_to_clip de reel_generator.py
    """
    print(f"  🎬 Generando clip con subtítulos animados...")

    # 1. Obtener timestamps de cada palabra
    words = get_word_timestamps(audio_path)

    # 2. Construir filtro de subtítulos
    subtitle_filter = build_subtitle_filter(words)

    # 3. Ken Burns: zoom lento del 100% al 115%
    ken_burns = (
        f"scale={REEL_WIDTH * 2}:{REEL_HEIGHT * 2},"
        f"zoompan="
        f"z='min(zoom+0.0008,1.15)':"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"d=9000:"
        f"s={REEL_WIDTH}x{REEL_HEIGHT}:"
        f"fps=25"
    )

    # 4. Combinar Ken Burns + subtítulos
    full_filter = f"{ken_burns},{subtitle_filter}"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-vf", full_filter,
        "-preset", "fast",
        output_path
    ]

    subprocess.run(cmd, check=True, capture_output=True)
    print(f"  ✅ Clip con subtítulos animados: {output_path}")


# ─────────────────────────────────────────────
# TEST RÁPIDO
# Ejecuta: python subtitulos_animados.py
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # Cambia estas rutas por archivos reales para probar
    TEST_IMAGE = "test_image.jpg"
    TEST_AUDIO = "test_audio.mp3"
    TEST_OUTPUT = "test_clip_output.mp4"

    if not os.path.exists(TEST_IMAGE) or not os.path.exists(TEST_AUDIO):
        print("⚠️  Para testear, pon test_image.jpg y test_audio.mp3 en este directorio")
    else:
        image_audio_to_clip(TEST_IMAGE, TEST_AUDIO, TEST_OUTPUT)
        print(f"\n✅ Test completado: {TEST_OUTPUT}")