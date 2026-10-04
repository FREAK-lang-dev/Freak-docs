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


class ReviewedInputTests(unittest.TestCase):
    """Reviewed stdin, arguments and exit codes are part of an example's claim."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ['examples', 'content', 'tools']:
            (self.root / name).mkdir()
        (self.root / 'examples/game.fk').write_text('say ask("? ")\n')
        (self.root / 'v3-release.txt').write_text('v0.14.2\n')

    def expect(self, expectation):
        (self.root / 'examples/expectations.json').write_text(json.dumps({'game': expectation}))
        return evidence.expectations(self.root)

    def test_optional_fields_are_accepted_and_typed(self):
        self.expect({'stdout_any_of': ['? 7'], 'stdin': '7\n', 'args': ['42'], 'exit_code': 3})
        for bad in [{'stdout_any_of': ['x'], 'stdin': 7}, {'stdout_any_of': ['x'], 'args': 'one'},
                    {'stdout_any_of': ['x'], 'args': [1]}, {'stdout_any_of': ['x'], 'exit_code': '3'},
                    {'stdout_any_of': ['x'], 'exit_code': True}, {'stdout_any_of': ['x'], 'exit_code': 256},
                    {'stdout_any_of': ['x'], 'timeout': 5}, {'stdin': '7\n'}]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.expect(bad)

    def run_example(self, expectation, *, exit_code=0, stdout='? 7\n'):
        seen = {}
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'game.fk'
            source.write_text('say ask("? ")')
            def run(command, work, **kwargs):
                if command[1:2] == ['build']:
                    (work / 'game').touch()
                    return 0, 'BUILD SUCCESSFUL', ''
                seen['command'] = command
                seen['kwargs'] = kwargs
                return exit_code, stdout, ''
            with patch.object(verify, 'run', side_effect=run):
                result = verify.verify_one(Path('freak'), source, expectation.get('args', []), expectation)
        return result, seen

    def test_strict_borrow_build_is_run_and_recorded(self):
        result, _ = self.run_example({'stdout_any_of': ['? 7'], 'strict_borrow': True})
        self.assertTrue(result['passed'])
        self.assertIs(result['strict_borrow'], True)
        result, _ = self.run_example({'stdout_any_of': ['? 7']})
        self.assertNotIn('strict_borrow', result)
        with self.assertRaises(ValueError):
            self.expect({'stdout_any_of': ['x'], 'strict_borrow': 'yes'})

    def test_every_book_listing_claims_the_strict_build(self):
        reviewed = json.loads((Path(__file__).resolve().parents[1] / 'examples/expectations.json').read_text(encoding='utf-8'))
        book = {name: row for name, row in reviewed.items() if name.startswith('book_')}
        self.assertTrue(book)
        self.assertEqual([name for name, row in book.items() if row.get('strict_borrow') is not True], [])

    def test_reviewed_input_and_arguments_reach_the_program(self):
        result, seen = self.run_example({'stdout_any_of': ['? 7'], 'stdin': '7\n', 'args': ['42']})
        self.assertTrue(result['passed'])
        self.assertEqual(seen['kwargs']['stdin_text'], '7\n')
        self.assertEqual(seen['command'][1:], ['42'])
        self.assertEqual((result['stdin'], result['args']), ('7\n', ['42']))

    def test_programs_without_reviewed_input_keep_the_inherited_stdin(self):
        _, seen = self.run_example({'stdout_any_of': ['? 7']})
        self.assertNotIn('stdin_text', seen['kwargs'])

    def test_empty_reviewed_input_closes_the_pipe(self):
        process = subprocess.CompletedProcess([], 0, b'', b'')
        with patch.object(verify.subprocess, 'run', return_value=process) as invoke:
            verify.run(['program'], Path('.'), stdin_text='')
            self.assertEqual(invoke.call_args.kwargs['input'], b'')
            verify.run(['program'], Path('.'))
            self.assertIsNone(invoke.call_args.kwargs['input'])

    def test_exit_code_must_match_the_reviewed_one(self):
        self.assertTrue(self.run_example({'stdout_any_of': ['? 7'], 'exit_code': 3}, exit_code=3)[0]['passed'])
        for expectation, actual in [({'stdout_any_of': ['? 7'], 'exit_code': 3}, 0),
                                    ({'stdout_any_of': ['? 7']}, 3)]:
            with self.subTest(expectation=expectation, actual=actual):
                self.assertFalse(self.run_example(expectation, exit_code=actual)[0]['passed'])


class RejectedProgramTests(unittest.TestCase):
    """A rejected program passes only for the reviewed compiler diagnostic."""

    REJECTION = ('  Lexing (1ms)\ntype error: unknown binding \'altitude\' (line 2)\n --> bad.fk:2:1\n'
                 '2 |     say altitude\n  | ^\n  Type checking (9ms)\n'
                 '  1 type/borrow error(s) -- code generation skipped\n  BUILD FAILED\n')

    def reject(self, *, output=None, code=1, binary=False, contains=("unknown binding 'altitude'",), timeout=False):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'bad.fk'
            source.write_text('task main() {\n    say altitude\n}\n')
            def run(command, work, **kwargs):
                if timeout:
                    raise subprocess.TimeoutExpired(command, 180)
                if binary:
                    (work / 'bad').touch()
                self.command = command
                return code, self.REJECTION if output is None else output, ''
            with patch.object(verify, 'run', side_effect=run):
                return verify.verify_rejected(Path('freak'), source,
                                              {'contains': list(contains), 'flags': ['--strict-borrow']})

    def test_reviewed_diagnostic_passes_and_keeps_only_compiler_lines(self):
        result = self.reject()
        self.assertTrue(result['passed'])
        self.assertEqual(self.command[1:], ['build', 'bad.fk', '--strict-borrow'])
        self.assertTrue(result['message'].startswith("type error: unknown binding 'altitude'"))
        self.assertIn('2 |     say altitude', result['message'])
        for banner in ['Lexing', 'Type checking', 'BUILD FAILED', 'error(s)']:
            self.assertNotIn(banner, result['message'])

    def test_acceptance_crash_timeout_or_another_diagnostic_fail(self):
        for options in [{'output': 'BUILD SUCCESSFUL', 'code': 0}, {'binary': True},
                        {'output': 'Segmentation fault', 'code': 139},
                        {'output': 'error: something else\n  BUILD FAILED\n'},
                        {'contains': ('a different message',)}, {'timeout': True}]:
            with self.subTest(options=options):
                result = self.reject(**options)
                self.assertFalse(result['passed'])
                self.assertTrue(result['errors'])

    def test_expectations_cover_exactly_the_rejected_programs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(evidence.diagnostic_expectations(root), {})
            folder = root / 'diagnostics/v3'
            folder.mkdir(parents=True)
            (folder / 'bad.fk').write_text('say altitude\n')
            with self.assertRaisesRegex(ValueError, 'expectations.json'):
                evidence.diagnostic_expectations(root)
            listing = folder / 'expectations.json'
            for bad in [{}, {'bad': {}}, {'bad': {'contains': []}}, {'bad': {'contains': ['  ']}},
                        {'bad': {'contains': ['x'], 'flags': 'strict'}}, {'bad': {'contains': ['x'], 'other': 1}},
                        {'bad': {'contains': ['x']}, 'extra': {'contains': ['x']}}]:
                with self.subTest(bad=bad):
                    listing.write_text(json.dumps(bad))
                    with self.assertRaises(ValueError):
                        evidence.diagnostic_expectations(root)
            listing.write_text(json.dumps({'bad': {'contains': ['unknown binding']}}))
            self.assertEqual(set(evidence.diagnostic_expectations(root)), {'bad'})


class BookEvidenceTests(unittest.TestCase):
    """Rejected programs and V4 notes are published only with matching evidence."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ['examples', 'content', 'tools', 'diagnostics/v3', 'examples-v4']:
            (self.root / name).mkdir(parents=True)
        (self.root / 'examples/hello.fk').write_text('say "hello"\n')
        (self.root / 'examples/expectations.json').write_text(json.dumps({'hello': {'stdout_any_of': ['hello']}}))
        (self.root / 'diagnostics/v3/bad.fk').write_text('say altitude\n')
        (self.root / 'diagnostics/v3/expectations.json').write_text(
            json.dumps({'bad': {'contains': ["unknown binding 'altitude'"]}}))
        (self.root / 'examples-v4/hello.fk').write_text('task main() -> int { give back 0 }\n')
        (self.root / 'examples-v4/broken.fk').write_text('say "top level"\n')
        (self.root / 'examples-v4/expectations.json').write_text(json.dumps({
            'hello': {'stdout_any_of': [''], 'exit_code': 0},
            'broken': {'rejected_with': 'unexpected token at top level'}}))
        (self.root / 'tools/verify_v4.py').write_text('# verifier\n')
        (self.root / 'tools/evidence.py').write_text('# shared rules\n')
        (self.root / 'v4-snapshot.txt').write_text('a' * 40 + '\n')
        (self.root / 'v3-release.txt').write_text('v0.14.2\n')
        (self.root / 'content/index.md').write_text('{{example:hello}}\n{{diagnostic:bad}}\n{{v4:hello}}\n{{v4:broken}}\n')
        self.v3 = {
            'schema_version': 1, 'generation': 'v3', 'channel': 'release',
            'compiler': 'freak 0.14.2 (Maverick)', 'generated_utc': '2026-10-05T00:00:00Z',
            'input_sha256': evidence.input_hash(self.root),
            'provenance': {'compiler_commit': 'a' * 40, 'compiler_sha256': 'b' * 64,
                           'archive_sha256': 'c' * 64, 'release': 'v0.14.2'},
            'total': 1, 'compiled': 1, 'passed': 1,
            'examples': {'hello': {'file': 'hello.fk', 'source': 'say "hello"\n', 'compiled': True,
                                   'ran': True, 'exit_code': 0, 'stdout': 'hello', 'errors': []}},
            'diagnostics': {'bad': {'file': 'bad.fk', 'source': 'say altitude\n', 'flags': [],
                                    'rejected': True, 'passed': True, 'errors': [],
                                    'message': "type error: unknown binding 'altitude' (line 1)"}},
        }
        self.v4 = {
            'schema_version': 1, 'generation': 'v4', 'channel': 'development',
            'snapshot': {'repository': 'FREAK-lang-dev/Freak-lang', 'commit': 'a' * 40,
                         'commit_date': '2026-10-04T12:28:44+03:00'},
            'input_sha256': evidence.v4_input_hash(self.root), 'generated_utc': '2026-10-05T00:00:00Z',
            'total': 2, 'passed': 2,
            'examples': {
                'hello': {'file': 'hello.fk', 'source': 'task main() -> int { give back 0 }\n',
                          'built': True, 'passed': True, 'exit_code': 0, 'stdout': '', 'errors': []},
                'broken': {'file': 'broken.fk', 'source': 'say "top level"\n', 'built': False, 'passed': True,
                           'diagnostic': '2|0@0:15|unexpected token at top level|say', 'errors': []}},
        }

    def test_complete_evidence_for_all_three_lanes_is_accepted(self):
        evidence.validate(self.v3, self.root)
        evidence.validate_v4(self.v4, self.root)
        self.assertTrue(evidence.uses_v4(self.root))

    def test_shared_evidence_tooling_is_part_of_the_v4_input_hash(self):
        (self.root / 'tools/evidence.py').write_text('# changed\n')
        with self.assertRaisesRegex(ValueError, 'stale'):
            evidence.validate_v4(self.v4, self.root)

    def test_rejected_programs_are_part_of_the_v3_input_hash(self):
        (self.root / 'diagnostics/v3/bad.fk').write_text('say other\n')
        with self.assertRaisesRegex(ValueError, 'stale'):
            evidence.validate(self.v3, self.root)

    def test_v3_rejects_missing_wrong_or_unverified_diagnostics(self):
        changes = [lambda d: d.pop('diagnostics'),
                   lambda d: d['diagnostics']['bad'].update(message='type error: something else'),
                   lambda d: d['diagnostics']['bad'].update(rejected=False),
                   lambda d: d['diagnostics']['bad'].update(passed=False),
                   lambda d: d['diagnostics']['bad'].update(source='say other\n'),
                   lambda d: d['diagnostics']['bad'].update(flags=['--strict-borrow']),
                   lambda d: d['examples']['hello'].update(args=['42']),
                   lambda d: d['examples']['hello'].update(strict_borrow=True)]
        for change in changes:
            with self.subTest(change=change):
                data = copy.deepcopy(self.v3)
                change(data)
                with self.assertRaises(ValueError):
                    evidence.validate(data, self.root)

    def test_unknown_diagnostic_or_v4_reference_is_rejected(self):
        (self.root / 'content/index.md').write_text('{{diagnostic:missing}}\n')
        self.v3['input_sha256'] = evidence.input_hash(self.root)
        with self.assertRaisesRegex(ValueError, 'unknown diagnostic'):
            evidence.validate(self.v3, self.root)
        (self.root / 'content/index.md').write_text('{{v4:missing}}\n')
        with self.assertRaisesRegex(ValueError, 'unknown V4 example'):
            evidence.validate_v4(self.v4, self.root)

    def test_v4_evidence_is_tied_to_the_pinned_snapshot_and_its_inputs(self):
        for field, value in [('generation', 'v3'), ('channel', 'release'), ('schema_version', 2),
                             ('passed', 1), ('total', 1), ('generated_utc', '')]:
            with self.subTest(field=field):
                data = copy.deepcopy(self.v4)
                data[field] = value
                with self.assertRaises(ValueError):
                    evidence.validate_v4(data, self.root)
        other = copy.deepcopy(self.v4)
        other['snapshot']['commit'] = 'b' * 40
        with self.assertRaisesRegex(ValueError, 'v4-snapshot.txt'):
            evidence.validate_v4(other, self.root)
        (self.root / 'examples-v4/hello.fk').write_text('task main() -> int { give back 1 }\n')
        with self.assertRaisesRegex(ValueError, 'stale'):
            evidence.validate_v4(self.v4, self.root)

    def test_v4_rows_must_match_their_reviewed_expectation(self):
        changes = [lambda d: d['examples']['hello'].update(exit_code=7),
                   lambda d: d['examples']['hello'].update(stdout='surprise'),
                   lambda d: d['examples']['hello'].update(built=False),
                   lambda d: d['examples']['broken'].update(built=True),
                   lambda d: d['examples']['broken'].update(diagnostic='2|0@0:1|another problem|x'),
                   lambda d: d['examples']['broken'].update(passed=False),
                   lambda d: d['examples'].pop('broken')]
        for change in changes:
            with self.subTest(change=change):
                data = copy.deepcopy(self.v4)
                change(data)
                with self.assertRaises(ValueError):
                    evidence.validate_v4(data, self.root)

    def test_v3_evidence_never_certifies_v4(self):
        with self.assertRaises(ValueError):
            evidence.validate_v4(self.v3, self.root)
        with self.assertRaises(ValueError):
            evidence.validate(self.v4, self.root)

    def test_snapshot_pin_and_v4_expectations_are_strict(self):
        (self.root / 'v4-snapshot.txt').write_text('main\n')
        with self.assertRaises(ValueError):
            evidence.pinned_snapshot(self.root)
        listing = self.root / 'examples-v4/expectations.json'
        for bad in [{'hello': {}, 'broken': {'rejected_with': 'x'}},
                    {'hello': {'stdout_any_of': ['']}, 'broken': {'rejected_with': ' '}},
                    {'hello': {'stdout_any_of': [''], 'rejected_with': 'x'}, 'broken': {'rejected_with': 'x'}},
                    {'hello': {'stdout_any_of': [''], 'exit_code': 999}, 'broken': {'rejected_with': 'x'}},
                    {'hello': {'stdout_any_of': ['']}}]:
            with self.subTest(bad=bad):
                listing.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):
                    evidence.v4_expectations(self.root)

    def render(self, markdown, v4=None):
        return build_docs.render_blocks(markdown.split('\n'), self.v3, [], [], 'page', 'Page', v4)

    def test_cards_show_the_recorded_evidence(self):
        html_text = self.render('{{diagnostic:bad}}\n\n{{v4:hello}}\n\n{{v4:broken}}', self.v4)
        self.assertIn('does not compile', html_text)
        self.assertIn('unknown binding &#x27;altitude&#x27;', html_text)
        self.assertIn('V4 snapshot aaaaaaaaaa', html_text)
        self.assertIn('unexpected token at top level', html_text)
        self.assertIn('Missing V4 example', self.render('{{v4:hello}}'))
        self.assertIn('Missing diagnostic', self.render('{{diagnostic:nope}}'))

    def test_book_callouts_have_their_own_titles(self):
        html_text = self.render('> [!maverick] differs\n\n> [!planned] later\n\n> [!v4] absent')
        for title in ['In V4', 'Planned', 'Not in V3']:
            self.assertIn(f'<div class="callout-title">{title}</div>', html_text)
        self.assertIn('class="callout planned"', html_text)

    def test_v4_diagnostic_lines_exclude_build_noise(self):
        import verify_v4
        output = ('v4-build-stage=parse diagnostics=1\nV4 compilation failed:\n'
                  '2|0@0:16|unexpected token at top level|say\nv4-errors=1\n'
                  'v4-native-contract-error=native type not yet supported: unknown\nTraceback (most recent call last):\n')
        self.assertEqual(verify_v4.diagnostic_lines(output),
                         '2|0@0:16|unexpected token at top level|say\n'
                         'v4-native-contract-error=native type not yet supported: unknown')

    def test_v4_listings_colour_keywords_by_exact_case(self):
        # V3 reserves `Max` along with `max`; V4 treats `Max` as an ordinary name.
        self.assertIn('<span class="c-kw">Max</span>', build_docs.highlight_fk('pilot Max = 4'))
        v4_text = build_docs.highlight_fk('pilot Max: uint = 4u', v4=True)
        self.assertNotIn('>Max</span>', v4_text)
        self.assertIn('<span class="c-kw">pilot</span>', v4_text)
        self.assertIn('<span class="c-type">uint</span>', v4_text)

    def test_page_contents_render_inline_code(self):
        toc = build_docs.toc_html([
            {'level': 2, 'text': '`if`', 'anchor': 'if'},
            {'level': 2, 'text': 'Summary', 'anchor': 'summary'},
        ])
        self.assertIn('<a href="#if"><code>if</code></a>', toc)
        self.assertNotIn('`', toc)
