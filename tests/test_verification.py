import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import evidence
import verify
import build_docs
import check_publication
import refresh


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ['examples', 'content', 'tools']:
            (self.root / name).mkdir()
        (self.root / 'examples/hello.fk').write_text('say "hello"\n')
        (self.root / 'examples/expectations.json').write_text(json.dumps({'hello': {'stdout_any_of': ['hello']}}))
        (self.root / 'content/index.md').write_text('{{example:hello}}')
        (self.root / 'v3-release.txt').write_text('v0.14.2\n')
        self.data = {
            'schema_version': 1, 'generation': 'v3', 'channel': 'release',
            'compiler': 'freak 0.14.2 (Maverick)', 'generated_utc': '2026-09-19T00:00:00Z',
            'input_sha256': evidence.input_hash(self.root),
            'provenance': {'compiler_commit': 'a' * 40, 'compiler_sha256': 'b' * 64,
                           'archive_sha256': 'c' * 64, 'release': 'v0.14.2'},
            'total': 1, 'compiled': 1, 'passed': 1,
            'examples': {'hello': {'file': 'hello.fk', 'source': 'say "hello"\n',
                                   'compiled': True, 'ran': True, 'exit_code': 0,
                                   'stdout': 'hello', 'errors': []}},
        }

    def test_complete_matching_evidence_is_accepted(self):
        evidence.validate(self.data, self.root)

    def test_navigation_covers_content_exactly_once(self):
        nav = [('Start', [('index', 'Overview')])]
        build_docs.validate_navigation(self.root / 'content', nav)
        for invalid in [[], [('Start', [('missing', 'Missing')])], nav + nav]:
            with self.subTest(nav=invalid), self.assertRaises(ValueError):
                build_docs.validate_navigation(self.root / 'content', invalid)
        (self.root / 'content/new.md').write_text('New page')
        with self.assertRaisesRegex(ValueError, 'unlisted pages'):
            build_docs.validate_navigation(self.root / 'content', nav)

    def test_refresh_defaults_to_pin_and_keeps_manual_override(self):
        for argv, expected in [([], 'v0.14.2'), (['--release', ''], 'v0.14.2'),
                               (['--release', 'v0.14.3'], 'v0.14.3')]:
            with self.subTest(argv=argv), patch.object(refresh, 'ROOT', self.root), \
                 patch.object(sys, 'argv', ['refresh.py', *argv]), \
                 patch.object(refresh, 'fetch', side_effect=RuntimeError('stop before download')) as fetch:
                with self.assertRaisesRegex(RuntimeError, 'stop before download'):
                    refresh.main()
                self.assertEqual(fetch.call_args.args[0], expected)
        (self.root / 'v3-release.txt').write_text('latest')
        with self.assertRaises(ValueError):
            evidence.pinned_release(self.root)

    def publication_repo(self):
        (self.root / 'site').mkdir()
        (self.root / 'site/index.html').write_text('rendered page')
        (self.root / 'tools/build_docs.py').write_text(
            "from pathlib import Path\nPath('site/index.html').write_text('rendered page')\n")
        self.data['input_sha256'] = evidence.input_hash(self.root)
        (self.root / 'examples/verified.json').write_text(json.dumps(self.data))
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        subprocess.run(['git', 'add', '.'], cwd=self.root, check=True)
        subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                        'commit', '-qm', 'fixture'], cwd=self.root, check=True)

    def test_publication_rejects_stale_committed_html_and_new_generated_files(self):
        self.publication_repo()
        check_publication.check(self.root)
        (self.root / 'site/index.html').write_text('stale committed page')
        subprocess.run(['git', 'add', '.'], cwd=self.root, check=True)
        subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                        'commit', '-qm', 'stale'], cwd=self.root, check=True)
        with self.assertRaisesRegex(ValueError, 'committed site is stale'):
            check_publication.check(self.root)
        # New generated pages must be detected even when git diff is empty.
        subprocess.run(['git', 'add', '.'], cwd=self.root, check=True)
        subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                        'commit', '-qm', 'refresh'], cwd=self.root, check=True)
        (self.root / 'site/new.html').write_text('new generated page')
        with self.assertRaisesRegex(ValueError, 'new.html'):
            check_publication.check(self.root)

    def test_publication_rejects_stale_evidence_before_rendering(self):
        self.publication_repo()
        (self.root / 'content/index.md').write_text('changed input')
        with self.assertRaisesRegex(ValueError, 'stale'):
            check_publication.check(self.root)
        self.assertEqual((self.root / 'site/index.html').read_text(), 'rendered page')

    def test_publication_rejects_evidence_from_another_release(self):
        self.publication_repo()
        self.data['provenance']['release'] = 'v0.14.3'
        (self.root / 'examples/verified.json').write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, 'does not match v3-release.txt'):
            check_publication.check(self.root)

    def test_rejects_partial_failed_or_wrong_generation_evidence(self):
        for field, value in [('examples', {}), ('passed', 0), ('generation', 'v4'),
                             ('channel', 'development'), ('schema_version', 0)]:
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data[field] = value
                with self.assertRaises(ValueError):
                    evidence.validate(data, self.root)

    def test_rejects_runtime_failures_and_changed_output_or_source(self):
        for field, value in [('ran', False), ('exit_code', 9), ('stdout', 'wrong'),
                             ('source', 'different source'), ('errors', ['timeout'])]:
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data['examples']['hello'][field] = value
                with self.assertRaises(ValueError):
                    evidence.validate(data, self.root)

    def test_missing_render_metadata_does_not_touch_published_files(self):
        output = self.root / 'site'
        output.mkdir()
        sentinel = output / 'index.html'
        sentinel.write_text('last verified site')
        report = self.root / 'examples/verified.json'
        for field in ['compiler', 'generated_utc']:
            for value in [None, '', '   ', 123]:
                with self.subTest(field=field, value=value):
                    data = copy.deepcopy(self.data)
                    if value is None:
                        data.pop(field)
                    else:
                        data[field] = value
                    report.write_text(json.dumps(data))
                    with patch.object(build_docs, 'ROOT', self.root), patch.object(build_docs, 'VERIFIED', report), \
                         patch.object(build_docs, 'NAV', [('Start', [('index', 'Overview')])]), \
                         patch.object(build_docs, 'SITE', output), patch.object(build_docs, 'CONTENT', self.root / 'content'), \
                         patch.object(build_docs, 'ASSETS', output / 'assets'), patch.object(sys, 'argv', ['build_docs.py']):
                        self.assertEqual(build_docs.main(), 1)
                    self.assertEqual(sentinel.read_text(), 'last verified site')
                    self.assertFalse((output / 'assets').exists())

    def test_changed_inputs_invalidate_old_evidence(self):
        (self.root / 'content/index.md').write_text('Changed documented behavior')
        with self.assertRaisesRegex(ValueError, 'stale'):
            evidence.validate(self.data, self.root)

    def test_unverified_example_reference_is_rejected(self):
        (self.root / 'content/index.md').write_text('{{example:missing}}')
        self.data['input_sha256'] = evidence.input_hash(self.root)
        with self.assertRaisesRegex(ValueError, 'unknown example'):
            evidence.validate(self.data, self.root)

    def test_new_program_requires_reviewed_expectation(self):
        (self.root / 'examples/new.fk').write_text('say "new"')
        with self.assertRaisesRegex(ValueError, 'expectations'):
            evidence.expectations(self.root)

    def test_invalid_evidence_does_not_touch_published_files(self):
        report = self.root / 'examples/verified.json'
        report.write_text('{}')
        output = self.root / 'site'
        output.mkdir()
        sentinel = output / 'index.html'
        sentinel.write_text('last verified site')
        with patch.object(build_docs, 'ROOT', self.root), patch.object(build_docs, 'VERIFIED', report), \
             patch.object(build_docs, 'SITE', output), patch.object(build_docs, 'CONTENT', self.root / 'content'), \
             patch.object(build_docs, 'ASSETS', output / 'assets'), patch.object(sys, 'argv', ['build_docs.py']):
            self.assertEqual(build_docs.main(), 1)
        self.assertEqual(sentinel.read_text(), 'last verified site')
        self.assertFalse((output / 'assets').exists())


class RuntimeTests(unittest.TestCase):
    def test_capture_ignores_terminal_colour_preferences(self):
        process = subprocess.CompletedProcess([], 0, b'hello\n', b'')
        with patch.dict(verify.os.environ, {'NO_COLOR': '1', 'FORCE_COLOR': '1'}), \
             patch.object(verify.subprocess, 'run', return_value=process) as invoke:
            verify.run(['program'], Path('.'), keep_ansi=True)
        self.assertNotIn('NO_COLOR', invoke.call_args.kwargs['env'])
        self.assertNotIn('FORCE_COLOR', invoke.call_args.kwargs['env'])

    def verify(self, *, exit_code=0, stdout='hello\n', binary=True, timeout=False):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'hello.fk'
            source.write_text('say "hello"')
            def run(command, work, **kwargs):
                if command[1:2] == ['build']:
                    if binary:
                        (work / 'hello.exe').touch()
                    return 0, 'BUILD SUCCESSFUL', ''
                if timeout:
                    raise subprocess.TimeoutExpired(command, 60)
                return exit_code, stdout, ''
            with patch.object(verify, 'run', side_effect=run):
                return verify.verify_one(Path('freak'), source, [], {'stdout_any_of': ['hello']})

    def test_successful_compile_and_matching_run_pass(self):
        self.assertTrue(self.verify()['passed'])

    def test_only_one_customary_final_newline_is_ignored(self):
        self.assertTrue(self.verify(stdout='hello')['passed'])
        for stdout in ['hello\n\n', 'hello\n\n\n', 'hello\r']:
            with self.subTest(stdout=stdout):
                result = self.verify(stdout=stdout)
                self.assertFalse(result['passed'])
                self.assertEqual(result['stdout'], stdout.removesuffix('\n'))

    def test_crashes_wrong_output_missing_binary_and_timeouts_fail(self):
        for options in [{'exit_code': 7}, {'stdout': 'wrong'}, {'binary': False}, {'timeout': True}]:
            with self.subTest(options=options):
                result = self.verify(**options)
                self.assertTrue(result['compiled'])
                self.assertFalse(result['passed'])
                self.assertTrue(result['errors'])


if __name__ == '__main__':
    unittest.main()
