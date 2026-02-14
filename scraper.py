import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# Targets
SOURCES = [
    {
        "niche": "SLP",
        "name": "ASHFoundation",
        "url": "https://www.ashfoundation.org/apply/",
        "selector": "h3 a",
    },
    {
        "niche": "PT",
        "name": "Foundation4PT",
        "url": "https://foundation4pt.org/scholarships/",
        "selector": "h3, h4",
    },
    {
        "niche": "OT",
        "name": "AOTF",
        "url": "https://www.aotf.org/Scholarships/Available-Scholarships",
        "selector": ".ContentPane h3, .ContentPane h4",
    },
    {
        "niche": "Family",
        "name": "UHCCF",
        "url": "https://www.uhccf.org/apply-for-a-grant/",
        "selector": "h1, h2, h3", # Broad selector for landing page
    }
]

# Updated Path
OUTPUT_FILE = "data/grants_data.json"

def scrape():
    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    print("--- Starting Scraping Run ---")

    for source in SOURCES:
        print(f"Scanning {source['niche']}: {source['name']}...")
        try:
            resp = requests.get(source['url'], headers=headers, timeout=10)
            if resp.status_code != 200:
                print(f"  [Error] Status {resp.status_code}")
                continue
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            items_found = 0
            
            # Extract links containing keywords
            for link in soup.find_all('a', href=True):
                text = link.get_text(strip=True)
                href = link['href']
                
                # Filter for relevance
                keywords = ["Grant", "Scholarship", "Award", "Fellowship", "Fund", "Apply"]
                if any(k in text for k in keywords) and len(text) > 5 and len(text) < 100:
                    
                    if href.startswith("/"):
                        base = "/".join(source['url'].split("/")[:3]) 
                        href = base + href
                    
                    results.append({
                        "niche": source['niche'],
                        "source": source['name'],
                        "title": text,
                        "link": href,
                        "found_at": datetime.now().isoformat()
                    })
                    items_found += 1
            
            print(f"  Found {items_found} potential opportunities.")
            
        except Exception as e:
            print(f"  [Exception] {e}")

    # Ensure dir exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nTotal Opportunities: {len(results)}")
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    scrape()
