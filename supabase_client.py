import os
import time
import random
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_sb: Client | None = None


def get_supabase() -> Client:
    global _sb
    if _sb is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY son obligatorios")
        _sb = create_client(url, key)
    return _sb


# ─────────────────────────────────────────────
# RSS Feeds
# ─────────────────────────────────────────────

def get_active_feeds() -> list[str]:
    result = get_supabase().table("rss_feeds").select("url").eq("active", True).execute()
    return [row["url"] for row in result.data]


# ─────────────────────────────────────────────
# Articles (reemplaza Google Sheets)
# ─────────────────────────────────────────────

def sync_rss_to_db(feeds: list[str], limit: int = 5):
    from rss_client import get_rss_news
    sb = get_supabase()

    feeds = feeds.copy()
    random.shuffle(feeds)

    for feed_url in feeds:
        print(f"📡 Leyendo feed: {feed_url}")
        articles = get_rss_news(feed_url, limit=5)
        print(f"Artículos encontrados: {len(articles)}")

        for article in articles:
            url = article["link"].split("?")[0]
            existing = sb.table("articles").select("id").eq("url", url).execute()
            if not existing.data:
                sb.table("articles").insert({"url": url, "status": "pending"}).execute()
                print(f"✅ Añadido: {url}")
                return

        print(f"⚠️ Sin artículos nuevos en {feed_url}")

    print("⚠️ No hay artículos nuevos en ningún feed")


def get_next_unpublished() -> dict | None:
    result = (
        get_supabase()
        .table("articles")
        .select("id, url")
        .eq("status", "pending")
        .order("created_at")
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def mark_as_published(article_id: str) -> str:
    get_supabase().table("articles").update({
        "status": "published",
        "published_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }).eq("id", article_id).execute()
    return "Supabase actualizado"


# ─────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────

def get_prompt(name: str) -> dict:
    result = (
        get_supabase()
        .table("prompts")
        .select("system_prompt, user_prompt")
        .eq("name", name)
        .execute()
    )
    if not result.data:
        raise ValueError(f"Prompt '{name}' no encontrado en Supabase")
    return result.data[0]
