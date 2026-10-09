#!/usr/bin/env python3
"""Check the deployable folder without downloading dependencies."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import re

ROOT = Path(__file__).resolve().parents[1] / "dist"
errors = []

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.anchors, self.resources = set(), [], []
        self.headings = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            if a["id"] in self.ids:
                errors.append(f"Duplicate ID: {a['id']}")
            self.ids.add(a["id"])
        if tag == "h1": self.headings += 1
        if tag == "img" and not all(k in a for k in ("alt", "width", "height")):
            errors.append("Image missing alt text or intrinsic size")
        if "style" in a or any(k.startswith("on") for k in a):
            errors.append("Inline style or event handler conflicts with CSP")
        if "src" in a: self.resources.append(a["src"])
        if "srcset" in a:
            self.resources.extend(item.strip().split()[0] for item in a["srcset"].split(","))
        if tag == "link" and a.get("rel") in ("stylesheet", "preload"):
            self.resources.append(a["href"])
        if tag == "a" and a.get("href", "").startswith("#"):
            self.anchors.append(a["href"][1:])

for file in ROOT.glob("*.html"):
    page = Page()
    page.feed(file.read_text())
    if page.headings != 1: errors.append(f"{file.name}: expected one h1")
    for anchor in page.anchors:
        if anchor not in page.ids: errors.append(f"Broken anchor: {anchor}")
    for reference in page.resources:
        url = urlsplit(reference)
        if url.scheme or url.netloc:
            errors.append(f"External runtime resource: {reference}")
        elif not (ROOT / url.path.lstrip("/")).is_file():
            errors.append(f"Missing asset: {reference}")

css = (ROOT / "styles.css").read_text()
compact_css = re.sub(r"\s+", "", css)
for reference in re.findall(r"url\(['\"]?([^)'\"]+)", css):
    if not (ROOT / reference).is_file(): errors.append(f"Missing CSS asset: {reference}")
if "prefers-reduced-motion:reduce" not in compact_css:
    errors.append("Reduced-motion override missing")
if "prefers-color-scheme:light" not in compact_css:
    errors.append("Light appearance missing")
for required in ("_headers", "assets/fonts/OFL.txt", "assets/fonts/bricolage-OFL.txt", "assets/social-preview.jpg"):
    if not (ROOT / required).is_file(): errors.append(f"Missing release file: {required}")
total = sum(p.stat().st_size for p in ROOT.rglob("*") if p.is_file())
if total > 3_000_000: errors.append(f"Release exceeds 3 MB: {total} bytes")
if errors:
    raise SystemExit("\n".join(errors))
print(f"Release checks passed. Total payload: {total:,} bytes ({total / 1_000_000:.2f} MB).")
