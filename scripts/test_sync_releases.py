import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("sync_releases", Path(__file__).with_name("sync-releases.py"))
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def release(version="1.0.0", **changes):
    return {"tag_name": f"v{version}", "published_at": "2026-10-09T14:16:04Z", "draft": False,
            "prerelease": False, "body": "### Added\n\n- **Calendar:** a clearer day.", **changes}


class ReleaseSyncTests(unittest.TestCase):
    def test_drafts_are_excluded(self):
        result = sync.published_releases([release(), release("1.0.1", draft=True)])
        self.assertEqual([item["version"] for item in result], ["1.0.0"])

    def test_prereleases_are_excluded(self):
        result = sync.published_releases([release(), release("1.0.1", prerelease=True)])
        self.assertEqual(len(result), 1)

    def test_versions_are_sorted_numerically(self):
        result = sync.published_releases([release("1.0.2"), release("1.0.10")])
        self.assertEqual(result[0]["version"], "1.0.10")

    def test_unpublished_tags_are_excluded(self):
        result = sync.published_releases([release(), release("1.0.1", published_at=None)])
        self.assertEqual(len(result), 1)

    def test_empty_releases_fail_without_generating_output(self):
        with self.assertRaises(ValueError):
            sync.published_releases([])

    def test_raw_html_is_escaped(self):
        self.assertEqual(sync.markdown('<script>alert(1)</script>'), '<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>')

    def test_unsafe_link_is_not_emitted(self):
        self.assertEqual(sync.inline('[click](javascript:alert)'), 'click')

    def test_release_sections_and_bold_bullets_render(self):
        self.assertEqual(sync.markdown('### Added\n\n- **Calendar:** a clearer day.'),
                         '<h3>Added</h3>\n<ul>\n<li><strong>Calendar:</strong> a clearer day.</li>\n</ul>')

    def test_fenced_code_is_escaped(self):
        self.assertEqual(sync.markdown('```sh\n<command>\n```'), '<pre><code>&lt;command&gt;</code></pre>')

    def test_history_has_version_anchor_and_latest_label(self):
        versions, entries = sync.history(sync.published_releases([release()]))
        self.assertIn('href="#v1-0-0"', versions)
        self.assertIn('id="v1-0-0"', entries)
        self.assertIn('>Latest</span>', entries)
        self.assertIn('datetime="2026-10-09"', entries)

    def test_generation_updates_both_homepage_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'dist').mkdir()
            (root / 'templates').mkdir()
            (root / 'dist/index.html').write_text('<!-- release:tag -->v1.0.0<!-- /release:tag --> '
                                                '<!-- release:version -->1.0.0<!-- /release:version -->')
            (root / 'templates/changelog.html').write_text('{{versions}}{{releases}}')
            result = sync.outputs([release('1.0.1')], root)
            self.assertIn('>v1.0.1<', result[root / 'dist/index.html'])
            self.assertIn('>1.0.1<', result[root / 'dist/index.html'])
            self.assertIn('1.0.1', result[root / 'data/releases.json'])

    def test_missing_marker_fails_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'dist').mkdir()
            index = root / 'dist/index.html'
            index.write_text('original')
            with self.assertRaises(ValueError):
                sync.outputs([release()], root)
            self.assertEqual(index.read_text(), 'original')

    def test_generation_is_deterministic(self):
        raw = [release()]
        self.assertEqual(sync.outputs(raw), sync.outputs(raw))

    def test_api_pagination_fetches_later_releases(self):
        class Response:
            def __init__(self, payload):
                import io, json
                self.file = io.StringIO(json.dumps(payload))
            def __enter__(self): return self.file
            def __exit__(self, *_): self.file.close()
        with patch.object(sync, 'urlopen', side_effect=[Response([release()] * 100), Response([release('0.9.0')])]) as fetch:
            self.assertEqual(len(sync.fetch_releases()), 101)
            self.assertIn('page=2', fetch.call_args[0][0].full_url)


if __name__ == '__main__':
    unittest.main()
