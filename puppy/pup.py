import time
import random
import sys
import re
import urllib.parse

from bs4 import BeautifulSoup as bs, NavigableString
from selenium import webdriver
from puppy.utils.nlp import tokenize
from puppy.utils.http import politely_get

class Puppy:

    def __init__(self, websocket_event_emitter):
        self.current_url = None
        self.start = None
        self.target = None
        self.history = list()
        self.tokenized_target = None
        self.skip = list()
        self.websocket_event_emitter = websocket_event_emitter
        self.socket_id = None
        self.running = False

    def goodbye(self):
        self.running = False
        self.socket_id = None
        self.websocket_event_emitter = None

    def emit_update(self, update_data):
        if self.running:
            self.websocket_event_emitter("puppy live update", {"update": update_data}, to=self.socket_id)

    def tokenize_article(self, article_url):
        response_text = politely_get(article_url)
        target_soup = bs(response_text, 'lxml')
        elements = target_soup.select(".mw-parser-output > p")
        all_text_content = ' '.join([element.get_text() for element in elements])
        tokenized_target = tokenize(all_text_content)
        return tokenized_target

    def generate_sentence_map(self, inner_html):
        reg = re.compile(r"\.(?= [A-Z]|<)|$|!|\?(?![^<]*>)")
        sentences = re.split(reg, inner_html)
        sentences = filter(None, sentences)
        sentences_2_similarity = dict()
        for sentence in sentences:
            sentence_soup = bs(sentence, "lxml")
            sentence_anchors = sentence_soup.find_all("a")
            sentence_text = sentence_soup.get_text()
            if not sentence_anchors or not sentence_text:
                continue
            tokenized_sentence = tokenize(sentence_text)
            similarity = tokenized_sentence.similarity(self.tokenized_target)
            hashable_anchors_list = tuple(sentence_anchors)
            sentences_2_similarity[hashable_anchors_list] = similarity
        return sentences_2_similarity

    def get_best_paragraph(self, current_article_soup):
        content_paragraphs = current_article_soup.select(".mw-parser-output > p")
        best_paragraph = None
        max_similarity = -1
        best_sentences = None
        for paragraph in content_paragraphs:
            if paragraph.find("a"):
                paragraph_html = str(paragraph).strip()
                sentences_2_similarity = self.generate_sentence_map(paragraph_html)
                if sentences_2_similarity:
                    for sentence in sentences_2_similarity:
                        if sentences_2_similarity[sentence] > max_similarity:
                            max_similarity = sentences_2_similarity[sentence]
                            best_paragraph = paragraph
                            best_sentences = sentences_2_similarity
        return best_paragraph, best_sentences

    def process_anchors(self, all_article_anchors):
        for anchor in all_article_anchors:
            link = anchor.get("href")
            if not link or not link.startswith("/wiki/"):
                anchor.unwrap()
                continue
            link = urllib.parse.unquote(link)
            if "Main_Page" in link or re.search('#|\?|!|Template|Help', link):
                anchor.unwrap()
                continue
            clean_article_link = f"https://en.wikipedia.org{link}"
            anchor["href"] = clean_article_link
            if self.target == clean_article_link:
                return anchor
        return None

    def make_update(self, best_paragraph_text_content, similarity, update_type="INFO"):
        update_data = {
            "paragraph": best_paragraph_text_content,
            "similarity": "{:.2f}".format(similarity),
            "current_url": self.current_url,
        }
        update = { "type": update_type, "data": update_data }
        return update

    def make_loop_failure(self):
        update_data = { "current_url": self.current_url }
        update = { "type": "LOOP", "data": update_data }
        return update

    def end_run(self, target):
        clean_target_link = target.get("href")
        self.history.extend([self.current_url, clean_target_link])
        tokenized_sentence = tokenize(target.parent.text.strip())
        similarity = tokenized_sentence.similarity(self.tokenized_target)
        best_paragraph_text_content = self.highlight_target(target.parent, target)
        update = self.make_update(best_paragraph_text_content, similarity, update_type="SUCCESS")
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

    def highlight_target(self, soup, target_anchor):
        for tag in soup.find_all(True):
            if tag == target_anchor:
                tag["class"] = "target"
                del tag["title"]
            elif tag.unwrap:
                tag.unwrap()
        return f"“{soup.decode_contents().strip()}”"

    def run(self, start, target, socket_id):
        self.current_url = self.start = start
        self.target = target
        self.socket_id = socket_id
        self.tokenized_target = self.tokenize_article(target)
        self.running = True
        while self.running:
            response_text = politely_get(self.current_url)
            current_article_soup = bs(response_text, "lxml")
            all_superscript_tags = current_article_soup.find_all("sup")
            for superscript_tag in all_superscript_tags:
                superscript_tag.decompose()
            all_anchors = current_article_soup.find_all("a")
            target_found = self.process_anchors(all_anchors)
            if target_found:
                self.end_run(target_found)
                self.running = False
                break
            best_paragraph, best_sentences = self.get_best_paragraph(current_article_soup)
            if not best_sentences: # silently go back to the last page visited and try another link
                self.history = []
                self.skip.append(self.current_url)
                self.current_url = self.history.pop()
                continue
            best_anchors = max(best_sentences, key=best_sentences.get)
            similarity = best_sentences[best_anchors]
            self.history.append(self.current_url)
            if best_anchors:
                best_anchor = random.choice(best_anchors)
                best_link = best_anchor.get("href")
                loop = self.loop_check(best_link)
                if loop:
                    continue
                update_content = self.highlight_target(best_paragraph, best_anchor)
                update = self.make_update(update_content, similarity)
                self.current_url = best_link
                self.emit_update(update)
