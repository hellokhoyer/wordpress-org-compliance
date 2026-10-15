# WordPress.org Compliance

An evidence-led Codex skill for auditing and remediating WordPress plugins
before a first WordPress.org submission, routine update, re-review, or release.

It selects the workflow that fits the plugin instead of assuming every project
has been rejected, uses a freemium model, ships companion plugins, has existing
users, or needs a migration.

The skill focuses on the decisions that automated checks cannot make safely:

- running proactive audits before a first submission;
- comparing routine updates with their released contracts;
- distinguishing reviewer requirements from scanner candidates;
- preserving released data and integration contracts;
- tracing Free, Pro, theme, and companion-plugin consumers when they exist;
- reviewing nonce, capability, ownership, validation, and output boundaries;
- testing previous/current provider-consumer combinations;
- validating the exact distributable instead of only the source tree;
- requiring separate dependency currency, provenance, licence and advisory evidence;
- blocking overall readiness when a required technical check is unverified.

It does not replace the WordPress.org Plugin Directory Guidelines, Plugin Check,
PHPCS/WPCS, security review, or the Plugins Team's independent judgment. It does
not promise that a submission will be accepted.

## Install

Copy this repository to your Codex skills directory:

```bash
cp -R wordpress-org-compliance ~/.codex/skills/wordpress-org-compliance
```

Start a new Codex session so the skill is discovered.

## Use

Invoke it explicitly when you want a compliance audit:

```text
Use $wordpress-org-compliance to audit this plugin and produce an
evidence-backed remediation and release-gate report.
```

The skill can also be selected automatically for proactive submission audits,
routine updates, WordPress.org reviewer emails, Plugin Check or PHPCS findings,
public-prefix work, applicable ownership splits, request-security remediation,
package audits, and resubmission decisions.

## Read-only inventory helper

The included helper inventories a plugin source tree and an optional release
ZIP:

```bash
python3 scripts/audit_inventory.py /path/to/plugin \
  --slug plugin-slug \
  --prefix plugin_prefix \
  --package /path/to/plugin-slug.zip
```

Its output contains candidates. A match is not automatically a policy violation
or security defect. Inspect reachability, authorization, stored-data semantics,
and every relevant consumer before changing code.

## Evidence and readiness helpers

For a full audit start with the unresolved matrix before collecting evidence:

```bash
python3 scripts/verify_readiness.py init --mode=new --scope=full \
  --package=/path/plugin.zip --output=/path/audit/audit.json
```

Inventory all distributed dependencies. The read-only npm helper checks declared
vendored versions against live official metadata, binds their bytes to the ZIP,
and saves raw upstream responses. Unsupported/manual checks remain unverified.

```bash
python3 scripts/check_dependencies.py --manifest=/path/audit/dependencies.json \
  --package=/path/plugin.zip --output=/path/audit/currency.json
python3 scripts/verify_readiness.py check /path/audit/audit.json \
  --package=/path/plugin.zip --output=/path/audit/readiness.json
```

See [evidence-ledger.md](references/evidence-ledger.md) for the manifest, evidence
fields, first-submission exceptions and decision rules. Python 3.9+ is required.
The validator returns zero only for a complete `READY FOR SUBMISSION DECISION`
record. It checks completeness, dates, hashes and decision consistency; it cannot
prove an inventory/source judgment is correct or guarantee directory acceptance.
Neither helper replaces advisory checks, source review or runtime tests.

Run helper regressions with `python3 -m unittest discover -s tests -v`.

## Contents

- `SKILL.md` contains the core workflow and approval boundaries.
- `references/evidence-and-triage.md` classifies review evidence.
- `references/contract-safety.md` covers released and persisted contracts.
- `references/release-gates.md` defines exact-package readiness checks.
- `references/audit-report-template.md` provides a reusable audit format.
- `references/official-sources.md` routes audits to current official guidance.
- `scripts/audit_inventory.py` performs deterministic read-only inventory.
- `references/evidence-ledger.md` defines the check/evidence/dependency records.
- `scripts/check_dependencies.py` checks declared npm dependency currency.
- `scripts/verify_readiness.py` initializes/validates overall audit readiness.
- `tests/` verifies incomplete, stale, outdated and narrow-scope failure paths.

## Background

I wrote about the engineering problem behind this skill in
[Preparing an Established Freemium Plugin for Modern WordPress.org Review](https://abulkhoyer.com/notes/preparing-established-freemium-plugin-wordpress-org-review/).

## License

MIT
