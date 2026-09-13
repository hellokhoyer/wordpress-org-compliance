# Audit Report Template

Use this structure. Omit empty sections; do not invent evidence.

## Executive decision

- **Decision:** `NOT READY` / `CODE READY; RELEASE GATES PENDING` /
  `READY FOR SUBMISSION DECISION`
- **Audit mode:** proactive / new / update / closed-plugin re-review /
  package-only
- **Candidate:** repository, branch, commit
- **Exact package:** path, SHA-256, size
- **Compared baseline:** released/default revision and version, or `none` for an
  initial submission
- **Confidence:** high / medium / low, with one-sentence reason
- **Acceptance caveat:** WordPress.org approval remains an independent Plugins
  Team decision.

## Scope and authority

- Plugin slug/main file/prefix/text domain
- Maintained companions/themes/clients checked
- Supported WordPress/PHP/site modes
- Reviewer/QA artifact identity, or `none`
- Authorized changes and explicitly excluded actions

## Reviewer and audit ledger

| ID | Claim/source | Evidence | Disposition | Severity | Confidence | Contract impact | Action/status |
| --- | --- | --- | --- | --- | --- | --- | --- |

For each confirmed item add:

- root cause;
- pattern-wide inventory;
- files and behavior changed;
- why the fix meets the cited official requirement;
- compatibility and data-risk analysis;
- focused baseline/candidate evidence;
- remaining live or package validation.

For false positives add the reachable-path analysis and why changing the code
would be neutral or harmful. Do not dismiss findings with opinion alone.

## Public and persisted contract matrix

| Contract | Previous provider | Current provider | Consumers | Mixed-version result | Migration/transition |
| --- | --- | --- | --- | --- | --- |

Explicitly list stable CPT/taxonomy/meta/option/table/role/content identifiers
that were preserved.

## Security boundary results

| Entry point | Public/private | Nonce | Capability | Ownership | Schema/validation | Output | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Verification evidence

- Static commands, tool/ruleset versions, warnings, and raw-output location
- Focused tests and baseline failure
- Clean install/update/deactivation/multisite/companion matrix results
- WP_DEBUG/server/browser log result
- Exact ZIP integrity, inventory, extracted-package scan, and installation result
- Temporary-state cleanup confirmation

Never say a test covers email, filesystem, database, browser, or network behavior
when those layers were mocked.

## Remaining risks and owners

| Risk/gate | Impact | Owner | Required action | Blocks submission? |
| --- | --- | --- | --- | --- |

Separate code blockers from manager-owned versioning, build, SVN, release
confirmation, source-link, and reviewer-reply tasks.

## Proposed reviewer reply (reviewer-driven work only)

Keep it concise:

> Thank you for the review. We addressed the reported categories and completed a
> pattern-wide review of the updated release package. The corrected version has
> been uploaded to the plugin SVN repository. [Add only a necessary clarification
> with one concrete example.] Please let us know if you need anything further.

Do not list every internal change unless the reviewer asks. Do not claim
guaranteed compliance or acceptance.
