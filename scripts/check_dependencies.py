#!/usr/bin/env python3
"""Check declared vendored npm versions against live official stable metadata.

This checks currency only. It does not discover every dependency, check
advisories/licences, install packages, or certify WordPress.org compliance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

MAX_RESPONSE = 4 * 1024 * 1024
MAX_MEMBER = 32 * 1024 * 1024


def load_json(raw):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Ambiguous duplicate JSON key: ' + key)
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError('Invalid JSON number: ' + value)

    return json.loads(raw, object_pairs_hook=unique_keys, parse_constant=invalid_constant)


def digest(path):
    with Path(path).open('rb') as stream:
        value = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
        return value.hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def fetch_metadata(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'wordpress-org-compliance/1'})
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read(MAX_RESPONSE + 1)
    if len(raw) > MAX_RESPONSE:
        raise ValueError('Upstream metadata exceeds the size limit')
    return raw


def stable_version(value):
    return isinstance(value, str) and bool(re.fullmatch(r'\d+\.\d+\.\d+(?:\+[0-9A-Za-z.-]+)?', value))


def check(manifest, package, output, fetch=fetch_metadata):
    if not isinstance(manifest, dict):
        raise ValueError('Dependency manifest must be an object')
    actual = digest(package)
    if manifest.get('package_sha256') != actual:
        raise ValueError('Manifest does not identify the supplied ZIP')
    dependencies = manifest.get('dependencies')
    if not isinstance(dependencies, list):
        raise ValueError('dependencies must be an explicit list, including when empty')
    ids = [row.get('id') for row in dependencies if isinstance(row, dict)]
    if len(ids) != len(dependencies) or any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError('Each dependency needs a unique nonempty id')
    report = {'schema_version': 1, 'tool': 'wordpress-org-compliance/check_dependencies',
              'scope': 'dependency_currency_only', 'package_sha256': actual,
              'checked_at': utc_now(), 'inventory_complete': manifest.get('inventory_complete') is True,
              'records': []}
    output = Path(output)
    snapshot_dir = output.parent / (output.stem + '-evidence')
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(package) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP integrity check failed')
        members = archive.infolist()
        if len({m.filename for m in members}) != len(members):
            raise ValueError('Ambiguous duplicate ZIP members')
        for dependency in dependencies:
            row = {key: dependency.get(key) for key in ('id', 'ecosystem', 'package', 'version')}
            row.update({'status': 'UNVERIFIED', 'files': [], 'source_url': '', 'latest_stable': None})
            try:
                paths = dependency.get('paths')
                if not isinstance(paths, list) or not paths or any(not isinstance(p, str) for p in paths) or len(paths) != len(set(paths)):
                    raise ValueError('List the dependency files in this exact ZIP')
                marker = dependency.get('version_marker')
                if not isinstance(marker, str) or not isinstance(row['version'], str) or row['version'] not in marker:
                    raise ValueError('version_marker must contain the declared version and match bundled bytes')
                marker_found = False
                for name in paths:
                    if not isinstance(name, str) or '\\' in name or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:
                        raise ValueError('Unsafe dependency ZIP path')
                    info = archive.getinfo(name)
                    if info.is_dir() or (info.external_attr >> 16) & 0o170000 == 0o120000 or info.file_size > MAX_MEMBER:
                        raise ValueError('Dependency path must be a bounded regular ZIP member')
                    raw = archive.read(info)
                    marker_found = marker_found or marker.encode('utf-8') in raw
                    row['files'].append({'path': name, 'sha256': hashlib.sha256(raw).hexdigest()})
                if not marker_found:
                    raise ValueError('Declared version marker was not found in the supplied dependency bytes')
                if row['ecosystem'] != 'npm':
                    raise ValueError('Automatic lookup supports npm only; verify this upstream manually and retain evidence')
                name = row['package']
                if not isinstance(name, str) or not re.fullmatch(r'(?:@[a-z0-9._-]+/)?[a-z0-9._-]+', name):
                    raise ValueError('Invalid npm package name')
                if not stable_version(row['version']):
                    raise ValueError('Bundled npm version is not a stable semantic version')
                url = 'https://registry.npmjs.org/' + urllib.parse.quote(name, safe='@') + '/latest'
                row['source_url'] = url
                raw = fetch(url)
                if len(raw) > MAX_RESPONSE:
                    raise ValueError('Upstream metadata exceeds the size limit')
                metadata = load_json(raw)
                if not isinstance(metadata, dict) or metadata.get('name') != name or not stable_version(metadata.get('version')):
                    raise ValueError('Upstream response does not identify this package and a stable version')
                filename = hashlib.sha256(url.encode()).hexdigest() + '.json'
                snapshot = snapshot_dir / filename
                snapshot.write_bytes(raw)
                row['upstream_evidence'] = {'path': snapshot.relative_to(output.parent).as_posix(), 'sha256': digest(snapshot)}
                row['latest_stable'] = metadata['version']
                if metadata.get('deprecated'):
                    raise ValueError('Latest npm release is deprecated; investigate maintained support/replacement')
                bundled = tuple(map(int, row['version'].split('+')[0].split('.')))
                latest = tuple(map(int, row['latest_stable'].split('+')[0].split('.')))
                if bundled > latest:
                    raise ValueError('Bundled version is ahead of npm latest; investigate release channels before changing it')
                row['status'] = 'CURRENT' if row['version'] == row['latest_stable'] else 'OUTDATED'
            except (ValueError, OSError, KeyError, TypeError, RuntimeError, zipfile.BadZipFile) as error:
                row['error'] = str(error)
            report['records'].append(row)
    states = {r['status'] for r in report['records']}
    report['status'] = ('FAIL' if 'OUTDATED' in states else
                        'UNVERIFIED' if not report['inventory_complete'] or 'UNVERIFIED' in states else 'PASS')
    output.write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--package', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.output.resolve() in {args.manifest.resolve(), args.package.resolve()}:
            raise ValueError('Output must not overwrite the manifest or package')
        result = check(load_json(args.manifest.read_text()), args.package, args.output)
    except (ValueError, OSError, TypeError, RuntimeError, zipfile.BadZipFile) as error:
        print(json.dumps({'status': 'UNVERIFIED', 'error': str(error)}))
        return 2
    print(json.dumps({key: value for key, value in result.items() if key != 'records'}))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
