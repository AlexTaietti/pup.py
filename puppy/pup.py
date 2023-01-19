import time
import random
import sys
import re
import urllib.parse
import pprint
import spacy

from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.by import By


class Puppy:

    nlp = spacy.load('en_core_web_lg')

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

    def get_tokenized_target(self):
        self.driver.get(self.target)
        target_paragraphs = self.driver.find_elements(By.CSS_SELECTOR, ".mw-parser-output p, .mw-parser-output h1, .mw-parser-output h2, .mw-parser-output h3, .mw-parser-output h4, .mw-parser-output dd")
        all_text_content = ''
        for paragraph in target_paragraphs:
            clean_paragraph = re.sub("\[.*?\]", "", paragraph.text)
            clean_paragraph = clean_paragraph.replace("\n", " ")
            all_text_content = ' '.join([all_text_content, clean_paragraph])
        doc = self.nlp(all_text_content.lower())
        tokenized_target = self.nlp(' '.join([str(token) for token in doc if token.pos_ in ["NOUN", "PROPN"]]))
        return tokenized_target

    def generate_sentence_map(self, inner_html):
        sentences = re.split(r"(\.( |$|<)|!|\?)(?![^<]*>)", inner_html)
        sentences_map = dict()
        for sentence in sentences:
            if not sentence:
                continue
            soupy_sentence = bs(sentence, features="html.parser")
            clean_sentence = soupy_sentence.get_text().replace("\n", " ")
            doc = self.nlp(clean_sentence.lower())
            tokenized_sentence = self.nlp(' '.join([str(token) for token in doc if token.pos_ in ["NOUN", "PROPN"]]))
            if not tokenized_sentence:
                continue
            similarity = tokenized_sentence.similarity(self.tokenized_target)
            sentence_anchors = soupy_sentence.find_all("a")
            if not sentence_anchors:
                continue
            sentence_links = []
            for anchor in sentence_anchors:
                url = anchor.get("href")
                if not url or not url.startswith("/wiki/"):
                    continue
                url = f"https://en.wikipedia.org{urllib.parse.unquote(url)}"
                sentence_links.append(url)
            clean_links = []
            for link in sentence_links:
                link = self.clean_link(link)
                if not link:
                    continue
                clean_links.append(link)
            if not clean_links:
                continue
            clean_links = tuple(clean_links)
            sentences_map[clean_links] = similarity
        return sentences_map

    def generate_paragraph_map(self):
        content_paragraphs = self.driver.find_elements(By.CSS_SELECTOR, ".mw-parser-output p, .mw-parser-output h1, .mw-parser-output h2, .mw-parser-output h3, .mw-parser-output h4, .mw-parser-output dd")
        paragraph_map = dict()
        for paragraph in content_paragraphs:
            if paragraph.find_elements(By.TAG_NAME, "a"):
                clean_paragraph_html = re.sub("\[.*?\]", "", paragraph.get_attribute("innerHTML"))
                sentences_map = self.generate_sentence_map(clean_paragraph_html)
                if not sentences_map:
                    continue
                clean_paragraph = re.sub("\[.*?\]", "", paragraph.text.replace("\n", " ")) 
                doc = self.nlp(clean_paragraph.lower())
                tokenized_paragraph = self.nlp(' '.join([str(token) for token in doc if token.pos_ in ["NOUN", "PROPN"]]))
                similarity = tokenized_paragraph.similarity(self.tokenized_target)
                paragraph_map[paragraph] = {"sim": similarity, "sents_map": sentences_map}
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

    def clean_link(self, link):
        if not link or "/en.wikipedia.org/wiki/" not in link:
            return None
        link = urllib.parse.unquote(link)
        new_article_id = link.split("/")[4]
        if new_article_id == "Main_Page" or new_article_id == self.target_id or "#" in new_article_id or "?" in new_article_id or ":" in new_article_id:
            return None
        return link

    def get_best_links(self, paragraph_map):
        anchors = []
        max_p = max(paragraph_map, key=lambda p: paragraph_map[p]['sim'])
        sents_map = paragraph_map[max_p]["sents_map"]
        max_urls = max(sents_map, key=sents_map.get)
        similarity = "{:.2f}".format(sents_map[max_urls])
        url_decoded_current_url = urllib.parse.unquote(self.driver.current_url)
        viable_articles = []
        current_page_id = url_decoded_current_url.split("/")[4]
        print(f"[+] primary search found these: {max_urls}")
        for url in max_urls:
            valid_link = self.clean_link(url)
            if valid_link:
                viable_articles.append(valid_link)
        print(f"[+] {len(viable_articles)} viable articles found @ page {url_decoded_current_url} (similarity ~ {similarity})")
        if not self.history or not self.history[-1] == current_page_id:
            self.history.append(current_page_id)
        return viable_articles

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
            if viable_articles:
                best_link = random.choice(viable_articles)
                self.driver.get(best_link)
                continue
            print("[!] Puppy got completely lost, going back to the beginning...")
            self.driver.get(self.start)


if __name__ == "__main__":
    puppy = Puppy(sys.argv[1].strip(), sys.argv[2].strip())
    puppy.target_freq = puppy.get_target_tokens_freq("https://en.wikipedia.org/wiki/Lionel_Messi")
    fit = puppy.generate_paragraph_map("https://en.wikipedia.org/wiki/Cristiano_Ronaldo")
    best_links = puppy.get_best_links(fit)

