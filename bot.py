from rss_client import get_rss_news
from writer import rewrite_news
from twitter_client import post_tweet, post_thread
from google_client import get_unpublished_urls, sync_rss_to_sheet, get_next_unpublished, mark_as_published
from scraper import extract_article_img, extract_text_from_url
from utils.utils import format_caption
from instagram_client import post_to_ig, post_reel_to_ig
from linkedin_client import post_to_linkedin
from notifier import notify
from reel_generator import generate_reel
import traceback
import os

RSS_FEED = [
    "https://www.genbeta.com/feedburner.xml",
    "https://www.technologyreview.com/feed/"
    ]


POST_REEL = os.getenv("POST_REEL", "false").lower() == "true"


def job():
    try:
        sync_rss_to_sheet(RSS_FEED, limit=5)
        row, url, ws = get_next_unpublished()
        
        if not url:
            notify('TaskPilot', 'No hay URLs nuevas ni artículos en la hoja')
            return

        print('Selected article:', url)
        text = extract_text_from_url(url)

        if not text:
            print("Failed to extract text from the article.")
            return

        rewritten = rewrite_news(title='', description=text)
        caption = rewritten.strip()
        caption = caption.replace('\r\n', '\n').replace('\r', '\n')
        caption = caption.replace('. ', '.\n\n')

        if POST_REEL:
            # ── Flujo Reel ──────────────────────────────
            print("🎬 Generando Reel...")
            image_url = extract_article_img(url=url)
            reel_path = generate_reel(text, image_url=image_url, output_path="/tmp/reel_output.mp4")    
            result = post_reel_to_ig(caption=caption, video_path=reel_path)

            # Limpiar vídeo temporal
            if os.path.exists(reel_path):
                os.remove(reel_path)
        else:
            # ── Flujo post estático (original) ──────────
            image_url = extract_article_img(url=url)
            result = post_to_ig(caption=caption, image_url=image_url)

        print(result)
        update_sheet = mark_as_published(ws, row)
        print(update_sheet)
        notify(
            "✅ TaskPilot - Publicación realizada",
            f"Artículo: {url}\n\nResultado:\n{result}",
            update_sheet
        )

    except Exception as e:
        err = traceback.format_exc()
        print('Error en job')
        notify("❌ TaskPilot - Error crítico", f"{e}\n\nTraceback:\n{err}")


if __name__ == "__main__":
    job()