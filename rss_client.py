import feedparser
def get_rss_news(url, limit = 5):
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:limit]:
        articles.append({
            'title': entry.title,
            'description': entry.description,
            'link': entry.link
        })
    return articles

if __name__ == "__main__":
    url = "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada"
    news = get_rss_news(url, limit=5)
    for i, article in enumerate(news, 3):
        print(f"\nNoticia {i}:")
        print("Título:", article["title"])
        print("Descripción:", article["description"])
        print("URL:", article["link"])