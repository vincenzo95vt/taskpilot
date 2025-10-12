def format_caption(text, max_sentences_per_paragraph=2):
    sentences = text.split('. ')
    paragraphs = [
        '. '.join(sentences[i:i + max_sentences_per_paragraph]) 
        for i in range(0, len(sentences), max_sentences_per_paragraph)
    ]
    return '\n\n'.join(paragraphs)