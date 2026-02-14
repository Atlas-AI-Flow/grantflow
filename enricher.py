"""
GrantFlow Enricher v2 — Regex-based, no AI dependency.
Visits each grant link, extracts deadline, amount, eligibility, and summary.
Falls back gracefully when data isn't found.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import os
from datetime import datetime

INPUT_FILE = "data/grants_data.json"
OUTPUT_FILE = "data/grants_enriched.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def clean_text(soup):
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.extract()
    return soup.get_text(separator="\n", strip=True)


def extract_deadline(text):
    """Try multiple deadline patterns."""
    patterns = [
        # "Deadline: April 22, 2026"
        r'(?:Deadline|Due Date|Due|Closes|Closing Date)[:\s]*([A-Z][a-z]+\s\d{1,2},?\s\d{4})',
        # "April 22, 2026" near deadline keywords
        r'(?:submit|application|due|deadline).*?([A-Z][a-z]+\s\d{1,2},?\s\d{4})',
        # MM/DD/YYYY
        r'(?:Deadline|Due)[:\s]*(\d{1,2}/\d{1,2}/\d{4})',
        # YYYY-MM-DD
        r'(?:Deadline|Due)[:\s]*(\d{4}-\d{2}-\d{2})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Check for rolling/open
    if re.search(r'\b(rolling|open|ongoing|no deadline|continuous)\b', text, re.IGNORECASE):
        return "Rolling"

    return None


def extract_amount(text):
    """Find dollar amounts, return the largest one (likely the max award)."""
    amounts = re.findall(r'\$(\d{1,3}(?:,\d{3})*)', text)
    if amounts:
        numeric = [int(a.replace(',', '')) for a in amounts]
        largest = max(numeric)
        return f"{largest:,}"
    return None


def extract_eligibility(text):
    """Try to find eligibility snippets."""
    patterns = [
        r'(?:Eligib(?:le|ility)|Who (?:Can|May|Should) Apply)[:\s]*([^\n.]{10,150})',
        r'(?:Open to|Available to|Applicants must be)[:\s]*([^\n.]{10,150})',
        r'(?:must be enrolled|must be a|candidates should)[^\n.]{5,120}',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result = match.group(1) if match.lastindex else match.group(0)
            return result.strip()[:200]
    return None


def extract_summary(soup, text):
    """Extract a summary from meta description or first meaningful paragraph."""
    # Try meta description first
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content") and len(meta["content"]) > 20:
        return meta["content"].strip()[:200]

    # Try OG description
    og = soup.find("meta", attrs={"property": "og:description"})
    if og and og.get("content") and len(og["content"]) > 20:
        return og["content"].strip()[:200]

    # First meaningful paragraph
    for p in soup.find_all("p"):
        t = p.get_text(strip=True)
        if len(t) > 40 and not t.startswith(("Cookie", "Privacy", "©", "Skip")):
            return t[:200]

    return None


def enrich():
    if not os.path.exists(INPUT_FILE):
        print(f"File not found: {INPUT_FILE}. Run scraper.py first.")
        return

    with open(INPUT_FILE, 'r') as f:
        grants = json.load(f)

    enriched = []
    success = 0
    print(f"--- Enriching {len(grants)} Grants ---")

    for i, grant in enumerate(grants):
        print(f"[{i+1}/{len(grants)}] {grant['title'][:60]}...")

        try:
            resp = requests.get(grant['link'], headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                print(f"  [HTTP {resp.status_code}]")
                enriched.append(grant)
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')
            text = clean_text(soup)

            # Extract fields
            grant['deadline'] = extract_deadline(text)
            grant['amount'] = extract_amount(text)
            grant['eligibility'] = extract_eligibility(text)
            grant['summary'] = extract_summary(soup, text)
            grant['enriched_at'] = datetime.now().isoformat()

            found = []
            if grant['deadline']:
                found.append(f"deadline={grant['deadline']}")
            if grant['amount']:
                found.append(f"${grant['amount']}")
            if grant['eligibility']:
                found.append("eligibility")
            if grant['summary']:
                found.append("summary")

            if found:
                print(f"  OK: {', '.join(found)}")
                success += 1
            else:
                print(f"  -- no structured data found")

            enriched.append(grant)

        except Exception as e:
            print(f"  [Error] {e}")
            enriched.append(grant)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(enriched, f, indent=2)

    print(f"\n--- Done ---")
    print(f"Enriched: {success}/{len(grants)} grants with at least one field")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    enrich()
