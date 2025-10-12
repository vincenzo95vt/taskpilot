from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
openai_api = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openai_api)

def rewrite_news(title: str, description: str = "") -> str:
    prompt = f"""
        Eres periodista y trabajas para un medio digital profesional.
        Tu tarea es escribir un texto para publicar en Instagram basado en la siguiente noticia,
        con un tono informativo, atractivo y serio, pensado para captar la atención en las primeras líneas.

        Descripción: {description}

        Instrucciones:
        - Escribe entre 600 y 900 caracteres.
        - Comienza con una frase de impacto o dato relevante que resuma la esencia de la noticia.
        - Desarrolla la información en 2 o 3 párrafos cortos (usa saltos de línea dobles entre ellos).
        - Mantén un tono periodístico, sobrio y claro, con ritmo narrativo que mantenga el interés.
        - No incluyas hashtags, emojis ni enlaces.
        - No inventes datos; céntrate en el mensaje principal de la noticia.
        - Cierra con una frase breve que resuma la implicación o consecuencia del hecho.
        """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=350,
        temperature=0.5
    )

    return response.choices[0].message.content.strip()
