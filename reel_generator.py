"""
Generador de Reels para Instagram
===================================
Flujo: RSS → GPT (guión) → ElevenLabs (voz) → DALL-E (imágenes) → FFmpeg (vídeo 9:16)

REQUISITOS:
    pip install requests openai python-dotenv pillow

    FFmpeg instalado en el sistema:
    - Mac:     brew install ffmpeg
    - Ubuntu:  sudo apt install ffmpeg
    - Windows: https://ffmpeg.org/download.html

VARIABLES EN .env:
    OPENAI_API_KEY=...
    ELEVENLABS_API_KEY=...
    ELEVENLABS_VOICE_ID=...        # Tu voz clonada
"""

import os
import re
import json
import requests
import tempfile
import subprocess
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from animated_subtitles import image_audio_to_clip, video_audio_to_clip
from broll_pexels import get_broll_clips

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

# Resolución vertical para Reels (9:16)
REEL_WIDTH = 1080
REEL_HEIGHT = 1920


# ─────────────────────────────────────────────
# 1. GPT: convierte el artículo en guión por escenas
# ─────────────────────────────────────────────
def generate_script(article_text: str) -> list[dict]:
    """
    Devuelve una lista de escenas:
    [{"narration": "texto narrado", "image_prompt": "prompt para DALL-E"}, ...]
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """Eres el community manager de The SynthSight, empresa de software en Málaga.
                Tono: directo, técnico pero accesible, con opinión propia. Frases cortas.
                Tu tarea: convertir un artículo en un guión para un Reel de Instagram.
                Divide el contenido en 3-5 escenas cortas.

                IMPORTANTE:
                - La ÚLTIMA escena siempre debe cerrar con una frase corta y definitiva, por ejemplo: 
                "Esto es todo por hoy." o "¿Tú qué opinas? Déjalo en comentarios." o "Síguenos para más noticias tech."
                - Nunca termines con una frase inconclusa o que suene a que hay más contenido después.
                - Cada narración debe sonar completa por sí sola, con pausas naturales.

                Responde SOLO con un JSON válido, sin backticks ni explicaciones:
                [
                {
                    "narration": "texto que se narrará en voz alta (máx 2 frases)",
                    "image_prompt": "prompt en inglés para DALL-E, estilo tech moderno, vertical 9:16"
                }
                ]"""
            },
            {
                "role": "user",
                "content": f"Convierte este artículo en guión de Reel:\n\n{article_text}"
            }
        ],
        temperature=0.7,
    )

    raw = response.choices[0].message.content.strip()
    # Limpiar posibles backticks
    raw = re.sub(r"```json|```", "", raw).strip()
    return json.loads(raw)


# ─────────────────────────────────────────────
# 2. ElevenLabs: genera audio por escena
# ─────────────────────────────────────────────
def generate_audio(text: str, output_path: str, is_last: bool = False):
    """Genera un archivo MP3 con tu voz clonada."""
    TEST_MODE = False
    if TEST_MODE:
        import shutil
        shutil.copy('test_audio.mp3', output_path)
        print(f"Audio de prueba copiado:", {output_path})
        return
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_v3",
        "voice_settings": {
            "stability": 0.35,          # Más bajo = más expresivo y natural
            "similarity_boost": 0.75,   # Ligeramente más bajo = menos robótico
            "style": 0.45,              # Añade variación de estilo
            "use_speaker_boost": True   # Mejora claridad de voz clonada
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"ElevenLabs error: {response.status_code} - {response.text}")

    with open(output_path, "wb") as f:
        f.write(response.content)

    # Añadir 0.8s de silencio al final de la última escena para cierre natural
    if is_last:
        silent_path = output_path.replace(".mp3", "_silent.mp3")
        subprocess.run([
            "ffmpeg", "-y", "-i", output_path,
            "-af", "apad=pad_dur=0.8",
            silent_path
        ], capture_output=True)
        os.replace(silent_path, output_path)

    print(f"  ✅ Audio generado: {output_path}")


# ─────────────────────────────────────────────
# 3. Imagen del RSS + gradiente oscuro en bordes
# ─────────────────────────────────────────────
def prepare_image(image_url: str, output_path: str):
    """
    Descarga la imagen del artículo RSS, la adapta a 9:16
    y añade gradiente oscuro en bordes para que el texto resalte.
    """
    import io
    from PIL import ImageDraw, ImageFilter

    print(f"  🖼️  Descargando imagen del RSS...")
    response = requests.get(image_url, timeout=30)
    if response.status_code != 200:
        raise Exception(f"Error descargando imagen RSS: {response.status_code}")

    img = Image.open(io.BytesIO(response.content)).convert("RGB")

    # Crop centrado a 9:16
    target_ratio = REEL_WIDTH / REEL_HEIGHT
    img_ratio = img.width / img.height

    if img_ratio > target_ratio:
        new_width = int(img.height * target_ratio)
        left = (img.width - new_width) // 2
        img = img.crop((left, 0, left + new_width, img.height))
    else:
        new_height = int(img.width / target_ratio)
        top = (img.height - new_height) // 2
        img = img.crop((0, top, img.width, top + new_height))

    img = img.resize((REEL_WIDTH, REEL_HEIGHT), Image.LANCZOS)

    # Gradiente oscuro: negro transparente en bordes → imagen visible en centro
    gradient = Image.new("RGBA", (REEL_WIDTH, REEL_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)

    # Gradiente superior (30% de altura)
    for i in range(int(REEL_HEIGHT * 0.35)):
        alpha = int(180 * (1 - i / (REEL_HEIGHT * 0.35)))
        draw.line([(0, i), (REEL_WIDTH, i)], fill=(0, 0, 0, alpha))

    # Gradiente inferior (40% de altura) — más oscuro para el texto
    for i in range(int(REEL_HEIGHT * 0.45)):
        y = REEL_HEIGHT - 1 - i
        alpha = int(210 * (1 - i / (REEL_HEIGHT * 0.45)))
        draw.line([(0, y), (REEL_WIDTH, y)], fill=(0, 0, 0, alpha))

    # Componer imagen + gradiente
    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, gradient).convert("RGB")
    result.save(output_path)
    print(f"  ✅ Imagen preparada con gradiente: {output_path}")


# ─────────────────────────────────────────────
# 4. FFmpeg: une imagen + audio en clip de vídeo
# ─────────────────────────────────────────────
# def image_audio_to_clip(image_path: str, audio_path: str, output_path: str, narration: str = ""):
#     """Crea un clip de vídeo con efecto Ken Burns + subtítulos amarillos centrados."""

#     # Escapar caracteres especiales para FFmpeg drawtext
#     def escape_text(t):
#         return t.replace("\\", "").replace("'", "\'").replace(":", "\:").replace("%", "\%")

#     # Dividir el texto en líneas de máx 30 caracteres para que quepa en pantalla
#     import textwrap
#     words = narration.strip()
#     lines = textwrap.wrap(words, width=28)
#     text_escaped = "\n".join([escape_text(l) for l in lines])

#     # Ken Burns: zoom lento del 100% al 115%
#     ken_burns = (
#         f"scale={REEL_WIDTH*2}:{REEL_HEIGHT*2},"
#         f"zoompan="
#         f"z='min(zoom+0.0008,1.15)':"
#         f"x='iw/2-(iw/zoom/2)':"
#         f"y='ih/2-(ih/zoom/2)':"
#         f"d=9000:"
#         f"s={REEL_WIDTH}x{REEL_HEIGHT}:"
#         f"fps=25"
#     )

#     # Subtítulos: texto amarillo, fondo negro semitransparente, centrado verticalmente
#     subtitle_filter = (
#         f"drawtext="
#         f"text='{text_escaped}':"
#         f"fontsize=62:"
#         f"fontcolor=yellow:"
#         f"font=Arial:"
#         f"borderw=3:"
#         f"bordercolor=black:"
#         f"box=1:"
#         f"boxcolor=black@0.45:"
#         f"boxborderw=18:"
#         f"x=(w-text_w)/2:"          # centrado horizontal
#         f"y=(h-text_h)/2:"          # centrado vertical
#         f"line_spacing=12"
#     )

#     full_filter = f"{ken_burns},{subtitle_filter}"

#     cmd = [
#         "ffmpeg", "-y",
#         "-loop", "1",
#         "-i", image_path,
#         "-i", audio_path,
#         "-c:v", "libx264",
#         "-c:a", "aac",
#         "-b:a", "192k",
#         "-pix_fmt", "yuv420p",
#         "-shortest",
#         "-vf", full_filter,
#         "-preset", "fast",
#         output_path
#     ]
#     subprocess.run(cmd, check=True, capture_output=True)
#     print(f"  ✅ Clip con Ken Burns + subtítulos: {output_path}")


# ─────────────────────────────────────────────
# 5. FFmpeg: concatena todos los clips en un Reel
# ─────────────────────────────────────────────
def concatenate_clips(clip_paths: list[str], output_path: str):
    """Une todos los clips en el vídeo final y mezcla música de fondo."""
    # Paso 1: Concatenar todos los clips en un vídeo sin música
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for clip in clip_paths:
            f.write(f"file '{os.path.abspath(clip)}'\n")
        concat_file = f.name

    raw_output = output_path.replace(".mp4", "_raw.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c:v", "libx264",     
        "-c:a", "aac",         
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        raw_output
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    os.remove(concat_file)

    # Paso 2: Mezclar música de fondo si existe el archivo
    music_path = os.path.join(os.path.dirname(__file__), "assets", "background_music.mp3")

    if os.path.exists(music_path):
        print("🎵 Mezclando música de fondo...")
        cmd_mix = [
            "ffmpeg", "-y",
            "-i", raw_output,           # Vídeo con voz
            "-stream_loop", "-1",       # Loop infinito de la música
            "-i", music_path,           # Música de fondo
            "-filter_complex",
            # voz al 100%, música al 15% (baja pero se nota)
            "[1:a]volume=0.15[music];[0:a][music]amix=inputs=2:duration=first[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_path
        ]
        subprocess.run(cmd_mix, check=True, capture_output=True)
        os.remove(raw_output)
        print("✅ Música mezclada correctamente")
    else:
        # Sin música, usar el vídeo raw directamente
        os.rename(raw_output, output_path)
        print("⚠️  No se encontró assets/background_music.mp3 — Reel sin música")

    print(f"\n✅ Reel final: {output_path}")


# ─────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────
def generate_reel(article_text: str, image_url: str, output_path: str = "reel_output.mp4") -> str:
    """
    Recibe el texto del artículo y la imagen del RSS y genera el Reel completo.
    Devuelve la ruta del vídeo final.
    """
    work_dir = Path(tempfile.mkdtemp())
    print(f"\n🎬 Generando Reel en {work_dir}")

    # Paso 1: Guión
    print("\n📝 Generando guión...")
    scenes = generate_script(article_text)
    print(f"  {len(scenes)} escenas generadas")

    # Paso 2: Preparar imagen del RSS una sola vez (con gradiente)
    base_image_path = str(work_dir / "base_image.png")
    prepare_image(image_url, base_image_path)
    print("\n🎥 Descargando clips de b-roll...")
    broll_clips = get_broll_clips(article_text, num_clips=4, duration=7)

    clips = []

    for i, scene in enumerate(scenes):
        print(f"\n🎞️  Escena {i+1}/{len(scenes)}")

        audio_path = str(work_dir / f"audio_{i}.mp3")
        clip_path  = str(work_dir / f"clip_{i}.mp4")

        generate_audio(scene["narration"], audio_path, is_last=(i == len(scenes) - 1))

        if broll_clips:
            broll_index = i % len(broll_clips)
            video_audio_to_clip(broll_clips[broll_index], audio_path, clip_path, narration=scene["narration"])
        else:
            image_audio_to_clip(base_image_path, audio_path, clip_path, narration=scene["narration"])

        clips.append(clip_path)

        # Paso 5: Reel final
        print("\n🔗 Concatenando clips...")
        concatenate_clips(clips, output_path)

        return output_path

if __name__ == "__main__":
    # Texto de prueba — cámbialo por cualquier noticia tech
    test_article = """
    OpenAI ha lanzado GPT-5, su modelo de inteligencia artificial más avanzado hasta la fecha.
    El nuevo modelo supera a sus predecesores en razonamiento, codificación y comprensión del lenguaje.
    Según la compañía, GPT-5 es capaz de resolver problemas matemáticos complejos y escribir código
    de producción con una precisión nunca vista. El lanzamiento llega en un momento de intensa
    competencia con Google, Meta y Anthropic. El acceso estará disponible primero para usuarios
    de ChatGPT Plus y la API de OpenAI.
    """

    # URL de imagen de prueba (cualquier imagen tech de internet)
    test_image_url = "https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=1080"

    resultado = generate_reel(
        article_text=test_article,
        image_url=test_image_url,
        output_path="reel_prueba.mp4"
    )

    print(f"\n🎬 Reel generado: {resultado}")