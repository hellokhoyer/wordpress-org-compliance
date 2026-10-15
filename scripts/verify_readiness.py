#!/usr/bin/env python3
"""Initialize and validate an artifact-bound audit ledger; never certify approval.

The validator checks completeness, evidence hashes and decision consistency.
It cannot determine whether a human/agent's source analysis or inventory is true.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath

from check_dependencies import MAX_MEMBER, digest, load_json, stable_version, utc_now

CHECKS = (
    'artifact_identity', 'official_policy', 'reviewer_categories',
    'request_authorization', 'input_validation', 'output_escaping', 'sql_and_storage',
    'privacy_and_external_services', 'admin_behavior', 'dependency_inventory',
    'dependency_licenses', 'dependency_source_integrity', 'dependency_currency',
    'dependency_advisories', 'php_compatibility', 'static_analysis', 'behavioral_tests',
    'activation_lifecycle', 'upgrade_compatibility', 'site_modes', 'ui_and_exports',
    'readme_and_metadata', 'package_inventory', 'package_scans', 'package_activation',
    'cleanup', 'owner_actions',
)
DEPENDENCY_CHECKS = {'dependency_licenses', 'dependency_source_integrity', 'dependency_currency', 'dependency_advisories'}
STATUSES = {'PASS', 'FAIL', 'UNVERIFIED', 'N_A'}
MODES = {'new', 'update', 'proactive', 're-review', 'package-only'}
CONTEXT_FIELDS = ('has_reviewer_message', 'has_third_party_dependencies',
                  'has_prior_public_release', 'has_independently_updated_consumers',
                  'has_admin_ui_or_notices', 'has_ui_or_exports')
SHA256 = re.compile(r'[0-9a-f]{64}')
LEDGER_SCHEMA = 2


def parse_time(value):
    if not isinstance(value, str):
        raise ValueError('Evidence needs an ISO-8601 timestamp with timezone')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Evidence timestamp must include a timezone')
    return result


def proof(item, directory):
    if not isinstance(item, dict) or not isinstance(item.get('path'), str) or not SHA256.fullmatch(str(item.get('sha256', ''))):
        raise ValueError('Evidence needs a relative file path and SHA-256')
    name = item['path']
    if not name or '\\' in name or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:
        raise ValueError('Evidence must stay inside the audit directory')
    path = directory
    for part in PurePosixPath(name).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('Evidence must not escape through a symlink')
    if not path.resolve().is_relative_to(directory.resolve()):
        raise ValueError('Evidence must remain inside its audit directory')
    if not path.is_file() or path.stat().st_size == 0 or digest(path) != item['sha256']:
        raise ValueError('Evidence file is missing, empty or changed: ' + name)
    return path


def na_allowed(key, context):
    if key == 'reviewer_categories':
        return context.get('has_reviewer_message') is False
    if key in DEPENDENCY_CHECKS:
        return context.get('has_third_party_dependencies') is False
    if key == 'upgrade_compatibility':
        return context.get('has_prior_public_release') is False and context.get('has_independently_updated_consumers') is False
    if key == 'admin_behavior':
        return context.get('has_admin_ui_or_notices') is False
    if key == 'ui_and_exports':
        return context.get('has_ui_or_exports') is False
    return False


def currency_window(policy):
    if not isinstance(policy, dict):
        raise ValueError('Declare a project/audit-specific currency_freshness policy')
    hours = policy.get('max_age_hours')
    if type(hours) not in (int, float) or hours <= 0:
        raise ValueError('Currency freshness max_age_hours must be an explicit positive finite number')
    if not isinstance(policy.get('reason'), str) or not policy['reason'].strip():
        raise ValueError('Currency freshness needs its project/audit rationale')
    try:
        if not math.isfinite(hours):
            raise ValueError('Currency freshness max_age_hours must be finite')
        return timedelta(hours=hours)
    except OverflowError as error:
        raise ValueError('Currency freshness exceeds the supported timestamp range') from error


def validate_currency(item, directory, expected, started, inventory_ids, package, freshness):
    report_path = item.get('report')
    references = {entry['path']: entry for entry in item.get('evidence', [])}
    if report_path not in references:
        raise ValueError('Currency PASS needs its hashed dependency report in evidence')
    report_file = proof(references[report_path], directory)
    report = load_json(report_file.read_text())
    if not isinstance(report, dict) or type(report.get('schema_version')) is not int or report['schema_version'] != 1 or report.get('scope') != 'dependency_currency_only':
        raise ValueError('Unsupported dependency currency report schema/scope')
    if report.get('package_sha256') != expected or report.get('inventory_complete') is not True:
        raise ValueError('Currency report has a different artifact or incomplete inventory')
    checked = parse_time(report.get('checked_at'))
    now = datetime.now(timezone.utc)
    age_limit = currency_window(freshness)
    if checked < started or checked > now + timedelta(minutes=5) or now - checked > age_limit:
        raise ValueError('Currency lookup must be from this audit and within its declared freshness window; future/stale evidence cannot pass')
    rows = report.get('records')
    if not isinstance(rows, list) or not rows:
        raise ValueError('Currency report must account for every declared dependency')
    ids = [row.get('id') for row in rows if isinstance(row, dict)]
    if len(ids) != len(rows) or any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids) or set(ids) != set(inventory_ids):
        raise ValueError('Currency report does not cover the exact dependency inventory')
    exceptions = []
    for row in rows:
        if any(not isinstance(row.get(key), str) or not row[key].strip() for key in ('version', 'latest_stable')):
            raise ValueError('Every dependency needs explicit bundled and current upstream versions')
        files, source = row.get('files'), row.get('source_url')
        if not isinstance(files, list) or not files or not isinstance(source, str) or not source.startswith('https://'):
            raise ValueError('Dependency currency needs bundled file bindings and an official upstream source URL')
        for member in files:
            if not isinstance(member, dict) or not isinstance(member.get('path'), str) or not member['path'] or not SHA256.fullmatch(str(member.get('sha256', ''))):
                raise ValueError('Dependency file binding is incomplete')
            with zipfile.ZipFile(package) as archive:
                info = archive.getinfo(member['path'])
                if info.file_size > MAX_MEMBER or info.is_dir() or (info.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError('Invalid dependency ZIP member')
                if hashlib.sha256(archive.read(info)).hexdigest() != member['sha256']:
                    raise ValueError('Dependency bytes differ from the currency evidence')
        upstream = proof(row.get('upstream_evidence'), report_file.parent)
        if report.get('tool') == 'wordpress-org-compliance/check_dependencies' and row.get('ecosystem') == 'npm':
            metadata = load_json(upstream.read_text())
            if not isinstance(metadata, dict) or metadata.get('name') != row.get('package') or metadata.get('version') != row.get('latest_stable') or not stable_version(metadata.get('version')) or metadata.get('deprecated'):
                raise ValueError('npm currency report contradicts its upstream metadata')
        if row.get('status') == 'CURRENT':
            if not isinstance(row.get('version'), str) or not row['version'] or row['version'] != row.get('latest_stable'):
                raise ValueError('CURRENT dependency does not match the verified stable version')
        elif row.get('status') == 'SUPPORTED_EXCEPTION':
            if not isinstance(row.get('reason'), str) or not row['reason'].strip():
                raise ValueError('A supported-version exception needs a specific rationale')
            for key in ('upstream_support_evidence', 'risk_assessment_evidence', 'owner_authorization_evidence'):
                proof(row.get(key), report_file.parent)
            exceptions.append(row['id'])
        else:
            raise ValueError('Outdated/unverified dependency must be updated or explicitly resolved with evidence: ' + str(row.get('id')))
    return exceptions


def initialize(package, scope, mode):
    return {'schema_version': LEDGER_SCHEMA, 'scope': scope, 'mode': mode, 'started_at': utc_now(),
            'package_sha256': digest(package),
            'currency_freshness': {'max_age_hours': None, 'reason': ''},
            'context': {'has_reviewer_message': None, 'has_third_party_dependencies': None,
                        'has_prior_public_release': None, 'has_independently_updated_consumers': None,
                        'has_admin_ui_or_notices': None, 'has_ui_or_exports': None},
            'dependency_ids': [],
            'checks': {key: {'status': 'UNVERIFIED', 'package_sha256': '', 'reason': '', 'evidence': []} for key in CHECKS}}


def validate(ledger, package, directory):
    if not isinstance(ledger, dict):
        raise ValueError('Audit ledger must be an object')
    errors, failures, pending, exceptions = [], [], [], []
    expected = digest(package)
    with zipfile.ZipFile(package) as archive:
        members = archive.infolist()
        if archive.testzip() is not None or len({m.filename for m in members}) != len(members):
            errors.append('ZIP has corrupt or ambiguous members')
    if ledger.get('schema_version') != LEDGER_SCHEMA or type(ledger.get('schema_version')) is not int:
        errors.append('Unsupported ledger schema; initialize the current matrix and preserve/review prior evidence')
    if ledger.get('mode') not in MODES or ledger.get('scope') not in {'full', 'limited'}:
        errors.append('Missing or invalid audit mode/scope')
    if ledger.get('package_sha256') != expected:
        errors.append('Ledger does not identify the supplied ZIP')
    try:
        started = parse_time(ledger.get('started_at'))
        if started > datetime.now(timezone.utc) + timedelta(minutes=5):
            raise ValueError('Audit start is in the future')
    except (ValueError, TypeError) as error:
        errors.append(str(error)); started = datetime.now(timezone.utc)
    context = ledger.get('context')
    if not isinstance(context, dict):
        errors.append('Missing applicability context'); context = {}
    for name in CONTEXT_FIELDS:
        if type(context.get(name)) is not bool:
            errors.append('Applicability must be explicitly resolved: ' + name)
    dependencies = ledger.get('dependency_ids')
    if not isinstance(dependencies, list) or any(not isinstance(i, str) or not i for i in dependencies) or len(dependencies) != len(set(dependencies)):
        errors.append('Dependency inventory needs unique nonempty ids'); dependencies = []
    if context.get('has_third_party_dependencies') is True and not dependencies:
        errors.append('Third-party dependencies are declared but not inventoried')
    if context.get('has_third_party_dependencies') is False and dependencies:
        errors.append('No-dependency context contradicts the dependency inventory')
    if type(context.get('has_third_party_dependencies')) is not bool:
        errors.append('Dependency applicability is unverified')
    checks = ledger.get('checks')
    if not isinstance(checks, dict):
        checks = {}; errors.append('Missing check matrix')
    if set(checks) - set(CHECKS):
        errors.append('Unknown checks cannot replace required gates')
    for key in CHECKS:
        try:
            item = checks.get(key)
            if not isinstance(item, dict) or item.get('status') not in STATUSES:
                raise ValueError('Missing check or invalid status')
            status = item['status']
            if status == 'UNVERIFIED':
                pending.append(key); continue
            if item.get('package_sha256') != expected:
                raise ValueError('Check is bound to a different or unknown artifact')
            if not isinstance(item.get('reason'), str) or not item['reason'].strip():
                raise ValueError('Check needs its result or applicability rationale')
            evidence = item.get('evidence')
            if not isinstance(evidence, list) or not evidence:
                raise ValueError('Check has no reproducible evidence files')
            for entry in evidence:
                proof(entry, directory)
            if status == 'N_A' and not na_allowed(key, context):
                raise ValueError('N_A is not justified by this check and plugin context')
            if status == 'FAIL':
                failures.append(key)
            if status == 'PASS' and key == 'dependency_currency':
                exceptions.extend(validate_currency(item, directory, expected, started, dependencies, package, ledger.get('currency_freshness')))
        except (ValueError, OSError, KeyError, TypeError, RuntimeError, zipfile.BadZipFile) as error:
            errors.append(key + ': ' + str(error))
    technical_failures = [key for key in failures if key != 'owner_actions']
    technical_pending = [key for key in pending if key != 'owner_actions']
    if ledger.get('scope') != 'full' or ledger.get('mode') == 'package-only':
        decision = 'LIMITED REVIEW; NO FULL READINESS DECISION'
    elif technical_failures:
        decision = 'NOT READY'
    elif errors or technical_pending:
        decision = 'INCOMPLETE AUDIT; READINESS UNVERIFIED'
    elif 'owner_actions' in pending or 'owner_actions' in failures:
        decision = 'CODE READY; RELEASE GATES PENDING'
    else:
        decision = 'READY FOR SUBMISSION DECISION'
    return {'decision': decision, 'package_sha256': expected, 'validation_errors': errors,
            'currency_freshness': ledger.get('currency_freshness'),
            'failed_checks': failures, 'unverified_checks': pending,
            'supported_dependency_exceptions': exceptions,
            'limitation': 'Evidence completeness and consistency only; source judgments, inventory completeness and WordPress.org approval are not certified.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init')
    init.add_argument('--package', required=True, type=Path)
    init.add_argument('--output', required=True, type=Path)
    init.add_argument('--scope', choices=['full', 'limited'], default='full')
    init.add_argument('--mode', choices=['new', 'update', 'proactive', 're-review', 'package-only'], required=True)
    check = commands.add_parser('check')
    check.add_argument('ledger', type=Path)
    check.add_argument('--package', required=True, type=Path)
    check.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            result = initialize(args.package, args.scope, args.mode)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open('x') as stream:
                stream.write(json.dumps(result, indent=2) + '\n')
            print('Created UNVERIFIED check matrix: ' + str(args.output)); return 0
        result = validate(load_json(args.ledger.read_text()), args.package, args.ledger.parent)
        encoded = json.dumps(result, indent=2) + '\n'
        if args.output:
            if args.output.resolve() in {args.ledger.resolve(), args.package.resolve()}:
                raise ValueError('Output must not overwrite the ledger or package')
            args.output.write_text(encoded)
        print(encoded, end='')
        return 0 if result['decision'] == 'READY FOR SUBMISSION DECISION' else 1
    except (ValueError, OSError, TypeError, RuntimeError, zipfile.BadZipFile) as error:
        print(json.dumps({'decision': 'INCOMPLETE AUDIT; READINESS UNVERIFIED', 'error': str(error)})); return 2


if __name__ == '__main__':
    sys.exit(main())
