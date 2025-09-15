from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
openai_api = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openai_api)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "Escribe un tuit objetivo sobre la subida del precio del petróleo."}
    ],
    max_tokens=120,
    temperature=0.5
)

print(response.choices[0].message.content)
