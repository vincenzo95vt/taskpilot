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