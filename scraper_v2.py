import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time

INPUT_FILE = "data/grants_data.json"
OUTPUT_FILE = "data/grants_enriched.json"
OLLAMA_MODEL = "qwen2.5:14b"

def call_ollama(text):
    prompt = f"""
    Extract data from this grant page text. Return ONLY a JSON object:
    {{
        "deadline": "YYYY-MM-DD or 'Rolling'",
        "amount": "Max dollar amount (e.g. 5000)",
        "eligibility": "Brief summary (e.g. PhD students)",
        "tldr": "One sentence summary of who this is for and why they want it."
    }}
    
    Text:
    {text[:3000]}
    """
    
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        resp = requests.post("http://localhost:11434/api/generate", json=payload, timeout=40)
        if resp.status_code == 200:
            return json.loads(resp.json()['response'])
    except Exception as e:
        print(f"  [Ollama Error] {e}")
    return {}

def clean_text(soup):
    for script in soup(["script", "style", "nav", "footer"]):
        script.extract()
    return soup.get_text(separator="\n").strip()

def enrich():
    if not os.path.exists(INPUT_FILE):
        print(f"File not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, 'r') as f:
        grants = json.load(f)
    
    enriched_grants = []
    print(f"--- Enriching {len(grants)} Grants ---")
    
    # Process ALL grants (Full Run)
    for i, grant in enumerate(grants): 
        print(f"[{i+1}/{len(grants)}] Processing: {grant['title']}")
        
        try:
            resp = requests.get(grant['link'], timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            text = clean_text(soup)
            
            # 1. Regex Scan
            deadline_match = re.search(r'(Deadline|Due Date):\s*([A-Za-z]+\s\d{1,2},?\s\d{4})', text, re.IGNORECASE)
            amount_match = re.search(r'\$(\d{1,3}(,\d{3})*)', text)
            
            grant['deadline'] = deadline_match.group(2) if deadline_match else None
            grant['amount'] = amount_match.group(1) if amount_match else None
            
            # 2. Ollama Enrichment (Always run for TLDR)
            print("  Calling AI for details...")
            ai_data = call_ollama(text)
            
            # Merge AI data if regex failed or for new fields
            if not grant['deadline']: grant['deadline'] = ai_data.get('deadline')
            if not grant['amount']: grant['amount'] = ai_data.get('amount')
            grant['tldr'] = ai_data.get('tldr', 'Details inside.')
            grant['eligibility'] = ai_data.get('eligibility', 'See website.')
            
            print(f"  -> {grant['tldr'][:50]}...")
            enriched_grants.append(grant)
            
        except Exception as e:
            print(f"  [Error] {e}")
            enriched_grants.append(grant)

    # Save
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(enriched_grants, f, indent=2)
    print(f"Saved enriched data to {OUTPUT_FILE}")

if __name__ == "__main__":
    enrich()
