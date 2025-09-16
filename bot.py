from rss_client import get_rss_news
from writer import rewrite_news
from twitter_client import post_tweet
from google_client import google_sheet_data
from scraper import extract_text_from_url
import random

RSS_FEED = "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada" 
USE_GOOGLE_SHEETS = True
def job():
    if USE_GOOGLE_SHEETS:
        rows = google_sheet_data()
        print(rows)
        if not rows:
            print("No URLs found in Google Sheets.")
            articles = get_rss_news(RSS_FEED,limit=5)
            sources = [{'link': a['link'], 'title': a['title'],  'description': a['description']} for a in articles]
        else:
            sources = [{'link': row, 'title': None,  'description': None} for row in rows if row.startswith('http')]
    else:
        articles = get_rss_news(RSS_FEED,limit=5)
        sources = [{'link': a['link'], 'title': a['title'],  'description': a['description']} for a in articles]
    if not sources:
        print("No articles found.")
        return
    
    article = random.choice(sources)
    print("Selected article:", article['link'])
    text = extract_text_from_url(article['link'])
    if not text:
        print("Failed to extract text from the article.")
        return
    rewritten = rewrite_news(title='' ,description=text)
    tweet = f"{rewritten}"
    if len(tweet) > 280:
        tweet = tweet[:277] + "..."

    result = post_tweet(tweet)
    print('Publicado en twitter', result)

if __name__ == "__main__":
    job()