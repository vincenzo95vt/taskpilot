from rss_client import get_rss_news
from writer import rewrite_news
from twitter_client import post_tweet, post_thread
from google_client import get_unpublished_urls, sync_rss_to_sheet, get_next_unpublished, mark_as_published
from scraper import extract_text_from_url
from notifier import notify
import traceback

RSS_FEED = "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada" 
def job():
    try:
        sync_rss_to_sheet(RSS_FEED, limit= 5)
        row, url, ws = get_next_unpublished()
        if not url:
            notify('TaskPilot', 'No hay URLs nuevas ni articulos en la hoja')
            return
        print('Selected article:' , url)
        text = extract_text_from_url(url)
        if not text:
            print("Failed to extract text from the article.")
            return
        rewritten = rewrite_news(title='' ,description=text)
        if len(rewritten) > 280:
            result = post_thread(rewritten)
        else:
            result = post_tweet(rewritten)
        print('Publicado en twitter', result)
        notify( "✅ TaskPilot - Publicación realizada",
            f"Artículo: {url}\n\nTweet:\n{result}")
        mark_as_published(ws, row)
    except Exception as e:
        err = traceback.format_exc()
        print('Error en job')
        notify("❌ TaskPilot - Error crítico", f"{e}\n\nTraceback:\n{err}")

if __name__ == "__main__":
    job()