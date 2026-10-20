import os
import requests
from datetime import datetime, timezone, timedelta

# SEC EDGAR API parameters for Veradermics (CIK: 0001827635)
CIK = "0001827635"
HEADERS = {
    "User-Agent": "LinaLahoz nivalis@capital.com"
}
NTFY_TOPIC = os.getenv("NTFY_TOPIC")
EVENT_NAME = os.getenv("GITHUB_EVENT_NAME", "schedule")

def send_ntfy(title, message, priority="urgent"):
    if not NTFY_TOPIC:
        print("Error: NTFY_TOPIC secret is not set.")
        return
    resp = requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers={
            "Title": title,
            "Priority": priority,
            "Tags": "chart_with_upward_trend,pill"
        },
        timeout=10
    )
    print(f"ntfy status: {resp.status_code}")

def check_sec_filings():
    url = f"https://data.sec.gov/submissions/CIK{CIK}.json"
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    
    recent = response.json().get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accept_times = recent.get("acceptanceDateTime", [])
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])

    # 1. If triggered manually via "Run workflow", always send a test alert with the latest filing
    if EVENT_NAME == "workflow_dispatch" and forms:
        acc_clean = accessions[0].replace("-", "")
        filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(CIK)}/{acc_clean}/{primary_docs[0]}"
        msg = f"✅ Manual Test OK! Latest MANE filing is {forms[0]} ({dates[0]}): {filing_url}"
        send_ntfy("MANE Monitor Test", msg, priority="default")
        return

    # 2. On scheduled 30-min runs, only alert if an 8-K or 6-K was accepted in the last 45 minutes
    now_utc = datetime.now(timezone.utc)
    for i in range(min(5, len(forms))):
        if forms[i] in ["8-K", "8-K/A", "6-K"]:
            # SEC acceptanceDateTime is formatted like "2026-10-19T11:30:12.000Z"
            accepted_dt = datetime.fromisoformat(accept_times[i].replace("Z", "+00:00"))
            age = now_utc - accepted_dt
            if age <= timedelta(minutes=45):
                acc_clean = accessions[i].replace("-", "")
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(CIK)}/{acc_clean}/{primary_docs[i]}"
                msg = f"🚨 NEW MANE {forms[i]} Filed ({dates[i]})! Check readout/news: {filing_url}"
                send_ntfy("MANE Clinical Readout Alert", msg, priority="urgent")
                break

if __name__ == "__main__":
    check_sec_filings()
