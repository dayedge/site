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
