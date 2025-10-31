#!/usr/bin/env python3
"""
Set <changefreq> to "never" for sitemap entries older than 365 days or with priority <= 0.5.
Creates a backup sitemap.xml.never.bak before writing.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
SITEMAP = ROOT / 'sitemap.xml'
BACKUP = ROOT / 'sitemap.xml.never.bak'

TODAY = datetime(2025, 10, 31)
ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
ET.register_namespace('', ns['sm'])

tree = ET.parse(SITEMAP)
root = tree.getroot()

changed = 0
for url in root.findall('sm:url', ns):
    lastmod = url.find('sm:lastmod', ns)
    priority_el = url.find('sm:priority', ns)
    pr = None
    if priority_el is not None and priority_el.text:
        try:
            pr = float(priority_el.text.strip())
        except Exception:
            pr = None
    lm_date = None
    if lastmod is not None and lastmod.text:
        try:
            lm_date = datetime.fromisoformat(lastmod.text.strip())
        except Exception:
            try:
                lm_date = datetime.strptime(lastmod.text.strip(), '%Y-%m-%d')
            except Exception:
                lm_date = None
    days = None
    if lm_date:
        days = (TODAY - lm_date).days
    # condition: older than 365 days OR priority <= 0.5
    if (days is not None and days > 365) or (pr is not None and pr <= 0.5):
        cf = url.find('sm:changefreq', ns)
        if cf is None:
            cf = ET.SubElement(url, 'changefreq')
        if cf.text != 'never':
            cf.text = 'never'
            changed += 1

shutil.copy2(SITEMAP, BACKUP)
tree.write(SITEMAP, encoding='utf-8', xml_declaration=True)
print('Set changefreq="never" for', changed, 'entries. Backup at', BACKUP)
