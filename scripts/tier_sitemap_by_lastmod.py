#!/usr/bin/env python3
"""
Read sitemap.xml, compute days since each <lastmod> (relative to 2025-10-31 or today),
and update <changefreq> and <priority> according to recency tiers.
Produces a backup sitemap.xml.tiered.bak before writing.

Tiers (days since lastmod):
 - 0-30d: weekly, priority 1.0
 - 31-90d: weekly, priority 0.9
 - 91-180d: monthly, priority 0.8
 - 181-365d: monthly, priority 0.7
 - >365d: yearly, priority 0.5

Usage:
  python scripts/tier_sitemap_by_lastmod.py
"""
from pathlib import Path
import xml.etree.ElementTree as ET
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
SITEMAP = ROOT / 'sitemap.xml'
BACKUP = ROOT / 'sitemap.xml.tiered.bak'

# Use fixed today to match repo context
TODAY = datetime(2025, 10, 31)

ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
ET.register_namespace('', ns['sm'])

tree = ET.parse(SITEMAP)
root = tree.getroot()

counts = {'0-30':0,'31-90':0,'91-180':0,'181-365':0,'>365':0,'no-lastmod':0}

for url in root.findall('sm:url', ns):
    # find lastmod
    lastmod = url.find('sm:lastmod', ns)
    if lastmod is None or not lastmod.text:
        counts['no-lastmod'] += 1
        # default to monthly/0.7
        cf, pr = 'monthly','0.7'
    else:
        try:
            lm = datetime.fromisoformat(lastmod.text.strip())
        except Exception:
            # try date-only
            try:
                lm = datetime.strptime(lastmod.text.strip(), '%Y-%m-%d')
            except Exception:
                counts['no-lastmod'] += 1
                lm = None
        if lm is None:
            cf, pr = 'monthly','0.7'
        else:
            days = (TODAY - lm).days
            if days <= 30:
                cf, pr = 'weekly', '1.0'
                counts['0-30'] += 1
            elif days <= 90:
                cf, pr = 'weekly', '0.9'
                counts['31-90'] += 1
            elif days <= 180:
                cf, pr = 'monthly', '0.8'
                counts['91-180'] += 1
            elif days <= 365:
                cf, pr = 'monthly', '0.7'
                counts['181-365'] += 1
            else:
                cf, pr = 'yearly', '0.5'
                counts['>365'] += 1

    # set or update changefreq and priority
    changefreq = url.find('sm:changefreq', ns)
    if changefreq is None:
        changefreq = ET.SubElement(url, 'changefreq')
    changefreq.text = cf

    priority = url.find('sm:priority', ns)
    if priority is None:
        priority = ET.SubElement(url, 'priority')
    priority.text = pr

# backup and write
shutil.copy2(SITEMAP, BACKUP)
# write pretty (ElementTree doesn't pretty print; write as-is)
tree.write(SITEMAP, encoding='utf-8', xml_declaration=True)

print('Sitemap tiering complete. Summary:')
for k,v in counts.items():
    print(f'  {k}: {v}')
print('Backup at', BACKUP)
