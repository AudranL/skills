# ApprovalTests.Java: what a golden master needs

## Dependency

```xml
<dependency>
    <groupId>com.approvaltests</groupId>
    <artifactId>approvaltests</artifactId>
    <version>31.0.0</version> <!-- or newer: check Maven Central -->
    <scope>test</scope>
</dependency>
```

If the project already has ApprovalTests, keep its version. If a company BOM manages the versions, check that it does not already set one.

## Useful imports

```java
import org.approvaltests.Approvals;
import org.approvaltests.combinations.CombinationApprovals;
import org.approvaltests.core.Options;
import org.approvaltests.reporters.QuietReporter;
import org.approvaltests.scrubbers.RegExScrubber;
```

## Files produced

- `<TestClass>.<method>.received.txt`: the output of the last run, created **only** when it differs from the approved one.
- `<TestClass>.<method>.approved.txt`: the reference, **to be versioned**.
- Both are written **next to the test's source file** (`src/test/java/<package>/`). If the project wants them elsewhere, a `PackageSettings` class in the test's package can set `public static String ApprovalBaseDirectory = "../resources";`.
- Approving means renaming: `mv X.received.txt X.approved.txt`.
- Add `*.received.*` to the project's `.gitignore` if it is not there.

## Reporter

By default, ApprovalTests tries to open a graphical diff tool. For an agent or a CI, use `QuietReporter`, which only prints the `mv` command to the console:

```java
private static final Options OPTIONS = new Options().withReporter(new QuietReporter());
```

Pass `OPTIONS` as the last argument of every `verify…`.

## API

### A single result

```java
Approvals.verify(text, OPTIONS);
```

### A list of inputs (real samples, JSON files)

```java
Approvals.verifyAll("Product", samples, s -> s.name() + " => " + print(mapper.apply(s)), OPTIONS);
```

### Cartesian product: the golden master's main tool

```java
CombinationApprovals.verifyAllCombinations(
        (a, b, c) -> callTarget(a, b, c),      // lambda that returns the object to print
        valuesA, valuesB, valuesC,             // one array per axis (up to 9 axes)
        OPTIONS);
```

- Each line of the file reads `[valueA, valueB, valueC] => result.toString()`.
- If the lambda throws, the exception is caught and printed in place of the result: do not catch it yourself, except to add information (e.g. the state of a mock).
- The arrays must be typed (`new Integer[]{null, 0, 1}`, `ShippingMode.values()`). To add `null` to an enum's values, build the array by hand or with a small helper:

```java
@SafeVarargs
static <T> T[] withNull(T... values) {
    T[] result = Arrays.copyOf(values, values.length + 1);
    System.arraycopy(result, 0, result, 1, values.length);
    result[0] = null;
    return result;
}
// withNull(ShippingMode.values()) -> [null, WAREHOUSE, STORE, PUBLISHER]
```

- More than 9 axes: group related axes into an `enum` of "shapes" (see `axes-and-printing.md`), or split into several tests.

## Scrubbers: masking what cannot be made deterministic

A last resort, for a value that drives no branch (otherwise, control it upstream: a fixed clock, a frozen generator).

```java
Options options = new Options()
        .withReporter(new QuietReporter())
        .withScrubber(new RegExScrubber("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "[uuid]"));
```

## Several checks in one method

One test method, one approved file. Rather than several `verify` calls in the same method, write one test method per piece of logic (`mapToDto`, `extractPackSize`, `buildBook`…).

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| The test is green on its very first run | An old `.approved.txt` already exists | Check `git status` and the file's content |
| A diff on every run | Non-deterministic output | See `axes-and-printing.md`, "Determinism" |
| `received` empty or a single line | An axis array is empty | Check every array |
| Line endings differ between Windows and Mac | `core.autocrlf` | `.gitattributes`: `*.approved.txt text eol=lf` |
