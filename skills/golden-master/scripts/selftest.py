#!/usr/bin/env python3
"""Auto-test des scripts de rapport : génère des rapports JaCoCo et PIT factices et vérifie les sorties."""
import contextlib
import io
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coverage_report  # noqa: E402
import mutation_report  # noqa: E402

SOURCE = """package com.exemple;

public class Cible {
    public static String f(String key) {
        if ("A".equals(key)) {
            return "a";
        }
        return null;
    }
}
"""

JACOCO = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<!DOCTYPE report PUBLIC "-//JACOCO//DTD Report 1.1//EN" "report.dtd">
<report name="demo">
  <package name="com/exemple">
    <class name="com/exemple/Cible" sourcefilename="Cible.java">
      <method name="f" desc="(Ljava/lang/String;)Ljava/lang/String;" line="5">
        <counter type="INSTRUCTION" missed="2" covered="5"/>
      </method>
      <counter type="INSTRUCTION" missed="2" covered="5"/>
      <counter type="BRANCH" missed="1" covered="1"/>
      <counter type="LINE" missed="1" covered="2"/>
      <counter type="METHOD" missed="0" covered="1"/>
    </class>
    <class name="com/exemple/CibleAutre" sourcefilename="CibleAutre.java">
      <counter type="LINE" missed="9" covered="0"/>
    </class>
    <sourcefile name="Cible.java">
      <line nr="5" mi="0" ci="3" mb="1" cb="1"/>
      <line nr="6" mi="2" ci="0" mb="0" cb="0"/>
      <line nr="8" mi="0" ci="2" mb="0" cb="0"/>
    </sourcefile>
  </package>
</report>
"""

JACOCO_FULL = JACOCO.replace('missed="1" covered="1"', 'missed="0" covered="2"') \
    .replace('<counter type="LINE" missed="1" covered="2"/>', '<counter type="LINE" missed="0" covered="3"/>') \
    .replace('mb="1" cb="1"', 'mb="0" cb="2"').replace('mi="2" ci="0"', 'mi="0" ci="2"')

PIT = """<?xml version="1.0" encoding="UTF-8"?>
<mutations partial="false">
  <mutation detected="true" status="KILLED" numberOfTestsRun="1"><sourceFile>Cible.java</sourceFile><mutatedClass>com.exemple.Cible</mutatedClass><mutatedMethod>f</mutatedMethod><methodDescription>(Ljava/lang/String;)Ljava/lang/String;</methodDescription><lineNumber>5</lineNumber><mutator>org.pitest.mutationtest.engine.gregor.mutators.NegateConditionalsMutator</mutator><description>negated conditional</description></mutation>
  <mutation detected="false" status="SURVIVED" numberOfTestsRun="1"><sourceFile>Cible.java</sourceFile><mutatedClass>com.exemple.Cible</mutatedClass><mutatedMethod>f</mutatedMethod><methodDescription>(Ljava/lang/String;)Ljava/lang/String;</methodDescription><lineNumber>8</lineNumber><mutator>org.pitest.mutationtest.engine.gregor.mutators.returns.NullReturnValsMutator</mutator><description>replaced return value with "" for com/exemple/Cible::f</description></mutation>
  <mutation detected="false" status="NO_COVERAGE" numberOfTestsRun="0"><sourceFile>Cible.java</sourceFile><mutatedClass>com.exemple.Cible$1</mutatedClass><mutatedMethod>lambda$f$0</mutatedMethod><methodDescription>()V</methodDescription><lineNumber>6</lineNumber><mutator>org.pitest.mutationtest.engine.gregor.mutators.returns.EmptyObjectReturnValsMutator</mutator><description>replaced return value</description></mutation>
  <mutation detected="false" status="SURVIVED" numberOfTestsRun="1"><sourceFile>CibleAutre.java</sourceFile><mutatedClass>com.exemple.CibleAutre</mutatedClass><mutatedMethod>g</mutatedMethod><methodDescription>()V</methodDescription><lineNumber>3</lineNumber><mutator>X</mutator><description>ignored</description></mutation>
</mutations>
"""


def run(func, argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = func(argv)
    return code, out.getvalue()


def check(condition, message):
    if not condition:
        print("ÉCHEC : " + message)
        sys.exit(1)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "src")
        os.makedirs(os.path.join(src, "com", "exemple"))
        with open(os.path.join(src, "com", "exemple", "Cible.java"), "w") as handle:
            handle.write(SOURCE)
        files = {"jacoco.xml": JACOCO, "jacoco-full.xml": JACOCO_FULL, "mutations.xml": PIT}
        for name, content in files.items():
            with open(os.path.join(tmp, name), "w") as handle:
                handle.write(content)

        code, out = run(coverage_report.main, [os.path.join(tmp, "jacoco.xml"), "com.exemple.Cible", "--src", src])
        check(code == 1, "couverture incomplète doit sortir en 1\n" + out)
        check("BRANCHES 1/2" in out and 'if ("A".equals(key))' in out, "branche partielle ligne 5\n" + out)
        check("NON COUVERTE" in out and 'return "a";' in out, "ligne 6 non couverte\n" + out)
        check("CibleAutre" not in out, "CibleAutre ne doit pas être comptée\n" + out)

        code, out = run(coverage_report.main, [os.path.join(tmp, "jacoco-full.xml"), "com.exemple.Cible"])
        check(code == 0 and "ATTEINT" in out, "couverture complète doit sortir en 0\n" + out)

        code, out = run(coverage_report.main, [os.path.join(tmp, "jacoco.xml"), "com.exemple.Absente"])
        check(code == 2, "classe absente doit sortir en 2\n" + out)

        code, out = run(mutation_report.main, [os.path.join(tmp, "mutations.xml"), "com.exemple.Cible", "--src", src])
        check(code == 1, "mutants survivants doivent sortir en 1\n" + out)
        check("1/3 tués" in out, "score sur les seuls mutants de la cible (lambda incluse)\n" + out)
        check("NullReturnValsMutator" in out and "> return null;" in out, "mutant survivant ligne 8 avec code\n" + out)
        check("NO_COVERAGE" in out and "lambda$f$0" in out, "mutant non couvert dans la classe interne\n" + out)
        check("ignored" not in out, "CibleAutre ne doit pas apparaître\n" + out)

    print("selftest OK")


if __name__ == "__main__":
    main()
