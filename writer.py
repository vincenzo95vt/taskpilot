from openai import OpenAI
from dotenv import load_dotenv
from supabase_client import get_prompt
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def rewrite_news(description: str = "") -> str:
    prompt_data = get_prompt("instagram_caption")
    prompt = prompt_data["user_prompt"].format(content=description)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()


def rewrite_for_linkedin(description: str) -> str:
    prompt_data = get_prompt("linkedin_post")
    prompt = prompt_data["user_prompt"].format(content=description)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()
