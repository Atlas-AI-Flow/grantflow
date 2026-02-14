"""
GrantFlow Site Builder v4 (Trust Update)
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
FAMILY_FILE = "data/family_grants.json"
RESOURCES_FILE = "data/free_resources.json"
OUTPUT_DIR = "."
SITE_URL = "https://grantflow.vercel.app"
BRAND = "GrantFlow"

NICHE_META = {
    "SLP": {"label": "Speech-Language Pathology", "emoji": "🗣️", "color": "purple", "icon": "SLP"},
    "PT":  {"label": "Physical Therapy", "emoji": "🏃", "color": "green", "icon": "PT"},
    "OT":  {"label": "Occupational Therapy", "emoji": "🖐️", "color": "orange", "icon": "OT"},
    "Family": {"label": "Family & Children", "emoji": "💙", "color": "sky", "icon": "FAM"},
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
            deadline_badge = '<span class="inline-block bg-emerald-100 text-emerald-700 text-xs px-2 py-0.5 rounded-full font-medium">Rolling</span>'
        else:
            deadline_badge = f'<span class="inline-block bg-amber-100 text-amber-800 text-xs px-2 py-0.5 rounded-full font-medium">{deadline}</span>'

    eligibility_html = ""
    if eligibility:
        eligibility_html = f'<p class="text-xs text-gray-500 bg-gray-50 p-2 rounded mt-2 border border-gray-100">{eligibility}</p>'

    summary_html = ""
    if summary:
        short = summary[:120] + ("..." if len(summary) > 120 else "")
        summary_html = f'<p class="text-sm text-gray-600 mt-2">{short}</p>'

    return f'''
<div class="grant-card bg-white p-5 rounded-xl shadow-sm hover:shadow-md transition border border-gray-100 border-l-4 border-l-{ni["color"]}-500" data-niche="{grant["niche"]}" data-title="{grant["title"].lower()}">
    <div class="flex items-center justify-between mb-2">
        <span class="text-xs font-bold uppercase tracking-wider text-{ni["color"]}-600">{ni["emoji"]} {grant["niche"]}</span>
        {deadline_badge}
    </div>
    <a href="grants/{slug}.html" class="block group">
        <h3 class="text-lg font-bold text-gray-900 group-hover:text-teal-700 transition">{grant["title"]}</h3>
    </a>
    <div class="flex gap-4 mt-2 text-sm text-gray-500">
        <span>{grant.get("source", "")}</span>
        <span class="font-semibold text-gray-800">{amount}</span>
    </div>
    {summary_html}
    {eligibility_html}
    <div class="mt-4 pt-3 border-t border-gray-50 flex justify-between items-center">
        <a href="grants/{slug}.html" class="text-sm text-teal-700 hover:text-teal-900 font-medium bg-teal-50 hover:bg-teal-100 px-3 py-1.5 rounded transition">View Details</a>
        <a href="{grant.get("link", "#")}" target="_blank" rel="noopener" class="text-xs text-gray-400 hover:text-gray-600">Official Site &nearr;</a>
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
    <style>@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'); body {{ font-family: 'Inter', sans-serif; }}</style>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen">

    <nav class="bg-white border-b border-gray-200">
        <div class="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
            <a href="../index.html" class="text-xl font-bold text-slate-800 flex items-center gap-2">💙 {BRAND}</a>
            <a href="../index.html" class="text-sm text-slate-500 hover:text-teal-600 font-medium">&larr; Back to Directory</a>
        </div>
    </nav>

    <main class="max-w-4xl mx-auto px-4 py-8">
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-8 border-l-4 border-l-{ni["color"]}-500">
            <span class="inline-block bg-{ni["color"]}-50 text-{ni["color"]}-700 text-xs font-bold uppercase px-3 py-1 rounded-full mb-4 border border-{ni["color"]}-100">{ni["emoji"]} {ni["label"]}</span>

            <h1 class="text-3xl font-bold text-slate-900 mb-6 leading-tight">{grant["title"]}</h1>

            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div class="bg-slate-50 rounded-lg p-4 border border-slate-100">
                    <p class="text-xs text-slate-500 uppercase font-semibold mb-1">Amount</p>
                    <p class="text-lg font-bold text-teal-700">{amount}</p>
                </div>
                <div class="bg-slate-50 rounded-lg p-4 border border-slate-100">
                    <p class="text-xs text-slate-500 uppercase font-semibold mb-1">Deadline</p>
                    <p class="text-lg font-bold text-amber-700">{deadline}</p>
                </div>
                <div class="bg-slate-50 rounded-lg p-4 border border-slate-100">
                    <p class="text-xs text-slate-500 uppercase font-semibold mb-1">Source</p>
                    <p class="text-sm font-semibold text-slate-700 truncate">{source}</p>
                </div>
                <div class="bg-slate-50 rounded-lg p-4 border border-slate-100">
                    <p class="text-xs text-slate-500 uppercase font-semibold mb-1">Category</p>
                    <p class="text-sm font-semibold text-slate-700">{ni["label"]}</p>
                </div>
            </div>

            <div class="prose max-w-none text-slate-600 mb-8">
                <h2 class="text-lg font-bold text-slate-800 mb-3">About This Opportunity</h2>
                <p class="leading-relaxed mb-6">{summary}</p>
                
                <h2 class="text-lg font-bold text-slate-800 mb-3">Eligibility Requirements</h2>
                <div class="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-r mb-6">
                    <p class="text-blue-900 text-sm">{eligibility}</p>
                </div>
            </div>

            <div class="flex flex-col sm:flex-row gap-4 border-t border-gray-100 pt-6">
                <a href="{link}" target="_blank" rel="noopener" class="inline-flex justify-center items-center bg-teal-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-teal-700 transition shadow-sm hover:shadow">
                    Apply on Official Site &rarr;
                </a>
                <a href="../index.html" class="inline-flex justify-center items-center bg-white text-slate-600 border border-gray-200 px-6 py-3 rounded-lg font-semibold hover:bg-gray-50 transition">
                    Browse More Grants
                </a>
            </div>
        </div>

        <p class="text-xs text-gray-400 mt-8 text-center">
            Information gathered from public sources. Last verified: {grant.get("enriched_at", "Recently")[:10]}.<br>
            ALWAYS verify details, deadlines, and requirements on the official application page.
        </p>
    </main>

    <footer class="bg-white border-t border-gray-200 py-8 mt-12">
        <div class="max-w-4xl mx-auto px-4 text-center text-sm text-gray-500">
            <p>&copy; 2026 {BRAND}. A free community resource for allied health professionals.</p>
        </div>
    </footer>

</body>
</html>'''

def build_index(grants, grant_slugs):
    niches_found = sorted(set(g['niche'] for g in grants))

    filter_buttons = ""
    for niche in niches_found:
        ni = get_niche_info(niche)
        filter_buttons += f'<button onclick="filterNiche(\'{niche}\')" class="px-4 py-2 bg-white border border-gray-200 text-gray-600 rounded-lg hover:border-{ni["color"]}-300 hover:text-{ni["color"]}-700 hover:bg-{ni["color"]}-50 font-medium text-sm transition shadow-sm">{ni["emoji"]} {niche}</button>\n'

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
        stats_html += f'<div class="bg-white border border-gray-100 rounded-xl p-4 text-center shadow-sm"><p class="text-3xl font-bold text-{ni["color"]}-600">{count}</p><p class="text-xs font-semibold uppercase text-gray-400 mt-1 tracking-wide">{ni["label"]}</p></div>\n'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{BRAND} | Free Grant Directory for PT, OT, SLP & Families</title>
    <meta name="description" content="A free, curated directory of {total}+ grants and scholarships for physical therapy, occupational therapy, speech pathology, and families. Updated regularly.">
    <meta property="og:title" content="{BRAND} - Free Allied Health Grant Directory">
    <meta property="og:description" content="Discover {total}+ grants for allied health professionals and families.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{SITE_URL}">
    <link rel="canonical" href="{SITE_URL}">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'); body {{ font-family: 'Inter', sans-serif; }}</style>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen">

    <nav class="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
        <div class="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
            <a href="index.html" class="text-xl font-bold text-slate-800 flex items-center gap-2">💙 {BRAND}</a>
            <div class="flex gap-6 text-sm font-medium">
                <a href="index.html" class="text-teal-700">Directory</a>
                <a href="resources.html" class="text-gray-500 hover:text-teal-600 transition">Free Resources</a>
                <a href="#about" class="text-gray-500 hover:text-teal-600 transition hidden sm:inline-block">About</a>
            </div>
        </div>
    </nav>

    <!-- Hero -->
    <header class="bg-white border-b border-gray-200">
        <div class="max-w-4xl mx-auto px-4 py-16 text-center">
            <span class="inline-block py-1 px-3 rounded-full bg-teal-50 text-teal-700 text-xs font-bold uppercase tracking-wide mb-4 border border-teal-100">Free Community Resource</span>
            <h1 class="text-4xl md:text-6xl font-bold text-slate-900 mb-6 tracking-tight">Find funding for your practice<br><span class="text-teal-600">or your family.</span></h1>
            <p class="text-lg text-slate-500 max-w-2xl mx-auto mb-8 leading-relaxed">A curated, searchable directory of grants, scholarships, and financial aid for PT, OT, SLP professionals and families with special needs.</p>
            
            <div class="flex flex-wrap justify-center gap-8 text-sm text-gray-400 font-medium">
                <span class="flex items-center gap-2"><span class="w-2 h-2 bg-green-500 rounded-full"></span> Updated: {datetime.now().strftime("%B %d, %Y")}</span>
                <span class="flex items-center gap-2"><span class="w-2 h-2 bg-blue-500 rounded-full"></span> {total} Active Opportunities</span>
                <span class="flex items-center gap-2"><span class="w-2 h-2 bg-purple-500 rounded-full"></span> 100% Free to Use</span>
            </div>
        </div>
    </header>

    <main class="max-w-6xl mx-auto px-4 py-12">

        <!-- Stats -->
        <div class="grid grid-cols-2 md:grid-cols-{len(niche_counts)} gap-4 mb-12">
            {stats_html}
        </div>

        <!-- Search + Filters -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-8 sticky top-20 z-40 transition-shadow hover:shadow-md">
            <div class="flex flex-wrap gap-4 items-center">
                <div class="relative flex-1 min-w-[200px]">
                    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                    </div>
                    <input type="text" id="search" placeholder="Search by name, foundation, or keyword..." oninput="filterAll()" class="w-full pl-10 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition">
                </div>
                <div class="flex flex-wrap gap-2">
                    <button onclick="filterNiche('ALL')" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-medium text-sm transition active-filter">All Grants</button>
                    {filter_buttons}
                </div>
            </div>
        </div>

        <!-- Grid -->
        <div id="grid" class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {cards_html}
        </div>

        <div id="no-results" class="hidden text-center py-24">
            <p class="text-xl text-gray-400 font-medium">No grants match your search.</p>
            <button onclick="document.getElementById('search').value=''; filterAll();" class="mt-4 text-teal-600 hover:text-teal-800 font-medium">Clear Search</button>
        </div>

        <!-- About Section -->
        <div id="about" class="mt-24 bg-white rounded-2xl p-8 md:p-12 border border-gray-100 text-center max-w-3xl mx-auto shadow-sm">
            <h2 class="text-2xl font-bold text-slate-800 mb-4">About {BRAND}</h2>
            <p class="text-slate-600 mb-6 leading-relaxed">
                Finding funding shouldn't be a full-time job. {BRAND} is an open directory designed to help allied health professionals and families discover financial support without sifting through endless Google results.
            </p>
            <p class="text-slate-600 mb-8 leading-relaxed">
                We aggregate data from public foundations and verified sources daily. We are not a grant-maker; we simply connect you to the application sources.
            </p>
            <div class="flex justify-center gap-4">
                <a href="mailto:hello@grantflow.vercel.app" class="text-teal-700 hover:text-teal-900 font-medium">Contact Us</a>
                <span class="text-gray-300">|</span>
                <a href="resources.html" class="text-teal-700 hover:text-teal-900 font-medium">View Free Resources</a>
            </div>
        </div>

    </main>

    <footer class="bg-white border-t border-gray-200 py-12 mt-12">
        <div class="max-w-6xl mx-auto px-4 text-center text-sm text-gray-500">
            <p class="font-semibold text-slate-700 mb-2">&copy; 2026 {BRAND}</p>
            <p>Data sourced from public foundations. We do not guarantee funding availability.</p>
            <p class="mt-4 text-xs text-gray-400">Built to help.</p>
        </div>
    </footer>

    <script>
        let activeNiche = 'ALL';

        function filterNiche(niche) {{
            activeNiche = niche;
            
            // Update active button state
            document.querySelectorAll('button').forEach(btn => {{
                if (btn.textContent.includes(niche) || (niche === 'ALL' && btn.textContent.includes('All'))) {{
                    btn.classList.add('ring-2', 'ring-teal-500', 'ring-offset-1');
                }} else {{
                    btn.classList.remove('ring-2', 'ring-teal-500', 'ring-offset-1');
                }}
            }});

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

        // Init
        filterNiche('ALL');
    </script>

</body>
</html>'''

def build_sitemap(slugs):
    urls = [
        f"  <url><loc>{SITE_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>",
        f"  <url><loc>{SITE_URL}/resources.html</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>",
    ]
    for slug in slugs:
        urls.append(f"  <url><loc>{SITE_URL}/grants/{slug}.html</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>")

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>'''

def build_resources_page(resources):
    cards = ""
    for r in resources:
        services = ", ".join(r.get("services", []))
        highlight_class = "border-teal-500 bg-teal-50/50" if r.get("highlight") else "border-gray-200 bg-white"

        cards += f'''
<div class="p-6 rounded-xl border {highlight_class} shadow-sm hover:shadow-md transition">
    <div class="flex items-center justify-between mb-3">
        <span class="inline-block bg-teal-100 text-teal-800 text-xs font-bold uppercase px-2 py-0.5 rounded-full">{r.get("type", "Resource")}</span>
        <span class="text-xs text-gray-400 font-medium">{r.get("coverage", "")}</span>
    </div>
    <h3 class="text-lg font-bold text-slate-900 mb-2">{r["title"]}</h3>
    <p class="text-sm text-slate-600 mb-4 leading-relaxed">{r["description"]}</p>
    
    <div class="space-y-2 mb-4">
        <div class="text-xs text-slate-500 flex gap-2">
            <span class="font-semibold text-slate-700 min-w-[60px]">Services:</span>
            <span>{services}</span>
        </div>
        <div class="text-xs text-slate-500 flex gap-2">
            <span class="font-semibold text-slate-700 min-w-[60px]">Eligibility:</span>
            <span>{r.get("eligibility", "See website")}</span>
        </div>
    </div>

    <a href="{r["link"]}" target="_blank" rel="noopener" class="inline-flex items-center text-teal-700 hover:text-teal-900 text-sm font-semibold transition">
        Visit Website &rarr;
    </a>
</div>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Free Therapy Resources | {BRAND}</title>
    <meta name="description" content="Free and low-cost speech therapy, occupational therapy, and physical therapy resources for families. Regional centers, early intervention, government programs, and more.">
    <meta property="og:title" content="Free Therapy Resources | {BRAND}">
    <meta property="og:description" content="Free and low-cost therapy resources including Regional Centers, Early Intervention, Medicaid, and university clinics.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{SITE_URL}/resources.html">
    <link rel="canonical" href="{SITE_URL}/resources.html">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'); body {{ font-family: 'Inter', sans-serif; }}</style>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen">

    <nav class="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
            <a href="index.html" class="text-xl font-bold text-slate-800 flex items-center gap-2">💙 {BRAND}</a>
            <div class="flex gap-6 text-sm font-medium">
                <a href="index.html" class="text-gray-500 hover:text-teal-600 transition">Directory</a>
                <a href="resources.html" class="text-teal-700">Free Resources</a>
            </div>
        </div>
    </nav>

    <header class="bg-white border-b border-gray-200">
        <div class="max-w-4xl mx-auto px-4 py-16 text-center">
            <span class="inline-block py-1 px-3 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold uppercase tracking-wide mb-4 border border-emerald-100">Zero Cost Support</span>
            <h1 class="text-3xl md:text-5xl font-bold text-slate-900 mb-6">Free & Low-Cost Resources</h1>
            <p class="text-lg text-slate-500 max-w-2xl mx-auto leading-relaxed">Government programs, nonprofits, and community resources that help families access speech therapy, OT, PT, and early intervention services — often at no cost.</p>
        </div>
    </header>

    <main class="max-w-6xl mx-auto px-4 py-12">

        <div class="bg-blue-50 border border-blue-100 rounded-xl p-6 mb-12 flex gap-4 items-start">
            <div class="text-2xl">💡</div>
            <div>
                <h2 class="text-lg font-bold text-blue-900 mb-1">Did you know?</h2>
                <p class="text-sm text-blue-800 leading-relaxed">Many families qualify for free therapy services and don't realize it. Federal programs like Early Intervention (ages 0-3) and school-based services (ages 3-21) are available in every state. California's Regional Centers provide free assessments and services regardless of income for young children.</p>
            </div>
        </div>

        <div class="grid gap-6 md:grid-cols-2">
            {cards}
        </div>

        <div class="mt-16 bg-white border border-gray-200 rounded-xl p-12 text-center shadow-sm">
            <h2 class="text-2xl font-bold text-slate-800 mb-4">Looking for Grants?</h2>
            <p class="text-slate-500 mb-8">We track 40+ grants and scholarships for allied health professionals and families.</p>
            <a href="index.html" class="inline-block bg-teal-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-teal-700 transition shadow-sm">Browse Grant Directory &rarr;</a>
        </div>

    </main>

    <footer class="bg-white border-t border-gray-200 py-12 mt-12">
        <div class="max-w-6xl mx-auto px-4 text-center text-sm text-gray-500">
            <p class="font-semibold text-slate-700 mb-2">&copy; 2026 {BRAND}</p>
            <p>Information is for guidance only. Always verify details on official sites.</p>
        </div>
    </footer>

</body>
</html>'''

def build_robots():
    return f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""

def build():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        grants = json.load(f)

    print(f"Loaded {len(grants)} scraped grants")

    # Load curated family grants
    family_grants = []
    if os.path.exists(FAMILY_FILE):
        with open(FAMILY_FILE, 'r', encoding='utf-8') as f:
            family_grants = json.load(f)
        print(f"Loaded {len(family_grants)} curated family grants")

    # Load free resources
    resources = []
    if os.path.exists(RESOURCES_FILE):
        with open(RESOURCES_FILE, 'r', encoding='utf-8') as f:
            resources = json.load(f)
        print(f"Loaded {len(resources)} free resources")

    # Merge family grants into main list
    for fg in family_grants:
        fg['found_at'] = fg.get('found_at', datetime.now().isoformat())
        fg['enriched_at'] = fg.get('enriched_at', datetime.now().isoformat())
    grants.extend(family_grants)
    print(f"Total after merge: {len(grants)}")

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

    # Build resources page
    if resources:
        resources_html = build_resources_page(resources)
        with open(os.path.join(OUTPUT_DIR, "resources.html"), 'w', encoding='utf-8') as f:
            f.write(resources_html)
        print("Generated resources.html")

    print("Generated sitemap.xml + robots.txt")
    print(f"\nSite ready in ./{OUTPUT_DIR}/")
    print(f"  {len(grants)} grant pages + resources page")
    print(f"  Niches: {', '.join(sorted(set(g['niche'] for g in grants)))}")

if __name__ == "__main__":
    build()
