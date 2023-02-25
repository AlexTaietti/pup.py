import time
import random
import sys
import re
import urllib.parse
import requests

from bs4 import BeautifulSoup as bs, NavigableString
from selenium import webdriver
from puppy.utils.nlp import tokenize

class Puppy:

    def __init__(self, websocket_event_emitter):
        self.history = list()
        self.tokenized_target = None
        self.skip = list()
        self.start = None
        self.target = None
        self.websocket_event_emitter = websocket_event_emitter
        self.socket_id = None
        self.current_url = None

    def tokenize_article(self, article_text): # need to find a way of fetching the response from the manager
        target_soup = bs(article_text, 'lxml')
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

    def reset(self):
        self.start = None
        self.target = None
        self.tokenized_target = None
        return None

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
            if clean_article_link in self.skip:
                anchor.unwrap()
                continue
            anchor["href"] = clean_article_link
            if self.target == clean_article_link:
                return anchor
        return None

    def make_update(self, best_paragraph_text_content, similarity, update_type="INFO"):
        update_data = {
            "paragraph": best_paragraph_text_content,
            "similarity": "{:.2f}".format(similarity),
            "current_url": self.current_url
        }
        update = { "type": update_type, "data": update_data }
        self.websocket_event_emitter("puppy live update", {"update": update}, to=self.socket_id)

    def make_loop_failure(self):
        update_data = {"current_url": self.current_url}
        update = { "type": "LOOP", "data": update_data }
        self.websocket_event_emitter("puppy live update", {"update": update}, to=self.socket_id)

    def unbind(self):
        self.reset()
        self.socket_id = None
        return None

    def end_run(self, article_soup, target):
        clean_target_link = target.get("href")
        tokenized_sentence = tokenize(target.parent.text.strip())
        similarity = tokenized_sentence.similarity(self.tokenized_target)
        current_node = target
        best_paragraph_text_content = None
        while current_node.parent:
            parent = current_node.parent
            if parent.name == "p":
                best_paragraph_text_content = self.highlight_target(target.parent, target)
                break
            if parent.name == "table":
                if parent.has_attr('class') and "wikitable" in parent.get("class"):
                    best_paragraph_text_content = str(parent)
                    break
                if parent.has_attr('class') and "navbox-inner" in parent.get("class"):
                    new_table_element = article_soup.new_tag("table")
                    new_table_header = article_soup.new_tag("th")
                    table_rows = parent.select("tbody tr", recursive=False)
                    table_title = table_rows.pop(0)
                    abbreviations = table_title.select("abbr")
                    for abbr in abbreviations:
                        abbr.decompose()
                    new_table_header.string = table_title.get_text()
                    new_table_element.append(new_table_header)
                    for row in table_rows:
                        new_table_row = article_soup.new_tag("tr")
                        if row.find("th", recursive=False):
                            current_row_title = row.find("th").get_text()
                            new_row_title = article_soup.new_tag("h4")
                            new_row_title.string = current_row_title
                            new_table_row.append(new_row_title.decode_contents())
                        row_data = row.find("td")
                        if row_data.find("ul"):
                            new_list = article_soup.new_tag("ul")
                            new_row_data = article_soup.new_tag("td")
                            inner_list = row_data.find("ul")
                            list_items = inner_list.find_all("li")
                            for item in list_items:
                                item_anchor = item.find("a")
                                if item_anchor and item_anchor != target:
                                    item_anchor.unwrap()
                                new_item = article_soup.new_tag("li")
                                new_list.append(item)
                            new_row_data.append(new_list)
                            new_table_row.append(new_row_data)
                        else:
                            new_table_row.append(row_data)
                        new_table_element.append(new_table_row)
                    best_paragraph_text_content = str(new_table_element)
                break
            if parent.has_attr('class') and "thumbinner" in parent.get("class"):
                best_paragraph_text_content = str(parent)
                break
            current_node = parent
        self.make_update(best_paragraph_text_content, similarity, update_type="SUCCESS")
        return self.unbind()


    def highlight_target(self, soup, target_anchor):
        for tag in soup.find_all(True):
            if tag == target_anchor:
                tag["class"] = "target"
                del tag["title"]
            elif tag.unwrap:
                tag.unwrap()
        return f"“{soup.decode_contents().strip()}”"


    def process_article(self, article_content):
        current_article_soup = bs(article_content, "lxml")
        all_superscript_tags = current_article_soup.find_all("sup")
        for superscript_tag in all_superscript_tags:
            superscript_tag.decompose()
        all_anchors = current_article_soup.find_all("a")
        target_found = self.process_anchors(all_anchors)
        if target_found:
            return self.end_run(current_article_soup, target_found)
        best_paragraph, best_sentences = self.get_best_paragraph(current_article_soup)
        if best_sentences:
            best_anchors = max(best_sentences, key=best_sentences.get)
            similarity = best_sentences[best_anchors]
            best_anchor = random.choice(best_anchors)
            best_link = best_anchor.get("href")
            if self.history.count(best_link) > 3:
                self.skip.append(best_link) # if stuck in a loop silently try another link on the current page
                return self.current_url
            update_content = self.highlight_target(best_paragraph, best_anchor)
            self.make_update(update_content, similarity)
            self.history.append(self.current_url)
            return best_link
        self.skip.append(self.current_url) # if the current article cannot be used for lack of viable anchor tags silently go back to the last page visited and try another link
        return self.history.pop()

    def go(self, article_url, manager_queue):
        self.current_url = article_url
        article_content = requests.get(article_url).text
        next_article = self.process_article(article_content)
        if not next_article:
            return 1337
        manager_queue.insert(0, (self, "go", (next_article, manager_queue)))


    def init_run(self, start, target, socket_id, manager_queue):
        self.start = start
        self.target = target
        target_content = requests.get(target).text
        self.tokenized_target = self.tokenize_article(target_content)
        self.socket_id = socket_id
        manager_queue.insert(0, (self, "go", (self.start, manager_queue)))

