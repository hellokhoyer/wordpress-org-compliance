"""Offline behavioral regressions; no WordPress, network or real messages."""
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile
from datetime import datetime, timedelta, timezone
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import check_dependencies as currency
import verify_readiness as readiness
import audit_inventory as inventory

READY = 'READY FOR SUBMISSION DECISION'
INCOMPLETE = 'INCOMPLETE AUDIT; READINESS UNVERIFIED'


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        seed = int(hashlib.sha256(self.id().encode()).hexdigest()[:8], 16)
        self.slug = 'fixture-' + format(seed, 'x')
        self.component_id = 'dependency-' + format(seed, 'x')
        self.component = 'fixture-library-' + format(seed, 'x')
        major, minor, patch = seed % 7 + 1, seed % 11 + 1, seed % 13 + 1
        self.version = f'{major}.{minor}.{patch}'
        self.newer_version = f'{major}.{minor}.{patch + 1}'
        self.older_version = f'{major}.{minor}.{patch - 1}'
        self.marker = 'Fixture library v' + self.version
        self.freshness_hours = seed % 5 + 1
        self.main_member = f'{self.slug}/bootstrap.php'
        self.member = f'{self.slug}/resources/library-{seed}.js'
        self.package = self.root / 'plugin.zip'
        with zipfile.ZipFile(self.package, 'w') as archive:
            archive.writestr(self.main_member, '<?php\n/*\nPlugin Name: Generated fixture\n*/\n')
            archive.writestr(self.member, '/*! ' + self.marker + ' */')
        self.manifest = {
            'package_sha256': currency.digest(self.package),
            'inventory_complete': True,
            'dependencies': [{'id': self.component_id, 'ecosystem': 'npm', 'package': self.component,
                              'version': self.version, 'version_marker': self.marker,
                              'paths': [self.member]}],
        }

    def fetch(self, version=None, **fields):
        metadata = {'name': self.component, 'version': version or self.version, **fields}
        return lambda url: json.dumps(metadata).encode()

    def report(self, fetch=None):
        return currency.check(self.manifest, self.package, self.root / 'currency.json', fetch=fetch or self.fetch())

    def evidence(self, name, text='Executed fixture evidence'):
        path = self.root / name
        path.write_text(text)
        return {'path': name, 'sha256': currency.digest(path)}

    def ledger(self, dependencies=False):
        ledger = readiness.initialize(self.package, 'full', 'new')
        ledger['context'] = {key: False for key in readiness.CONTEXT_FIELDS}
        # Synthetic fixture evidence is sufficient only for testing the validator,
        # never a real plugin audit. The helper does not judge source analysis.
        for key, item in ledger['checks'].items():
            item.update(status='PASS', reason='Synthetic proof for validator regression',
                        package_sha256=ledger['package_sha256'], evidence=[self.evidence(key + '.txt')])
        for key in readiness.DEPENDENCY_CHECKS | {'reviewer_categories', 'upgrade_compatibility', 'admin_behavior', 'ui_and_exports'}:
            ledger['checks'][key]['status'] = 'N_A'
        if dependencies:
            ledger['currency_freshness'] = {'max_age_hours': self.freshness_hours, 'reason': 'Synthetic audit window for this generated fixture'}
            ledger['context']['has_third_party_dependencies'] = True
            ledger['dependency_ids'] = [self.component_id]
            for key in readiness.DEPENDENCY_CHECKS:
                ledger['checks'][key]['status'] = 'PASS'
            self.report()
            self.bind_report(ledger)
        return ledger

    def bind_report(self, ledger):
        item = ledger['checks']['dependency_currency']
        item['report'] = 'currency.json'
        item['evidence'] = [{'path': 'currency.json', 'sha256': currency.digest(self.root / 'currency.json')}]

    def edit_report(self, ledger, change):
        path = self.root / 'currency.json'
        report = json.loads(path.read_text())
        change(report)
        path.write_text(json.dumps(report))
        self.bind_report(ledger)

    def verdict(self, ledger):
        return readiness.validate(ledger, self.package, self.root)

    def cli(self, script, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)],
                              text=True, capture_output=True, timeout=10)

    def test_current_version_has_raw_metadata_and_exact_member_hash(self):
        report = self.report()
        self.assertEqual(report['status'], 'PASS')
        row = report['records'][0]
        self.assertEqual(row['status'], 'CURRENT')
        raw = readiness.proof(row['upstream_evidence'], self.root)
        self.assertEqual(json.loads(raw.read_text())['version'], self.version)
        with zipfile.ZipFile(self.package) as archive:
            self.assertEqual(row['files'][0]['sha256'], hashlib.sha256(archive.read(self.member)).hexdigest())

    def test_authentic_older_version_is_outdated(self):
        report = self.report(self.fetch(self.newer_version))
        self.assertEqual(report['status'], 'FAIL')
        self.assertEqual(report['records'][0]['status'], 'OUTDATED')

    def test_registry_tag_behind_bundle_requires_investigation(self):
        report = self.report(self.fetch(self.older_version))
        self.assertEqual(report['status'], 'UNVERIFIED')
        self.assertIn('ahead', report['records'][0]['error'])

    def test_failed_lookup_is_unverified(self):
        def offline(url):
            raise OSError('offline')
        report = self.report(offline)
        self.assertEqual(report['status'], 'UNVERIFIED')
        self.assertIn('offline', report['records'][0]['error'])

    def test_invalid_upstream_metadata_never_passes(self):
        name, version, newer = map(json.dumps, (self.component, self.version, self.newer_version))
        samples = [b'[]', b'null', b'not json',
                   f'{{"name":{name},"version":{version},"version":{newer}}}'.encode(),
                   f'{{"name":{name},"version":NaN}}'.encode(),
                   json.dumps({'name': 'different-fixture', 'version': self.version}).encode(),
                   json.dumps({'name': self.component, 'version': self.newer_version + '-beta.1'}).encode(),
                   json.dumps({'name': self.component, 'version': self.version, 'deprecated': 'unmaintained'}).encode()]
        for raw in samples:
            with self.subTest(raw=raw):
                self.assertEqual(self.report(lambda url: raw)['status'], 'UNVERIFIED')

    def test_incomplete_inventory_does_not_pass(self):
        self.manifest['inventory_complete'] = False
        self.assertEqual(self.report()['status'], 'UNVERIFIED')

    def test_empty_inventory_needs_explicit_completeness(self):
        self.manifest['dependencies'] = []
        self.assertEqual(self.report()['status'], 'PASS')
        del self.manifest['inventory_complete']
        self.assertEqual(self.report()['status'], 'UNVERIFIED')

    def test_unsupported_ecosystem_is_retained_as_unverified(self):
        self.manifest['dependencies'][0]['ecosystem'] = 'composer'
        report = self.report()
        self.assertEqual(len(report['records']), 1)
        self.assertEqual(report['status'], 'UNVERIFIED')

    def test_version_claim_must_match_bytes(self):
        self.manifest['dependencies'][0].update(version=self.newer_version, version_marker='Fixture library v' + self.newer_version)
        self.assertEqual(self.report()['status'], 'UNVERIFIED')

    def test_duplicate_dependency_id_is_rejected(self):
        self.manifest['dependencies'] *= 2
        with self.assertRaises(ValueError):
            self.report()

    def test_unsafe_or_missing_or_duplicate_member_paths_are_unverified(self):
        for paths in [['../secret'], ['/secret'], ['sample\\secret'], ['missing.js'], [self.member] * 2, [None]]:
            with self.subTest(paths=paths):
                self.manifest['dependencies'][0]['paths'] = paths
                self.assertEqual(self.report()['status'], 'UNVERIFIED')

    def test_symlink_member_is_unverified(self):
        with zipfile.ZipFile(self.package, 'w') as archive:
            info = zipfile.ZipInfo(self.member)
            info.create_system = 3
            info.external_attr = 0o120777 << 16
            archive.writestr(info, self.marker)
        self.manifest['package_sha256'] = currency.digest(self.package)
        self.assertEqual(self.report()['status'], 'UNVERIFIED')

    def test_different_package_cannot_reuse_manifest(self):
        self.manifest['package_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            self.report()

    def test_duplicate_zip_members_are_rejected(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(self.package, 'a') as archive:
                archive.writestr(self.member, 'another')
        self.manifest['package_sha256'] = currency.digest(self.package)
        with self.assertRaises(ValueError):
            self.report()

    def test_fully_evidenced_first_submission_can_close(self):
        result = self.verdict(self.ledger())
        self.assertEqual(result['decision'], READY, result)

    def test_currency_with_matching_evidence_can_close(self):
        result = self.verdict(self.ledger(True))
        self.assertEqual(result['decision'], READY, result)

    def test_currency_policy_must_be_explicit_and_justified(self):
        for policy in [None, {}, {'max_age_hours': self.freshness_hours, 'reason': ''}]:
            with self.subTest(policy=policy):
                ledger = self.ledger(True)
                ledger['currency_freshness'] = policy
                self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_invalid_currency_age_cannot_pass_or_crash(self):
        for age in [None, False, 0, -1, '2', float('inf'), float('nan'), 10 ** 1000]:
            with self.subTest(age=age):
                ledger = self.ledger(True)
                ledger['currency_freshness']['max_age_hours'] = age
                self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_each_audit_uses_its_own_freshness_window(self):
        ledger = self.ledger(True)
        elapsed_hours = self.freshness_hours * 2
        ledger['started_at'] = (datetime.now(timezone.utc) - timedelta(hours=elapsed_hours * 2)).isoformat()
        self.edit_report(ledger, lambda r: r.update(checked_at=(datetime.now(timezone.utc) - timedelta(hours=elapsed_hours)).isoformat()))
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)
        ledger['currency_freshness']['max_age_hours'] = elapsed_hours * 2
        self.assertEqual(self.verdict(ledger)['decision'], READY)

    def test_old_ledger_schema_cannot_silently_reuse_defaults(self):
        ledger = self.ledger(True)
        ledger['schema_version'] = readiness.LEDGER_SCHEMA - 1
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_entry_point_is_discovered_from_header_not_slug(self):
        result = inventory.package_inventory(self.package, self.slug)
        self.assertEqual(result['main_file_candidates'], [self.main_member])
        self.assertTrue(result['main_file_present'])

    def test_missing_header_is_reported_as_missing_entry_point(self):
        with zipfile.ZipFile(self.package, 'w') as archive:
            archive.writestr(f'{self.slug}/{self.slug}.php', '<?php // no plugin header')
        result = inventory.package_inventory(self.package, self.slug)
        self.assertEqual(result['main_file_candidates'], [])
        self.assertFalse(result['main_file_present'])

    def test_arbitrary_scoped_package_and_asset_path(self):
        component = '@fixture-scope/' + self.component
        self.manifest['dependencies'][0]['package'] = component
        result = self.report(self.fetch(name=component))
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['records'][0]['package'], component)

    def test_existing_release_with_consumers_uses_supported_states(self):
        ledger = self.ledger()
        ledger['mode'] = 'update'
        for name in readiness.CONTEXT_FIELDS:
            ledger['context'][name] = True
        ledger['context']['has_third_party_dependencies'] = False
        for key in ['reviewer_categories', 'upgrade_compatibility', 'admin_behavior', 'ui_and_exports']:
            ledger['checks'][key]['status'] = 'PASS'
        self.assertEqual(self.verdict(ledger)['decision'], READY)

    def test_missing_technical_check_cannot_hide_behind_test_count(self):
        ledger = self.ledger()
        ledger['checks']['behavioral_tests']['reason'] = 'Many unrelated behavioral checks passed'
        del ledger['checks']['dependency_inventory']
        ledger['checks']['owner_actions']['status'] = 'UNVERIFIED'
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_unverified_technical_check_prevents_code_ready(self):
        ledger = self.ledger()
        ledger['checks']['php_compatibility']['status'] = 'UNVERIFIED'
        ledger['checks']['owner_actions']['status'] = 'UNVERIFIED'
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_owner_only_pending_is_distinct(self):
        ledger = self.ledger()
        for status in ['UNVERIFIED', 'FAIL']:
            with self.subTest(status=status):
                ledger['checks']['owner_actions']['status'] = status
                self.assertEqual(self.verdict(ledger)['decision'], 'CODE READY; RELEASE GATES PENDING')

    def test_confirmed_technical_failure_is_not_ready(self):
        ledger = self.ledger()
        ledger['checks']['request_authorization']['status'] = 'FAIL'
        self.assertEqual(self.verdict(ledger)['decision'], 'NOT READY')

    def test_missing_evidence_does_not_close_check(self):
        ledger = self.ledger()
        ledger['checks']['activation_lifecycle']['evidence'] = []
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_changed_evidence_does_not_close_check(self):
        ledger = self.ledger()
        (self.root / 'package_scans.txt').write_text('different result')
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_symlink_or_traversal_evidence_is_rejected(self):
        ledger = self.ledger()
        real = self.root / 'input_validation.txt'
        (self.root / 'linked.txt').symlink_to(real)
        for path in ['../input_validation.txt', str(real), 'linked.txt']:
            with self.subTest(path=path):
                ledger['checks']['input_validation']['evidence'][0]['path'] = path
                self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_empty_evidence_or_reason_is_rejected(self):
        ledger = self.ledger()
        (self.root / 'cleanup.txt').write_text('')
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)
        ledger = self.ledger()
        ledger['checks']['cleanup']['reason'] = ' '
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_wrong_package_invalidates_overall_decision(self):
        ledger = self.ledger()
        with zipfile.ZipFile(self.package, 'a') as archive:
            archive.writestr(f'{self.slug}/new.php', '<?php')
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_wrong_per_check_package_hash_is_rejected(self):
        ledger = self.ledger()
        ledger['checks']['package_activation']['package_sha256'] = '0' * 64
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_security_cannot_be_waived_as_not_applicable(self):
        ledger = self.ledger()
        ledger['checks']['request_authorization']['status'] = 'N_A'
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_upgrade_not_applicable_needs_both_no_history_and_no_consumers(self):
        for context in ['has_prior_public_release', 'has_independently_updated_consumers']:
            with self.subTest(context=context):
                ledger = self.ledger()
                ledger['context'][context] = True
                self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_applicability_must_be_explicit_boolean(self):
        for value in [None, 0, 'false', [], {}]:
            with self.subTest(value=value):
                ledger = self.ledger()
                ledger['context']['has_reviewer_message'] = value
                self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_limited_or_package_only_never_claims_full_readiness(self):
        ledger = self.ledger()
        ledger['scope'] = 'limited'
        self.assertEqual(self.verdict(ledger)['decision'], 'LIMITED REVIEW; NO FULL READINESS DECISION')
        ledger['scope'], ledger['mode'] = 'full', 'package-only'
        self.assertEqual(self.verdict(ledger)['decision'], 'LIMITED REVIEW; NO FULL READINESS DECISION')

    def test_outdated_dependency_blocks_green_source_and_behavioral_checks(self):
        ledger = self.ledger(True)
        self.report(self.fetch(self.newer_version))
        self.bind_report(ledger)
        self.assertNotEqual(self.verdict(ledger)['decision'], READY)
        ledger['checks']['dependency_currency']['status'] = 'FAIL'
        self.assertEqual(self.verdict(ledger)['decision'], 'NOT READY')

    def test_currency_report_cannot_omit_an_inventory_row(self):
        ledger = self.ledger(True)
        ledger['dependency_ids'].append('font')
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_currency_evidence_must_be_fresh_and_within_this_audit(self):
        outside_window = timedelta(hours=self.freshness_hours + 1)
        for age in [outside_window, timedelta(minutes=5), -timedelta(minutes=10)]:
            with self.subTest(age=age):
                ledger = self.ledger(True)
                if age == outside_window:
                    ledger['started_at'] = (datetime.now(timezone.utc) - outside_window * 2).isoformat()
                self.edit_report(ledger, lambda report: report.update(checked_at=(datetime.now(timezone.utc) - age).isoformat()))
                self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_changed_upstream_evidence_is_rejected(self):
        ledger = self.ledger(True)
        report = json.loads((self.root / 'currency.json').read_text())
        (self.root / report['records'][0]['upstream_evidence']['path']).write_text('different version')
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_contradictory_npm_latest_claim_is_rejected(self):
        ledger = self.ledger(True)
        self.edit_report(ledger, lambda r: r['records'][0].update(version=self.newer_version, latest_stable=self.newer_version))
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_wrong_dependency_member_hash_is_rejected(self):
        ledger = self.ledger(True)
        self.edit_report(ledger, lambda r: r['records'][0]['files'][0].update(sha256='0' * 64))
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_currency_pass_needs_hashed_report_reference(self):
        ledger = self.ledger(True)
        ledger['checks']['dependency_currency']['report'] = 'missing.json'
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_supported_exception_needs_support_risk_and_owner_proof(self):
        ledger = self.ledger(True)
        self.report(self.fetch(self.newer_version))
        self.edit_report(ledger, lambda r: r['records'][0].update(status='SUPPORTED_EXCEPTION', reason='Maintained supported branch'))
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)
        def close(report):
            for key in ['upstream_support_evidence', 'risk_assessment_evidence', 'owner_authorization_evidence']:
                report['records'][0][key] = self.evidence(key + '.txt')
        self.edit_report(ledger, close)
        result = self.verdict(ledger)
        self.assertEqual(result['decision'], READY, result)
        self.assertEqual(result['supported_dependency_exceptions'], [self.component_id])
        ledger['checks']['dependency_advisories']['status'] = 'FAIL'
        self.assertEqual(self.verdict(ledger)['decision'], 'NOT READY')
        ledger['checks']['dependency_advisories']['status'] = 'PASS'
        self.edit_report(ledger, lambda r: r['records'][0].pop('version'))
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_malformed_currency_report_fails_cleanly(self):
        for malformed in [[], None, {'records': []}]:
            with self.subTest(report=malformed):
                ledger = self.ledger(True)
                (self.root / 'currency.json').write_text(json.dumps(malformed))
                self.bind_report(ledger)
                self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_malformed_currency_rows_cannot_pass(self):
        for field, value in [('files', {}), ('source_url', None), ('version', 4), ('id', [])]:
            with self.subTest(field=field, value=value):
                ledger = self.ledger(True)
                self.edit_report(ledger, lambda r: r['records'][0].update({field: value}))
                self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_unknown_check_cannot_replace_a_required_check(self):
        ledger = self.ledger()
        ledger['checks']['everything_else'] = ledger['checks'].pop('privacy_and_external_services')
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_dependency_context_cannot_contradict_inventory(self):
        ledger = self.ledger()
        ledger['context']['has_third_party_dependencies'] = True
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)
        ledger = self.ledger(True)
        ledger['context']['has_third_party_dependencies'] = False
        self.assertEqual(self.verdict(ledger)['decision'], INCOMPLETE)

    def test_non_npm_manual_evidence_can_close_without_parsing_as_npm(self):
        ledger = self.ledger(True)
        manual = self.evidence('official-font-release.html', f'<h1>Official stable release {self.version}</h1>')
        self.edit_report(ledger, lambda r: r['records'][0].update(ecosystem='font', upstream_evidence=manual))
        self.assertEqual(self.verdict(ledger)['decision'], READY)

    def test_unverified_initializer_cannot_pass_and_does_not_overwrite(self):
        path = self.root / 'audit.json'
        result = self.cli('verify_readiness.py', 'init', '--mode=new', '--package', self.package, '--output', path)
        self.assertEqual(result.returncode, 0, result.stderr)
        checked = self.cli('verify_readiness.py', 'check', path, '--package', self.package)
        self.assertEqual(checked.returncode, 1, checked.stderr)
        self.assertEqual(json.loads(checked.stdout)['decision'], INCOMPLETE)
        original = path.read_bytes()
        self.assertEqual(self.cli('verify_readiness.py', 'init', '--mode=new', '--package', self.package, '--output', path).returncode, 2)
        self.assertEqual(path.read_bytes(), original)

    def test_cli_ready_and_limited_exit_status(self):
        ledger = self.ledger()
        path = self.root / 'audit.json'
        path.write_text(json.dumps(ledger))
        self.assertEqual(self.cli('verify_readiness.py', 'check', path, '--package', self.package).returncode, 0)
        ledger['scope'] = 'limited'
        path.write_text(json.dumps(ledger))
        self.assertEqual(self.cli('verify_readiness.py', 'check', path, '--package', self.package).returncode, 1)

    def test_malformed_manifest_cli_has_no_traceback(self):
        path = self.root / 'dependencies.json'
        for raw in ['[]', 'null', '{"dependencies":NaN}', '{"a":1,"a":2}']:
            with self.subTest(raw=raw):
                path.write_text(raw)
                result = self.cli('check_dependencies.py', '--manifest', path, '--package', self.package, '--output', self.root / 'report.json')
                self.assertEqual(result.returncode, 2)
                self.assertNotIn('Traceback', result.stderr)
                self.assertEqual(json.loads(result.stdout)['status'], 'UNVERIFIED')

    def test_cli_cannot_overwrite_input(self):
        ledger = self.ledger()
        path = self.root / 'audit.json'
        path.write_text(json.dumps(ledger))
        original = path.read_bytes()
        result = self.cli('verify_readiness.py', 'check', path, '--package', self.package, '--output', path)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(path.read_bytes(), original)

    def test_non_git_package_never_appears_verified_clean(self):
        result = self.cli('audit_inventory.py', self.root, '--slug', self.slug)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('**Dirty paths:** unknown', result.stdout)
        self.assertIsNone(inventory.run_git(self.root, 'status', '--porcelain'))

    def test_no_git_flag_prevents_git_probes(self):
        output = io.StringIO()
        with patch.object(sys, 'argv', ['audit_inventory.py', str(self.root), '--slug', self.slug, '--no-git']), patch.object(inventory, 'run_git', side_effect=AssertionError('Git inspection is forbidden')), redirect_stdout(output):
            self.assertEqual(inventory.main(), 0)
        self.assertIn('**Git inspection:** skipped by request', output.getvalue())
        self.assertIn('**Dirty paths:** unknown', output.getvalue())

    def test_prefix_guess_is_not_reported_as_a_discovered_contract(self):
        result = self.cli('audit_inventory.py', self.root, '--slug', self.slug, '--no-git')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('slug-derived heuristic; public contract is unverified', result.stdout)

    def test_supplied_prefix_is_separate_from_slug_heuristic(self):
        prefix = 'public_contract_' + self.component_id.replace('-', '_')
        result = self.cli('audit_inventory.py', self.root, '--slug', self.slug, '--prefix', prefix, '--no-git')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('**Prefix used for candidate scan:** ' + prefix, result.stdout)
        self.assertIn('supplied --prefix; verify against project declarations', result.stdout)

    def test_verified_empty_git_status_remains_zero(self):
        root = self.root / 'empty-checkout'
        root.mkdir()
        subprocess.run(['git', 'init', '-q', str(root)], check=True, capture_output=True)
        self.assertEqual(inventory.run_git(root, 'status', '--porcelain'), '')
        result = self.cli('audit_inventory.py', root, '--slug', self.slug)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('**Dirty paths:** 0', result.stdout)


if __name__ == '__main__':
    unittest.main()
