# Axes of variation and deterministic printing

## 1. Finding the axes

Go through the target line by line, then through **every method called on the inputs** (computed getters, the model's utility methods, `fromName`, formatted `toString`). Note each decision point:

- `if` conditions, ternaries, `&&` / `||` (each operand counts: `a != null && a.getB() != null` gives two axes);
- `switch`, `equals` on a constant, `X.name().equals(...)`, `fromName(...)`;
- accesses that can throw: dereferencing (`x.getY().toString()`), `Integer.parseInt`, `get(0)`, `Optional.get()`;
- loops and streams (`filter`, `findFirst`, `max`): the content and the **order** of the collection;
- implicit dependencies: `LocalDate.now()`, `UUID.randomUUID()`, the default `Locale`, environment variables, `@Value` properties.

Build a table:

| # | Axis | Where | Values |
|---|---|---|---|
| 1 | active edition | `getCurrentActiveEdition()` | absent, present |
| 2 | shipping mode | `extractPackSize` line 93 | `null`, `WAREHOUSE`, `STORE`, `PUBLISHER` |
| … | | | |

## 2. Choosing the values

- **Every** value of an enum, plus `null`. An enum that gains a value later must show up in the file.
- For a key compared with enum names: each name, `null`, an unknown value, a case variant.
- For a number: the exact bounds of each comparison (`< 10` gives 9, 10, 11), `0`, a negative, `null` for a boxed type.
- For a nested object: `null`, "empty" (every field `null`), "complete".
- For a collection: `null`, empty, one element, several elements including one that wins the sort, then the reverse order.
- **Distinct values** for each possible source of an output value (carton = 12, bundle = 3, shipped pallet = 480, delivered pallet = 960). If two branches return the same test value, PIT cannot tell them apart.
- Add the **real cases** the user provides or that the existing test resources hold (`src/test/resources/*.json`).

## 3. Complex objects: shapes rather than fields

When an input object has many optional parts, do not make one axis per field: define an `enum` of meaningful shapes, with a telling `toString`, and a function that builds the object.

```java
enum Logistics {
    NULL, EMPTY, CARTON_NO_BUNDLE, CARTON_WITH_BUNDLE, SHIPPED_PALLET_ONLY, DELIVERED_PALLET_ONLY, COMPLETE
}

static Packaging fixture(Logistics shape, String out, String in) { … }
```

The shapes come from the table of axes: one shape per combination of parts that changes a branch.

## 4. Keeping the combinations down

Number of lines = product of the axes' sizes. Targets: under 2,000 per test method, under 10 s to run (PIT runs the test again for every mutant).

Levers, in this order:

1. **Split**: test a very combinatorial public method directly (e.g. `extractPackSize`), and keep only one or two shapes of that axis in the test of the calling method.
2. **Separate independent axes**: if axis X only affects a part of the result that depends on no other axis, test it in a method of its own with the other axes fixed.
3. **Group** related fields into shapes (section 3).
4. Only as a last resort, drop "in-between" values (never the bounds, never `null`, never an enum value).

Check every reduction afterwards with coverage and mutation (step 5).

## 5. Printing

### What to print

- **Every field** of the result, including those that look uninteresting.
- The **exception**: class and message (done automatically by `CombinationApprovals`).
- The **state of the arguments** after the call, if the target can modify them.
- The **interactions** with the dependencies, in order (see `services-and-dependencies.md`).
- For a `void` method: only the side effects, but all of them.

### How

1. If the output type has a generated `toString()` (Lombok `@Data` / `@Value` / `@ToString`, a record) that includes every field, use it as is.
2. Otherwise, write a `print(...)` in the test: fields in a **fixed order**, `null` printed explicitly.
3. For a deep object graph, serialize to JSON with an `ObjectMapper` set up to be stable:

```java
private static final ObjectMapper PRINTER = JsonMapper.builder()
        .enable(MapperFeature.SORT_PROPERTIES_ALPHABETICALLY)
        .enable(SerializationFeature.ORDER_MAP_ENTRIES_BY_KEYS)
        .addModule(new JavaTimeModule())
        .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
        .build();

static String print(Object o) {
    try { return PRINTER.writeValueAsString(o); }
    catch (JsonProcessingException e) { throw new UncheckedIOException(e); }
}
```

Do not print with the production `ObjectMapper`: if it changes during the refactoring, the printout would change with it.

### Determinism

| Source of noise | Remedy |
|---|---|
| `Object@1b6d3586` (no `toString`) | print the fields or serialize to JSON |
| `HashMap` / `HashSet` in the output | sort when printing (`new TreeMap<>(map)`, `ORDER_MAP_ENTRIES_BY_KEYS`) |
| Current date or time | a fixed `Clock` (see `services-and-dependencies.md`), a scrubber as a last resort |
| UUID, randomness | an injected generator or a mocked static, a scrubber as a last resort |
| Default `Locale` or time zone (number and date formats) | set `Locale.setDefault` and `TimeZone.setDefault` in a `@BeforeAll` and restore them in `@AfterAll` |
| `BigDecimal` `1.0` vs `1.00` | print as is: the scale is part of the behavior |
| Iteration order of a `Set` given as **input** | use `LinkedHashSet` in the fixtures |
