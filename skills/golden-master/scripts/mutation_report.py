#!/usr/bin/env python3
"""Résume les mutants PIT d'une classe cible (et de ses classes internes / lambdas).

Usage :
    python3 mutation_report.py target/pit-reports/mutations.xml com.exemple.Cible [--src src/main/java]

Affiche le score de mutation, puis chaque mutant non tué (SURVIVED, NO_COVERAGE),
trié par ligne, avec le code source si --src est fourni.
Code de sortie : 0 si aucun mutant ne survit, 1 sinon, 2 en cas d'erreur.
"""
import argparse
import os
import sys
import xml.etree.ElementTree as ET
from collections import Counter

KILLED = {"KILLED", "TIMED_OUT", "MEMORY_ERROR", "RUN_ERROR"}
NOT_KILLED = {"SURVIVED", "NO_COVERAGE"}

HINTS = {
    "NO_COVERAGE": "ligne jamais exécutée : ajouter une valeur d'axe (voir coverage_report.py)",
    "SURVIVED": "exécutée mais non détectée : borne manquante, ou sortie / effet de bord non imprimé",
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
    parser.add_argument("target", help="nom complet de la classe cible, ex. com.exemple.Cible")
    parser.add_argument("--src", help="racine des sources de production, ex. src/main/java")
    args = parser.parse_args(argv)

    if not os.path.isfile(args.mutations_xml):
        print("Fichier introuvable : " + args.mutations_xml, file=sys.stderr)
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
        print("Aucun mutant pour {} : vérifier -DtargetClasses et que le rapport XML est activé.".format(args.target),
              file=sys.stderr)
        return 2

    killed = sum(count for status, count in statuses.items() if status in KILLED)
    relevant = killed + sum(count for status, count in statuses.items() if status in NOT_KILLED)
    score = 100.0 * killed / relevant if relevant else 100.0

    print("Mutation de " + args.target)
    print("  Score : {}/{} tués ({:.1f} %)".format(killed, relevant, score))
    print("  Détail : " + ", ".join("{}={}".format(s, c) for s, c in sorted(statuses.items())))

    if remaining:
        print("\nMutants à tuer ou à justifier :")
        for status in sorted({m["status"] for m in remaining}):
            print("\n  {} — {}".format(status, HINTS[status]))
            for m in sorted((m for m in remaining if m["status"] == status), key=lambda m: (m["file"], m["line"])):
                print("    {}:{:<5} {}()  [{}] {}".format(m["file"], m["line"], m["method"], m["mutator"], m["description"]))
                if m["code"]:
                    print("          > " + m["code"])

    print("\nObjectif aucun mutant survivant : " + ("ATTEINT" if not remaining else "NON ATTEINT"))
    return 0 if not remaining else 1


if __name__ == "__main__":
    sys.exit(main())
