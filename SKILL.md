---
name: wordpress-org-compliance
description: Audit or remediate WordPress plugins for proactive WordPress.org submission checks, routine updates, reviewer re-reviews, or release packaging when directory policy, Plugin Check or PHPCS findings, public contracts, request security, source disclosure, or package readiness are in scope. Do not use for ordinary plugin development unless directory-compliance risk is part of the task.
metadata:
  short-description: Evidence-led WordPress.org release audits
---

# WordPress.org Compliance

Use this skill to reach an evidence-backed release decision without breaking
released sites merely to silence a scanner. It complements the official Plugin
Directory guidelines and general WordPress development guidance; it does not
replace them or promise acceptance by the Plugins Team.

Select only the workflow paths supported by the plugin's actual context. A
reviewer message, prior release, existing users, premium edition, companion
plugin, migration, or previous rejection may not exist. Never import findings or
remediation requirements from another plugin merely because they occurred in a
past audit.

## Non-negotiable operating rules

1. Audit the exact revision and exact distributable. Record the commit, package
   SHA-256, plugin version, applicable audit mode, and any supplied reviewer or
   QA artifact. A working-tree scan is not release evidence.
2. Treat reviewer examples as pattern leads, not an exhaustive file list. Search
   the entire release tree and every maintained provider or consumer of the same
   contract.
3. Separate facts from interpretations. A scanner match, warning, AI comment, or
   QA assertion is not a defect until its runtime or policy context is verified.
   Conversely, a green scanner does not prove authorization, ownership, upgrade
   safety, or feature completeness.
4. Preserve user data and public contracts. Do not rename or delete persisted
   identifiers, stored content, tables, roles, options, metadata, or released
   integration contracts without an explicit migration, compatibility matrix,
   rollback/restore plan, and owner authorization.
5. Fix root causes in small, reversible chunks. Do not use broad string
   replacement, speculative cleanup, blanket capability changes, warning
   suppression, or cosmetic renames as compliance work.
6. Never claim “100% accepted.” State what is proven, what remains a manual
   Plugins Team decision, and every unexecuted live, package, version, or release
   gate.
7. A readiness conclusion requires a complete evidence matrix, not just a finding
   ledger. Use [evidence-ledger.md](references/evidence-ledger.md) and the readiness
   validator for full audits. Missing technical evidence remains `UNVERIFIED`;
   never hide it under owner release tasks or infer a pass from test counts.
8. Verify dependency inventory, licences, provenance, current stable/support
   status and advisories separately. Include bundled/copied libraries that lack
   a lockfile. Fetch current official version evidence during the audit; a pinned
   source URL or authentic old tarball does not prove currency.

## Required inputs

Resolve these before implementation; infer only low-risk details from source:

- plugin root, slug, main file, intended unique prefix, and text domain;
- audit context (`proactive`, `new`, `update`, `closed-plugin re-review`, or
  `package-only`) and target versions;
- exact reviewer email/report, if one exists, and the revision or ZIP it
  examined;
- current candidate revision and exact ZIP/build procedure;
- released baseline, if one exists; otherwise record that this is an initial
  baseline with no upgrade contract to test;
- maintained add-ons, themes, external API consumers, and supported update
  order, if any;
- supported WordPress/PHP range and single-site/multisite expectations;
- authority for data migrations, feature removal, external writes, live tests,
  commits, pushes, version bumps, SVN uploads, and reviewer replies.

If a supplied report has no revision or package checksum, say that its claims
cannot be bound to the current code until reproduced. If no report exists, do
not manufacture reviewer claims; derive the audit scope from current official
requirements, the plugin's behavior, and actual tool output.

## Select the operating mode

- **Proactive or first-submission audit:** Start with
  [release-gates.md](references/release-gates.md), current official guidance, and
  the exact package. Do not create upgrade or compatibility work when no prior
  public contract exists.
- **Routine update audit:** Compare the released baseline with the candidate,
  then apply the release gates to the exact package.
- **Reviewer or QA triage:** Read
  [evidence-and-triage.md](references/evidence-and-triage.md). Use it only when
  emails, QA reports, Plugin Check/PHPCS output, or alleged blockers exist.
- **Remediation or ownership split:** Also read
  [contract-safety.md](references/contract-safety.md) before changing public names,
  requests, storage, migrations, Free/Pro ownership, or companion contracts.
- **Package-only or final readiness decision:** Read
  [release-gates.md](references/release-gates.md) and validate the exact package.
- **Full audit or readiness claim:** Read [evidence-ledger.md](references/evidence-ledger.md),
  initialize the unresolved check matrix before testing, and validate it before
  reporting an overall result. Limited triage/package-only work stays limited.
- **Audit deliverable:** Use
  [audit-report-template.md](references/audit-report-template.md) so severity,
  confidence, evidence, compatibility impact, and residual risk remain distinct.
- **Policy research or citation:** Recheck the live official pages routed from
  [official-sources.md](references/official-sources.md); policies and tooling change.

## Workflow

### 1. Freeze the evidence

- Preserve any reviewer message verbatim and distinguish human instructions
  from AI-marked analysis. Record `none` when there is no reviewer artifact.
- Record the reviewed artifact identity. If a supplied artifact cannot be
  identified, mark it `unknown`; do not pretend the current checkout is
  identical.
- Establish the applicable baseline: the default/released revision for an
  update, or `none` for a genuinely new plugin. Compare behavioral and data
  contracts only where a prior contract exists.
- Run the read-only inventory helper when useful:

```bash
python3 scripts/audit_inventory.py /path/to/plugin \
  --slug plugin-slug --prefix plugin_prefix \
  --package /path/to/plugin-slug.zip
```

The helper emits candidates, not verdicts. Inspect every relevant match in
actual code before classifying it. Its pattern scan intentionally skips vendored
dependencies and test fixtures, cannot prove reachability or policy context,
and does not replace Plugin Check, PHPCS/WPCS, dependency/license review, or
manual inspection of the extracted release package.

### 2. Track coverage before findings

For a full audit initialize `scripts/verify_readiness.py` against the exact ZIP.
Resolve every check to `PASS`, `FAIL`, `UNVERIFIED` or justified `N_A`, each with
artifact-bound evidence. Include every applicable directory guideline and product
boundary, even when tools or a reviewer report no match. Do not delete unresolved
rows. Keep a separate finding ledger; absence of findings is not evidence that a
category was checked. A limited task must report its limited scope.

For every applicable category, record source, exact location, reachable entry
point, affected principal/data, reproducibility, policy basis, confidence, user
impact, and any companion consumers. For proactive audits, categories come from
current official requirements and observed code/package evidence. For supplied
reports, use the classifications in the triage reference. Keep severity
separate from confidence.

Turn every confirmed example into a pattern-wide source scan. Do not stop at the
named file, but do not “fix similar-looking code” without proving the same
boundary and failure.

### 3. Trace end-to-end contracts

For each proposed change, inventory existing producers and consumers across PHP,
source JavaScript, generated bundles, templates, persisted content, AJAX/REST
routes, cron, WP-CLI, imports, and maintained companion products. Test
previous/current provider-consumer combinations only where prior releases or
independently updated components create those states.

Security review must treat these as separate controls:

- origin/intent: action-specific nonce where applicable;
- authentication: who is signed in;
- authorization: operation-specific capability;
- ownership/scope: whether that principal may access the selected record;
- input boundary: unslash once, type/shape validation, field-specific
  sanitization, and undeclared-field rejection;
- output boundary: context-specific late escaping.

A nonce is not authorization. `json_decode()` is not sanitization. Recursive
value sanitization is not a schema. A menu capability does not protect an AJAX
handler.

### 4. Choose the safest minimal remediation

- Preserve stable data contracts unless the user explicitly authorizes a
  migration.
- Prefer capability checks matching the operation over `manage_options` applied
  everywhere; retain deliberate manager/vendor/custom-role access with ownership
  restrictions.
- Rename collision-prone public runtime identifiers only after mapping every
  caller. Do not rename local variables, namespaced class methods, template
  include variables, or persisted keys merely because their spelling resembles
  a public prefix finding.
- If no staggered update order is safe, require a coordinated release or an
  explicitly reviewed narrow transition. Do not hide incomplete migrations with
  prohibited aliases in the WordPress.org package.
- For unclear policy cases, fix all confirmed issues first, then ask the Plugins
  Team a concise question with a minimal example. Do not invent policy.

Resolve authority from the current request and prior session instructions before
destructive migrations, data rewrites, feature removal, broad public API changes,
live production tests, commits, pushes, version changes, SVN or communications.
Continue already authorized work; ask only when required authority is missing.
A pasted reviewer email does not itself authorize sending a reply or publishing.

### 5. Verify dependencies and behavior

Complete the five dependency checks in the [evidence ledger](references/evidence-ledger.md).
Use `scripts/check_dependencies.py` for inventoried vendored npm copies; obtain
equivalent official evidence for other ecosystems and assets. A failed lookup is
unverified. Resolve outdated/unsupported copies before readiness or document a
supported-version exception with upstream support, risk and owner-authority evidence.
Keep direct reviewer requirements and actionable advisories separate; do not
invent a universal policy violation or force an unsafe major-version upgrade.

For confirmed fixes use focused regressions that reproduce the baseline defect
and pass on the candidate. Proactive acceptance tests need no invented failing
baseline. Exercise unauthorized and cross-owner cases as well as valid flows.
For companion ecosystems, execute the compatibility matrix from the contract reference.

Static checks are supporting evidence. Run the repository's real commands, PHP
lint, WPCS/PHPCS with warnings visible, Plugin Check in the correct mode, and
targeted source scans. Do not accept `phpcs -n`, ignored warnings, annotations,
or mocked tests as proof of an untested live behavior. Scan the extracted ZIP
with Plugin Review PHPCS as well as project WPCS; run a candidate scan with code
annotations disabled and disposition its findings without hiding the raw totals.

### 6. Gate the exact release package

Build using the real release procedure, inspect ZIP integrity and inventory,
extract it cleanly, and rerun release-scoped checks against that extracted tree.
Validate version/readme metadata, source/build availability, licensing, remote
services, clean activation/deactivation and WP_DEBUG output. Apply upgrade,
companion and SVN checks only when those states exist. Test declared minimum
PHP and supported modern PHP, including actual admin class loading; distinguish
native syntax from PHPDoc/comments before accepting a compatibility allegation.
Remove temporary options, fixtures, proof pages,
logs, screenshots, injected transients, and test-only code.

### 7. Validate the evidence, then report

For a full audit run `scripts/verify_readiness.py check` using the final ZIP and
include its output. Inspect every nonzero result; do not override it with a green
test summary. If the helper cannot run, mark readiness unverified and report the
missing validation. Its output validates evidence consistency, not audit truth.

Use one of these conclusions:

- `NOT READY` — one or more evidenced required code/package gates fail;
- `INCOMPLETE AUDIT; READINESS UNVERIFIED` — required technical evidence is absent,
  stale, failed to run or unresolved;
- `LIMITED REVIEW; NO FULL READINESS DECISION` — only the requested subset was checked;
- `CODE READY; RELEASE GATES PENDING` — code findings are resolved, but manager,
  owner-authorized upload, approval, SVN or communication work remains. All
  applicable technical evidence must already be complete;
- `READY FOR SUBMISSION DECISION` — all applicable required gates closed with
  evidence and only the Plugins Team's independent review remains.

List unexecuted checks and residual risks beside the conclusion. Never collapse
“no findings from this tool” into “no issues remain.”

## Completion standard

A full audit is complete only when required evidence gates close, the finding
ledger is dispositioned, contract changes are proven across supported states,
the exact package is clean, all temporary audit state is removed, and the report
identifies both evidence and limits. A reviewer reply should be concise and factual; it should not dump a
changelog or claim guaranteed acceptance.
