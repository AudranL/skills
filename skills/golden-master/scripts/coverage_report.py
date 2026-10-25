#!/usr/bin/env python3
"""Résume la couverture JaCoCo d'une classe cible (et de ses classes internes).

Usage :
    python3 coverage_report.py target/site/jacoco/jacoco.xml com.exemple.Cible [--src src/main/java]

Affiche les compteurs (lignes, branches, instructions, méthodes), puis chaque ligne
non couverte ou partiellement couverte, avec le code source si --src est fourni.
Code de sortie : 0 si toutes les lignes et branches sont couvertes, 1 sinon, 2 en cas d'erreur.
"""
import argparse
import os
import sys
import xml.etree.ElementTree as ET

COUNTERS = ("LINE", "BRANCH", "INSTRUCTION", "METHOD")


def is_target(class_name, target):
    return class_name == target or class_name.startswith(target + "$")


def read_source(src_root, package_path, filename):
    if not src_root:
        return None
    path = os.path.join(src_root, package_path, filename)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read().splitlines()


def pct(missed, covered):
    total = missed + covered
    return "n/a" if total == 0 else "{:.1f} %".format(100.0 * covered / total)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("jacoco_xml")
    parser.add_argument("target", help="nom complet de la classe cible, ex. com.exemple.Cible")
    parser.add_argument("--src", help="racine des sources de production, ex. src/main/java")
    args = parser.parse_args(argv)

    if not os.path.isfile(args.jacoco_xml):
        print("Fichier introuvable : " + args.jacoco_xml, file=sys.stderr)
        return 2

    root = ET.parse(args.jacoco_xml).getroot()
    target = args.target.replace(".", "/")
    package_path = target.rsplit("/", 1)[0] if "/" in target else ""

    totals = {name: [0, 0] for name in COUNTERS}
    source_files = set()
    methods_with_misses = []
    missed_lines = []
    found = False

    for package in root.iter("package"):
        if package.get("name") != package_path:
            continue
        for cls in package.findall("class"):
            name = cls.get("name")
            if not is_target(name, target):
                continue
            found = True
            if cls.get("sourcefilename"):
                source_files.add(cls.get("sourcefilename"))
            for counter in cls.findall("counter"):
                kind = counter.get("type")
                if kind in totals:
                    totals[kind][0] += int(counter.get("missed"))
                    totals[kind][1] += int(counter.get("covered"))
            for method in cls.findall("method"):
                for counter in method.findall("counter"):
                    if counter.get("type") == "INSTRUCTION" and int(counter.get("missed")) > 0:
                        methods_with_misses.append((name.rsplit("/", 1)[-1], method.get("name"), method.get("line")))

        for sourcefile in package.findall("sourcefile"):
            if sourcefile.get("name") not in source_files:
                continue
            lines = read_source(args.src, package_path, sourcefile.get("name"))
            for line in sourcefile.findall("line"):
                nr, mi, ci = int(line.get("nr")), int(line.get("mi")), int(line.get("ci"))
                mb, cb = int(line.get("mb")), int(line.get("cb"))
                if mi == 0 and mb == 0:
                    continue
                if ci == 0 and cb == 0:
                    state = "NON COUVERTE"
                elif mb > 0:
                    state = "BRANCHES {}/{}".format(cb, mb + cb)
                else:
                    state = "PARTIELLE"
                code = lines[nr - 1].strip() if lines and nr - 1 < len(lines) else ""
                missed_lines.append((sourcefile.get("name"), nr, state, code))

    if not found:
        print("Classe {} absente du rapport : le test a-t-il tourné avec le profil golden-master ?".format(args.target),
              file=sys.stderr)
        return 2

    print("Couverture de " + args.target)
    for kind in COUNTERS:
        missed, covered = totals[kind]
        print("  {:<12} {:>5}/{:<5} {}".format(kind, covered, missed + covered, pct(missed, covered)))

    if methods_with_misses:
        print("\nMéthodes incomplètement exécutées :")
        for cls_name, method, line in methods_with_misses:
            print("  {}#{} (l.{})".format(cls_name, method, line))

    if missed_lines:
        print("\nLignes à couvrir :")
        for filename, nr, state, code in missed_lines:
            print("  {}:{:<5} {:<16} {}".format(filename, nr, state, code))

    complete = totals["LINE"][0] == 0 and totals["BRANCH"][0] == 0
    print("\nObjectif 100 % lignes et branches : " + ("ATTEINT" if complete else "NON ATTEINT"))
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())
