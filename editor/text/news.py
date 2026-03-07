import requests
import os
from dotenv import load_dotenv
load_dotenv()

NEWS_API_KEY = os.getenv("NEWSAPI_KEY")

def get_latest_news(category = 'general', language="es", limit=5):
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json().get("articles", [])
        return articles
    else:
        print(f"Error fetching news: {response.status_code}")
        return []

if __name__ == "__main__":
    print(NEWS_API_KEY)
    news = get_latest_news( limit=3)
    print(news)
    for i, article in enumerate(news, 1):
        print(f"\nNoticia {i}:")
        print("Título:", article["title"])
        print("Descripción:", article["description"])
        print("URL:", article["url"])