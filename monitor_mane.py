import os
import json
import requests

# SEC EDGAR API parameters for Veradermics (CIK: 0001827635)
CIK = "0001827635"
HEADERS = {
    "User-Agent": "LinaLahoz nivalis@capital.com"
}
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "lina-mane-cat-alerts")
CACHE_FILE = "seen_mane_filings.json"

def load_seen():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_seen(seen):
    with open(CACHE_FILE, "w") as f:
        json.dump(list(seen), f)

def check_sec_filings():
    url = f"https://data.sec.gov/submissions/CIK{CIK}.json"
    response = requests.get(url, headers=HEADERS, timeout=15)
    if response.status_code != 200:
        return
    
    data = response.json()
    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])
    
    seen = load_seen()
    
    # Check the 3 most recent filings to catch any fresh drops
    for i in range(min(3, len(forms))):
        latest_form = forms[i]
        latest_date = dates[i]
        acc_no = accessions[i]
        acc_no_hyphen = acc_no.replace("-", "")
        doc_name = primary_docs[i]
        filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(CIK)}/{acc_no_hyphen}/{doc_name}"
        
        # Track unique accession number
        if acc_no in seen:
            continue
            
        # Target 8-K or 6-K material filings
        if latest_form in ["8-K", "6-K"]:
            message = f"🚨 MANE {latest_form} Filed on {latest_date}! Check clinical readout / data: {filing_url}"
            send_ntfy(message)
            seen.add(acc_no)
            
    save_seen(seen)

def send_ntfy(message):
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers={
            "Title": "MANE Clinical Readout Alert",
            "Priority": "urgent",
            "Tags": "chart_with_upward_trend,pill"
        },
        timeout=10
    )

if __name__ == "__main__":
    check_sec_filings()
