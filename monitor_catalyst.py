import os
import re
import urllib.request
import xml.etree.ElementTree as ET

# Target topic from repository secret or environment variable
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "smmt-catalyst-alert-9472x")

# RSS feed for Summit Therapeutics press releases / News
FEED_URL = "https://www.globenewswire.com/RssFeed/orgseq/504780"

KEYWORDS = [
    r"\bsquamous\b",
    r"\bprogression-free survival\b",
    r"\bpfs\b",
    r"\boverall survival\b",
    r"\bharmoni-3\b",
    r"\bivonescimab\b",
]


def check_feed():
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        content = resp.read()

    root = ET.fromstring(content)
    for item in root.findall(".//item"):
        title = item.find("title").text or ""
        link = item.find("link").text or ""
        desc = item.find("description").text or ""
        text_corpus = f"{title} {desc}".lower()

        has_squamous = bool(re.search(r"squamous", text_corpus))
        has_endpoint = bool(
            re.search(
                r"(progression-free|overall survival|\bpfs\b|\bos\b)",
                text_corpus,
            )
        )

        if has_squamous and has_endpoint:
            send_alert(title, link)
            break


def send_alert(title, url):
    req = urllib.request.Request(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=f"Summit Squamous Readout Triggered:\n{title}\n{url}".encode(
            "utf-8"
        ),
        headers={
            "Title": "CATALYST ALERT: SMMT Squamous Data",
            "Priority": "urgent",
            "Tags": "rotating_light,pill",
            "Click": url,
        },
        method="POST",
    )
    urllib.request.urlopen(req)


if __name__ == "__main__":
    check_feed()
