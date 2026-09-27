import json
import os
import re
import urllib.request

# Target topic from repository secret or environment variable
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "smmt-catalyst-alert-9472x")

# SEC EDGAR Submissions API for Summit Therapeutics Inc. (CIK: 0001599298)
CIK = "0001599298"
SEC_URL = f"https://data.sec.gov/submissions/CIK{CIK}.json"


def check_sec_filings():
    headers = {
        "User-Agent": "CatalystTracker lina.patricia@researchportal.org",
        "Accept-Encoding": "gzip, deflate",
        "Host": "data.sec.gov",
    }

    print("Fetching SEC disclosures for Summit Therapeutics (SMMT)...")
    req = urllib.request.Request(SEC_URL, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Error fetching SEC data: {e}")
        return

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    primary_docs = recent.get("primaryDocument", [])
    accession_nums = recent.get("accessionNumber", [])
    descriptions = recent.get("primaryDocDescription", [])

    print(f"Retrieved {len(forms)} recent filings. Checking newest 8-Ks...")

    for i in range(min(10, len(forms))):
        form = forms[i]
        desc = descriptions[i] or ""
        doc = primary_docs[i] or ""
        acc = accession_nums[i].replace("-", "") if accession_nums else ""

        filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(CIK)}/{acc}/{doc}"
        text_corpus = f"{form} {desc}".lower()

        # Check for 8-K clinical press releases or material disclosures
        if form in ["8-K", "8-K/A"]:
            has_squamous = bool(re.search(r"squamous", text_corpus))
            has_endpoint = bool(
                re.search(
                    r"(progression-free|overall survival|\bpfs\b|\bos\b|harmoni-3|ivonescimab)",
                    text_corpus,
                )
            )

            if has_squamous or has_endpoint:
                print(f"Catalyst match identified: {desc}")
                send_alert(f"SMMT 8-K: {desc}", filing_url)
                return

    print("Pipeline check complete: No new squamous catalyst filings detected.")


def send_alert(title, url):
    print(f"Dispatching notification via ntfy...")
    req = urllib.request.Request(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=f"Summit Catalyst Readout Published:\n{title}\n{url}".encode("utf-8"),
        headers={
            "Title": "CATALYST ALERT: SMMT Squamous Data",
            "Priority": "urgent",
            "Tags": "rotating_light,pill",
            "Click": url,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"ntfy status: {resp.status}")
    except Exception as e:
        print(f"Failed to push alert: {e}")


if __name__ == "__main__":
    check_sec_filings()
