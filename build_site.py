import json
from datetime import datetime

INPUT_FILE = "allied_grants/grants_enriched.json"
OUTPUT_HTML = "allied_grants/index.html"

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Allied Health Grants 2026 | PT, OT, SLP Funding</title>
    <meta name="description" content="Find the latest research grants and scholarships for Physical Therapy, Occupational Therapy, and Speech-Language Pathology.">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 text-gray-800">

    <header class="bg-blue-600 text-white py-8">
        <div class="container mx-auto px-4">
            <h1 class="text-4xl font-bold">Allied Grants 🏥</h1>
            <p class="mt-2 text-lg">Automated funding monitor for PT, OT, and SLP professionals.</p>
            <p class="text-sm opacity-75">Last updated: {DATE}</p>
        </div>
    </header>

    <main class="container mx-auto px-4 py-8">
        
        <!-- Filters -->
        <div class="flex gap-4 mb-8 justify-center">
            <button onclick="filter('ALL')" class="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300 font-bold active-filter">All</button>
            <button onclick="filter('SLP')" class="px-4 py-2 bg-purple-100 text-purple-800 rounded hover:bg-purple-200 font-bold">SLP 🗣️</button>
            <button onclick="filter('PT')" class="px-4 py-2 bg-green-100 text-green-800 rounded hover:bg-green-200 font-bold">PT 🏃</button>
            <button onclick="filter('OT')" class="px-4 py-2 bg-orange-100 text-orange-800 rounded hover:bg-orange-200 font-bold">OT 🖐️</button>
        </div>

        <div class="mb-8">
            <h2 class="text-2xl font-bold mb-4">Latest Opportunities</h2>
            <div id="grid" class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {CARDS}
            </div>
        </div>

    </main>

    <script>
        function filter(niche) {
            const cards = document.querySelectorAll('.grant-card');
            cards.forEach(card => {
                if (niche === 'ALL' || card.dataset.niche === niche) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }
    </script>

    <footer class="bg-gray-800 text-white py-6 mt-12">
        <div class="container mx-auto px-4 text-center">
            <p>Built by Atlas AI. Data sourced from public foundations.</p>
        </div>
    </footer>

</body>
</html>
"""

CARD_TEMPLATE = """
<div class="grant-card bg-white p-6 rounded-lg shadow hover:shadow-lg transition border-l-4 {BORDER_COLOR}" data-niche="{NICHE}">
    <span class="text-xs font-bold uppercase tracking-wider text-gray-500">{NICHE}</span>
    <h3 class="text-xl font-bold mt-1 mb-2 text-blue-900">{TITLE}</h3>
    
    <div class="text-sm text-gray-600 mb-4">
        <p><strong>Source:</strong> {SOURCE}</p>
        <p><strong>Deadline:</strong> <span class="{DEADLINE_CLASS}">{DEADLINE}</span></p>
        <p><strong>Amount:</strong> {AMOUNT}</p>
    </div>
    
    <p class="text-sm font-medium text-gray-800 mb-2 italic">"{TLDR}"</p>
    
    {ELIGIBILITY}
    
    <a href="{LINK}" target="_blank" class="inline-block bg-blue-100 text-blue-700 px-3 py-1 rounded text-sm font-medium hover:bg-blue-200">
        Apply Now &rarr;
    </a>
</div>
"""

def build():
    with open(INPUT_FILE, 'r') as f:
        grants = json.load(f)
    
    cards_html = ""
    
    for g in grants:
        # Determine Color by Niche
        color = "border-gray-400"
        if g['niche'] == "SLP": color = "border-purple-500"
        elif g['niche'] == "PT": color = "border-green-500"
        elif g['niche'] == "OT": color = "border-orange-500"
        
        # Format Amount
        amount = g.get('amount', 'See details')
        if amount and amount.replace(',','').isdigit():
            amount = f"${amount}"
            
        # Format Eligibility
        eligibility = ""
        if g.get('eligibility'):
            eligibility = f'<p class="text-xs text-gray-500 mb-4 bg-gray-100 p-2 rounded">{g["eligibility"]}</p>'

        # Deadline Logic
        deadline = g.get('deadline', 'Unknown')
        deadline_class = "text-gray-800"
        # (Could add logic here to flag 'Approaching' dates in red)

        # Format TLDR
        tldr = g.get('tldr', 'Details inside.')

        card = CARD_TEMPLATE.format(
            BORDER_COLOR=color,
            NICHE=g['niche'],
            TITLE=g['title'],
            SOURCE=g['source'],
            DEADLINE=deadline,
            DEADLINE_CLASS=deadline_class,
            AMOUNT=amount,
            TLDR=tldr,
            ELIGIBILITY=eligibility,
            LINK=g['link']
        )
        cards_html += card

    final_html = TEMPLATE.format(
        DATE=datetime.now().strftime("%Y-%m-%d"),
        CARDS=cards_html
    )
    
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    print(f"Site built: {OUTPUT_HTML}")

if __name__ == "__main__":
    build()
