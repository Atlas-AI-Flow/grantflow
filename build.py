"""
GrantFlow Site Builder v3
Generates:
  - index.html (main listing with filters + search)
  - grants/<slug>.html (individual SEO pages per grant)
  - sitemap.xml
  - robots.txt
"""

import json
import re
import os
import hashlib
from datetime import datetime

INPUT_FILE = "data/grants_enriched.json"
OUTPUT_DIR = "site"
SITE_URL = "https://grantflow.vercel.app"
BRAND = "GrantFlow"

NICHE_META = {
    "SLP": {"label": "Speech-Language Pathology", "emoji": "🗣️", "color": "purple", "icon": "SLP"},
    "PT":  {"label": "Physical Therapy", "emoji": "🏃", "color": "green", "icon": "PT"},
    "OT":  {"label": "Occupational Therapy", "emoji": "🖐️", "color": "orange", "icon": "OT"},
    "Family": {"label": "Family & Children", "emoji": "👨‍👩‍👧‍👦", "color": "pink", "icon": "FAM"},
    "STEM": {"label": "STEM", "emoji": "🔬", "color": "blue", "icon": "STEM"},
}

def slugify(text):
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug[:80]

def dedupe_grants(grants):
    """Remove duplicate grants based on title+source."""
    seen = set()
    unique = []
    for g in grants:
        key = f"{g['title'].lower().strip()}|{g.get('source','')}"
        if key not in seen:
            seen.add(key)
            unique.append(g)
    return unique

def filter_junk(grants):
    """Remove non-grant entries (nav links, 'View Awardees', etc.)."""
    junk_titles = {
        "funding opportunities", "view awardees", "awards and honors",
        "aotf award recipients", "start a fundraiser", "how to apply",
        "external research funding", "pte awards", "available scholarships",
        "grants", "scholarships", "awards and honors", "apply now",
    }
    filtered = []
    for g in grants:
        title_lower = g['title'].lower().strip()
        if title_lower in junk_titles:
            continue
        if len(g['title']) < 5:
            continue
        # Skip entries with '#' as link
        if g.get('link', '').startswith('#'):
            continue
        filtered.append(g)
    return filtered

def format_amount(amount):
    if not amount:
        return "See details"
    s = str(amount).replace(',', '')
    if s.isdigit():
        return f"${int(s):,}"
    return str(amount)

def get_niche_info(niche):
    return NICHE_META.get(niche, {"label": niche, "emoji": "📋", "color": "gray", "icon": niche})

def build_card_html(grant, slug):
    ni = get_niche_info(grant['niche'])
    amount = format_amount(grant.get('amount'))
    deadline = grant.get('deadline', 'See website')
    summary = grant.get('summary', '')
    eligibility = grant.get('eligibility', '')

    deadline_badge = ""
    if deadline and deadline != "See website":
        if deadline == "Rolling":
            deadline_badge = '<span class="inline-block bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded-full font-medium">Rolling</span>'
        else:
            deadline_badge = f'<span class="inline-block bg-yellow-100 text-yellow-700 text-xs px-2 py-0.5 rounded-full font-medium">{deadline}</span>'

    eligibility_html = ""
    if eligibility:
        eligibility_html = f'<p class="text-xs text-gray-500 bg-gray-50 p-2 rounded mt-2">{eligibility}</p>'

    summary_html = ""
    if summary:
        short = summary[:120] + ("..." if len(summary) > 120 else "")
        summary_html = f'<p class="text-sm text-gray-600 mt-2">{short}</p>'

    return f'''
<div class="grant-card bg-white p-5 rounded-xl shadow-sm hover:shadow-md transition border-l-4 border-{ni["color"]}-500" data-niche="{grant["niche"]}" data-title="{grant["title"].lower()}">
    <div class="flex items-center justify-between mb-2">
        <span class="text-xs font-bold uppercase tracking-wider text-{ni["color"]}-600">{ni["emoji"]} {grant["niche"]}</span>
        {deadline_badge}
    </div>
    <a href="grants/{slug}.html" class="block">
        <h3 class="text-lg font-bold text-gray-900 hover:text-blue-700 transition">{grant["title"]}</h3>
    </a>
    <div class="flex gap-4 mt-2 text-sm text-gray-500">
        <span>{grant.get("source", "")}</span>
        <span class="font-semibold text-gray-800">{amount}</span>
    </div>
    {summary_html}
    {eligibility_html}
    <div class="mt-3 flex gap-2">
        <a href="grants/{slug}.html" class="text-sm text-blue-600 hover:text-blue-800 font-medium">Details &rarr;</a>
        <a href="{grant.get("link", "#")}" target="_blank" rel="noopener" class="text-sm text-gray-400 hover:text-gray-600">Source &nearr;</a>
    </div>
</div>'''

def build_grant_page(grant, slug):
    ni = get_niche_info(grant['niche'])
    amount = format_amount(grant.get('amount'))
    deadline = grant.get('deadline', 'Not specified')
    summary = grant.get('summary', 'Visit the source for full details.')
    eligibility = grant.get('eligibility', 'See the official page for requirements.')
    link = grant.get('link', '#')
    source = grant.get('source', 'Unknown')

    title = f"{grant['title']} | {BRAND}"
    desc = summary[:155]

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{desc}">
    <meta property="og:title" content="{grant["title"]}">
    <meta property="og:description" content="{desc}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{SITE_URL}/grants/{slug}.html">
    <link rel="canonical" href="{SITE_URL}/grants/{slug}.html">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 text-gray-800 min-h-screen">

    <nav class="bg-white border-b">
        <div class="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
            <a href="../index.html" class="text-xl font-bold text-blue-700">🚀 {BRAND}</a>
            <a href="../index.html" class="text-sm text-gray-500 hover:text-blue-600">&larr; All Grants</a>
        </div>
    </nav>

    <main class="max-w-4xl mx-auto px-4 py-8">
        <div class="bg-white rounded-xl shadow-sm p-8 border-l-4 border-{ni["color"]}-500">
            <span class="inline-block bg-{ni["color"]}-100 text-{ni["color"]}-700 text-xs font-bold uppercase px-3 py-1 rounded-full mb-4">{ni["emoji"]} {ni["label"]}</span>

            <h1 class="text-3xl font-bold text-gray-900 mb-4">{grant["title"]}</h1>

            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div class="bg-gray-50 rounded-lg p-3 text-center">
                    <p class="text-xs text-gray-500 uppercase">Amount</p>
                    <p class="text-lg font-bold text-green-700">{amount}</p>
                </div>
                <div class="bg-gray-50 rounded-lg p-3 text-center">
                    <p class="text-xs text-gray-500 uppercase">Deadline</p>
                    <p class="text-lg font-bold text-yellow-700">{deadline}</p>
                </div>
                <div class="bg-gray-50 rounded-lg p-3 text-center">
                    <p class="text-xs text-gray-500 uppercase">Source</p>
                    <p class="text-sm font-semibold text-gray-700">{source}</p>
                </div>
                <div class="bg-gray-50 rounded-lg p-3 text-center">
                    <p class="text-xs text-gray-500 uppercase">Niche</p>
                    <p class="text-sm font-semibold text-gray-700">{ni["label"]}</p>
                </div>
            </div>

            <div class="mb-6">
                <h2 class="text-lg font-semibold mb-2">About This Opportunity</h2>
                <p class="text-gray-600 leading-relaxed">{summary}</p>
            </div>

            <div class="mb-6">
                <h2 class="text-lg font-semibold mb-2">Eligibility</h2>
                <p class="text-gray-600">{eligibility}</p>
            </div>

            <div class="flex gap-3">
                <a href="{link}" target="_blank" rel="noopener" class="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition">
                    Apply Now &rarr;
                </a>
                <a href="../index.html" class="inline-block bg-gray-100 text-gray-700 px-6 py-3 rounded-lg font-semibold hover:bg-gray-200 transition">
                    Browse All Grants
                </a>
            </div>
        </div>

        <p class="text-xs text-gray-400 mt-6 text-center">Last verified: {grant.get("enriched_at", "Recently")[:10]} | Data sourced from public foundations | Always verify details on the official site.</p>
    </main>

    <footer class="bg-gray-800 text-gray-400 py-6 mt-12">
        <div class="max-w-4xl mx-auto px-4 text-center text-sm">
            <p>&copy; 2026 {BRAND}. Automated grant discovery for allied health professionals.</p>
        </div>
    </footer>

</body>
</html>'''

def build_index(grants, grant_slugs):
    niches_found = sorted(set(g['niche'] for g in grants))

    filter_buttons = ""
    for niche in niches_found:
        ni = get_niche_info(niche)
        filter_buttons += f'<button onclick="filterNiche(\'{niche}\')" class="px-4 py-2 bg-{ni["color"]}-50 text-{ni["color"]}-700 rounded-lg hover:bg-{ni["color"]}-100 font-medium text-sm transition">{ni["emoji"]} {niche}</button>\n'

    cards_html = ""
    for grant, slug in zip(grants, grant_slugs):
        cards_html += build_card_html(grant, slug)

    total = len(grants)
    with_amounts = sum(1 for g in grants if g.get('amount'))
    niche_counts = {}
    for g in grants:
        niche_counts[g['niche']] = niche_counts.get(g['niche'], 0) + 1

    stats_html = ""
    for niche, count in sorted(niche_counts.items()):
        ni = get_niche_info(niche)
        stats_html += f'<div class="bg-{ni["color"]}-50 rounded-lg p-4 text-center"><p class="text-2xl font-bold text-{ni["color"]}-700">{count}</p><p class="text-xs text-gray-500">{ni["label"]}</p></div>\n'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{BRAND} | Allied Health Grants & Scholarships 2026</title>
    <meta name="description" content="Discover {total}+ grants, scholarships, and fellowships for PT, OT, SLP, and allied health professionals. Updated daily.">
    <meta property="og:title" content="{BRAND} - Allied Health Grant Finder">
    <meta property="og:description" content="Discover {total}+ grants for allied health professionals.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{SITE_URL}">
    <link rel="canonical" href="{SITE_URL}">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 text-gray-800 min-h-screen">

    <!-- Hero -->
    <header class="bg-gradient-to-br from-blue-700 to-indigo-800 text-white">
        <div class="max-w-6xl mx-auto px-4 py-12">
            <h1 class="text-4xl md:text-5xl font-bold">🚀 {BRAND}</h1>
            <p class="mt-3 text-lg text-blue-100 max-w-2xl">Automated grant discovery for allied health professionals. PT, OT, SLP funding — scraped, enriched, and organized daily.</p>
            <p class="mt-2 text-sm text-blue-200">Last updated: {datetime.now().strftime("%B %d, %Y")} &middot; {total} opportunities tracked</p>
        </div>
    </header>

    <main class="max-w-6xl mx-auto px-4 py-8">

        <!-- Stats -->
        <div class="grid grid-cols-2 md:grid-cols-{len(niche_counts)} gap-3 mb-8">
            {stats_html}
        </div>

        <!-- Search + Filters -->
        <div class="bg-white rounded-xl shadow-sm p-4 mb-8 flex flex-wrap gap-3 items-center">
            <input type="text" id="search" placeholder="Search grants..." oninput="filterAll()" class="flex-1 min-w-[200px] border border-gray-200 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300">
            <button onclick="filterNiche('ALL')" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-medium text-sm transition active-filter">All</button>
            {filter_buttons}
        </div>

        <!-- Grid -->
        <div id="grid" class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {cards_html}
        </div>

        <p id="no-results" class="hidden text-center text-gray-400 py-12 text-lg">No grants match your search.</p>

    </main>

    <footer class="bg-gray-800 text-gray-400 py-6 mt-12">
        <div class="max-w-6xl mx-auto px-4 text-center text-sm">
            <p>&copy; 2026 {BRAND}. Automated grant discovery for allied health professionals.</p>
            <p class="mt-1">Data sourced from public foundations. Always verify details on official sites.</p>
        </div>
    </footer>

    <script>
        let activeNiche = 'ALL';

        function filterNiche(niche) {{
            activeNiche = niche;
            filterAll();
        }}

        function filterAll() {{
            const query = document.getElementById('search').value.toLowerCase();
            const cards = document.querySelectorAll('.grant-card');
            let visible = 0;

            cards.forEach(card => {{
                const matchNiche = activeNiche === 'ALL' || card.dataset.niche === activeNiche;
                const matchSearch = !query || card.dataset.title.includes(query) || card.textContent.toLowerCase().includes(query);

                if (matchNiche && matchSearch) {{
                    card.style.display = 'block';
                    visible++;
                }} else {{
                    card.style.display = 'none';
                }}
            }});

            document.getElementById('no-results').classList.toggle('hidden', visible > 0);
        }}
    </script>

</body>
</html>'''

def build_sitemap(slugs):
    urls = [f"  <url><loc>{SITE_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>"]
    for slug in slugs:
        urls.append(f"  <url><loc>{SITE_URL}/grants/{slug}.html</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>")

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>'''

def build_robots():
    return f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""

def build():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        grants = json.load(f)

    print(f"Loaded {len(grants)} grants")

    # Clean up
    grants = filter_junk(grants)
    print(f"After filtering junk: {len(grants)}")

    grants = dedupe_grants(grants)
    print(f"After dedup: {len(grants)}")

    # Sort: grants with amounts first, then by niche
    grants.sort(key=lambda g: (
        0 if g.get('amount') else 1,
        g.get('niche', 'ZZZ'),
        g.get('title', '')
    ))

    # Create output dirs
    os.makedirs(os.path.join(OUTPUT_DIR, "grants"), exist_ok=True)

    # Generate slugs
    slug_counts = {}
    grant_slugs = []
    for g in grants:
        base_slug = slugify(g['title'])
        if base_slug in slug_counts:
            slug_counts[base_slug] += 1
            base_slug = f"{base_slug}-{slug_counts[base_slug]}"
        else:
            slug_counts[base_slug] = 0
        grant_slugs.append(base_slug)

    # Build individual pages
    for grant, slug in zip(grants, grant_slugs):
        page = build_grant_page(grant, slug)
        path = os.path.join(OUTPUT_DIR, "grants", f"{slug}.html")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(page)

    print(f"Generated {len(grants)} individual grant pages")

    # Build index
    index_html = build_index(grants, grant_slugs)
    with open(os.path.join(OUTPUT_DIR, "index.html"), 'w', encoding='utf-8') as f:
        f.write(index_html)
    print("Generated index.html")

    # Sitemap + robots
    sitemap = build_sitemap(grant_slugs)
    with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), 'w', encoding='utf-8') as f:
        f.write(sitemap)

    robots = build_robots()
    with open(os.path.join(OUTPUT_DIR, "robots.txt"), 'w', encoding='utf-8') as f:
        f.write(robots)

    print("Generated sitemap.xml + robots.txt")
    print(f"\nSite ready in ./{OUTPUT_DIR}/")
    print(f"  {len(grants)} grant pages")
    print(f"  Niches: {', '.join(sorted(set(g['niche'] for g in grants)))}")

if __name__ == "__main__":
    build()
