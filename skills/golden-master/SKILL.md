---
name: golden-master
description: "Put a golden master (characterization test, approval test) on existing Java / Spring Boot code to freeze its current behavior before a refactoring: ApprovalTests.Java over a combinatorial generation of the inputs (CombinationApprovals), then proof that the net holds with JaCoCo (branch coverage) and PIT (mutation testing). Covers pure code (mappers, utilities, calculation rules) as well as services with dependencies (mocks that record the calls, clock and randomness under control). Load as soon as the user mentions a golden master, a characterization test, an approval test, a snapshot test, legacy code without tests, securing a class before refactoring it, or asks how to touch some code without breaking anything, even without the words golden master. Scope: a Maven project. The skill stops at the safety net and proposes a refactoring plan; it does not refactor."
metadata:
  internal: true
---

# Golden master for Java / Spring Boot

## Principle

A golden master does not say whether the code is right: it records **what the code does today**, bugs included, so that the slightest change of behavior during a refactoring shows.

1. The inputs vary along every **axis** that influences the code (null or not, each enum value, each branch…), as a **cartesian product**.
2. For each combination, the test prints one **deterministic** line of text: the inputs, then the output, the exception thrown, and the side effects (calls to the dependencies).
3. ApprovalTests compares this text (`*.received.txt`) with the versioned reference file (`*.approved.txt`). Any difference fails the test.
4. The net is then **proved** tight enough: JaCoCo shows that every branch runs, PIT shows that every mutation of the code fails the test.

A golden master without coverage and mutation is a false sense of safety: a branch that never runs, or a field that is never printed, can change without anything breaking.

## Absolute rules

- **Do not modify the production code** while building the golden master. The only exception: a minimal seam (injecting a `Clock`, extracting a static call) made through an automated IDE refactoring, **after the user's explicit agreement**. Check with `git diff --stat -- src/main` that nothing else changed.
- **Never fix a suspicious behavior** (an NPE, an inconsistent value, a comment the code contradicts): freeze it as it is and list it in the report. Fixing it is a business decision, made later, in a separate commit.
- **Deterministic output**: no `Object@1b6d3586`, no current date, no random UUID, no `HashMap` / `HashSet` order. The test must produce exactly the same file twice in a row.
- **Read the first `received` file before approving it.** After that, during the refactoring, a difference is **never** resolved by approving again: the code is wrong.
- Work on a dedicated branch with a clean working tree.
- The golden master is **temporary**: it will be replaced by real business unit tests once the code is refactored.

## Step 1: Scope

1. Identify the **target**: the class, and its public methods (or those called from outside). Pick the **highest call point** that stays fast and isolated: a public method covers the private methods it calls. When a public method holds a very combinatorial logic of its own (e.g. `extractPackSize` in the example), give it a test of its own to keep the number of combinations down.
2. Classify the target:
   - **pure code** (mapper, static utility, calculation): go straight to "Step 3: Write the test";
   - **service with dependencies** (repositories, HTTP clients, Kafka, clock, `@Value`): also read `references/services-and-dependencies.md`.
3. Check the build (`pom.xml`):
   - JUnit 5 present; Mockito if the target has dependencies;
   - ApprovalTests present? Otherwise add it in `test` scope (see `references/approvaltests.md`);
   - JaCoCo / PIT already configured? Otherwise the `golden-master` Maven profile from `references/maven-verification.md` will be added at step 5.
4. A clean `git status`, then `git checkout -b test/golden-master-<target-in-kebab-case>`.

## Step 2: Map the axes of variation

Read the target **and every method it calls on its inputs**, including the computed getters of the model (e.g. `getCurrentActiveEdition()`, `getFirstSalePriceAsString()`): they often hide branches, dates or formats.

Each decision point becomes an axis:

| In the code | Values of the axis |
|---|---|
| `x != null ? … : …`, `if (x == null)` | `null`, not null |
| `enum`, `switch`, `X.name().equals(key)` | `null`, **every** value of the enum, an unknown value (`"UNKNOWN"`) |
| numeric comparison, threshold | just below, equal, just above, `0`, negative |
| string | `null`, `""`, nominal value, different case if `equals` / `fromName` |
| collection, loop | `null`, empty, one element, several (with duplicates, in a different order) |
| exception from a dependency | nominal response, empty, exception |

The details (choosing the values, nested objects, keeping the number of combinations down) are in `references/axes-and-printing.md`.

Show the table of axes to the user, with the number of combinations, and ask whether they know **real business cases** missing from it (an unusual data format, a particular product). Add them as axis values.

Keep the total under about 2,000 combinations per test. Beyond that, split along independent pieces of logic (one test per public method, or per axis that combines with no other).

## Step 3: Write the test

Create `<Target>GoldenMasterTest` in the **same package** as the target (access to package-private methods), under `src/test/java`.

Typical structure (pure code):

```java
class PriceCalculatorGoldenMasterTest {

    private static final Options OPTIONS = new Options().withReporter(new QuietReporter());

    @Test
    void compute() {
        CombinationApprovals.verifyAllCombinations(
                (customer, quantity, promo) -> print(PriceCalculator.compute(fixture(customer), quantity, promo)),
                CustomerShape.values(),                 // axis 1: shape of the input object
                new Integer[]{null, -1, 0, 1, 10, 11},  // axis 2: bounds around the threshold 10
                new String[]{null, "", "SUMMER", "summer", "UNKNOWN"},
                OPTIONS);
    }
}
```

Key points:

- Every axis value needs a **readable `toString()`**: `CombinationApprovals` prints it at the start of the line. For complex objects, use an `enum` of "shapes" (`CustomerShape.NO_ADDRESS`) and a `fixture(shape)` function that builds the object.
- Build the inputs **as production does**: the project's builders, constructors or JSON deserialization. Use **distinct values** for each possible source of a piece of data (carton = 12, bundle = 3, pallet = 480): the output then shows which branch was taken.
- **Print the whole output**: every field of the result, the exception (class and message), the modified state of the arguments, the interactions with the dependencies. A field not printed is a field not protected.
- The exceptions thrown by the target are caught and printed by `CombinationApprovals`: do not catch them yourself.

Full example: `references/example-book-dto-mapper.md`.

## Step 4: Generate, read, approve

1. Run the test alone:
   ```bash
   mvn -q test -Dtest='<Target>GoldenMasterTest' -Dsurefire.failIfNoSpecifiedTests=false
   ```
   The first run **fails** (no approved file yet) and creates `<Target>GoldenMasterTest.<method>.received.txt` next to the test class.
2. **Read** the received file (at least a sample per axis) and check:
   - no non-deterministic trace (`@` followed by a hash, the current date, a UUID): otherwise fix the printing or add a scrubber;
   - not every line gives the same output: otherwise an axis does not reach the code (a fixture built wrong);
   - the exceptions are the ones the code throws, not errors in the test's fixture.
3. Check **determinism**: copy the `received` file, run again, compare (`diff`). No difference allowed.
4. Approve: `mv X.received.txt X.approved.txt`, run again: green.
5. Commit the test and the approved file: `git commit -m "test: golden master on <Target>"`.

## Step 5: Prove that the net holds

Add the `golden-master` Maven profile if needed (`references/maven-verification.md`), then loop until both criteria are met.

`<this skill's folder>` is the folder of this file: for instance `~/.claude/skills/golden-master` in Claude Code, `~/.copilot/skills/golden-master` in Copilot, `~/.config/opencode/skills/golden-master` in opencode.

### 5a. Coverage (JaCoCo): 100% of the target's branches

```bash
mvn -q -P golden-master test -Dtest='<Target>GoldenMasterTest' -Dsurefire.failIfNoSpecifiedTests=false
python3 <this skill's folder>/scripts/coverage_report.py target/site/jacoco/jacoco.xml <fqn.Target> --src src/main/java
```

For each missed line or branch: add the axis value that reaches it, or justify it in the report (dead code, a branch that cannot be reached without changing the code).

### 5b. Mutation (PIT): every mutant killed or justified

```bash
mvn -q -P golden-master -Djacoco.skip=true test-compile org.pitest:pitest-maven:mutationCoverage \
    -DtargetClasses='<fqn.Target>*' -DtargetTests='<fqn.Target>GoldenMasterTest'
python3 <this skill's folder>/scripts/mutation_report.py target/pit-reports/mutations.xml <fqn.Target> --src src/main/java
```

For each mutant not killed:

| Status | Usual cause | Action |
|---|---|---|
| `NO_COVERAGE` | line never executed | back to 5a |
| `SURVIVED` on a condition (`<` to `<=`, negation) | a bound value is missing | add the exact bound to the axis |
| `SURVIVED` on a return value or a removed call | output or side effect not printed | complete the printing (field, interaction, modified argument) |
| `SURVIVED` with no possible observable effect | equivalent mutant | justify it in the report |

Each time inputs are added, the approved file changes: this is allowed **only** if `git diff --stat -- src/main` is empty. Read the new `received` file, approve it again, commit.

## Step 6: Report and refactoring proposal

Stop here and present to the user:

```markdown
## Golden master: <Target>
- Test: <Target>GoldenMasterTest (N combinations, M test methods), branch test/golden-master-<target>
- Coverage: lines X/Y, branches X/Y (justified gaps: …)
- Mutation: K/T mutants killed (justified survivors: …)

### Suspicious behaviors frozen (not fixed)
| Case | Current behavior | Why it is suspicious |
|---|---|---|
| bookKey null | NullPointerException | thrown before the business check NoActiveEdition |

### Refactoring proposal (small steps, golden master run again after each one)
1. …

### After the refactoring
Write readable business unit tests (one behavior, one named test), fix the suspicious behaviors once validated,
then delete the golden master, its approved file and the `golden-master` Maven profile.
```

Do not start the refactoring without an explicit request from the user.

## Resources

| File | Content |
|---|---|
| `references/approvaltests.md` | Dependency, API (`verify`, `CombinationApprovals`, `Options`, reporters, scrubbers), where the files go |
| `references/axes-and-printing.md` | Finding the axes, choosing the values, keeping the combinations down, writing a deterministic printout |
| `references/services-and-dependencies.md` | Spring services: recording mocks, clock, randomness, static calls, `@Value` |
| `references/maven-verification.md` | JaCoCo and PIT Maven profile, commands, multi-module projects, pitfalls |
| `references/example-book-dto-mapper.md` | Full example on `BookDtoMapperFromFeedUtils` |
| `scripts/coverage_report.py` | Extracts the target's missed lines and branches from `jacoco.xml` |
| `scripts/mutation_report.py` | Extracts the target's mutants not killed from `mutations.xml` |

The scripts use only the Python 3.8+ standard library. After changing them, run `python3 scripts/selftest.py`.
