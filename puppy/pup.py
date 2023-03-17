import random
import re
import urllib.parse
import requests

from bs4 import BeautifulSoup as bs
from puppy.utils.nlp import tokenize, tokenize_article
from puppy.utils.soup import derive_new_table, derive_new_table_sidebar, derive_new_table_infobox, \
                             derive_new_thumbnail, remove_all_tags, highlight_target_anchor,\
                             element_has_parent_with_tagname, prepare_target_anchor


class Puppy:

    def __init__(self, socket_id):
        self.history = list()
        self.skip = list()
        self.socket_id = socket_id
        self.update_data = None
        self.start = None
        self.target = None
        self.current_url = None
        self.next_article = None
        self.tokenized_target = None

    def generate_sentence_map(self, inner_html):
        reg = re.compile(r"\.(?= [A-Z]|<)|$|!|\?(?![^<]*>)")
        sentences = re.split(reg, inner_html)
        sentences = filter(None, sentences)
        sentences_2_similarity = dict()
        for sentence in sentences:
            sentence_soup = bs(sentence, "lxml")
            sentence_anchors = sentence_soup.find_all("a")
            sentence_text = sentence_soup.get_text()
            if sentence_anchors and sentence_text:
                tokenized_sentence = tokenize(sentence_text)
                similarity = tokenized_sentence.similarity(self.tokenized_target)
                hashable_anchors_list = tuple(sentence_anchors)
                sentences_2_similarity[hashable_anchors_list] = similarity
        return sentences_2_similarity

    def get_best_paragraph(self, current_article_soup):
        # todo: in the future should look for next article in thumbnail description and tables too
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
        self.next_article = None
        return self

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

    def make_update(self, best_element, similarity, update_type="INFO"):
        update_data = {
            "paragraph": str(best_element),
            "similarity": "{:.2f}".format(similarity),
            "current_url": self.current_url
        }
        update = {"type": update_type, "data": update_data}
        return update

    def end_run(self, target):
        best_paragraph = None
        for parent in target.parents:
            if parent.has_attr('class') and "thumbinner" in parent.get("class"):
                best_paragraph = derive_new_thumbnail(target, parent)
                break
            if parent.has_attr('class') and "navbox-inner" in parent.get("class"):
                best_paragraph = derive_new_table(target, parent)
                break
            if parent.has_attr("class") and "infobox" in parent.get("class"):
                best_paragraph = derive_new_table_infobox(target, parent)
                break
            if parent.has_attr("class") and "sidebar" in parent.get("class"):
                best_paragraph = derive_new_table_sidebar(target, parent)
                break
            if parent.has_attr("class") and "wikitable" in parent.get("class"):
                best_paragraph = remove_all_tags(parent, "a", action="unwrap", save=target, save_action=prepare_target_anchor)
        if not best_paragraph:
            best_paragraph = element_has_parent_with_tagname(target, "p")
            if not best_paragraph:
                best_paragraph = target.parent
            best_paragraph = remove_all_tags(best_paragraph, True, action="unwrap", save=target, save_action=prepare_target_anchor)
            best_paragraph = highlight_target_anchor(best_paragraph, target)
        tokenized_sentence = tokenize(best_paragraph.get_text().strip())
        similarity = tokenized_sentence.similarity(self.tokenized_target)
        self.update_data = self.make_update(best_paragraph, similarity, update_type="SUCCESS")
        return self

    def process_article(self, article_content):
        current_article_soup = bs(article_content, "lxml")
        article_body = current_article_soup.find("body")
        remove_all_tags(article_body, "sup", action="delete")
        all_anchors = current_article_soup.find_all("a")
        target_found = self.process_anchors(all_anchors)
        if target_found:
            self.next_article = None
            return self.end_run(target_found)
        best_paragraph, best_sentences = self.get_best_paragraph(current_article_soup)
        if best_sentences:
            best_anchors = max(best_sentences, key=best_sentences.get)
            similarity = best_sentences[best_anchors]
            best_anchor = random.choice(best_anchors)
            best_link = best_anchor.get("href")
            if self.history.count(best_link) > 3:
                self.skip.append(best_link)  # if stuck in a loop silently try another link on the current page
                self.next_article = self.current_url
                return self
            best_paragraph = remove_all_tags(best_paragraph, True, action="unwrap", save=best_anchor, save_action=prepare_target_anchor)
            self.update_data = self.make_update(best_paragraph, similarity)
            self.history.append(self.current_url)
            self.next_article = best_link
            return self
        # if the current article cannot be used for lack of viable anchor tags silently go back to the last page
        # visited and try another link
        self.skip.append(self.current_url)
        self.next_article = self.history.pop()
        return self

    def init_run_parameters(self, start, target, socket_id):
        self.start = start
        self.target = target
        self.next_article = None
        self.socket_id = socket_id

    def go(self):
        self.current_url = self.next_article
        article_content = requests.get(self.current_url).text
        return self.process_article(article_content)

    def tokenize_target(self):
        target_content = requests.get(self.target).text
        target_content_soup = bs(target_content, "lxml")
        self.tokenized_target = tokenize_article(target_content_soup)
        self.next_article = self.start
        return self

