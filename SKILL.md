---
name: wordpress-org-compliance
description: Audit or remediate WordPress plugins for WordPress.org submission, re-review, or release when reviewer emails, Plugin Check or PHPCS findings, freemium separation, public-prefix changes, request security, packaging, or resubmission readiness are in scope. Do not use for ordinary plugin development unless directory-compliance risk is part of the task.
metadata:
  short-description: Evidence-led WordPress.org release audits
---

# WordPress.org Compliance

Use this skill to reach an evidence-backed release decision without breaking
released sites merely to silence a scanner. It complements the official Plugin
Directory guidelines and general WordPress development guidance; it does not
replace them or promise acceptance by the Plugins Team.

## Non-negotiable operating rules

1. Audit the exact revision and exact distributable. Record the commit, package
   SHA-256, plugin version, review mode (`new` or `update`), and supplied reviewer
   message. A working-tree scan is not release evidence.
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

## Required inputs

Resolve these before implementation; infer only low-risk details from source:

- plugin root, slug, main file, intended unique prefix, and text domain;
- submission type (`new`, `update`, closed-plugin re-review) and target versions;
- exact reviewer email/report and the revision or ZIP it examined;
- current candidate revision and exact ZIP/build procedure;
- maintained add-ons, themes, external API consumers, and supported update order;
- supported WordPress/PHP range and single-site/multisite expectations;
- authority for data migrations, feature removal, external writes, live tests,
  commits, pushes, version bumps, SVN uploads, and reviewer replies.

If the report has no revision or package checksum, say that its claims cannot be
bound to the current code until reproduced.

## Select the operating mode

- **Reviewer triage:** Read [evidence-and-triage.md](references/evidence-and-triage.md).
  Use it for emails, QA reports, Plugin Check/PHPCS output, and alleged blockers.
- **Remediation or ownership split:** Also read
  [contract-safety.md](references/contract-safety.md) before changing public names,
  requests, storage, migrations, Free/Pro ownership, or companion contracts.
- **Release/readiness decision:** Read
  [release-gates.md](references/release-gates.md) and validate the exact package.
- **Audit deliverable:** Use
  [audit-report-template.md](references/audit-report-template.md) so severity,
  confidence, evidence, compatibility impact, and residual risk remain distinct.
- **Policy research or citation:** Recheck the live official pages routed from
  [official-sources.md](references/official-sources.md); policies and tooling change.

## Workflow

### 1. Freeze the evidence

- Preserve the reviewer message verbatim and distinguish human instructions from
  AI-marked analysis.
- Record the reviewed artifact identity. If unavailable, mark it `unknown`; do
  not pretend the current checkout is identical.
- Establish a baseline: default/released branch, candidate branch, and their
  behavioral and data-contract diff.
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

### 2. Build a finding ledger

For every reviewer category, record source, exact location, reachable entry
point, affected principal/data, reproducibility, policy basis, confidence, user
impact, and companion consumers. Use the classifications in the triage
reference. Keep severity separate from confidence.

Turn every confirmed example into a pattern-wide source scan. Do not stop at the
named file, but do not “fix similar-looking code” without proving the same
boundary and failure.

### 3. Trace end-to-end contracts

For each proposed change, inventory producers and consumers across PHP, source
JavaScript, generated bundles, templates, persisted content, AJAX/REST routes,
cron, WP-CLI, imports, and maintained companion products. Test previous/current
provider-consumer combinations where users can update components separately.

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

Pause for explicit authority before destructive migrations, user-data rewrites,
feature removal, broad public API changes, live production tests, commits,
pushes, version changes, SVN operations, or external communications.

### 5. Verify behavior, not wording

Use focused tests that fail on the baseline and pass on the candidate. Exercise
unauthorized and cross-owner cases as well as valid flows. For companion
ecosystems, execute the compatibility matrix from the contract reference.

Static checks are supporting evidence. Run the repository's real commands, PHP
lint, WPCS/PHPCS with warnings visible, Plugin Check in the correct mode, and
targeted source scans. Do not accept `phpcs -n`, ignored warnings, annotations,
or mocked tests as proof of an untested live behavior.

### 6. Gate the exact release package

Build using the real release procedure, inspect ZIP integrity and inventory,
extract it cleanly, and rerun release-scoped checks against that extracted tree.
Validate version/readme/SVN metadata, source/build availability, licensing,
remote services, clean activation/update/deactivation, WP_DEBUG output, and the
supported upgrade matrix. Remove temporary options, fixtures, proof pages,
logs, screenshots, injected transients, and test-only code.

### 7. Report without sugar-coating

Use one of these conclusions:

- `NOT READY` — one or more required code/package gates fail;
- `CODE READY; RELEASE GATES PENDING` — code findings are resolved, but manager,
  version, build, live, SVN, or communication work remains;
- `READY FOR SUBMISSION DECISION` — all available gates passed and only the
  Plugins Team's independent review remains.

List unexecuted checks and residual risks beside the conclusion. Never collapse
“no findings from this tool” into “no issues remain.”

## Completion standard

The work is complete only when the finding ledger is dispositioned, contract
changes are proven across supported states, the exact package is clean, all
temporary audit state is removed, and the report identifies both evidence and
limits. A reviewer reply should be concise and factual; it should not dump a
changelog or claim guaranteed acceptance.
