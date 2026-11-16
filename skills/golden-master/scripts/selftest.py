#!/usr/bin/env python3
"""Self-test of the report scripts: generates fake JaCoCo and PIT reports and checks the outputs."""
import contextlib
import io
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coverage_report  # noqa: E402
import mutation_report  # noqa: E402

SOURCE = """package com.example;

public class Target {
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
  <package name="com/example">
    <class name="com/example/Target" sourcefilename="Target.java">
      <method name="f" desc="(Ljava/lang/String;)Ljava/lang/String;" line="5">
        <counter type="INSTRUCTION" missed="2" covered="5"/>
      </method>
      <counter type="INSTRUCTION" missed="2" covered="5"/>
      <counter type="BRANCH" missed="1" covered="1"/>
      <counter type="LINE" missed="1" covered="2"/>
      <counter type="METHOD" missed="0" covered="1"/>
    </class>
    <class name="com/example/TargetOther" sourcefilename="TargetOther.java">
      <counter type="LINE" missed="9" covered="0"/>
    </class>
    <sourcefile name="Target.java">
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
  <mutation detected="true" status="KILLED" numberOfTestsRun="1"><sourceFile>Target.java</sourceFile><mutatedClass>com.example.Target</mutatedClass><mutatedMethod>f</mutatedMethod><methodDescription>(Ljava/lang/String;)Ljava/lang/String;</methodDescription><lineNumber>5</lineNumber><mutator>org.pitest.mutationtest.engine.gregor.mutators.NegateConditionalsMutator</mutator><description>negated conditional</description></mutation>
  <mutation detected="false" status="SURVIVED" numberOfTestsRun="1"><sourceFile>Target.java</sourceFile><mutatedClass>com.example.Target</mutatedClass><mutatedMethod>f</mutatedMethod><methodDescription>(Ljava/lang/String;)Ljava/lang/String;</methodDescription><lineNumber>8</lineNumber><mutator>org.pitest.mutationtest.engine.gregor.mutators.returns.NullReturnValsMutator</mutator><description>replaced return value with "" for com/example/Target::f</description></mutation>
  <mutation detected="false" status="NO_COVERAGE" numberOfTestsRun="0"><sourceFile>Target.java</sourceFile><mutatedClass>com.example.Target$1</mutatedClass><mutatedMethod>lambda$f$0</mutatedMethod><methodDescription>()V</methodDescription><lineNumber>6</lineNumber><mutator>org.pitest.mutationtest.engine.gregor.mutators.returns.EmptyObjectReturnValsMutator</mutator><description>replaced return value</description></mutation>
  <mutation detected="false" status="SURVIVED" numberOfTestsRun="1"><sourceFile>TargetOther.java</sourceFile><mutatedClass>com.example.TargetOther</mutatedClass><mutatedMethod>g</mutatedMethod><methodDescription>()V</methodDescription><lineNumber>3</lineNumber><mutator>X</mutator><description>ignored</description></mutation>
</mutations>
"""


def run(func, argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = func(argv)
    return code, out.getvalue()


def check(condition, message):
    if not condition:
        print("FAILED: " + message)
        sys.exit(1)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "src")
        os.makedirs(os.path.join(src, "com", "example"))
        with open(os.path.join(src, "com", "example", "Target.java"), "w") as handle:
            handle.write(SOURCE)
        files = {"jacoco.xml": JACOCO, "jacoco-full.xml": JACOCO_FULL, "mutations.xml": PIT}
        for name, content in files.items():
            with open(os.path.join(tmp, name), "w") as handle:
                handle.write(content)

        code, out = run(coverage_report.main, [os.path.join(tmp, "jacoco.xml"), "com.example.Target", "--src", src])
        check(code == 1, "incomplete coverage must exit with 1\n" + out)
        check("BRANCHES 1/2" in out and 'if ("A".equals(key))' in out, "partial branch on line 5\n" + out)
        check("NOT COVERED" in out and 'return "a";' in out, "line 6 not covered\n" + out)
        check("TargetOther" not in out, "TargetOther must not be counted\n" + out)

        code, out = run(coverage_report.main, [os.path.join(tmp, "jacoco-full.xml"), "com.example.Target"])
        check(code == 0 and "lines and branches: MET" in out, "full coverage must exit with 0\n" + out)

        code, out = run(coverage_report.main, [os.path.join(tmp, "jacoco.xml"), "com.example.Missing"])
        check(code == 2, "a missing class must exit with 2\n" + out)

        code, out = run(mutation_report.main, [os.path.join(tmp, "mutations.xml"), "com.example.Target", "--src", src])
        check(code == 1, "surviving mutants must exit with 1\n" + out)
        check("1/3 killed" in out, "score over the target's mutants only (lambda included)\n" + out)
        check("NullReturnValsMutator" in out and "> return null;" in out, "surviving mutant on line 8 with its code\n" + out)
        check("NO_COVERAGE" in out and "lambda$f$0" in out, "uncovered mutant in the inner class\n" + out)
        check("ignored" not in out, "TargetOther must not appear\n" + out)

    print("selftest OK")


if __name__ == "__main__":
    main()
