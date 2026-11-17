---
name: cyclomatic-complexity
description: "Measure the cyclomatic complexity (McCabe) of a method, a class or a set of Java, TypeScript or JavaScript files, to tell quickly whether the code still reads well or needs refactoring: a script (mccabe.py) that counts the decision points of each method and totals them per class; thresholds (10 per method, above 20 refactor first, a class total as a hint); how to read the result and when to measure (refactor step of TDD, before changing existing code, in review, before and after a refactoring); the refactoring that reduces each kind of decision point, without gaming the number; the script's limits. Load when the user mentions cyclomatic complexity, McCabe, a method too complex or too long, asks \"should I refactor this?\", wants quick feedback on readability or on complexity debt, or before and after a refactoring to show the gain, even without saying McCabe. Measures and recommends; never refactors without a safety net of tests."
metadata:
  internal: true
---

# Cyclomatic complexity

## The idea

Cyclomatic complexity counts the linearly independent paths through a method: **1 + the number of decision points**. It is also, roughly, the **minimum number of tests** that cover all its branches. The higher it climbs, the harder the method is to read *and* to test.

It is a signal, not a verdict: a flat `switch` of 12 cases is easier to read than a method with 8 nested loops. The number says **where to look**; judgment says **what to do**.

## What the script counts

Each method starts at 1, then +1 for each `if`, `for` (for-each included), `while` (the one closing a `do … while` included), `case`, `catch`, `&&`, `||`, `??` (TypeScript) and ternary operator `? :`.

Not counted: `else`, `default`, `try`, `finally`, `?.`, generic wildcards `<? extends X>`, nor anything inside comments and strings.

Lambdas, arrow functions and anonymous classes count toward the method that contains them: their logic is part of what the reader has to follow.

## Running the script

`scripts/mccabe.py` (Python 3, standard library only) reads Java, TypeScript and JavaScript.

```sh
python3 scripts/mccabe.py src/main/java/com/example/InvoiceService.java   # one file
python3 scripts/mccabe.py src/                                            # a folder
python3 scripts/mccabe.py --changed                                       # what I just touched
python3 scripts/mccabe.py --all src/                                      # simple methods too
python3 scripts/mccabe.py --json src/ > complexity.json                   # for another tool
python3 scripts/mccabe.py --fail-over --max-method 10 src/                # exit code 1 if over (CI, hook)
```

The script path is relative to this skill: resolve it from the folder where the skill is installed.

Test files (`*Test.java`, `*.spec.ts`…) are skipped unless `--tests` is given; so are build folders (`target`, `node_modules`, `dist`…).

The script has its own self-test: `python3 scripts/selftest.py`.

## Reading the result

| Complexity of a method | Verdict | What to do |
|---|---|---|
| 1 – 10 | `ok` | Nothing. |
| 11 – 20 | `refactor` | Add no logic to it before simplifying it. |
| > 20 | `refactor first` | Refactor before any change: at this level, nobody can tell what the method does any more. |

10 is the usual threshold. If the team has set another, pass it with `--max-method` (`refactor first` then starts above twice that value), and record it in an ADR or in the project's conventions, not in a conversation.

**For a class**, the script gives the **sum** of its methods' complexities (WMC, *Weighted Methods per Class*), the number of methods and the highest one. The threshold of 50 (`--max-class`) is a hint: a class above it almost always has several responsibilities. Read the total together with the number of methods: 50 spread over 25 simple methods is not the same problem as 50 in 3 methods.

**A method with a low number can still be too long or too deeply nested**: cyclomatic complexity sees neither. For a full readability judgment, add the `clean-code` skill (catalog of code smells), if installed.

## When to measure

- **In TDD, at the refactor step**: run `--changed`; a method above 10 is the signal to refactor now, while the tests are green and the context is fresh.
- **Before changing existing code**: measure the method you are about to touch. Above 20, secure it first (the `legacy-code` skill, then `golden-master` for Java, if installed).
- **In code review**: measure the files of the diff; a method that *crossed* the threshold in this diff is an "important" remark.
- **Before and after a refactoring**: rerun the same command and give both numbers. The gain must come from a better split, not from moving the complexity elsewhere (see below).

## Above the threshold

Find *which* kind of decision point dominates, then apply the matching refactoring. Details and examples: `references/refactorings.md`.

| What drives the number up | Refactoring |
|---|---|
| Nested `if`s | Guard clauses (early return) |
| A large loop body | Extract the body into a method named after its intent |
| A condition with several `&&` / `\|\|` | Extract a method or an explaining variable (`isEligible()`) |
| A `switch` / `if-else if` on a type or a code | Polymorphism (strategy, state) or a lookup table |
| Several `catch` blocks, chained validations | Extract the validation; domain exceptions rather than checking codes |
| Cascading defaults (`?:`, `??`) | A value object that holds its defaults, or `Optional` |

- **One refactoring at a time, tests green between each.** No tests, no refactoring: put the safety net in place first (the `legacy-code`, `golden-master` and `tdd` skills, if installed).
- **Do not game the number.** Splitting a method of complexity 18 into three methods of 6 that must be called in a fixed order, or tucking the `if`s away in a `doStuff2` method, moves the complexity without reducing it. Each extracted method has a **name that states its intent** and makes sense on its own.
- **Measure again** after the refactoring, and check that the **class** has not swollen: a pile of new private methods can mean a class that wants to split, which is another refactoring (moving them to a new class).
- **A refactoring does not change behavior**: no bug fix in the same commit.

## Limits of the script

The analysis is **lexical** (no full syntax tree), so it is approximate:

- it does not see the methods of an object literal or of an enum constant with a body, nor functions nested in other methods (counted in the enclosing method);
- expressions inside `${…}` of a TypeScript template literal, and regular expression literals, are not analyzed;
- it reads only Java, TypeScript and JavaScript; for another stack, use that stack's tool (Checkstyle, PMD, ESLint `complexity`, Radon…) with the same thresholds and the same refactorings.

The number may differ by 1 or 2 from SonarQube's or ESLint's (different conventions for `case`, `&&`, `catch`). To compare before and after, **always use the same tool**. SonarQube also measures *cognitive* complexity, which penalizes nesting: a related measure, not the same one.

If the script gets a real case wrong (a missed method, a wrong number), add it to `scripts/selftest.py` with the expected number, then fix the script.
