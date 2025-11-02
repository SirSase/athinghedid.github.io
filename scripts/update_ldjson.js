/*
Script: update_ldjson.js
Purpose: Scan events/*.html (skip *.bak), extract <title>, <meta name="description"> and <meta name="keywords"> and add/replace
<script type="application/ld+json"> in the <head> with a structured JSON-LD following the user's template.

Usage (from project root):
  node scripts/update_ldjson.js

This script makes an automatic .bak copy of each modified file with suffix .pre-ldbak
*/

const fs = require('fs');
const path = require('path');

const EVENTS_DIR = path.join(__dirname, '..', 'events');
const CREATOR = 'Tiago Batista';

function readFile(file) {
  return fs.readFileSync(file, { encoding: 'utf8' });
}

function writeFile(file, content) {
  fs.writeFileSync(file, content, { encoding: 'utf8' });
}

function makeBackup(file) {
  const backup = file + '.pre-ldbak';
  if (!fs.existsSync(backup)) {
    fs.copyFileSync(file, backup);
  }
}

function extractBetween(html, startTag, endTag) {
  const s = html.indexOf(startTag);
  if (s === -1) return '';
  const e = html.indexOf(endTag, s + startTag.length);
  if (e === -1) return '';
  return html.slice(s + startTag.length, e);
}

function extractTagContent(html, tagName) {
  const regex = new RegExp(`<${tagName}[^>]*>([\s\S]*?)<\\/${tagName}>`, 'i');
  const m = html.match(regex);
  if (m) return m[1].trim();
  return '';
}

function extractMeta(html, metaName) {
  const regex = new RegExp(`<meta\\s+[^>]*name=["']${metaName}["'][^>]*>`, 'i');
  const m = html.match(regex);
  if (!m) return '';
  const tag = m[0];
  const contentMatch = tag.match(/content=["']([\s\S]*?)["']/i);
  return contentMatch ? contentMatch[1].trim() : '';
}

function normalizeName(title) {
  if (!title) return '';
  // Remove common prefix like "Portfolio Details - " if present
  return title.replace(/^Portfolio Details\s*-\s*/i, '').trim();
}

function buildJsonLd(data) {
  const obj = {
    '@context': 'https://schema.org',
    '@type': 'CreativeWork',
    'name': `${data.name} by ${CREATOR}`,
    'headline': data.headline || data.name,
    'url': data.url,
    'keywords': data.keywords,
    'creator': [CREATOR],
    'author': [CREATOR]
  };
  return JSON.stringify(obj, null, 2);
}

function replaceOrInsertJsonLd(html, jsonLdString) {
  // Find existing <script type="application/ld+json"> ... </script> in head
    // locate head start/end in a case-insensitive but safe way
    const lower = html.toLowerCase();
    let headStart = lower.indexOf('<head');
    if (headStart !== -1) {
      // move to the end of the opening <head...> tag
      const gt = html.indexOf('>', headStart);
      headStart = gt === -1 ? headStart : headStart;
    }
    const headEnd = lower.indexOf('</head>');
  if (headStart === -1 || headEnd === -1) {
    // Can't find head, return original
    return html;
  }
  const headContent = html.slice(headStart, headEnd + 7); // include '</head>' length 7

  // build script regex using RegExp constructor to avoid literal escaping issues
  const scriptRegex = new RegExp('<script[^>]*type=["\\\']application/ld\\+json["\\\'][^>]*>[\\s\\S]*?<\\/script>', 'i');
  const newScript = `<script type="application/ld+json">\n${jsonLdString}\n</script>`;

  if (scriptRegex.test(headContent)) {
    const newHeadContent = headContent.replace(scriptRegex, newScript);
    return html.slice(0, headStart) + newHeadContent + html.slice(headEnd + 7);
  } else {
    // Insert before closing </head>
    const insertPos = headEnd;
    return html.slice(0, insertPos) + newScript + '\n' + html.slice(insertPos);
  }
}

function splitKeywords(raw) {
  if (!raw) return [];
  // Split on commas, semicolons, vertical bars, or slashes
  return raw.split(/[;,\\|/]+/).map(s => s.trim()).filter(Boolean);
}

function processFile(filePath) {
  const html = readFile(filePath);

  const title = extractTagContent(html, 'title') || '';
  const name = normalizeName(title) || path.basename(filePath, '.html');
  const description = extractMeta(html, 'description') || '';
  const rawKeywords = extractMeta(html, 'keywords') || '';
  const keywords = splitKeywords(rawKeywords);
  const urlPath = '/events/' + path.basename(filePath);

  const jsonLd = buildJsonLd({ name, headline: description, keywords: keywords, url: urlPath });

  const newHtml = replaceOrInsertJsonLd(html, jsonLd);

  if (newHtml !== html) {
    makeBackup(filePath);
    writeFile(filePath, newHtml);
    return { file: filePath, changed: true };
  }
  return { file: filePath, changed: false };
}

function main() {
  if (!fs.existsSync(EVENTS_DIR)) {
    console.error('Events directory not found:', EVENTS_DIR);
    process.exit(1);
  }

  const files = fs.readdirSync(EVENTS_DIR).filter(f => f.endsWith('.html') && !f.endsWith('.bak'));
  const results = [];
  for (const f of files) {
    const full = path.join(EVENTS_DIR, f);
    try {
      const r = processFile(full);
      results.push(r);
      console.log(`${r.changed ? 'UPDATED' : 'SKIPPED'}: ${f}`);
    } catch (err) {
      console.error('ERROR processing', f, err.message);
      results.push({ file: full, changed: false, error: err.message });
    }
  }

  const updated = results.filter(r => r.changed).length;
  console.log('Done. Files scanned:', results.length, 'Updated:', updated);
}

if (require.main === module) main();
