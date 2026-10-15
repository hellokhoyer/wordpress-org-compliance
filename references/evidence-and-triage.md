# Evidence and Finding Triage

Use this reference when translating reviewer emails, QA reports, scanner output,
or AI commentary into engineering decisions.

## Evidence hierarchy

Record the source and keep these levels distinct:

1. **Official requirement:** current WordPress.org guideline, Plugin Team common
   issue, or a direct human instruction in the reviewer email.
2. **Reproduced defect:** a reachable code path or test demonstrates the policy,
   security, compatibility, or functional failure on the reviewed artifact.
3. **Static finding:** Plugin Check, PHPCS/WPCS, dependency scanner, or a precise
   source query identifies a candidate that survives contextual review.
4. **Heuristic claim:** warning, approximate count, AI-marked reviewer comment,
   or QA conclusion without a reproducible path.
5. **Opinion/recommendation:** maintainability or style improvement that is not a
   submission requirement.

A human-reviewed email is authoritative about the category to resolve, but an
AI-marked explanation inside it can still misidentify the exact code behavior.
Treat the named example as a mandatory investigation lead; confirm the root
cause and audit the full pattern.

## Finding dispositions

Use exactly one primary disposition per item:

- `CONFIRMED POLICY VIOLATION`
- `CONFIRMED SECURITY DEFECT`
- `CONFIRMED FUNCTIONAL/COMPATIBILITY BLOCKER`
- `CONFIRMED PACKAGING/RELEASE BLOCKER`
- `NEEDS REVIEWER CLARIFICATION`
- `TOOL HEURISTIC — NO DEFECT PROVEN`
- `FALSE POSITIVE WITH EVIDENCE`
- `OPTIONAL QUALITY IMPROVEMENT`
- `OUTSIDE AUTHORIZED SCOPE`

Severity describes impact; confidence describes certainty. Do not make a
high-severity but low-confidence claim sound proven.

## Minimum evidence record

For every item capture:

- reviewed revision or ZIP SHA-256;
- source of the claim and whether it was AI-marked;
- exact file/line or package entry;
- registration/entry point and conditions required to reach it;
- data read or side effect performed;
- nonce, authentication, capability, ownership, validation, and escaping path;
- maintained consumers and persisted contracts affected by a fix;
- baseline reproduction and candidate validation;
- policy URL and date checked;
- final disposition, confidence, owner, and remaining action.

If the QA artifact identity is unknown, say so in the report. Do not bind its
line numbers or conclusions to a different checkout.

## Common reasoning traps

### Evidence coverage is separate from test success

A passing behavioral suite does not establish dependency currency, source/licence
completeness, current policy, readme validity or exact-package cleanliness. Keep
separate check statuses and raw evidence. Repeated audits cannot reuse an overall
pass simply because code, the model or the skill name is unchanged. Verify the
actually loaded skill path/revision and disclose stale installed copies.

### Scanner success is not a security proof

Static rules can miss an AJAX callback that verifies a nonce but lacks an
operation capability or object ownership check. Inspect reachable handlers and
negative cases even when Plugin Check is clean.

### Scanner matches are not automatic blockers

- A public filter/query can legitimately read sanitized GET data. Decide whether
  the request is intentionally public, sensitive, or state-changing before
  requiring a nonce or capability.
- A `tax_query` performance warning is a prompt to inspect query size, indexes,
  caching, and real usage—not proof of a directory violation.
- Direct use of a WordPress API is normal. Distinguish calling an API from
  directly bootstrapping `wp-load.php`, `wp-config.php`, or `wp-blog-header.php`.
  Conditional loading of an admin include may be appropriate only when the
  execution context does not already provide the required API and the API is
  used immediately.
- Binary download output must be authorized and correctly headed. Replacing
  byte output with HTML escaping can corrupt the file without improving safety.
- A namespaced class method or local variable is not a global collision merely
  because its basename has a short prefix.
- A no-op method is not a vulnerable mutation solely because a scanner sees a
  callback-shaped name.

### Parse runtime code before accepting syntax allegations

An unsupported-looking word in PHPDoc, a comment, a string or vendor/tool output
is not proof of a plugin parser failure. Inspect the exact ZIP's declaration;
run its files with the declared minimum PHP and load the actual activation/admin
path with WP_DEBUG. Preserve a false-positive claim and its reproduction rather
than changing correct runtime behavior or accurate annotations to silence it.

### Sanitization is not validation

- `wp_unslash()` only reverses request slashing.
- `json_decode()` only parses JSON.
- `map_deep()` sanitizes values when given a sanitizer; it does not declare
  allowed keys, required fields, types, relationships, or business invariants.
- Escaping at storage time is not a substitute for escaping at the final output
  context.

### Tool commands can conceal risk

- `php -l readme.txt` does not validate WordPress readme metadata.
- `phpcs -n` or an error-only mode hides warnings and cannot support a
  warning-clean claim.
- A source-tree scan does not prove the release ZIP inventory.
- A mocked regression proves only the modeled contract, not a live WordPress,
  database, email, filesystem, or browser flow.
- Counts without the exact command, ruleset, exclusions, revision, and output
  are not reproducible evidence.

### A broken harness is not a plugin defect

Distinguish plugin failures from Core/tool dependencies, an incomplete admin
bootstrap or invalid synthetic HTTP responses. Preserve the failed run, prove the
harness problem and rerun the corrected scenario. Do not weaken an assertion
merely to make it green. Missing/zero data is valid when the actual product
contract permits it; explicit transport/authentication/schema failures remain
separate errors.

### Fixes can be worse than findings

Reject these approaches unless independently justified:

- global search/replace of a short prefix;
- changing every capability to `manage_options`;
- adding public legacy aliases to silence broken companion consumers;
- deleting stored settings or content because their UI moved to an add-on;
- seeding migration flags to skip real upgrades;
- changing response envelopes without tracing shipped JavaScript;
- renaming template variables without tracing every include caller;
- suppressing a warning before documenting why it is a false positive.

## Pattern-wide review

For a confirmed reviewer category, search semantic equivalents, not just the
literal example. Examples:

- request security: all registrations, request producers, handlers, helpers,
  storage calls, and downloads;
- public prefix: declarations plus string registrations, browser globals,
  generated bundles, internal templates, persisted shortcode content, and
  companion callers;
- arbitrary code: authoring fields, imports, database reads, renderer allowlists,
  template output, and dormant execution paths;
- trialware: UI gates, processing gates, defaults, imports, templates, license
  checks, and complete Free-only user journeys;
- remote services: outbound requests, embeds, remote assets, cron/activation
  calls, consent storage, terms/privacy disclosure, and self-update code;
- lifecycle: activation, new-site, version gates, migrations, init hooks,
  deactivation, uninstall, and multisite/network paths.

Stop expanding only when the source pattern and maintained ecosystem have been
exhausted, not when the original line is fixed.
