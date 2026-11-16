#!/usr/bin/env python3
"""McCabe cyclomatic complexity per method and per class (Java, TypeScript, JavaScript).

Lexical analysis, no dependencies: comments and strings are blanked out, braces delimit
types and methods, then the decision points of each body are counted.

    mccabe.py <file|folder>...            methods above the threshold, classes with their total
    mccabe.py --changed                   files changed according to git (HEAD + untracked)
    mccabe.py --all src/                  also lists the simple methods
    mccabe.py --json src/                 machine-readable output
    mccabe.py --fail-over src/            exit code 1 if a method is above the threshold
"""
import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field

EXTENSIONS = {".java": "java", ".ts": "ts", ".tsx": "ts", ".js": "ts", ".jsx": "ts", ".mjs": "ts"}
IGNORED_DIRS = {".git", "node_modules", "target", "build", "dist", "out", ".gradle", ".angular", "coverage"}
TEST_FILE = re.compile(r"(Test|Tests|IT)\.java$|\.(spec|test)\.[jt]sx?$")
NOT_METHODS = {"if", "for", "while", "switch", "catch", "try", "synchronized", "function", "return", "else", "do"}
TYPE_HEADER = re.compile(r"\b(?:class|interface|enum|record|namespace)\s+([A-Za-z_$][\w$]*)")
DECISION = re.compile(r"\b(?:if|for|while|case|catch)\b|&&|\|\||\?\?")
TERNARY = re.compile(r"(?<![?<])\?(?![?.>,:)\]])(?!\s*(?:extends|super)\b)")
ARROW_NAME = re.compile(r"([A-Za-z_$][\w$]*)\s*(?::[^=]*)?=\s*[^=]*=>\s*$")
NAME_BEFORE_PAREN = re.compile(r"([A-Za-z_$][\w$]*)\s*(?:<[^()]*>)?\s*$")
AFTER_PARAMS = re.compile(r"^\s*(?:throws\s+[\w.,\s<>]+|:\s*[^=;{}]*)?\s*$")


@dataclass
class Method:
    name: str
    line: int
    complexity: int


@dataclass
class TypeReport:
    name: str
    line: int
    methods: list = field(default_factory=list)

    @property
    def total(self):
        return sum(m.complexity for m in self.methods)

    @property
    def worst(self):
        return max((m.complexity for m in self.methods), default=0)


def blank_comments_and_strings(source):
    """Replace comments and literals with spaces, keeping the length and the line breaks."""
    out, i, n = [], 0, len(source)

    def blank(chunk):
        return "".join(c if c == "\n" else " " for c in chunk)

    while i < n:
        two = source[i:i + 2]
        if two == "//":
            end = source.find("\n", i)
            end = n if end < 0 else end
        elif two == "/*":
            end = source.find("*/", i + 2)
            end = n if end < 0 else end + 2
        elif source.startswith('"""', i):
            end = source.find('"""', i + 3)
            end = n if end < 0 else end + 3
        elif source[i] in "\"'`":
            quote, end = source[i], i + 1
            while end < n and source[end] != quote:
                end += 2 if source[end] == "\\" else 1
                if quote != "`" and end < n and source[end] == "\n":
                    break
            end = min(end + 1, n)
        else:
            out.append(source[i])
            i += 1
            continue
        out.append(blank(source[i:end]))
        i = end
    return "".join(out)


def blank_annotations(header):
    """Blank out @Annotation(...) and @Decorator(...) so that their parentheses are not taken for a method."""
    chars = list(header)
    for match in re.finditer(r"@[A-Za-z_$][\w$.]*", header):
        end = match.end()
        probe = end
        while probe < len(header) and header[probe].isspace():
            probe += 1
        if probe < len(header) and header[probe] == "(":
            depth = 0
            while probe < len(header):
                depth += {"(": 1, ")": -1}.get(header[probe], 0)
                probe += 1
                if depth == 0:
                    break
            end = probe
        for k in range(match.start(), end):
            chars[k] = " "
    return "".join(chars)


def matching_paren(text, open_index):
    depth = 0
    for k in range(open_index, len(text)):
        depth += {"(": 1, ")": -1}.get(text[k], 0)
        if depth == 0:
            return k
    return -1


def parse_method_header(header, allow_arrow):
    """Return the method name if the header (the text before "{") declares a method, else None."""
    clean = blank_annotations(header).strip()
    if clean.endswith("=>"):
        found = ARROW_NAME.search(clean) if allow_arrow else None
        return found.group(1) if found else None
    if clean.endswith("->"):
        return None
    open_index = clean.find("(")
    if open_index < 0:
        return None
    named = NAME_BEFORE_PAREN.search(clean[:open_index])
    if not named or named.group(1) in NOT_METHODS:
        return None
    before = clean[:named.start()]
    if "=" in before or re.search(r"\bnew\b", before):
        return None
    close = matching_paren(clean, open_index)
    if close < 0 or not AFTER_PARAMS.match(clean[close + 1:].replace("=>", "")):
        return None
    return named.group(1)


def complexity_of(body):
    ternaries = len(TERNARY.findall(re.sub(r"\?[.?]", "  ", body)))
    return 1 + len(DECISION.findall(body)) + ternaries


def line_of(source, index):
    return source.count("\n", 0, index) + 1


def analyse(source, language):
    """Return the list of types (classes, interfaces, enums, records) with their methods."""
    code = blank_comments_and_strings(source)
    stack = [{"kind": "root", "report": None}]
    reports = []
    header_start, parens = 0, 0
    for index, char in enumerate(code):
        if char == "(":
            parens += 1
        elif char == ")":
            parens = max(0, parens - 1)
        elif char == ";" and parens == 0:
            header_start = index + 1
        elif char == "{":
            header = code[header_start:index]
            frame = classify(header, header_start, index, parens, stack, language, code, reports)
            stack.append(frame)
            if parens == 0:
                header_start = index + 1
        elif char == "}" and len(stack) > 1:
            frame = stack.pop()
            if frame["kind"] == "method":
                body = code[frame["open"] + 1:index]
                frame["report"].methods.append(Method(frame["name"], frame["line"], complexity_of(body)))
            if parens == 0:
                header_start = index + 1
    return reports


def classify(header, header_start, open_index, parens, stack, language, code, reports):
    parent = stack[-1]
    if parens > 0:
        return {"kind": "other", "report": parent["report"]}
    declared = TYPE_HEADER.search(header)
    if declared:
        qualified = declared.group(1)
        if parent["report"]:
            qualified = f"{parent['report'].name}.{qualified}"
        report = TypeReport(qualified, line_of(code, header_start + declared.start(1)))
        reports.append(report)
        return {"kind": "type", "report": report}
    in_type = parent["kind"] == "type"
    in_script_root = language == "ts" and parent["kind"] == "root"
    name = parse_method_header(header, allow_arrow=in_type or in_script_root) if in_type or in_script_root else None
    if name:
        report = parent["report"]
        if report is None:
            report = TypeReport("(top-level functions)", 1)
            reports.append(report)
            parent["report"] = report
        position = re.search(rf"\b{re.escape(name)}\b", header)
        line = line_of(code, header_start + (position.start() if position else 0))
        return {"kind": "method", "report": report, "name": name, "open": open_index, "line": line}
    return {"kind": "other", "report": parent["report"]}


def collect_files(targets, include_tests):
    files = []
    for target in targets:
        if os.path.isfile(target):
            files.append(target)
            continue
        for root, dirs, names in os.walk(target):
            dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS)
            files.extend(os.path.join(root, n) for n in sorted(names))
    kept = [f for f in files if os.path.splitext(f)[1] in EXTENSIONS]
    return kept if include_tests else [f for f in kept if not TEST_FILE.search(f)]


def changed_files():
    commands = (["git", "diff", "--name-only", "HEAD"], ["git", "ls-files", "--others", "--exclude-standard"])
    names = set()
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            sys.exit(f"git failed: {result.stderr.strip()}")
        names.update(line for line in result.stdout.splitlines() if os.path.isfile(line))
    return sorted(names)


def verdict(value, limit):
    if value <= limit:
        return "ok"
    return "refactor" if value <= 2 * limit else "refactor first"


def render(results, args):
    exceeded = 0
    for path, reports in results:
        lines = []
        for report in reports:
            shown = [m for m in sorted(report.methods, key=lambda m: -m.complexity)
                     if args.all or m.complexity > args.max_method]
            exceeded += sum(1 for m in report.methods if m.complexity > args.max_method)
            class_flag = " ⚠ class too complex" if report.total > args.max_class else ""
            if not shown and not class_flag:
                continue
            lines.append(f"  {report.name}  total {report.total} · {len(report.methods)} methods · "
                         f"max {report.worst}{class_flag}")
            lines.extend(f"    {m.complexity:>3}  {m.name}  (L{m.line})  {verdict(m.complexity, args.max_method)}"
                         for m in shown)
        if lines:
            print(path)
            print("\n".join(lines))
    totals = [m.complexity for _, reports in results for r in reports for m in r.methods]
    print(f"\n{len(totals)} methods analyzed, {exceeded} above {args.max_method}"
          + (f", most complex: {max(totals)}" if totals else ""))
    return exceeded


def as_json(results):
    return [{"file": path, "types": [{"name": r.name, "line": r.line, "total": r.total,
                                     "methods": [m.__dict__ for m in r.methods]} for r in reports]}
            for path, reports in results]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("targets", nargs="*", help="files or folders (Java, TypeScript, JavaScript)")
    parser.add_argument("--changed", action="store_true", help="files changed or untracked according to git")
    parser.add_argument("--all", action="store_true", help="also list the methods below the threshold")
    parser.add_argument("--tests", action="store_true", help="include the test files")
    parser.add_argument("--max-method", type=int, default=10, help="threshold per method (default 10)")
    parser.add_argument("--max-class", type=int, default=50, help="indicative threshold per class (default 50)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--fail-over", action="store_true", help="exit code 1 if a method is above the threshold")
    args = parser.parse_args(argv)
    targets = changed_files() if args.changed else args.targets
    if not targets:
        parser.error("give files or folders, or --changed")
    results = []
    for path in collect_files(targets, args.tests):
        with open(path, encoding="utf-8", errors="replace") as handle:
            results.append((path, analyse(handle.read(), EXTENSIONS[os.path.splitext(path)[1]])))
    if args.json:
        print(json.dumps(as_json(results), ensure_ascii=False, indent=2))
        exceeded = sum(1 for _, rs in results for r in rs for m in r.methods if m.complexity > args.max_method)
    else:
        exceeded = render(results, args)
    return 1 if args.fail_over and exceeded else 0


if __name__ == "__main__":
    sys.exit(main())
