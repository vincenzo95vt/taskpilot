import tweepy
import os
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

def split_into_tweets(text, limit =280):
    words = text.split()
    tweets = []
    current = ''

    for word in words:
        if len(current) + len(word) +1 <= limit:
            current += (" " if current else "") + word
        else: 
            tweets.append(current)
            current = word 
    if current:
        tweets.append(current)
    total = len(tweets)
    tweets =[f"{t} ({i + 1}/{total})" for i, t in enumerate(tweets)]
    return tweets

def post_thread(text):
    tweets = split_into_tweets(text)

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

    return ids