# Contract-Safe Remediation

Read this before renaming, deleting, relocating, or splitting released behavior.

## Contract inventory

Classify every affected identifier before editing:

| Contract | Examples | Default treatment |
| --- | --- | --- |
| Public runtime | global functions/classes/constants, hooks, AJAX actions, REST namespaces, shortcodes, script handles, browser globals, admin slugs | Use a unique prefix; migrate every producer and consumer atomically. |
| Persisted data | CPT/taxonomy slugs, table/column names, options, meta, roles/capabilities, saved shortcodes, widget/builder content | Preserve unless an authorized, versioned migration exists. |
| Extension | actions/filters and callback signatures | Inventory maintained and third-party consumers; preserve arguments or publish a transition. |
| Template include | caller-provided local variables and return/output behavior | Treat local names as an include contract, not public globals. |
| Client/server | localized objects, nonces, actions, request fields, response envelopes, generated bundles | Change source and built assets together; test the real UI. |
| Distribution | plugin slug/main file, text domain, asset paths, Composer autoload paths | Preserve unless release strategy explicitly changes them. |

The same string can represent more than one contract. Never rename by spelling
alone.

## Provider-consumer matrix

For each shared change, test or explicitly reject these states:

| Provider | Consumer | Required result |
| --- | --- | --- |
| previous | previous | released baseline still understood |
| current | current | intended new behavior works |
| current | previous | safe staggered update or explicit coordinated-release block |
| previous | current | safe staggered update or explicit coordinated-release block |
| current | absent/deactivated | base plugin remains complete and non-fatal |
| current | reactivated | saved data and hooks recover without duplication |

Also cover single-site/network activation, imported/restored legacy content after
a migration marker, repeated migrations, and partially migrated states when
those conditions are credible.

If neither mixed-version direction is safe, do not invent compatibility. Require
a coordinated maintenance window, a reviewed external-consumer transition, and
a backup/restore path.

## Prefix remediation

- Prefix collision-prone public runtime identifiers with a distinctive string of
  at least four characters, following current Plugin Team guidance.
- Do not rename local variables or namespaced class methods solely for prefix
  compliance.
- Do not rename stable stored keys/slugs as collateral cleanup.
- Treat a callback migration atomically: declaration, `function_exists()` guard,
  registration string, direct callers, and generated client action must agree.
- Treat a shortcode migration as provider plus saved content: registration,
  internal `do_shortcode()` calls, demo/import content, widgets/builders, options,
  and a rerunnable migration for content imported after the first marker.
- Treat browser globals and script handles as provider-consumer contracts. A
  narrow read-only fallback belongs in the external consumer when justified;
  the directory plugin should not republish a prohibited alias.

Use token/context-aware edits. Preview cross-repository changes outside source
trees, diff them, lint them, and apply only the verified file set.

## Request and API remediation

Review the full round trip:

1. UI/link/form generates the action-specific nonce and only intended fields.
2. Client source and committed bundle send the same action and field names.
3. Handler checks nonce where applicable.
4. Handler checks the operation capability.
5. Handler checks ownership/record scope independently.
6. Boundary unslashes once, validates shape/type/allowlist, sanitizes values, and
   discards undeclared fields.
7. Helpers receive only the validated payload.
8. Storage preserves intended data semantics.
9. Response envelope matches all clients.
10. Output is escaped for HTML, attribute, URL, JavaScript, CSS, or raw-byte
    context at the final boundary.

Public search/price/availability reads may deliberately be anonymous. Do not add
an admin capability to public functionality. Still validate every parameter and
keep form, sort link, pagination, related link, and AJAX redirect producers in
sync with the parser's nonce contract when one is used.

## Free/add-on ownership splits

The directory plugin must be complete without the commercial add-on. A safe
split requires all of the following:

- Free-owned UI has a working Free-owned processing and persistence path.
- Add-on-only code, not merely its UI, lives outside the directory package.
- Free does not ship locked local implementations, empty premium tabs, disabled
  controls, or license checks that unlock bundled behavior.
- Removing a premium gate cannot leave legacy premium metadata selecting an
  unsupported mode and rendering a blank/non-bookable Free screen. Resolve a
  complete Free default first; let the add-on extend it through neutral hooks.
- Existing premium metadata remains inert but preserved while the add-on is
  absent, unless explicit deletion authority exists.
- Settings, imports/exports, templates, pricing, checkout, order data, emails,
  and API surfaces agree on ownership.
- Deactivating the add-on returns to a safe Free path without deleting data.

Do not describe moving code to the existing commercial add-on as creating a new
product. Keep package ownership and product identity separate.

## Migrations and lifecycle

- Installation, table setup, page creation, and rewrite flushing belong in
  activation/new-site hooks or explicit version gates, not normal `init` work.
- Data-only migrations normally do not need rewrite flushing.
- Deactivation should stop runtime behavior, not permanently delete user content
  or settings. Explicit uninstall is the appropriate place for authorized
  permanent cleanup.
- Migrations must be idempotent and versioned. Re-running cannot duplicate or
  corrupt data.
- Distinguish source and destination value semantics before renaming dynamic
  option keys. Similar suffixes do not prove equivalent meaning.
- Write/copy the canonical value, validate it against authoritative records, and
  only then remove a legacy key when deletion is authorized.
- Define behavior when both legacy and canonical values exist, when the marker
  exists but legacy data is imported later, and when a downgrade is attempted.
- A code-embedded migration may remain while supported installations still need
  it. Removal is a product-support decision, not an aesthetic cleanup.

## Direct WordPress files and APIs

Using WordPress APIs is standard. Directly bootstrapping core loading files such
as `wp-load.php`, `wp-config.php`, or `wp-blog-header.php` from plugin files is
not. Before removing an admin include such as `wp-admin/includes/file.php`, trace
every execution entry point: some frontend or custom-request contexts may need a
conditional include before calling the API. Keep only the narrow include that
is necessary, check function availability, and use the function immediately.

## Change approval boundary

Obtain explicit product/data-owner approval before:

- deleting or rewriting customer data;
- changing public APIs with unknown external consumers;
- removing a user-visible workflow rather than relocating ownership;
- requiring an atomic upgrade with business impact;
- replacing an embedded migration with a separate migrator;
- narrowing legitimate custom-role/vendor/manager access;
- releasing, publishing, or communicating externally.

When authority is absent, report the blocker and safe alternatives instead of
assuming consent.
