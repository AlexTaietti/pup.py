import time
import random
import sys
import urllib.parse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


class Puppy:

    polite_wait = 1

    def __init__(self, start, target):
        self.current_url = self.start = start
        self.target = target
        self.start_id = start.split("/")[4]
        self.target_id = target.split("/")[4]
        self.driver = webdriver.Firefox()
        self.history = []

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
            if new_article_id == self.target_id:
                self.history.append(new_article_id)
                self.kill_driver()
                sys.exit(f"[*] Good boy! 🐶 fetched the target!\n[*] hops -> {self.history}")
            if current_page_id == new_article_id or ":" in new_article_id or "#" in new_article_id:
                continue
            viable_articles.append(link)
        print(f"[*] {len(viable_articles)} viable articles found @ page {url}")
        self.history.append(current_page_id)
        return viable_articles

    def go(self):
        viable_articles = self.find_viable_articles(self.current_url)
        self.current_url = random.choice(viable_articles)


if __name__ == "__main__":

    puppy = Puppy(sys.argv[1].strip(), sys.argv[2].strip())

    while True:
        puppy.go()


