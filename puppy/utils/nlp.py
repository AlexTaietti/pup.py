import spacy
import re

NLP = spacy.load('en_core_web_lg')
DIRT = re.compile(r"\.|\[.*?]|\(.*?\)|[1-9]*$|{.*?}")


def tokenize(text):
    lowercase_text = text.lower()
    doc = NLP(lowercase_text)
    clean_doc = NLP(' '.join([re.sub(DIRT, '', token.text) for token in doc if token.pos_ in ["PROPN", "NOUN"]]))
    doc = NLP(' '.join([token.text if token.pos_ == "PROPN" else token.lemma_ for token in clean_doc if token.pos_ == "NOUN"]))
    return doc


def tokenize_article(target_soup):
    elements = target_soup.select(".mw-parser-output > p")
    all_text_content = ' '.join([element.get_text() for element in elements])
    tokenized_target = tokenize(all_text_content)
    return tokenized_target
