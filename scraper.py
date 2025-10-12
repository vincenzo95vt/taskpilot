from newspaper import Article
def extract_article_img(url: str):
    try:
        article = Article(url)
        article.download()
        article.parse()
        image = article.top_image if article.top_image else None
        return image
    except Exception as e:
        print(f"Error al sacar la imagen del articulo: {e}" )
        return {image}

def extract_text_from_url(url: str):
    article = Article(url)
    article.download()
    article.parse()
    return article.title, article.text
extract_article_img('https://www.genbeta.com/laboral/los-trabajadores-jovenes-son-la-generacion-a-la-que-menos-les-importa-el-salario-pero-valoran-mucho-otras-cosas-de-una-empresa')