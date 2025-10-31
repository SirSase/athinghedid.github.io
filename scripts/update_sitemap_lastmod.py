#!/usr/bin/env python3
"""
Update sitemap.xml lastmod entries to match the event date found in each events/*.html page.
Creates sitemap.xml.bak before writing.

Usage:
  python scripts/update_sitemap_lastmod.py
"""
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
EVENTS_DIR = ROOT / 'events'
SITEMAP = ROOT / 'sitemap.xml'

MONTHS = {
    'jan': '01','janeiro':'01',
    'fev': '02','fevereiro':'02',
    'mar': '03','março':'03','marco':'03',
    'abr': '04','abril':'04',
    'mai': '05','maio':'05',
    'jun': '06','junho':'06',
    'jul': '07','julho':'07',
    'ago': '08','agosto':'08',
    'set': '09','setembro':'09',
    'out': '10','outubro':'10',
    'nov': '11','novembro':'11',
    'dez': '12','dezembro':'12'
}

portfolio_info_re = re.compile(r'<div[^>]+class=["\']portfolio-info["\'][^>]*>(.*?)</div>', re.I|re.S)
li_re = re.compile(r'<li[^>]*>(.*?)</li>', re.I|re.S)
span_date_marker = re.compile(r'data-i18n=["\']date["\']', re.I)
# fallback date pattern
date_pattern1 = re.compile(r'(\d{1,2})\s+([A-Za-zÀ-ÖØ-öø-ÿ]+)\s*,?\s*(\d{4})')
date_pattern2 = re.compile(r'([A-Za-zÀ-ÖØ-öø-ÿ]+)\s*[-–]\s*(\d{4})')

# read sitemap
smap_text = SITEMAP.read_text(encoding='utf-8')
updated = 0
skipped = []

for html_path in sorted(EVENTS_DIR.glob('*.html')):
    try:
        text = html_path.read_text(encoding='utf-8')
    except Exception as e:
        skipped.append((html_path.name, f'read error {e}'))
        continue

    pinfo_m = portfolio_info_re.search(text)
    found_date = None
    if pinfo_m:
        pblock = pinfo_m.group(1)
        # search for li containing the span marker first
        for li in li_re.finditer(pblock):
            li_html = li.group(1)
            if span_date_marker.search(li_html) or re.search(r'<strong[^>]*>\s*(Date|Data)\s*</strong>', li_html, re.I):
                # strip tags
                li_text = re.sub(r'<[^>]+>', '', li_html).strip()
                # li_text might be like 'Date: 19 Out, 2025' or 'Data: 19 Out, 2025'
                m1 = date_pattern1.search(li_text)
                if m1:
                    day = int(m1.group(1))
                    mon = m1.group(2).lower()
                    yr = int(m1.group(3))
                    mon_key = mon[:3]
                    mon_num = MONTHS.get(mon_key, MONTHS.get(mon))
                    if mon_num:
                        found_date = f"{yr:04d}-{mon_num}-{day:02d}"
                        break
                m2 = date_pattern2.search(li_text)
                if m2:
                    mon = m2.group(1).lower()
                    yr = int(m2.group(2))
                    mon_key = mon[:3]
                    mon_num = MONTHS.get(mon_key, MONTHS.get(mon))
                    if mon_num:
                        found_date = f"{yr:04d}-{mon_num}-01"
                        break
    # if not found, try fallback: search anywhere for a date-like pattern
    if not found_date:
        m1 = date_pattern1.search(text)
        if m1:
            day = int(m1.group(1))
            mon = m1.group(2).lower()
            yr = int(m1.group(3))
            mon_key = mon[:3]
            mon_num = MONTHS.get(mon_key, MONTHS.get(mon))
            if mon_num:
                found_date = f"{yr:04d}-{mon_num}-{day:02d}"

    if not found_date:
        skipped.append((html_path.name, 'no date parsed'))
        continue

    # find corresponding <loc> element in sitemap for this event
    url_path = f"https://www.athinghedid.com/events/{html_path.name}"
    # pattern to find <loc>...</loc> then the immediate following <lastmod>...</lastmod>
    # We'll replace the first <lastmod> after the matching <loc>
    loc_pos = smap_text.find(url_path)
    if loc_pos == -1:
        skipped.append((html_path.name, 'url not in sitemap'))
        continue
    # find the lastmod tag after loc_pos
    lastmod_search = re.search(r'<lastmod>\s*(.*?)\s*</lastmod>', smap_text[loc_pos:], re.I)
    if lastmod_search:
        old = lastmod_search.group(0)
        new_tag = f'<lastmod>{found_date}</lastmod>'
        # replace only the first occurrence after loc_pos
        prefix = smap_text[:loc_pos]
        suffix = smap_text[loc_pos:]
        suffix = suffix.replace(old, new_tag, 1)
        smap_text = prefix + suffix
        updated += 1
    else:
        skipped.append((html_path.name, 'no lastmod after loc'))

# backup and write sitemap
bak = SITEMAP.with_suffix('.xml.bak')
shutil.copy2(SITEMAP, bak)
SITEMAP.write_text(smap_text, encoding='utf-8')

print('Updated sitemap lastmod for', updated, 'events')
if skipped:
    print('Skipped or errors for:')
    for s in skipped:
        print(' -', s[0], ':', s[1])
