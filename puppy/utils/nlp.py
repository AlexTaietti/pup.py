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
