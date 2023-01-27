import time
import random
import sys
import re
import spacy
import urllib.parse
import requests

from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.by import By


class Puppy:

    nlp = spacy.load('en_core_web_lg')

    def __init__(self, start, target):
        self.current_url = self.start = start
        self.target = target
        self.history = list()
        self.tokenized_target = self.get_tokenized_target()
        self.skip = list()

    def tokenize(self, text):
        lowercase_text = text.lower()
        doc = self.nlp(lowercase_text)
        dirt = re.compile(r"\.|\[.*?]|\(.*?\)|[1-9]*$|{.*?}")
        doc = self.nlp(' '.join([re.sub(dirt, '', token.text) if token.pos_ == "PROPN" else re.sub(dirt, '', token.lemma_) for token in doc if token.pos_ == "NOUN"]))
        return doc

    def get_tokenized_target(self):
        response = requests.get(self.target)
        target_soup = bs(response.text, 'html.parser')
        elements = target_soup.select(".mw-parser-output p, .mw-parser-output h1, .mw-parser-output h2, .mw-parser-output h3, .mw-parser-output h4, .mw-parser-output dd")
        all_text_content = ' '.join([element.get_text() for element in elements])
        tokenized_target = self.tokenize(all_text_content)
        return tokenized_target

    def generate_sentence_map(self, inner_html):
        sentences = re.split(r"(\.( |$|<)|!|\?)(?![^<]*>)", inner_html)
        sentences_map = dict()
        for sentence in sentences:
            if not sentence:
                continue
            sentence_soup = bs(sentence, "html.parser")
            sentence_anchors = sentence_soup.find_all("a")
            if not sentence_anchors:
                continue
            tokenized_sentence = self.tokenize(sentence_soup.get_text())
            similarity = tokenized_sentence.similarity(self.tokenized_target)
            sentence_links = []
            for anchor in sentence_anchors:
                url = anchor.get("href")
                url = self.clean_link(url)
                if not url:
                    continue
                sentence_links.append(url)
            if not sentence_links:
                continue
            clean_links = tuple(sentence_links)
            sentences_map[clean_links] = similarity
        return sentences_map

    def generate_paragraph_map(self, current_article_soup):
        content_paragraphs = current_article_soup.select(".mw-parser-output p, .mw-parser-output h1, .mw-parser-output h2, .mw-parser-output h3, .mw-parser-output h4, .mw-parser-output dd")
        paragraph_map = dict()
        for paragraph in content_paragraphs:
            if paragraph.find("a"):
                paragraph_html = paragraph.decode_contents().strip()
                if not paragraph_html:
                    continue
                sentences_map = self.generate_sentence_map(paragraph_html)
                if not sentences_map:
                    continue
                tokenized_paragraph = self.tokenize(paragraph.get_text())
                similarity = tokenized_paragraph.similarity(self.tokenized_target)
                paragraph_map[paragraph] = {"sim": similarity, "sents_map": sentences_map}
        return paragraph_map

    def find_target(self, all_article_anchors):
        for anchor in all_article_anchors:
            link = anchor.get("href")
            if not link or not link.startswith("/wiki/"):
                continue
            link = urllib.parse.unquote(link)
            if self.target.endswith(link):
                return True
        return False

    def clean_link(self, link):
        if not link or not link.startswith("/wiki/"):
            return None
        link = urllib.parse.unquote(link)
        if "Main_Page" in link or link in self.target or "#" in link or "?" in link or ":" in link:
            return None
        link = f"https://en.wikipedia.org{link}"
        if link in self.skip:
            return None
        return link

    def get_best_links(self, paragraph_map):
        anchors = []
        max_p = max(paragraph_map, key=lambda p: paragraph_map[p]['sim'])
        sents_map = paragraph_map[max_p]["sents_map"]
        max_urls = max(sents_map, key=sents_map.get)
        similarity = "{:.2f}".format(sents_map[max_urls])
        print(f"[*] {len(max_urls)} viable articles found @ page {self.current_url} (similarity ~ {similarity})")
        self.history.append(self.current_url)
        return max_p, max_urls

    def run(self):
        while True:
            time.sleep(0.3)
            response = requests.get(self.current_url)
            current_article_soup = bs(response.text, "html.parser")
            all_anchors = current_article_soup.find_all("a")
            target_found = self.find_target(all_anchors)
            if target_found:
                self.history.extend([self.current_url, self.target])
                success_log = f"[*] Good boy! 🐶 fetched the target in {len(self.history)} hops!\n[*] {self.history}"
                print(success_log)
                return {"result": success_log}
            paragraphs = self.generate_paragraph_map(current_article_soup)
            if not paragraphs:
                print(f"[!] no viable paragraphs detected @ {self.current_url}")
                print(f"[!] banning {self.current_url} and going back to the starting page...")
                self.skip.append(self.current_url)
                self.history = []
                self.current_url = self.start
                continue
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            best_paragraph, viable_articles = self.get_best_links(paragraphs)
            if viable_articles:
                print(f"[+] following is the most promising paragraph found @ {self.current_url}:\n«{best_paragraph.get_text().strip()}»")
                best_link = random.choice(viable_articles)
                if self.history.count(best_link) > 3:
                    print(f"[!] loop detected! Puppy has visited {best_link} more than 3 times already during this run")
                    print(f"[!] banning {best_link} and going back to the starting page...")
                    self.skip.append(best_link)
                    self.history = []
                    best_link = self.start
                print(f"[+] next stop is {best_link}")
                self.current_url = best_link
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
                continue
            print("[!] Puppy got completely lost, going back to the beginning...")
            self.current_url = self.start

