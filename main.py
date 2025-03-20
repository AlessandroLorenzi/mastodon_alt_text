#!/usr/bin/env python
import ollama
import logging
import requests
import tempfile
import os
from mastodon import Mastodon
from bs4 import BeautifulSoup
import time

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


INSTANCE_URL = os.getenv("INSTANCE_URL")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
LANGUAGE = os.getenv("LANGUAGE", "italian")

mastodon = Mastodon(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    access_token=ACCESS_TOKEN,
    api_base_url=INSTANCE_URL,
)


class ImageDownloader:
    def __init__(self, url: str):
        self.url = url
        self.path = tempfile.mktemp()

    def __enter__(self) -> str:
        log.debug(f"Downloading image from {self.url}")
        response = requests.get(self.url)

        with open(self.path, "wb") as file:
            file.write(response.content)

        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        log.debug(f"Removing image {self.path}")
        os.remove(self.path)


def extract_description(img_path: str) -> str:
    log.debug(f"Extracting description from image {img_path}")
    res = ollama.chat(
        model="llava:7b",
        messages=[
            {
                "role": "user",
                "content": "Describe the image",
                "images": [img_path],
            }
        ],
    )
    return res["message"]["content"]


def translate(text: str, lang: str = "italian") -> str:
    log.debug(f"Translating text to {lang}")
    res = ollama.chat(
        model="mistral-nemo",
        messages=[
            {
                "role": "user",
                "content": f"Translate to {lang}: {text}",
            }
        ],
    )
    return res["message"]["content"]


def elaborate_toot(toot: dict):
    new_media_ids = []
    updated = False

    soup = BeautifulSoup(
        toot["content"], "html.parser"
    )  # because toot["content"] is inside <p></p> (facepalm)
    status = soup.get_text()
    for media in toot["media_attachments"]:
        if media["type"] == "image" and media["description"] == "":
            log.info(f"Elaborating media for toot {toot['uri']} - {status}")
            with ImageDownloader(media["url"]) as image_path:
                description = extract_description(image_path)
                if LANGUAGE != "en":
                    description = translate(description, lang=LANGUAGE)
                media_id = mastodon.media_post(image_path, description=description)
                updated = True
                new_media_ids.append(media_id)
        else:
            new_media_ids.append(media["id"])

    if updated:
        mastodon.status_update(
            id=toot["id"],
            media_ids=new_media_ids,
            status=status,
        )


if __name__ == "__main__":
    log.info("Starting the bot...")
    me = mastodon.me()
    my_toots = mastodon.account_statuses(me["id"], limit=10)

    for toot in my_toots:
        elaborate_toot(toot)

    last_seen_id = my_toots[0]["id"]
    while True:
        log.debug("Checking for new toots...")
        new_toots = mastodon.account_statuses(me["id"], since_id=last_seen_id)
        for toot in new_toots:
            elaborate_toot(toot)
            last_seen_id = toot["id"]
        time.sleep(60)
