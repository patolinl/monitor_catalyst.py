import feedparser
import requests
import os
import json

# ACHV SEC RSS Feed (Filtered specifically for 8-K filings)
SEC_FEED_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=ACHV&type=8-K&dateb=&owner=exclude&start=0&count=10&output=atom"
NTFY_TOPIC = os.environ.get("NTFY_TOPIC")

def check_achv_filings():
    headers = {'User-Agent': 'Mile (your_email@example.com)'} 
    feed = feedparser.parse(SEC_FEED_URL, request_headers=headers)
    
    state_file = 'achv_state.json'
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            seen_entries = set(json.load(f))
    else:
        seen_entries = set()

    for entry in feed.entries:
        if entry.id not in seen_entries:
            # Trigger an alert for EVERY new 8-K, no keyword filtering required.
            message = f"ACHV Alert: New 8-K Filed!\n{entry.title}\n{entry.link}"
            requests.post(
                f"https://ntfy.sh/{NTFY_TOPIC}",
                data=message.encode(encoding='utf-8'),
                headers={"Title": "Achieve Life Sciences (ACHV)", "Tags": "rotating_light,mega"}
            )
            seen_entries.add(entry.id)

    with open(state_file, 'w') as f:
        json.dump(list(seen_entries), f)

if __name__ == "__main__":
    check_achv_filings()
