import tweepy
import os
import time
import textwrap
from dotenv import load_dotenv
load_dotenv()

bearer_token = os.getenv("BEARER_TOKEN")
api_key = os.getenv("API_KEY")
api_key_secret = os.getenv("API_KEY_SECRET")
access_token = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

client = tweepy.Client(bearer_token, api_key, api_key_secret, access_token, access_token_secret)
def post_tweet(text: str):
    response = client.create_tweet(text=text)
    return response.data

def split_into_tweets_safe(text, limit=280):
    """
    Divide un texto largo en varios tweets de forma segura,
    garantizando que ningún tweet (incluyendo el sufijo (x/n))
    exceda los 280 caracteres.
    """
    words = text.split()
    tweets = []
    current = ""

    for word in words:
        if len(current) + len(word) + 1 <= limit:
            current += (" " if current else "") + word
        else:
            tweets.append(current)
            current = word
    if current:
        tweets.append(current)

    total = len(tweets)
    safe_tweets = []
    for i, t in enumerate(tweets):
        suffix = f" ({i+1}/{total})"
        if len(t) + len(suffix) > limit:
            t = t[: limit - len(suffix) - 1] + "…"
        safe_tweets.append(t + suffix)

    return safe_tweets

def post_thread(text):
    tweets = split_into_tweets_safe(text)
    try:
        response = client.create_tweet(text=tweets[0])
        reply_to_id = response.data["id"]
        ids = [reply_to_id]

        for t in tweets[1:]:
            response = client.create_tweet(
                text=t,
                in_reply_to_tweet_id=reply_to_id
            )
            reply_to_id = response.data["id"]
            ids.append(reply_to_id)
            time.sleep(5)

        return ids
    except tweepy.errors.Forbidden as e:
        print(e.response.text)
        raise