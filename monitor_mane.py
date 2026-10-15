import os
import time
import requests

# SEC EDGAR API parameters for Veradermics (CIK: 0001827635)
CIK = "0001827635"
HEADERS = {
    "User-Agent": "LinaLahoz nivalis@capital.com"
}
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "lina-mane-catalyst-alerts-9921")

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
    
    # Check the most recent filing (Index 0)
    if forms:
        latest_form = forms[0]
        latest_date = dates[0]
        acc_no_hyphen = accessions[0].replace("-", "")
        doc_name = primary_docs[0]
        filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(CIK)}/{acc_no_hyphen}/{doc_name}"
        
        # Target 8-K filings (Material Events / Press Releases / Topline Readouts)
        if latest_form == "8-K":
            message = f"🚨 MANE 8-K Filed on {latest_date}! Check clinical readout data: {filing_url}"
            send_ntfy(message)

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
