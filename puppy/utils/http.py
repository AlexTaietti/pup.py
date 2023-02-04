import requests
import datetime
import time


POLITE_WAIT = 0.15 # seconds
last_request_timestamp = datetime.datetime.now().timestamp() * 1000 # unix epoch in milliseconds


def politely_get(url):
    global last_request_timestamp
    now = datetime.datetime.now().timestamp() * 1000
    since_last_request = now - last_request_timestamp
    last_request_timestamp = now
    if since_last_request < (POLITE_WAIT * 1000):
        polite_delay = POLITE_WAIT - (since_last_request / 1000)
        time.sleep(polite_delay)
    response = requests.get(url)
    return response.text
