# Exact-Package Release Gates

Use this reference for a submission or re-review readiness decision. For full
readiness, initialize and validate the [evidence ledger](evidence-ledger.md).
Each applicable gate needs artifact-bound evidence and an explicit status.
Unknown/unexecuted technical checks cannot be reported as release-manager tasks.

## Gate 1: Identity and scope

- Record repository remote, branch, commit, dirty status, plugin slug, main file,
  version, Stable Tag, text domain, intended prefix, and submission mode.
- Record the previous public release and maintained companions, or evidence that
  none exist. First submission is not an upgrade from an internal Git snapshot.
- Bind every QA/reviewer claim to a revision or package hash. Mark unknowns.
- Compare candidate behavior and stored-data mutations with the released/default
  baseline, not merely the previous local commit.

## Gate 2: Reviewer ledger

- Every explicit reviewer category has a pattern-wide search and disposition.
- Every AI-marked example is verified in context.
- Confirmed findings have root-cause fixes and focused regressions.
- False positives have concise evidence; they are not silenced merely to improve
  a count.
- New findings discovered during remediation are recorded rather than hidden.

## Gate 3: Security and runtime contracts

- Nonce, capability, ownership, input schema, and late escaping are independently
  reviewed on private or state-changing requests.
- Public requests are intentionally public and strictly validated.
- REST routes have explicit permission callbacks with correct record scope.
- Uploads use WordPress APIs, MIME/extension controls, record authorization, and
  safe destinations. Downloads verify both request intent and access to the
  requested file/record.
- SQL uses prepared values; dynamic identifiers are allowlisted. Query warnings
  are evaluated for real cardinality and performance rather than auto-suppressed.
- Arbitrary PHP/JS/CSS/embed execution is absent unless the plugin's approved
  purpose and policy genuinely permit it.
- Activation is clean and bounded; migrations are gated and idempotent;
  deactivation is non-destructive; uninstall behavior is explicit.

## Gate 4: Policy, product, and dependencies

- Every feature in the directory package functions without a license, trial,
  artificial quota, or locked bundled implementation.
- Commercial code is owned by an external add-on or genuine documented service;
  Free remains end-to-end functional without it.
- Outbound services, data sent, circumstances, terms, and privacy links are
  documented; consent is obtained where required.
- No external self-update or remotely loaded executable code remains.
- Inventory all distributed third-party code/assets, including copied/minified
  bundles and fonts with no lockfile. Vendor exclusions in a first-party scanner
  do not remove this obligation.
- Verify licences, source/build integrity, currency/support and advisories as
  separate evidence checks. Fetch current official stable metadata; retain the
  retrieval time, source response and exact bundled file hashes. Never equate
  authentic/compatible/advisory-free with current.
- Resolve outdated/deprecated/unsupported copies or disclose an evidenced,
  supported-version exception. A network/tool failure is UNVERIFIED. Do not
  silently skip an ecosystem that the npm helper cannot check.
- WordPress-bundled libraries are consumed through Core handles/APIs rather than
  duplicated.
- Minified/generated files have public, maintained corresponding source and build
  instructions. Composer runtime implies a complete `composer.json` and an
  explainable production dependency set.

## Gate 5: Static and focused verification

Prefer project-defined commands. Record tool versions, rulesets, exclusions, and
raw outputs.

Minimum evidence generally includes:

```bash
php -l path/to/changed.php
phpcs --standard=WordPress path/to/changed.php
wp plugin check plugin-slug --mode=new --format=csv
```

Select `new` for first submission and the applicable `update` mode for an update.
Adapt to installed tooling after checking `wp help plugin check` and
`wp plugin list-checks`; do not assume options across versions. Run warnings, not
only errors. An ignore/suppression is acceptable only for a proven false
positive, narrow to the exact line/rule, and documented with the visible control
path.

Run Plugin Review PHPCS against the extracted ZIP as well as the project's WPCS
ruleset. Include a candidate scan with annotations disabled; retain both raw and
source-dispositioned counts. An unresolved warning is not a clean scan, and a
proven false positive is not automatically a code defect.

Focused regressions for a confirmed fix must reproduce the baseline defect and
pass on the candidate. Proactive acceptance tests need no failing predecessor.
Include negative authorization, malformed data, repeated
execution, and legitimate custom-role/owner cases where applicable.

## Gate 6: Live acceptance matrix

On a disposable/approved WordPress environment with `WP_DEBUG` enabled and logs
cleared before the run, exercise relevant states:

- clean install and activation on declared minimum PHP and supported modern PHP,
  including actual admin initialization/class loading;
- update from the previous released version with representative real data;
- repeat request/activation/migration;
- deactivation and reactivation;
- uninstall only when explicit cleanup behavior is part of the product;
- Free/base plugin alone;
- current base plus current companions;
- both mixed previous/current provider-consumer directions, or a documented
  coordinated-release constraint;
- supported custom roles, ownership boundaries, and unauthorized users;
- single site and multisite/network activation when supported;
- source JavaScript and generated production bundles on their owning screens;
- no plugin PHP warnings/notices/fatals and no new relevant browser-console or
  server-log errors.

Do not call a smoke test deep QA unless it exercises every touched contract and
the riskiest legacy state. A screenshot proves a rendered state only; it does not
prove the unobserved update path.

## Gate 7: Build the exact distributable

Use the same command or export rules as release management. Then:

1. Compute SHA-256 and store it with the report.
2. Verify ZIP integrity and one correct top-level slug directory.
3. Reject path traversal, absolute entries, symlinks when not intentionally
   supported, nested ZIPs, editor files, OS metadata, debug logs, audit reports,
   test fixtures, screenshots/proof pages, local agent instructions, and unused
   dependency trees.
4. Confirm the main file is `<slug>/<slug>.php` and readme is present.
5. Extract to a clean temporary directory.
6. Run Plugin Check/PHPCS and source scans against the extracted package, not the
   repository.
7. Compare package inventory to the intended manifest/export rules.
8. Install that exact ZIP and repeat the critical live acceptance paths.

Source maps are not automatically forbidden and tests are not automatically a
security defect, but unneeded development material can trigger review concerns.
Classify why every non-runtime file ships.

## Gate 8: Metadata and WordPress.org release

- Main header and readme declare consistent plugin identity, license, minimums,
  version, and text domain. Follow current guidance on which headers belong in
  the main file versus readme.
- Stable Tag, main plugin Version and changelog agree. Check Upgrade Notice and
  SVN tag when applicable; neither an earlier version nor an existing SVN repo
  should be invented for a first submission.
- Validate `readme.txt` with the official validator; PHP lint is irrelevant.
- Verify all public source, service, Terms, and Privacy links are reachable.
- After approval, when SVN deployment is in scope and authorized, trunk and the
  new tag must contain the approved release; do not upload a ZIP to SVN. Before
  approval submit/update the ZIP through the existing submission page.
- Release confirmation and reviewer reply are manager/committer actions unless
  explicitly delegated.

An Upgrade Notice is delivered only when WordPress receives a newer update
response containing its metadata. Installing the same version cannot prove that
notice. A controlled Core render can test the hook, but final production proof
requires the actual older-to-newer update offer.

## Gate 9: Audit cleanup

Before declaring readiness, verify:

- working trees contain no unintended changes;
- temporary database options/transients/users/content are removed or restored;
- injected update responses and filters are absent;
- proof HTML, screenshots, ZIPs, logs, fixtures, and temp directories are outside
  the distributable or removed;
- test plugins and debug configuration are restored to the agreed state;
- no secrets, local paths, private URLs, or credentials appear in source/package;
- maintained companion repositories are checked independently.

## Readiness language

Use `READY FOR SUBMISSION DECISION` only when Gates 1–9 are evidenced for the
exact candidate package, with justified non-applicability where appropriate.
This still does not guarantee acceptance because the
Plugins Team performs an independent full review and may identify additional
issues.

Use `INCOMPLETE AUDIT; READINESS UNVERIFIED` when technical evidence is missing.
A build, exact-package test, dependency lookup or required live acceptance check
is technical work, not a manager-action exception. Report optional live-service
recommendations separately from actual required checks; simulations prove only
the modeled contract.

Use `CODE READY; RELEASE GATES PENDING` only after all applicable technical checks
close and only owner upload/approval/SVN/reply actions remain. Limited scope
uses `LIMITED REVIEW; NO FULL READINESS DECISION`. The validator must support the
conclusion; no test count, automated submission-scan Pass, or tool exit code can
stand in for the complete evidence matrix.
