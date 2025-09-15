import tweepy


client = tweepy.Client(bearer_token, api_key, api_key_secret, access_token, access_token_secret)

response = client.create_tweet(text="Hello, world!")
print("Tweeted:", response.data)