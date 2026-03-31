from rss_client import get_rss_news
from writer import rewrite_news, rewrite_for_linkedin
from twitter_client import post_tweet, post_thread
from supabase_client import get_next_unpublished, sync_rss_to_db, mark_as_published, get_active_feeds
from scraper import extract_article_img, extract_text_from_url
from utils.utils import format_caption
from instagram_client import post_to_ig, post_reel_to_ig
from datetime import datetime
from linkedin_client import post_to_linkedin, post_video_to_linkedin
from notifier import notify, send_telegram
from reel_generator import generate_reel
import traceback
import os


POST_REEL = os.getenv("POST_REEL", "false").lower() == "true"


def job():
    try:
        feeds = get_active_feeds()
        sync_rss_to_db(feeds)
        article = get_next_unpublished()

        if not article:
            send_telegram('TaskPilot: No hay URLs nuevas ni artículos en la hoja')
            return

        url = article["url"]
        article_id = article["id"]
        print('Selected article:', url)

        text = extract_text_from_url(url)
        if not text:
            send_telegram("Failed to extract text from the article.")
            return

        rewritten = rewrite_news(description=text)
        caption = rewritten.strip()
        caption = caption.replace('\r\n', '\n').replace('\r', '\n')
        caption = caption.replace('. ', '.\n\n')
        caption_linkedin = rewrite_for_linkedin(text)

        if POST_REEL:
            # ── Flujo Reel ──────────────────────────────
            print("🎬 Generando Reel...")
            image_url = extract_article_img(url=url)
            reel_path = generate_reel(text, image_url=image_url, output_path="/tmp/reel_output.mp4")
            result = post_reel_to_ig(caption=caption, video_path=reel_path)
            day = datetime.now().weekday()
            if day in [1, 4]:
                print('🎬 Publicando vídeo en LinkedIn...')
                result_linkedin = post_video_to_linkedin(caption, reel_path)
            else:
                print("📝 Publicando texto + imagen en LinkedIn...")
                result_linkedin = post_to_linkedin(caption_linkedin, image_url)

            send_telegram(result_linkedin)
            if os.path.exists(reel_path):
                os.remove(reel_path)
        else:
            image_url = extract_article_img(url=url)
            result = post_to_ig(caption=caption, image_url=image_url)

        update_result = mark_as_published(article_id)
        print(update_result)
        notify(
            "✅ TaskPilot - Publicación realizada",
            f"Artículo: {url}\n\nResultado:\n{result}",
            update_result
        )

    except Exception as e:
        err = traceback.format_exc()
        print('Error en job')
        notify("❌ TaskPilot - Error crítico", f"{e}\n\nTraceback:\n{err}", url)


if __name__ == "__main__":
    job()
