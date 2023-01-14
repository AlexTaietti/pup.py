import time
import random
import sys
import spacy
import urllib.parse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


class Puppy:

    polite_wait = 1
    nlp = spacy.load('en_core_web_lg')

    def get_tokenized_target(self):
        self.driver.get(self.target)
        target_paragraphs = self.driver.find_elements(By.CSS_SELECTOR, ".mw-parser-output > p")
        print(target_paragraphs)
        all_text_content = ''
        for paragraph in target_paragraphs:
            all_text_content = ' '.join([all_text_content, paragraph.text])
        doc = self.nlp(all_text_content)
        tokenized_target = self.nlp(' '.join([str(token) for token in doc if token.pos_ in ['NOUN', 'PROPN']]))
        return tokenized_target


    def pick_random_link(self):
        anchors = self.driver.find_elements(By.TAG_NAME, "a")
        clean_links = []
        current_page_id = urllib.parse.unquote(self.driver.current_url.split("/")[4])
        for anchor in anchors:
            link = anchor.get_attribute("href")
            if not link or "/en.wikipedia.org/wiki/" not in link:
                continue
            link = urllib.parse.unquote(link)
            new_article_id = link.split("/")[4]
            if current_page_id == new_article_id or new_article_id in self.history or "?" in new_article_id or ":" in new_article_id or "#" in new_article_id:
                continue
            clean_links.append(link)
        return random.choice(clean_links)

    def generate_paragraph_map(self):
        content_paragraphs = self.driver.find_elements(By.CSS_SELECTOR, ".mw-parser-output > p")
        paragraph_map = dict()
        for paragraph in content_paragraphs:
            if paragraph.find_elements(By.TAG_NAME, "a"):
                doc = self.nlp(paragraph.text)
                tokenized_paragraph = self.nlp(' '.join([str(token) for token in doc if token.pos_ in ['NOUN', 'PROPN']]))
                similarity = tokenized_paragraph.similarity(self.tokenized_target)
                paragraph_map[paragraph] = similarity
        return paragraph_map

    def get_best_links(self, paragraph_map):
        anchors = []
        for paragraph in paragraph_map:
            if paragraph_map[paragraph] > 0.65:
                print("promising paragraph found:\n")
                print(paragraph.text)
                print("----------------------------------------\n\n\n")
                anchors.extend(paragraph.find_elements(By.TAG_NAME, "a"))
        viable_articles = []
        current_page_id = urllib.parse.unquote(self.driver.current_url.split("/")[4])
        for anchor in anchors:
            link = anchor.get_attribute("href")
            if not link or "/en.wikipedia.org/wiki/" not in link:
                continue
            link = urllib.parse.unquote(link)
            new_article_id = link.split("/")[4]
            if current_page_id == new_article_id or new_article_id in self.history or "?" in new_article_id or ":" in new_article_id or "#" in new_article_id:
                continue
            viable_articles.append(link)
        print(f"[*] {len(viable_articles)} viable articles found @ page {self.driver.current_url}")
        self.history.append(current_page_id)
        return viable_articles


    def __init__(self, start, target):
        self.current_url = self.start = start
        self.target = target
        self.start_id = start.split("/")[4]
        self.target_id = target.split("/")[4]
        self.driver = webdriver.Firefox()
        self.history = list()
        self.tokenized_target = None

    def kill_driver(self):
        self.driver.close()
        self.driver.quit()

    def run(self):
        self.tokenized_target = self.get_tokenized_target()
        self.driver.get(self.start)
        while True:
            paragraphs = self.generate_paragraph_map()
            viable_articles = self.get_best_links(paragraphs)
            if self.target in viable_articles:
                self.history.append(self.target_id)
                self.kill_driver()
                return f"[*] Good boy! 🐶 fetched the target!\n[*] hops -> {self.history}"
            if viable_articles:
                random_article = random.choice(viable_articles)
                self.driver.get(random_article)
            else:
                random_article = self.pick_random_link()
                self.driver.get(random_article)


if __name__ == "__main__":
    puppy = Puppy(sys.argv[1].strip(), sys.argv[2].strip())
    puppy.target_freq = puppy.get_target_tokens_freq("https://en.wikipedia.org/wiki/Lionel_Messi")
    fit = puppy.generate_paragraph_map("https://en.wikipedia.org/wiki/Cristiano_Ronaldo")
    best_links = puppy.get_best_links(fit)

