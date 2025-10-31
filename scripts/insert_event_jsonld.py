#!/usr/bin/env python3
"""
Insert a simple schema.org Event JSON-LD into every HTML file under events/.
Creates a .bak copy before changing a file. Skips files which already contain an Event JSON-LD.

Usage (from project root):
  python scripts/insert_event_jsonld.py

This script is conservative: it uses regex to extract title, meta description, portfolio-info Event/Date and first gallery image.
It writes site-root-relative URLs (starting with /) for `url` and `image` because no site domain was provided.
"""
from pathlib import Path
import re
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
EVENTS_DIR = ROOT / 'events'

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

# regex helpers
meta_desc_re = re.compile(r'<meta[^>]+name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', re.I)
head_close_re = re.compile(r'</head\s*>', re.I)
# capture portfolio-info block
portfolio_info_re = re.compile(r'<div[^>]+class=["\']portfolio-info["\'][^>]*>(.*?)</div>', re.I|re.S)
# capture <li><strong>Event</strong> ...</li>
event_li_re = re.compile(r'<li[^>]*>\s*<strong[^>]*>\s*Event\s*</strong>\s*[:\-–]*\s*(.*?)</li>', re.I|re.S)
# capture <li><strong>Date</strong> ...</li>
date_li_re = re.compile(r'<li[^>]*>\s*<strong[^>]*>\s*Date\s*</strong>\s*[:\-–]*\s*(.*?)</li>', re.I|re.S)
# first image in gallery
gallery_img_re = re.compile(r'<div[^>]+class=["\']portfolio-gallery["\'][^>]*>.*?<img[^>]+src=["\']([^"\']+)["\']', re.I|re.S)
# detect existing Event JSON-LD
existing_event_re = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I|re.S)

summary = {'scanned':0, 'patched':0, 'skipped_existing':0, 'errors':[]}

for html_path in sorted(EVENTS_DIR.glob('*.html')):
    summary['scanned'] += 1
    try:
        text = html_path.read_text(encoding='utf-8')
    except Exception as e:
        summary['errors'].append(f'{html_path}: read error {e}')
        continue

    # skip if already contains Event JSON-LD
    found_ld = False
    for m in existing_event_re.finditer(text):
        try:
            data = json.loads(m.group(1))
            # data can be object or list
            if isinstance(data, dict) and data.get('@type','').lower() == 'event':
                found_ld = True
                break
            # handle Graph or list
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get('@type','').lower() == 'event':
                        found_ld = True
                        break
        except Exception:
            # not json or not relevant
            continue
    if found_ld:
        summary['skipped_existing'] += 1
        continue

    # extract fields
    name = None
    description = None
    startDate = None
    image = None

    # title tag fallback
    title_m = re.search(r'<title[^>]*>(.*?)</title>', text, re.I|re.S)
    if title_m:
        title_text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>','',title_m.group(1))).strip()
    else:
        title_text = None

    # meta description
    md = meta_desc_re.search(text)
    if md:
        description = md.group(1).strip()

    # portfolio-info
    pinfo_m = portfolio_info_re.search(text)
    if pinfo_m:
        pblock = pinfo_m.group(1)
        ev = event_li_re.search(pblock)
        if ev:
            name = re.sub(r'<[^>]+>','',ev.group(1)).strip()
        dt = date_li_re.search(pblock)
        if dt:
            raw = re.sub(r'<[^>]+>','',dt.group(1)).strip()
            # try parse like '16 Fev, 2025' or 'Julho - 2025' or '2025'
            d_m = re.search(r'(\d{1,2})\s+([A-Za-zÀ-ÖØ-öø-ÿ]+)\s*,?\s*(\d{4})', raw)
            if d_m:
                day = int(d_m.group(1))
                mon = d_m.group(2).lower()
                yr = int(d_m.group(3))
                mon_key = mon[:3]
                mon_num = MONTHS.get(mon_key, MONTHS.get(mon))
                if mon_num:
                    startDate = f"{yr:04d}-{mon_num}-{day:02d}"
            else:
                # try Month - Year
                d_m2 = re.search(r'([A-Za-zÀ-ÖØ-öø-ÿ]+)\s*[-–]\s*(\d{4})', raw)
                if d_m2:
                    mon = d_m2.group(1).lower()
                    yr = int(d_m2.group(2))
                    mon_key = mon[:3]
                    mon_num = MONTHS.get(mon_key, MONTHS.get(mon))
                    if mon_num:
                        startDate = f"{yr:04d}-{mon_num}-01"

    # fallback to title if no name
    if not name and title_text:
        # remove prefix like 'Portfolio Details - '
        name = re.sub(r'^[^\-]*-\s*','',title_text).strip()

    # gallery image
    gi = gallery_img_re.search(text)
    if gi:
        img_src = gi.group(1).strip()
        # normalize to site-root-relative
        if img_src.startswith('../'):
            img_path = '/' + img_src.replace('../','')
        elif img_src.startswith('./'):
            img_path = '/' + img_src.replace('./','')
        elif img_src.startswith('/'):
            img_path = img_src
        else:
            img_path = '/' + img_src.lstrip('/')
        image = img_path

    # build JSON-LD
    ld = {'@context':'https://schema.org', '@type':'Event'}
    if name:
        ld['name'] = name
    if description:
        ld['description'] = description
    if startDate:
        ld['startDate'] = startDate
    # build url relative to site root
    url_path = '/' + 'events/' + html_path.name
    ld['url'] = url_path
    if image:
        ld['image'] = image

    # ensure at least name or description present
    if not (name or description):
        # nothing useful to add; skip
        summary['errors'].append(f'{html_path}: no name/description found; skipping')
        continue

    ld_json = json.dumps(ld, ensure_ascii=False, indent=2)
    script_tag = f"<script type=\"application/ld+json\">\n{ld_json}\n</script>\n"

    # insert before </head>
    if head_close_re.search(text):
        new_text = head_close_re.sub(script_tag + '\n</head>', text, count=1)
    else:
        summary['errors'].append(f'{html_path}: no </head> found; skipping')
        continue

    # backup and write
    bak = html_path.with_suffix(html_path.suffix + '.bak')
    try:
        shutil.copy2(html_path, bak)
        html_path.write_text(new_text, encoding='utf-8')
        summary['patched'] += 1
    except Exception as e:
        summary['errors'].append(f'{html_path}: write error {e}')

# print summary
print('Processed events directory:', EVENTS_DIR)
print('Scanned files:', summary['scanned'])
print('Patched files:', summary['patched'])
print('Skipped (existing Event JSON-LD):', summary['skipped_existing'])
if summary['errors']:
    print('\nErrors or skips:')
    for e in summary['errors']:
        print(' -', e)
else:
    print('No errors.')
