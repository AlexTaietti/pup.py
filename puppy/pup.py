import time
import random
import sys
import re
import urllib.parse

from bs4 import BeautifulSoup as bs
from selenium import webdriver
from puppy.utils.nlp import tokenize
from puppy.utils.http import politely_get

class Puppy:

    def __init__(self, start, target, websocket, client_sid):
        self.current_url = self.start = start
        self.target = target
        self.history = list()
        self.tokenized_target = self.get_tokenized_target()
        self.skip = list()
        self.websocket = websocket
        self.client_sid = client_sid

    def emit_update(self, update_data):
        self.websocket.emit("puppy live update", {"update": update_data}, to=self.client_sid)

    def get_tokenized_target(self):
        response_text = politely_get(self.target)
        target_soup = bs(response_text, 'html.parser')
        elements = target_soup.select(".mw-parser-output p, .mw-parser-output h1, .mw-parser-output h2, .mw-parser-output h3, .mw-parser-output h4, .mw-parser-output dd")
        all_text_content = ' '.join([element.get_text() for element in elements])
        tokenized_target = tokenize(all_text_content)
        return tokenized_target

    def generate_sentence_map(self, inner_html):
        sentences = re.split(r"(\.( |$|<)|!|\?)(?![^<]*>)", inner_html)
        sentences_2_similarity = dict()
        for sentence in sentences:
            if not sentence:
                continue
            sentence_soup = bs(sentence, "html.parser")
            sentence_anchors = sentence_soup.find_all("a")
            sentence_text = sentence_soup.get_text()
            if not sentence_anchors or not sentence_text:
                continue
            tokenized_sentence = tokenize(sentence_text)
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
            viable_links = tuple(sentence_links)
            sentences_2_similarity[viable_links] = similarity
        return sentences_2_similarity

    def get_best_paragraph(self, current_article_soup):
        content_paragraphs = current_article_soup.select(".mw-parser-output p, .mw-parser-output h1, .mw-parser-output h2, .mw-parser-output h3, .mw-parser-output h4, .mw-parser-output dd")
        best_paragraph = None
        max_similarity = 0
        best_sentences = None
        for paragraph in content_paragraphs:
            if paragraph.find("a"):
                paragraph_html = paragraph.decode_contents().strip()
                if not paragraph_html:
                    continue
                sentences_2_similarity = self.generate_sentence_map(paragraph_html)
                if not sentences_2_similarity:
                    continue
                for sentence in sentences_2_similarity:
                    if sentences_2_similarity[sentence] > max_similarity:
                        max_similarity = sentences_2_similarity[sentence]
                        best_paragraph = paragraph
                        best_sentences = sentences_2_similarity
        return best_paragraph, best_sentences

    def find_target(self, all_article_anchors):
        for anchor in all_article_anchors:
            if anchor.parent.name in ["li", "b", "span"] or not anchor.parent.text:
                continue
            link = anchor.get("href")
            if not link or not link.startswith("/wiki/"):
                continue
            link = urllib.parse.unquote(link)
            if self.target.endswith(link):
                return anchor
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

    def get_best_links(self, best_sentences):
        best_urls = max(best_sentences, key=best_sentences.get)
        similarity = best_sentences[best_urls]
        self.history.append(self.current_url)
        return best_urls, similarity

    def make_update(self, best_paragraph_text_content, similarity):
        update_data = {
            "paragraph": re.sub("\[.*?\]|{.*?}", "", best_paragraph_text_content),
            "similarity": "{:.2f}".format(similarity),
            "current_url": self.current_url,
        }
        update = { "type": "INFO", "data": update_data }
        return update

    def make_success_update(self, best_paragraph_text_content, similarity):
        update_data = {
            "paragraph": re.sub("\[.*?\]|{.*?}", "", best_paragraph_text_content),
            "similarity": "{:.2f}".format(similarity),
            "current_url": self.current_url,
        }
        update = { "type": "SUCCESS", "data": update_data }
        return update

    def make_loop_failure(self):
        update_data = { "current_url": self.current_url }
        update = { "type": "LOOP", "data": update_data }
        return update

    def end_run(self, target):
        self.history.extend([self.current_url, self.target])
        best_paragraph_text = target.parent.text.strip()
        tokenized_sentence = tokenize(best_paragraph_text)
        similarity = tokenized_sentence.similarity(self.tokenized_target)
        update = self.make_success_update(best_paragraph_text, similarity)
        return self.emit_update(update)

    def loop_check(self, best_link):
        repetition_count = self.history.count(best_link)
        if repetition_count > 3:
            update = self.make_loop_failure()
            self.skip.append(best_link)
            self.history = []
            self.emit_update(update)
            self.current_url = self.start
            return True
        return False

    def run(self):
        while True:
            response_text = politely_get(self.current_url)
            current_article_soup = bs(response_text, "html.parser")
            all_anchors = current_article_soup.find_all("a")
            target_found = self.find_target(all_anchors)
            if target_found:
                return self.end_run(target_found)
            best_paragraph, best_sentences = self.get_best_paragraph(current_article_soup)
            best_links, similarity = self.get_best_links(best_sentences)
            if best_links:
                best_link = random.choice(best_links)
                loop = self.loop_check(best_link)
                if loop:
                    continue
                best_paragraph_text_content = best_paragraph.get_text().strip()
                update = self.make_update(best_paragraph_text_content, similarity)
                self.current_url = best_link
                self.emit_update(update)
