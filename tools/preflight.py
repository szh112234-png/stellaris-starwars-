#!/usr/bin/env python3
"""Static preflight checks for the FOC Stellaris mod repository.

The checker is intentionally conservative: it targets high-confidence repository problems
without trying to fully parse Clausewitz script.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_EXTS = {".txt", ".mod", ".gui", ".gfx", ".asset", ".yml", ".yaml", ".md", ".py"}
SKIP_DIRS = {".git", "__pycache__"}
EVENT_ID_RE = re.compile(r"^\s*id\s*=\s*([A-Za-z0-9_.-]+)\s*$")
LOC_KEY_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+):\d*\s+")
TOP_DEF_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*=\s*\{")


def iter_text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTS:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def strip_comment(line: str) -> str:
    out = []
    quoted = False
    escaped = False
    for ch in line:
        if escaped:
            out.append(ch)
            escaped = False
            continue
        if ch == "\\":
            out.append(ch)
            escaped = True
            continue
        if ch == '"':
            quoted = not quoted
            out.append(ch)
            continue
        if ch == "#" and not quoted:
            break
        out.append(ch)
    return "".join(out)


def brace_delta(text: str) -> int:
    quoted = False
    escaped = False
    delta = 0
    for ch in text:
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == '"':
            quoted = not quoted
            continue
        if quoted:
            continue
        if ch == "{":
            delta += 1
        elif ch == "}":
            delta -= 1
    return delta


def read_utf8(path: Path, findings: list[str]) -> str | None:
    data = path.read_bytes()
    rel = path.relative_to(ROOT)
    is_loc = path.suffix.lower() == ".yml" and "localisation" in path.parts
    has_bom = data.startswith(b"\xef\xbb\xbf")
    if is_loc and not has_bom:
        findings.append(f"ERROR encoding: localisation file lacks UTF-8 BOM: {rel}")
    if not is_loc and has_bom:
        findings.append(f"ERROR encoding: ordinary text file has UTF-8 BOM: {rel}")
    try:
        return data.decode("utf-8-sig" if has_bom else "utf-8")
    except UnicodeDecodeError as exc:
        findings.append(f"ERROR encoding: invalid UTF-8 in {rel}: {exc}")
        return None


def check_braces(path: Path, text: str, findings: list[str]):
    depth = 0
    rel = path.relative_to(ROOT)
    for lineno, raw in enumerate(text.splitlines(), 1):
        depth += brace_delta(strip_comment(raw))
        if depth < 0:
            findings.append(f"ERROR braces: unexpected closing brace at {rel}:{lineno}")
            return
    if depth != 0:
        findings.append(f"ERROR braces: unbalanced braces in {rel} (net {depth:+d})")


def collect_event_ids(path: Path, text: str, event_ids: dict[str, list[str]]):
    if "events" not in path.parts:
        return
    rel = path.relative_to(ROOT)
    for lineno, line in enumerate(text.splitlines(), 1):
        m = EVENT_ID_RE.match(strip_comment(line))
        if m:
            event_ids[m.group(1)].append(f"{rel}:{lineno}")


def check_loc_duplicates(path: Path, text: str, findings: list[str]):
    if path.suffix.lower() != ".yml" or "localisation" not in path.parts:
        return
    rel = path.relative_to(ROOT)
    seen: dict[str, int] = {}
    for lineno, line in enumerate(text.splitlines(), 1):
        if lineno == 1 and line.lstrip().startswith("l_"):
            continue
        m = LOC_KEY_RE.match(line)
        if not m:
            continue
        key = m.group(1)
        if key in seen:
            findings.append(
                f"WARNING duplicate localisation key {key} in {rel}: lines {seen[key]} and {lineno}"
            )
        else:
            seen[key] = lineno


def parse_scripted_effects(text: str):
    effects: dict[str, list[str]] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        clean = strip_comment(lines[i])
        m = TOP_DEF_RE.match(clean)
        if not m:
            i += 1
            continue
        name = m.group(1)
        depth = brace_delta(clean)
        block = []  # Exclude the definition header itself from call detection.
        j = i + 1
        while j < len(lines) and depth > 0:
            c = strip_comment(lines[j])
            block.append(c)
            depth += brace_delta(c)
            j += 1
        effects[name] = block
        i = max(j, i + 1)
    return effects


def check_scripted_effect_depth(findings: list[str]):
    base = ROOT / "common" / "scripted_effects"
    if not base.exists():
        return
    definitions: dict[str, tuple[Path, list[str]]] = {}
    for path in base.rglob("*.txt"):
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        for name, block in parse_scripted_effects(text).items():
            definitions[name] = (path, block)

    names = set(definitions)
    graph: dict[str, set[str]] = {name: set() for name in names}
    patterns = {name: re.compile(rf"\b{re.escape(name)}\s*=") for name in names}
    for name, (_, block) in definitions.items():
        body = "\n".join(block)
        for candidate, pattern in patterns.items():
            if pattern.search(body):
                graph[name].add(candidate)

    memo: dict[str, int] = {}
    reported_cycles: set[tuple[str, ...]] = set()

    def depth(node: str, stack: list[str]) -> int:
        if node in memo:
            return memo[node]
        if node in stack:
            cycle = tuple(stack[stack.index(node):] + [node])
            if cycle not in reported_cycles:
                reported_cycles.add(cycle)
                findings.append("ERROR scripted_effects: recursion detected: " + " -> ".join(cycle))
            return 999
        stack.append(node)
        best = 1
        for nxt in graph[node]:
            best = max(best, 1 + depth(nxt, stack))
        stack.pop()
        if best < 999:
            memo[node] = best
        return best

    for name in sorted(names):
        d = depth(name, [])
        if 6 <= d < 999:
            rel = definitions[name][0].relative_to(ROOT)
            findings.append(f"ERROR scripted_effects: call depth {d} exceeds limit 5: {name} ({rel})")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-only", action="store_true", help="Print findings but always exit 0")
    args = parser.parse_args()

    findings: list[str] = []
    event_ids: dict[str, list[str]] = defaultdict(list)

    count = 0
    for path in iter_text_files():
        count += 1
        text = read_utf8(path, findings)
        if text is None:
            continue
        if path.suffix.lower() in {".txt", ".mod", ".gui", ".gfx", ".asset"}:
            check_braces(path, text, findings)
        collect_event_ids(path, text, event_ids)
        check_loc_duplicates(path, text, findings)

    for event_id, places in sorted(event_ids.items()):
        if len(places) > 1:
            findings.append(f"ERROR duplicate event id {event_id}: " + ", ".join(places))

    check_scripted_effect_depth(findings)

    print(f"FOC preflight scanned {count} text files.")
    if findings:
        for item in findings:
            print(item)
        errors = sum(item.startswith("ERROR") for item in findings)
        warnings = sum(item.startswith("WARNING") for item in findings)
        print(f"Findings: {errors} error(s), {warnings} warning(s).")
        if errors and not args.report_only:
            return 1
    else:
        print("PASS: no findings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
