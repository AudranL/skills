#!/usr/bin/env python3
"""Summarize the PIT mutants of a target class (and of its inner classes and lambdas).

Usage:
    python3 mutation_report.py target/pit-reports/mutations.xml com.example.Target [--src src/main/java]

Prints the mutation score, then every mutant not killed (SURVIVED, NO_COVERAGE),
sorted by line, with the source code when --src is given.
Exit code: 0 if no mutant survives, 1 otherwise, 2 on error.
"""
import argparse
import os
import sys
import xml.etree.ElementTree as ET
from collections import Counter

KILLED = {"KILLED", "TIMED_OUT", "MEMORY_ERROR", "RUN_ERROR"}
NOT_KILLED = {"SURVIVED", "NO_COVERAGE"}

HINTS = {
    "NO_COVERAGE": "line never executed: add an axis value (see coverage_report.py)",
    "SURVIVED": "executed but not detected: a missing bound, or an output or side effect not printed",
}


def is_target(class_name, target):
    return class_name == target or class_name.startswith(target + "$")


def text(node, tag):
    child = node.find(tag)
    return child.text.strip() if child is not None and child.text else ""


def read_source(src_root, target, filename):
    if not src_root or not filename:
        return None
    package_path = target.rsplit(".", 1)[0].replace(".", "/") if "." in target else ""
    path = os.path.join(src_root, package_path, filename)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read().splitlines()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mutations_xml")
    parser.add_argument("target", help="fully qualified name of the target class, e.g. com.example.Target")
    parser.add_argument("--src", help="root of the production sources, e.g. src/main/java")
    args = parser.parse_args(argv)

    if not os.path.isfile(args.mutations_xml):
        print("File not found: " + args.mutations_xml, file=sys.stderr)
        return 2

    root = ET.parse(args.mutations_xml).getroot()
    statuses = Counter()
    remaining = []
    sources = {}

    for mutation in root.iter("mutation"):
        mutated_class = text(mutation, "mutatedClass")
        if not is_target(mutated_class, args.target):
            continue
        status = mutation.get("status", "")
        statuses[status] += 1
        if status in NOT_KILLED:
            filename = text(mutation, "sourceFile")
            if filename not in sources:
                sources[filename] = read_source(args.src, args.target, filename)
            line_no = int(text(mutation, "lineNumber") or 0)
            lines = sources[filename]
            code = lines[line_no - 1].strip() if lines and 0 < line_no <= len(lines) else ""
            remaining.append({
                "status": status,
                "file": filename,
                "line": line_no,
                "method": text(mutation, "mutatedMethod"),
                "mutator": text(mutation, "mutator").rsplit(".", 1)[-1],
                "description": text(mutation, "description"),
                "code": code,
            })

    if not statuses:
        print("No mutant for {}: check -DtargetClasses and that the XML report is enabled.".format(args.target),
              file=sys.stderr)
        return 2

    killed = sum(count for status, count in statuses.items() if status in KILLED)
    relevant = killed + sum(count for status, count in statuses.items() if status in NOT_KILLED)
    score = 100.0 * killed / relevant if relevant else 100.0

    print("Mutation of " + args.target)
    print("  Score: {}/{} killed ({:.1f}%)".format(killed, relevant, score))
    print("  Breakdown: " + ", ".join("{}={}".format(s, c) for s, c in sorted(statuses.items())))

    if remaining:
        print("\nMutants to kill or justify:")
        for status in sorted({m["status"] for m in remaining}):
            print("\n  {} — {}".format(status, HINTS[status]))
            for m in sorted((m for m in remaining if m["status"] == status), key=lambda m: (m["file"], m["line"])):
                print("    {}:{:<5} {}()  [{}] {}".format(m["file"], m["line"], m["method"], m["mutator"], m["description"]))
                if m["code"]:
                    print("          > " + m["code"])

    print("\nGoal of no surviving mutant: " + ("MET" if not remaining else "NOT MET"))
    return 0 if not remaining else 1


if __name__ == "__main__":
    sys.exit(main())
