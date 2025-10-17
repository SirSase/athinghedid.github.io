This project now includes simple SEO/indexing helpers:

- `robots.txt` — allows all crawlers and points to `/sitemap.xml`.
- `sitemap.xml` — a starter sitemap listing key pages. Update this file when you add or remove pages.

Recommendations:
- Keep `sitemap.xml` up to date. For many pages, generate it automatically from your build/script or CMS.
- Submit the sitemap URL to Google Search Console: https://search.google.com/search-console
- If your site supports search, replace the `potentialAction.target` URL in the JSON-LD with the actual search URL.
- If hosting under a different domain or path, update the canonical and sitemap URLs in `index.html` and `robots.txt` accordingly.
