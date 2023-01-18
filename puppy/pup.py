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
        target_paragraphs = self.driver.find_elements(By.CSS_SELECTOR, ".mw-parser-output p, .mw-parser-output h1, .mw-parser-output h2, .mw-parser-output h3")
        all_text_content = ''
        for paragraph in target_paragraphs:
            all_text_content = ' '.join([all_text_content, paragraph.text])
        doc = self.nlp(all_text_content)
        tokenized_target = self.nlp(' '.join([str(token) for token in doc if token.pos_ in ['NOUN', 'PROPN']]))
        return tokenized_target

    def generate_paragraph_map(self):
        content_paragraphs = self.driver.find_elements(By.CSS_SELECTOR, ".mw-parser-output p, .mw-parser-output h1, .mw-parser-output h2, .mw-parser-output h3")
        paragraph_map = dict()
        for paragraph in content_paragraphs:
            if paragraph.find_elements(By.TAG_NAME, "a"):
                doc = self.nlp(paragraph.text)
                tokens = ' '.join([str(token) for token in doc if token.pos_ in ['NOUN', 'PROPN']])
                tokenized_paragraph = self.nlp(tokens)
                similarity = tokenized_paragraph.similarity(self.tokenized_target)
                paragraph_map[paragraph] = similarity
        return paragraph_map

    def find_target(self):
        anchors = self.driver.find_elements(By.TAG_NAME, "a")
        for anchor in anchors:
            link = anchor.get_attribute("href")
            if not link or "/en.wikipedia.org/wiki/" not in link:
                continue
            link = urllib.parse.unquote(link)
            if self.target == link:
                return True
        return False

    def clean_link(self, anchor):
        link = anchor.get_attribute("href")
        if not link or "/en.wikipedia.org/wiki/" not in link:
            return None
        link = urllib.parse.unquote(link)
        new_article_id = link.split("/")[4]
        if new_article_id == "Main_Page" or "?" in new_article_id or ":" in new_article_id or "#" in new_article_id:
            return None
        return link

    def get_best_links(self, paragraph_map):
        anchors = []
        for paragraph in paragraph_map:
            if paragraph_map[paragraph] > self.similarity_treshold:
                print("----------------------------------------")
                print("promising fragment found:\n")
                print(paragraph.text)
                print("----------------------------------------\n\n")
                anchors.extend(paragraph.find_elements(By.TAG_NAME, "a"))
        if not anchors and self.similarity_treshold > 0.35:
            self.similarity_treshold -= 0.05
            return self.get_best_links(paragraph_map)
        url_decoded_current_url = urllib.parse.unquote(self.driver.current_url)
        viable_articles = []
        current_page_id = url_decoded_current_url.split("/")[4]
        for anchor in anchors:
            valid_link = self.clean_link(anchor)
            if valid_link:
                viable_articles.append(valid_link)
        print(f"[*] {len(viable_articles)} viable articles found @ page {url_decoded_current_url} (similarity >= {self.similarity_treshold})\n")
        if not self.history or not self.history[-1] == current_page_id:
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
        self.similarity_treshold = 0.95

    def kill_driver(self):
        self.driver.close()
        self.driver.quit()

    def run(self):
        self.tokenized_target = self.get_tokenized_target()
        self.driver.get(self.start)
        while True:
            target_found = self.find_target()
            if target_found:
                self.history.append(self.target_id)
                self.kill_driver()
                return {"result": f"[*] Good boy! 🐶 fetched the target!\n[*] hops -> {self.history}"}
            paragraphs = self.generate_paragraph_map()
            viable_articles = self.get_best_links(paragraphs)
            if not viable_articles and self.similarity_treshold > 0.35:
                self.similarity_treshold -= 0.05
                continue
            if self.similarity_treshold < 0.95:
                self.similarity_treshold = 0.95
            if viable_articles:
                random_article = random.choice(viable_articles)
                self.driver.get(random_article)
                continue
            print("[!] Puppy got completely lost, going back to the beginning...")
            self.driver.get(self.start)


if __name__ == "__main__":
    puppy = Puppy(sys.argv[1].strip(), sys.argv[2].strip())
    puppy.target_freq = puppy.get_target_tokens_freq("https://en.wikipedia.org/wiki/Lionel_Messi")
    fit = puppy.generate_paragraph_map("https://en.wikipedia.org/wiki/Cristiano_Ronaldo")
    best_links = puppy.get_best_links(fit)

