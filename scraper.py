from newspaper import Article

def extract_text_from_url(url: str):
    article = Article(url)
    article.download()
    article.parse()
    return article.title, article.text
