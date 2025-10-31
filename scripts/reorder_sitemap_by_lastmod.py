#!/usr/bin/env python3
"""
Reorder sitemap.xml <url> entries by <lastmod> descending (newest first).
Creates a backup sitemap.xml.reordered.bak before writing.

Usage:
  python scripts/reorder_sitemap_by_lastmod.py
"""
from pathlib import Path
import xml.etree.ElementTree as ET
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
SITEMAP = ROOT / 'sitemap.xml'
BACKUP = ROOT / 'sitemap.xml.reordered.bak'

ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
ET.register_namespace('', ns['sm'])

# parse
tree = ET.parse(SITEMAP)
root = tree.getroot()

# collect url elements with parsed date
entries = []
for url in root.findall('sm:url', ns):
    lastmod = url.find('sm:lastmod', ns)
    date = None
    if lastmod is not None and lastmod.text:
        txt = lastmod.text.strip()
        try:
            # try ISO format
            date = datetime.fromisoformat(txt)
        except Exception:
            try:
                date = datetime.strptime(txt, '%Y-%m-%d')
            except Exception:
                date = None
    # if no date, treat as very old
    entries.append((date or datetime(1970,1,1), url))

# sort by date desc
entries.sort(key=lambda x: x[0], reverse=True)

# create new root and append sorted urls
new_root = ET.Element(root.tag, root.attrib)
for dt, url in entries:
    # append a deep copy of url
    new_root.append(url)

# backup and write
shutil.copy2(SITEMAP, BACKUP)
new_tree = ET.ElementTree(new_root)
new_tree.write(SITEMAP, encoding='utf-8', xml_declaration=True)

print('Reordered sitemap written to', SITEMAP)
print('Backup created at', BACKUP)
