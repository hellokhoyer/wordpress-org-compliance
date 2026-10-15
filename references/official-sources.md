# Official Source Routing

This file is a navigation baseline, not a dated certification. Recheck the live
pages during each audit because guidelines, WordPress Core, Plugin Check, and the
release process change.

Prefer WordPress.org, Developer.WordPress.org, Make.WordPress.org, WordPress Core
source/Trac, and the official `WordPress/*` GitHub repositories. Use third-party
articles only for context, never as the sole basis for a blocker.

## Directory policy and review

- Detailed Plugin Guidelines:
  https://developer.wordpress.org/plugins/wordpress-org/detailed-plugin-guidelines/
- Plugin Team common issues (explicitly non-exhaustive):
  https://developer.wordpress.org/plugins/wordpress-org/common-issues/
- Plugin Developer FAQ:
  https://developer.wordpress.org/plugins/wordpress-org/plugin-developer-faq/
- Planning, submitting, and maintaining plugins:
  https://developer.wordpress.org/plugins/wordpress-org/planning-submitting-and-maintaining-plugins/
- Block-specific guidelines, only for Block Directory submissions:
  https://developer.wordpress.org/plugins/wordpress-org/block-specific-plugin-guidelines/

## Security and APIs

- Security overview:
  https://developer.wordpress.org/apis/security/
- Nonces (not authorization):
  https://developer.wordpress.org/apis/security/nonces/
- Validating data:
  https://developer.wordpress.org/apis/security/data-validation/
- Sanitizing data:
  https://developer.wordpress.org/apis/security/sanitizing/
- Escaping data:
  https://developer.wordpress.org/apis/security/escaping/
- Roles and capabilities:
  https://developer.wordpress.org/plugins/users/roles-and-capabilities/
- REST routes and endpoints:
  https://developer.wordpress.org/rest-api/extending-the-rest-api/routes-and-endpoints/
- AJAX:
  https://developer.wordpress.org/plugins/javascript/ajax/
- HTTP API:
  https://developer.wordpress.org/plugins/http-api/
- Activation/deactivation hooks:
  https://developer.wordpress.org/plugins/plugin-basics/activation-deactivation-hooks/
- Uninstall methods:
  https://developer.wordpress.org/plugins/plugin-basics/uninstall-methods/

## Metadata, packaging, and release

- Plugin readme behavior:
  https://developer.wordpress.org/plugins/wordpress-org/how-your-readme-txt-works/
- Official readme validator:
  https://wordpress.org/plugins/developers/readme-validator/
- Header requirements:
  https://developer.wordpress.org/plugins/plugin-basics/header-requirements/
- Using WordPress.org SVN:
  https://developer.wordpress.org/plugins/wordpress-org/how-to-use-subversion/
- Release confirmation:
  https://developer.wordpress.org/plugins/wordpress-org/release-confirmation-emails/
- Plugin assets:
  https://developer.wordpress.org/plugins/wordpress-org/plugin-assets/

## Dependency currency and security

- Use each component's official release/support pages and registry metadata, not
  a search snippet, CDN filename or a pinned older source tag.
- npm registry and stable distribution tags:
  https://docs.npmjs.com/cli/using-npm/registry/
  https://docs.npmjs.com/adding-dist-tags-to-packages/
- Composer advisory auditing (separate from currency):
  https://getcomposer.org/doc/03-cli.md#audit
- npm advisory auditing (separate from currency):
  https://docs.npmjs.com/cli/commands/npm-audit/

Record current UTC retrieval time and retain the official response/page. A
reviewer's explicit stable-version instruction applies to that review; do not
invent a blanket policy that every non-latest supported library is automatically
insecure or noncompliant. Supported exceptions need evidence and authorization.

## Tooling and source truth

- Plugin Check project:
  https://github.com/WordPress/plugin-check
- Plugin Check CLI reference:
  https://github.com/WordPress/plugin-check/blob/trunk/docs/CLI.md
- WordPress Coding Standards:
  https://github.com/WordPress/WordPress-Coding-Standards
- WordPress Core development source:
  https://github.com/WordPress/wordpress-develop
- WordPress Core mirror:
  https://github.com/WordPress/WordPress

When behavior depends on an update hook, parser, REST controller, capability, or
other Core detail, inspect the target Core version's implementation or official
code reference rather than relying on memory.
