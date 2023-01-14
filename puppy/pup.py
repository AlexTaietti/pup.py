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
    nlp = spacy.load('en_core_web_sm')

    def get_target_tokens_freq(self):
        page_tokens = dict()
        self.driver.get(self.target)
        content_paragraphs = self.driver.find_elements(By.CSS_SELECTOR, "#bodyContent p")
        for paragraph in content_paragraphs:
            if paragraph.find_elements(By.TAG_NAME, "a"):
                doc = self.nlp(paragraph.text)
                tokens = [token.text for token in doc if token.pos_=="NOUN"]
                for token in tokens:
                    if token not in page_tokens:
                        page_tokens[token] = 1
                    page_tokens[token] += 1
        return page_tokens

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
        content_paragraphs = self.driver.find_elements(By.CSS_SELECTOR, "#bodyContent p")
        paragraph_map = dict()
        for paragraph in content_paragraphs:
            if paragraph.find_elements(By.TAG_NAME, "a"):
                paragraph_map[paragraph] = 0
                doc = self.nlp(paragraph.text)
                tokens = [token.text for token in doc if token.pos_=="NOUN"]
                for token in tokens:
                    if token in self.target_freq:
                        paragraph_map[paragraph] += self.target_freq[token]
        return paragraph_map

    def get_best_links(self, paragraph_map):
        sorted_paragraphs = {k: v for k, v in sorted(paragraph_map.items(), key=lambda item: item[1])}
        anchors = []
        if len(sorted_paragraphs) <= 5:
            for paragraph in sorted_paragraphs:
                print(sorted_paragraphs[paragraph])
                anchors.extend(paragraph.find_elements(By.TAG_NAME, "a"))
        else:
            for i in range(4):
                keys = list(sorted_paragraphs.keys())
                paragraph = keys[len(keys) - (1 + i)]
                print(sorted_paragraphs[paragraph])
                anchors.extend(paragraph.find_elements(By.TAG_NAME, "a"))
        viable_articles = []
        current_page_id = self.driver.current_url.split("/")[4]
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
        self.target_freq = dict()

    def kill_driver(self):
        self.driver.close()
        self.driver.quit()

    def find_viable_articles(self, url):
        self.driver.implicitly_wait(self.polite_wait)
        self.driver.get(url)
        print(f"[*] 🐶 is now visiting {url}")
        current_page_id = url.split("/")[4]
        anchors = self.driver.find_elements(By.TAG_NAME, 'a')
        viable_articles = []
        for anchor in anchors:
            link = anchor.get_attribute("href")
            if not link or "/en.wikipedia.org/wiki/" not in link:
                continue
            link = urllib.parse.unquote(link)
            new_article_id = link.split("/")[4]
            if current_page_id == new_article_id or new_article_id in self.history or "?" in new_article_id or ":" in new_article_id or "#" in new_article_id:
                continue
            viable_articles.append(link)
        print(f"[*] {len(viable_articles)} viable articles found @ page {url}")
        self.history.append(current_page_id)
        return viable_articles

    def go(self):
        self.target_freq = self.get_target_tokens_freq()
        while True:
            viable_articles = self.find_viable_articles(self.current_url)
            if self.target in viable_articles:
                self.history.append(self.target_id)
                self.kill_driver()
                return f"[*] Good boy! 🐶 fetched the target!\n[*] hops -> {self.history}"
            self.driver.get(random.choice(viable_articles))

    def run(self):
        self.target_freq = self.get_target_tokens_freq()
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
                print(random_article)
                self.driver.get(random_article)
            else:
                random_article = self.pick_random_link()
                self.driver.get(random_article)


if __name__ == "__main__":
    puppy = Puppy(sys.argv[1].strip(), sys.argv[2].strip())
    puppy.target_freq = puppy.get_target_tokens_freq("https://en.wikipedia.org/wiki/Lionel_Messi")
    fit = puppy.generate_paragraph_map("https://en.wikipedia.org/wiki/Cristiano_Ronaldo")
    best_links = puppy.get_best_links(fit)

