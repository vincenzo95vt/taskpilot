from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

openai_api = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api)


def rewrite_news(title: str, description: str = "") -> str:
    prompt = f"""
Eres el community manager de The SynthSight, empresa de software en Málaga.
Tu tarea es escribir una descripción corta en español para acompañar un Reel de Instagram sobre esta noticia, si viene en Inglés deberás traducirlo.
Noticia: {description}
Instrucciones:
- Escribe MÁXIMO 3 líneas en total.
- La primera línea debe ser un gancho que genere intriga o impacto, sin revelar toda la noticia.
- La segunda línea (opcional) añade un dato o contexto breve que pique la curiosidad.
- La última línea debe invitar a ver el vídeo, por ejemplo: "Mira el vídeo 👆" o "Te lo contamos en el Reel 👆"
- Tono directo, tech, sin corporativismos.
- No cuentes la noticia completa — eso lo hace el vídeo.
- Al final del texto, añade una línea en blanco y luego entre 8 y 12 hashtags relevantes.
- Los hashtags deben mezclar: 3-4 específicos de la noticia, 3-4 de nicho tech/IA en español, 2-3 generales.
- Ejemplo de formato hashtags: #GPT5 #OpenAI #InteligenciaArtificial #TechEspanol #IA #Tecnologia
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,  # ← subimos de 100 a 150 para que quepan los hashtags
        temperature=0.7
    )
    return response.choices[0].message.content.strip()