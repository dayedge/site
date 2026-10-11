# DayEdge website

Static landing page with self-hosted assets. No dependencies or build step.

## Local preview

Requires Python 3:

```sh
python3 scripts/preview.py
```

Open http://127.0.0.1:8080. Set another port with `--port 8084`.

## Editing

Site files live in `dist/`: HTML, CSS, JavaScript, images, and fonts.
Keep the font licenses in `dist/assets/fonts/`.

Validate before publishing:

```sh
python3 scripts/check-release.py
```

Publish the contents of `dist/` to serve the site.

## Releases and changelog

Published stable [DayEdge GitHub releases](https://github.com/dayedge/dayedge/releases)
are the source for the homepage version and `/changelog/`. Edit the release notes
on GitHub; the site renders their headings, paragraphs, lists, bold text, links,
and fenced code blocks. Other Markdown is shown as plain text; GitHub always has
the full original notes. Drafts, prereleases, and bare tags are excluded.

Update locally (Python 3, no dependencies):

```sh
python3 scripts/sync-releases.py
python3 scripts/check-release.py
python3 -m unittest discover -s scripts -p 'test_*.py'
```

`GH_TOKEN` is optional for public releases and increases the API rate limit.
`--check` reports stale generated files without writing. For offline testing, use
`--from-json path/to/github-release-response.json` with a saved GitHub API response.
The cached, normalized notes live in `data/releases.json`; generated HTML remains
fully readable without JavaScript or browser-side GitHub requests. Fetch or
validation failures leave existing output untouched. Edit changelog layout in
`templates/changelog.html`, then rerun the sync.

The **Sync published releases** GitHub Action runs every six hours and supports
**Run workflow** for immediate updates. It maintains one PR from
`automation/release-updates`, respecting protected `main`. Enable **Settings →
Actions → General → Allow GitHub Actions to create and approve pull requests**
if the repository disallows Actions-created PRs. No personal access token is needed.
Merge the update PR, then publish `dist/` through the existing hosting process;
this workflow does not deploy the website. Review the Homebrew cask separately
before advertising a new version; syncing this site does not update the tap.
