# WordPress.org Compliance

An evidence-led Codex skill for auditing and remediating WordPress plugins
before a WordPress.org submission, re-review, or release.

The skill focuses on the decisions that automated checks cannot make safely:

- distinguishing reviewer requirements from scanner candidates;
- preserving released data and integration contracts;
- tracing Free, Pro, theme, and companion-plugin consumers;
- reviewing nonce, capability, ownership, validation, and output boundaries;
- testing previous/current provider-consumer combinations;
- validating the exact distributable instead of only the source tree.

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

The skill can also be selected automatically for WordPress.org reviewer emails,
Plugin Check or PHPCS findings, public-prefix work, freemium ownership splits,
request-security remediation, package audits, and resubmission decisions.

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

## Contents

- `SKILL.md` contains the core workflow and approval boundaries.
- `references/evidence-and-triage.md` classifies review evidence.
- `references/contract-safety.md` covers released and persisted contracts.
- `references/release-gates.md` defines exact-package readiness checks.
- `references/audit-report-template.md` provides a reusable audit format.
- `references/official-sources.md` routes audits to current official guidance.
- `scripts/audit_inventory.py` performs deterministic read-only inventory.

## Background

I wrote about the engineering problem behind this skill in
[When Old Freemium Architecture Meets Today’s WordPress.org Review](https://abulkhoyer.com/notes/when-old-freemium-architecture-meets-todays-wordpress-org-review/).

## License

MIT
