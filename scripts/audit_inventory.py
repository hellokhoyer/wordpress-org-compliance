#!/usr/bin/env python3
"""Create a read-only WordPress.org plugin audit inventory.

This helper reports facts and review candidates. It intentionally does not
declare policy violations because reachability, authorization, data semantics,
and reviewer context require source-level analysis.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".inc",
    ".js",
    ".json",
    ".md",
    ".php",
    ".scss",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

FIRST_PARTY_SKIP_PARTS = {
    ".git",
    ".svn",
    "node_modules",
    "tests",
    "test",
    "vendor",
}

LOCAL_ONLY_NAMES = {
    ".DS_Store",
    ".editorconfig",
    ".gitignore",
    ".phpcs.xml",
    ".phpunit.result.cache",
    "AGENTS.md",
    "audit_report.md",
    "phpcs.xml",
    "phpcs.xml.dist",
    "phpunit.xml",
    "phpunit.xml.dist",
    "Thumbs.db",
}

LOCAL_ONLY_PARTS = {
    ".git",
    ".github",
    ".idea",
    ".svn",
    ".vscode",
    "coverage",
    "node_modules",
    "screenshots",
    "tasks",
    "tests",
}


@dataclass(frozen=True)
class Candidate:
    category: str
    path: str
    line: int
    value: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inventory a WordPress plugin and optional release ZIP."
    )
    parser.add_argument("plugin_root", type=Path)
    parser.add_argument("--slug", help="Expected WordPress.org plugin slug.")
    parser.add_argument(
        "--prefix",
        help="Public runtime prefix established from this project's declarations/contracts.",
    )
    parser.add_argument("--package", type=Path, help="Exact release ZIP to inspect.")
    parser.add_argument("--no-git", action="store_true", help="Skip Git inspection for archive-only/restricted audits.")
    parser.add_argument(
        "--max-matches",
        type=int,
        default=30,
        help="Maximum entries shown per candidate category (default: 30).",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_git(root: Path, *args: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if 0 == result.returncode else None


def iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file() and ".git" not in path.relative_to(root).parts:
            yield path


def is_first_party(path: Path, root: Path) -> bool:
    parts = set(path.relative_to(root).parts[:-1])
    return not bool(parts & FIRST_PARTY_SKIP_PARTS)


def find_main_file(root: Path, slug: str) -> Optional[Path]:
    preferred = root / f"{slug}.php"
    candidates = [preferred] if preferred.is_file() else []
    candidates.extend(path for path in sorted(root.glob("*.php")) if path != preferred)

    for path in candidates:
        source = read_text(path)[:8192]
        if re.search(r"^[ \t/*#@]*Plugin Name:\s*\S", source, re.MULTILINE | re.IGNORECASE):
            return path
    return None


def parse_header(source: str, name: str) -> str:
    match = re.search(
        rf"^[ \t/*#@]*{re.escape(name)}:\s*(.+?)\s*$",
        source[:8192],
        re.MULTILINE | re.IGNORECASE,
    )
    return match.group(1).strip() if match else ""


def parse_readme_header(source: str, name: str) -> str:
    match = re.search(
        rf"^{re.escape(name)}:\s*(.+?)\s*$",
        source,
        re.MULTILINE | re.IGNORECASE,
    )
    return match.group(1).strip() if match else ""


def line_number(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1


def add_regex_candidates(
    candidates: List[Candidate],
    category: str,
    path: Path,
    root: Path,
    source: str,
    pattern: str,
    flags: int = 0,
    group: int = 0,
) -> None:
    relative = path.relative_to(root).as_posix()
    for match in re.finditer(pattern, source, flags):
        value = " ".join(match.group(group).strip().split())
        candidates.append(
            Candidate(category, relative, line_number(source, match.start()), value[:240])
        )


def prefix_matches(value: str, prefix: str) -> bool:
    canonical = re.sub(r"[^a-z0-9]", "", prefix.lower())
    candidate = re.sub(r"[^a-z0-9]", "", value.lower())
    return bool(canonical) and candidate.startswith(canonical)


def scan_source(root: Path, prefix: str) -> Tuple[List[Candidate], Dict[str, int]]:
    candidates: List[Candidate] = []
    counters: Counter[str] = Counter()

    for path in iter_files(root):
        counters["all_files"] += 1
        suffix = path.suffix.lower()
        counters[f"extension:{suffix or '(none)'}"] += 1

        if suffix not in TEXT_SUFFIXES or not is_first_party(path, root):
            continue

        source = read_text(path)
        if not source:
            continue

        if ".php" == suffix:
            counters["first_party_php"] += 1
            add_regex_candidates(
                candidates,
                "raw request boundary",
                path,
                root,
                source,
                r"\$_(?:POST|GET|REQUEST|FILES|COOKIE|SERVER)\b",
            )
            add_regex_candidates(
                candidates,
                "direct WordPress bootstrap include",
                path,
                root,
                source,
                r"(?:include|include_once|require|require_once)\s*\(?[^;\n]*(?:wp-load|wp-config|wp-blog-header)\.php[^;\n]*",
                re.IGNORECASE,
            )
            add_regex_candidates(
                candidates,
                "direct WordPress library include",
                path,
                root,
                source,
                r"(?:include|include_once|require|require_once)\s*\(?[^;\n]*(?:wp-admin/includes|wp-includes)/[^;\n]+",
                re.IGNORECASE,
            )
            add_regex_candidates(
                candidates,
                "dynamic execution candidate",
                path,
                root,
                source,
                r"\b(?:eval|create_function|shell_exec|passthru|system|exec)\s*\(",
                re.IGNORECASE,
            )
            add_regex_candidates(
                candidates,
                "PHP debug output candidate",
                path,
                root,
                source,
                r"\b(?:var_dump|print_r|error_log)\s*\(",
                re.IGNORECASE,
            )
            add_regex_candidates(
                candidates,
                "PHP short tag candidate",
                path,
                root,
                source,
                r"<\?(?!php\b|=)",
                re.IGNORECASE,
            )
            add_regex_candidates(
                candidates,
                "rewrite flush call",
                path,
                root,
                source,
                r"\bflush_rewrite_rules\s*\([^;]*",
                re.IGNORECASE,
            )
            add_regex_candidates(
                candidates,
                "remote request candidate",
                path,
                root,
                source,
                r"\bwp_(?:safe_)?remote_(?:get|post|request|head)\s*\([^;]+",
                re.IGNORECASE,
            )
            add_regex_candidates(
                candidates,
                "remote executable asset candidate",
                path,
                root,
                source,
                r"\bwp_(?:register|enqueue)_(?:script|style)\s*\([^;]+https?://[^;]+",
                re.IGNORECASE | re.DOTALL,
            )

            for match in re.finditer(
                r"['\"]wp_ajax_(?:nopriv_)?([A-Za-z0-9_-]+)['\"]", source
            ):
                value = match.group(1)
                if prefix and not prefix_matches(value, prefix):
                    candidates.append(
                        Candidate(
                            "public AJAX name outside expected prefix",
                            path.relative_to(root).as_posix(),
                            line_number(source, match.start()),
                            value,
                        )
                    )

            for match in re.finditer(
                r"add_shortcode\s*\(\s*['\"]([^'\"]+)['\"]", source
            ):
                value = match.group(1)
                if prefix and not prefix_matches(value, prefix):
                    candidates.append(
                        Candidate(
                            "public shortcode outside expected prefix",
                            path.relative_to(root).as_posix(),
                            line_number(source, match.start()),
                            value,
                        )
                    )

            for match in re.finditer(
                r"register_rest_route\s*\(\s*['\"]([^'\"]+)['\"]", source
            ):
                value = match.group(1).split("/", 1)[0]
                if prefix and not prefix_matches(value, prefix):
                    candidates.append(
                        Candidate(
                            "REST namespace outside expected prefix",
                            path.relative_to(root).as_posix(),
                            line_number(source, match.start()),
                            value,
                        )
                    )

            has_namespace = bool(
                re.search(r"^\s*namespace\s+[A-Za-z_\\]", source, re.MULTILINE)
            )
            if prefix and not has_namespace:
                public_patterns = (
                    ("global function outside expected prefix", r"^\s*function\s+([A-Za-z_]\w*)\s*\("),
                    ("global class outside expected prefix", r"^\s*(?:final\s+|abstract\s+)?class\s+([A-Za-z_]\w*)\b"),
                    ("global constant outside expected prefix", r"\bdefine\s*\(\s*['\"]([A-Za-z_]\w*)['\"]"),
                )
                for category, pattern in public_patterns:
                    for match in re.finditer(pattern, source, re.MULTILINE):
                        value = match.group(1)
                        if not prefix_matches(value, prefix):
                            candidates.append(
                                Candidate(
                                    category,
                                    path.relative_to(root).as_posix(),
                                    line_number(source, match.start()),
                                    value,
                                )
                            )

            for match in re.finditer(
                r"\b(?:get|add|update|delete)_option\s*\(\s*['\"]([^'\"]+)['\"]",
                source,
            ):
                value = match.group(1)
                if prefix and not prefix_matches(value, prefix):
                    candidates.append(
                        Candidate(
                            "persisted option key outside expected prefix — do not rename automatically",
                            path.relative_to(root).as_posix(),
                            line_number(source, match.start()),
                            value,
                        )
                    )

        elif ".js" == suffix:
            counters["first_party_js"] += 1
            add_regex_candidates(
                candidates,
                "JavaScript debug candidate",
                path,
                root,
                source,
                r"\b(?:console\.(?:log|debug)|debugger\s*;)",
                re.IGNORECASE,
            )

    return candidates, dict(counters)


def package_inventory(package: Path, slug: str) -> Dict[str, object]:
    result: Dict[str, object] = {
        "path": str(package),
        "exists": package.is_file(),
    }
    if not package.is_file():
        return result

    result["sha256"] = sha256(package)
    result["size"] = package.stat().st_size
    try:
        with zipfile.ZipFile(package) as archive:
            entries = archive.infolist()
            result["entry_count"] = len(entries)
            result["integrity"] = "pass" if archive.testzip() is None else "fail"
            names = [entry.filename for entry in entries]
            main_candidates = []
            for entry in entries:
                parts = PurePosixPath(entry.filename).parts
                if len(parts) != 2 or parts[0] != slug or PurePosixPath(entry.filename).suffix.lower() != ".php":
                    continue
                with archive.open(entry) as stream:
                    header = stream.read(8192).decode("utf-8", errors="replace")
                if re.search(r"^[ \t/*#@]*Plugin Name:\s*\S", header, re.MULTILINE | re.IGNORECASE):
                    main_candidates.append(entry.filename)
    except (OSError, zipfile.BadZipFile) as error:
        result["integrity"] = f"fail: {error}"
        return result

    roots = sorted(
        {
            PurePosixPath(name).parts[0]
            for name in names
            if PurePosixPath(name).parts
        }
    )
    unsafe = []
    local_only = []
    nested_archives = []

    for name in names:
        item = PurePosixPath(name)
        parts = item.parts
        if name.startswith(("/", "\\")) or ".." in parts:
            unsafe.append(name)
        if item.name in LOCAL_ONLY_NAMES or set(parts) & LOCAL_ONLY_PARTS:
            local_only.append(name)
        if item.suffix.lower() in {".zip", ".tar", ".gz", ".tgz"}:
            nested_archives.append(name)

    result["top_level"] = roots
    result["main_file_candidates"] = sorted(main_candidates)
    result["main_file_present"] = bool(main_candidates)
    result["readme_present"] = f"{slug}/readme.txt" in names
    result["unsafe_entries"] = unsafe
    result["local_only_candidates"] = local_only
    result["nested_archives"] = nested_archives
    return result


def print_value(label: str, value: object) -> None:
    text = str(value) if value not in (None, "") else "unknown"
    print(f"- **{label}:** {text}")


def print_package(data: Dict[str, object]) -> None:
    print("\n## Exact package")
    print_value("Path", data.get("path"))
    print_value("Exists", data.get("exists"))
    if not data.get("exists"):
        return
    for label, key in (
        ("SHA-256", "sha256"),
        ("Size (bytes)", "size"),
        ("ZIP integrity", "integrity"),
        ("Entry count", "entry_count"),
        ("Top-level entries", "top_level"),
        ("Header-bearing main file candidates", "main_file_candidates"),
        ("Main file present", "main_file_present"),
        ("Readme present", "readme_present"),
    ):
        print_value(label, data.get(key))

    for label, key in (
        ("Unsafe path entries", "unsafe_entries"),
        ("Local/development file candidates", "local_only_candidates"),
        ("Nested archives", "nested_archives"),
    ):
        values = data.get(key) or []
        print(f"\n### {label} ({len(values)})")
        for value in list(values)[:50]:
            print(f"- `{value}`")
        if 50 < len(values):
            print(f"- … {len(values) - 50} more")


def print_candidates(candidates: Sequence[Candidate], maximum: int) -> None:
    grouped: Dict[str, List[Candidate]] = defaultdict(list)
    for candidate in candidates:
        grouped[candidate.category].append(candidate)

    print("\n## Source candidates")
    if not grouped:
        print("\nNo candidates matched this helper's limited patterns.")
        return

    for category in sorted(grouped):
        matches = grouped[category]
        print(f"\n### {category} ({len(matches)})")
        for match in matches[:maximum]:
            print(f"- `{match.path}:{match.line}` — `{match.value}`")
        if maximum < len(matches):
            print(f"- … {len(matches) - maximum} more")


def main() -> int:
    args = parse_args()
    root = args.plugin_root.expanduser().resolve()
    if not root.is_dir():
        print(f"error: plugin root is not a directory: {root}", file=sys.stderr)
        return 2

    slug = args.slug or root.name
    prefix = args.prefix or slug.replace("-", "_")
    main_file = find_main_file(root, slug)
    main_source = read_text(main_file) if main_file else ""
    readme = root / "readme.txt"
    readme_source = read_text(readme)

    minified_assets = [
        path
        for path in iter_files(root)
        if path.name.endswith((".min.js", ".min.css"))
    ]
    source_maps = [path for path in iter_files(root) if ".map" == path.suffix.lower()]

    version = parse_header(main_source, "Version")
    stable_tag = parse_readme_header(readme_source, "Stable tag")
    commit = run_git(root, "rev-parse", "HEAD") if not args.no_git else None
    branch = run_git(root, "branch", "--show-current") if not args.no_git else None
    status = run_git(root, "status", "--porcelain") if not args.no_git else None

    candidates, counters = scan_source(root, prefix)

    print("# WordPress.org Plugin Audit Inventory")
    print()
    print(
        "> This is a read-only candidate inventory, not a compliance verdict. "
        "Inspect reachability, policy context, data semantics, and all consumers."
    )
    print(
        "> First-party source patterns skip vendored dependencies and test "
        "fixtures. Run the official tools against the complete extracted package."
    )
    print("\n## Identity")
    print_value("Plugin root", root)
    print_value("Slug", slug)
    print_value("Prefix used for candidate scan", prefix)
    print_value("Prefix basis", "supplied --prefix; verify against project declarations" if args.prefix else "slug-derived heuristic; public contract is unverified")
    print_value("Main file", main_file.relative_to(root) if main_file else "not found")
    print_value("Plugin name", parse_header(main_source, "Plugin Name"))
    print_value("Version", version)
    print_value("Stable Tag", stable_tag)
    print_value("Version/Stable Tag match", bool(version and version == stable_tag))
    print_value("Text Domain", parse_header(main_source, "Text Domain"))
    print_value("Plugin license", parse_header(main_source, "License"))
    print_value("Readme license", parse_readme_header(readme_source, "License"))
    print_value("License URI", parse_header(main_source, "License URI"))
    print_value("Requires at least", parse_header(main_source, "Requires at least"))
    print_value("Requires PHP", parse_header(main_source, "Requires PHP"))
    print_value("Readme Tested up to", parse_readme_header(readme_source, "Tested up to"))
    print_value("Git inspection", "skipped by request" if args.no_git else "attempted; unavailable values remain unknown")
    print_value("Git branch", branch)
    print_value("Git commit", commit)
    print_value("Dirty paths", len(status.splitlines()) if status is not None else None)
    print_value("Files", counters.get("all_files", 0))
    print_value("First-party PHP files", counters.get("first_party_php", 0))
    print_value("First-party JavaScript files", counters.get("first_party_js", 0))

    print("\n## Build/source inventory")
    print_value("composer.json", (root / "composer.json").is_file())
    print_value("composer.lock", (root / "composer.lock").is_file())
    print_value("vendor directory", (root / "vendor").is_dir())
    print_value("package.json", (root / "package.json").is_file())
    print_value("package lock", any((root / name).is_file() for name in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock")))
    print_value("Minified JS/CSS assets", len(minified_assets))
    print_value("Source maps", len(source_maps))
    print_value(
        "Readme mentions source/build",
        bool(re.search(r"\b(?:source code|source repository|build tools?|npm|composer|webpack|vite|gulp|grunt)\b", readme_source, re.IGNORECASE)),
    )

    if args.package:
        print_package(package_inventory(args.package.expanduser().resolve(), slug))
    else:
        print("\n## Exact package")
        print("\nNo package supplied. Release-package gates are unproven.")

    print_candidates(candidates, max(1, args.max_matches))

    print("\n## Required next step")
    print()
    print(
        "Classify each relevant candidate using the skill's evidence ledger. "
        "Do not modify code merely to reduce this inventory."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
