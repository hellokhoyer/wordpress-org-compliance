# Evidence ledger and readiness validation

Use this for full compliance audits or an overall readiness decision. Limited
triage/package checks remain limited; do not expand an ordinary task merely to
complete this matrix. Reading a skill, completing a repair plan, a zero exit code,
or a large passing test count does not establish compliance coverage.

## Start with unresolved checks

Initialize before collecting evidence; keep the ledger, reports and raw evidence
outside the distributable. Helpers require Python 3.9+ and the standard library.

```bash
python3 scripts/verify_readiness.py init --mode=new --scope=full \
  --package=/path/plugin.zip --output=/path/audit/audit.json
```

The initializer enumerates all required checks as `UNVERIFIED`. Resolve each
applicability boolean from source/product facts. `has_prior_public_release=false`
does not mean no initial setup is needed: fresh/repeat activation still applies.

The matrix covers identity/current policy/reviewer categories, request authority,
input/output/SQL/storage/privacy/admin behavior, five separate dependency checks,
PHP compatibility/static/behavioral/lifecycle/upgrade/site-mode/UI verification,
readme/metadata, package inventory/scans/install, cleanup and owner actions. The
exact check IDs are emitted by the initializer; do not delete or rename them.

The `official_policy` evidence must map every current numbered directory
guideline to PASS/FAIL/UNVERIFIED/N_A with its source and applicability. Also
cover the current common-issues categories and any direct review instructions.
A short list of repaired findings is not this coverage map. For `admin_behavior`,
inspect notice scope, relevance, dismissal/self-resolution, promotions, links and
data collection on the screens where they actually appear.

Each check has one status:

- `PASS`: the named invariant is supported by executed checks or documented source
  review at the exact candidate. Record commands, tool/runtime versions, scope,
  raw outputs and analysis; a checker's mere successful execution is insufficient.
- `FAIL`: an evidenced required invariant fails. Retain the reproduction and impact.
- `UNVERIFIED`: missing, stale, unavailable, failed-to-run, out-of-scope or ambiguous
  evidence. Explain the limitation. This cannot support technical readiness.
- `N_A`: evidence shows the feature/context does not exist. An inconvenience,
  absent credentials or missing test environment is not non-applicability.

For a closed check record `package_sha256`, a meaningful `reason`, and evidence
files relative to the ledger directory, each with its actual SHA-256. Evidence
must be nonempty and must not traverse directories or use symlinks. The file's
contents must support this check; copying one generic “tests passed” note into
every row is invalid evidence even if a structural validator cannot detect it.

```json
{
  "status": "PASS",
  "package_sha256": "<actual ZIP SHA-256>",
  "reason": "Describe the invariant, executed command/review and actual result.",
  "evidence": [
    {"path": "activation-php74.json", "sha256": "<actual evidence SHA-256>"}
  ]
}
```

`N_A` is allowed only for absent reviewer input, absent dependencies, absent
upgrade/independently updated consumers, or absent admin/UI/export features, as
appropriate to the corresponding check and explicit context. It still needs
source/inventory evidence. Identity, core security review, initial activation,
package verification and cleanup cannot be waived with `N_A`.

## Dependency evidence is not interchangeable

Inventory **all distributed third-party components**, including copied libraries,
embedded/transitive code inside generated bundles, PHP vendor trees, fonts and CSS/assets without a
lockfile. The first-party inventory helper's vendor exclusions do not apply to
this inventory. Distinguish distributed runtime dependencies from development-only
tools and WordPress-provided handles. Record duplicate bundled copies separately
when their versions differ.

Record each embedded component's owning bundle and upstream-supported version
range. Investigate through that upstream release chain; do not splice a newer
transitive library into a generated third-party bundle just to change a version
string. Use a compatible parent update, justified backport or supported exception.

Close these checks separately: inventory, GPL-compatible licences/attribution,
source/build provenance and integrity, currency/support status, and advisories.
An old official tarball can be authentic and licensed while its version is stale.
No matching advisory does not prove that a library is current or maintained.

For currency, obtain current stable metadata from the official upstream during
this audit and within 24 hours of the final readiness validation. This is this
skill's evidence-freshness rule, not a WordPress.org policy deadline. Record
bundled version/file hashes, latest stable version, official
URL, UTC retrieval time and raw metadata/page snapshot. Never infer “latest” from
an unchanged header, pinned source tag, old audit or successful rendering.

The helper handles **declared vendored npm dependencies only**. Supply an inventory
manifest bound to the exact ZIP, with an explicit completeness declaration:

```json
{
  "package_sha256": "<actual ZIP SHA-256>",
  "inventory_complete": true,
  "dependencies": [
    {
      "id": "chartjs",
      "ecosystem": "npm",
      "package": "chart.js",
      "version": "4.4.1",
      "version_marker": "Chart.js v4.4.1",
      "paths": ["plugin-slug/assets/vendor/chart.umd.min.js"]
    }
  ]
}
```

```bash
python3 scripts/check_dependencies.py --manifest=/path/audit/dependencies.json \
  --package=/path/plugin.zip --output=/path/audit/currency.json
```

This reads public npm metadata over HTTPS; it sends package names, not ZIP bytes
or credentials. It never installs or executes downloaded code. It checks version
markers/file hashes and saves raw upstream metadata beside the output. An outdated
copy is `OUTDATED`; an unsupported ecosystem, failed lookup, invalid metadata,
prerelease, deprecated release or bundled version ahead of npm's latest tag is
`UNVERIFIED`. Both return nonzero. Investigate divergent release channels rather
than automatically downgrading or switching major versions.
Do not remove failed/unsupported rows to obtain a pass. The helper does not find
omitted dependencies, check advisories/licences or prove upstream maintenance.

Use native package-manager/advisory tools and official release/support information
for PHP, non-npm JS, fonts and other assets. Record manual currency results in the
same report structure (the npm helper's unsupported row is not a pass):
`schema_version: 1`, `scope: "dependency_currency_only"`, exact
`package_sha256`, `inventory_complete: true`, current `checked_at`, one `records` row per
ledger `dependency_ids`, `files` ZIP-member hashes, `source_url`, bundled `version`,
`latest_stable`, and a hashed `upstream_evidence` file relative to the report.
The auditor must verify official provenance and the recorded versions; the
validator checks bindings/coverage, not the truth of every manual observation.

For `dependency_currency=PASS`, set `report` to the report path and include that
report in the check's hashed evidence. Every inventory ID must be covered. An
older supported release can be retained only as an explicit `SUPPORTED_EXCEPTION`
row with a specific `reason` and hashed `upstream_support_evidence`,
`risk_assessment_evidence` and `owner_authorization_evidence`. These paths are
relative to the report. Preserve the original lookup result and disclose the
exception in the report. This does not waive an unresolved exploitable advisory
or a direct reviewer requirement; those gates still fail or need clarification.
Do not blindly cross a breaking major version or rewrite provenance headers.

## Validate before the conclusion

```bash
python3 scripts/verify_readiness.py check /path/audit/audit.json \
  --package=/path/plugin.zip --output=/path/audit/readiness.json
```

- `READY FOR SUBMISSION DECISION`: every required check closes with evidence.
- `CODE READY; RELEASE GATES PENDING`: every technical check closes; only named
  owner upload/approval/SVN/communication actions remain. Missing technical tests,
  credentials or an unverified dependency cannot use this conclusion.
- `INCOMPLETE AUDIT; READINESS UNVERIFIED`: technical evidence is missing,
  ambiguous, stale or invalid. State completed scope and remaining checks.
- `NOT READY`: an evidenced technical/code/package blocker remains.
- `LIMITED REVIEW; NO FULL READINESS DECISION`: requested scope is limited or
  package-only. Do not turn a narrow result into an overall pass.

The checker returns zero only for `READY FOR SUBMISSION DECISION`; all other
decisions return nonzero. A zero result verifies the recorded evidence's
completeness/consistency, **not security or acceptance**. Read the actual result.
An agent can still make an incorrect source judgment or incomplete inventory;
do not describe the helper as an unbypassable compliance certification.

New package bytes invalidate the old overall decision. Rebuild/rebind the ledger,
rerun affected checks and recheck live dependency metadata for the new audit.
Carry unchanged-scope evidence only with file hashes, old/new package identities,
an explicit applicability analysis and fresh package inventory/scans/install.
Never silently relabel historical test output as a new run.
