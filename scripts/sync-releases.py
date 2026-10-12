#!/usr/bin/env python3
"""Generate static release history and version labels from published GitHub releases."""
import argparse
from datetime import datetime
from html import escape
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "dayedge/dayedge"
VERSION = re.compile(r"v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\Z")
INLINE = re.compile(r"`([^`]+)`|\*\*(.+?)\*\*|\[([^\]]+)\]\(([^\s)]+)\)")


def inline(text):
    parts, position = [], 0
    for match in INLINE.finditer(text):
        parts.append(escape(text[position:match.start()]))
        code, bold, label, url = match.groups()
        if code is not None:
            parts.append(f"<code>{escape(code)}</code>")
        elif bold is not None:
            parts.append(f"<strong>{escape(bold)}</strong>")
        elif urlsplit(url).scheme == "https":
            parts.append(f'<a href="{escape(url, quote=True)}">{escape(label)}</a>')
        else:
            parts.append(escape(label))
        position = match.end()
    parts.append(escape(text[position:]))
    return "".join(parts)


def markdown(text):
    """The release-note subset: headings, paragraphs, lists, code, bold and links."""
    output, paragraph, code = [], [], []
    in_code = in_list = False

    def flush():
        if paragraph:
            output.append(f'<p>{inline(" ".join(paragraph))}</p>')
            paragraph.clear()

    for line in text.splitlines() + [""]:
        stripped = line.strip()
        if stripped.startswith("```"):
            flush()
            if in_list:
                output.append("</ul>")
                in_list = False
            if in_code:
                output.append("<pre><code>" + escape("\n".join(code)) + "</code></pre>")
                code.clear()
            in_code = not in_code
            continue
        if in_code:
            code.append(line)
            continue
        heading = re.match(r"^#{1,6}\s+(.+?)(?:\s+#+)?$", stripped)
        bullet = re.match(r"^(?:[-*+] |\d+[.)] )(.+)$", stripped)
        if not stripped or heading or bullet:
            flush()
        if in_list and not bullet:
            output.append("</ul>")
            in_list = False
        if heading:
            output.append(f"<h3>{inline(heading[1])}</h3>")
        elif bullet:
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append(f"<li>{inline(bullet[1])}</li>")
        elif stripped and stripped not in ("---", "***"):
            paragraph.append(stripped)
    if in_code:
        output.append("<pre><code>" + escape("\n".join(code)) + "</code></pre>")
    return "\n".join(output)


def fetch_releases():
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "DayEdge-site-release-sync",
               "X-GitHub-Api-Version": "2026-03-10"}
    if token := os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    releases, page = [], 1
    while True:
        request = Request(f"https://api.github.com/repos/{REPOSITORY}/releases?per_page=100&page={page}", headers=headers)
        with urlopen(request, timeout=30) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise ValueError("GitHub did not return a releases list")
        releases.extend(batch)
        if len(batch) < 100:
            return releases
        page += 1


def published_releases(raw):
    releases = []
    for release in raw:
        tag = release.get("tag_name", "")
        if release.get("draft") or release.get("prerelease") or not VERSION.fullmatch(tag) or not release.get("published_at"):
            continue
        published = datetime.fromisoformat(release["published_at"].replace("Z", "+00:00")).date()
        releases.append({"version": tag[1:], "published": published.isoformat(),
                         "url": f"https://github.com/{REPOSITORY}/releases/tag/{tag}",
                         "notes": (release.get("body") or "").strip()})
    releases.sort(key=lambda release: tuple(map(int, release["version"].split("."))), reverse=True)
    if not releases:
        raise ValueError("No published stable releases; existing site left unchanged")
    return releases


def history(releases):
    versions, entries = [], []
    for index, release in enumerate(releases):
        version = release["version"]
        anchor = "v" + version.replace(".", "-")
        versions.append(f'<a href="#{anchor}">{version}</a>')
        date = datetime.fromisoformat(release["published"])
        label = date.strftime("%b") + f" {date.day}, {date.year}"
        latest = '<span class="release-latest">Latest</span>' if index == 0 else ""
        notes = markdown(release["notes"]) or '<p>See the release on GitHub for details.</p>'
        entries.append(f'''<article class="release-entry" id="{anchor}" aria-labelledby="{anchor}-title">
  <header class="release-heading">
    <div class="release-version"><h2 id="{anchor}-title">{version}</h2>{latest}</div>
    <div class="release-meta"><time datetime="{release['published']}">{label}</time><a href="{release['url']}">View on GitHub <span aria-hidden="true">↗</span></a></div>
  </header>
  <div class="release-notes">{notes}</div>
</article>''')
    return "\n".join(versions), "\n".join(entries)


def outputs(raw, root=ROOT):
    releases = published_releases(raw)
    version = releases[0]["version"]
    homepage = (root / "dist/index.html").read_text()
    for key, value in (("tag", "v" + version), ("version", version)):
        homepage, count = re.subn(rf"(<!-- release:{key} -->).*?(<!-- /release:{key} -->)",
                                  lambda match: match[1] + value + match[2], homepage)
        if count != 1:
            raise ValueError(f"Expected one homepage release:{key} marker; existing site left unchanged")
    versions, entries = history(releases)
    template = (root / "templates/changelog.html").read_text()
    if template.count("{{versions}}") != 1 or template.count("{{releases}}") != 1:
        raise ValueError("Changelog template markers are missing or duplicated")
    return {
        root / "dist/index.html": homepage,
        root / "dist/changelog/index.html": template.replace("{{versions}}", versions).replace("{{releases}}", entries),
        root / "data/releases.json": json.dumps(releases, ensure_ascii=False, indent=2) + "\n",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-json", type=Path, help="Use a saved GitHub API response instead of the network")
    parser.add_argument("--check", action="store_true", help="Report stale files without writing")
    args = parser.parse_args()
    try:
        raw = json.loads(args.from_json.read_text()) if args.from_json else fetch_releases()
        generated = outputs(raw)
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as error:
        parser.exit(1, f"Release sync failed: {error}\n")
    changed = [path for path, content in generated.items() if not path.exists() or path.read_text() != content]
    if args.check and changed:
        parser.exit(1, "Release files are stale: " + ", ".join(str(path.relative_to(ROOT)) for path in changed) + "\n")
    for path in changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(generated[path])
        temporary.replace(path)
    print(f"Release files {'updated' if changed else 'already current'}: {len(changed)} changed.")


if __name__ == "__main__":
    main()
