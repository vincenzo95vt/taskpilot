from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
openai_api = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openai_api)

def rewrite_news(title: str, description: str = "") -> str:
    title_part = f"Titular: {title}" if title else ""

    prompt = f"""
    Eres un periodista profesional y trabajas para mi periodico y necesitamos que hagas un resumen de esta noticia con una visión conservadora y profesional:

    {title_part}
    Descripción: {description}
    El tuit debe ser conciso, claro y atractivo, con un máximo de 1120 caracteres. No pongas hashtags ni emojis. y bajo ningun concepto te pases de esos 1120 caracteres
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=120,
        temperature=0.5
    )
    return response.choices[0].message.content
