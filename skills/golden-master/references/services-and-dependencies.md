# Services with dependencies

For a Spring service, the "output" is not only the returned value: it is also the calls made to the dependencies (a save, a Kafka message, an HTTP call) and their arguments. The golden master must print them.

## 1. No Spring context

Build the target by hand, with Mockito mocks. No `@SpringBootTest`: it is slow, and every PIT mutant would start the context again.

```java
ProductRepository repository = mock(ProductRepository.class);
PricingClient pricing = mock(PricingClient.class);
Clock clock = Clock.fixed(Instant.parse("2026-01-15T10:00:00Z"), ZoneOffset.UTC);
ProductService service = new ProductService(repository, pricing, clock);
```

- `@Value` fields become axes: `ReflectionTestUtils.setField(service, "threshold", threshold)`.
- A field injected by `@Autowired` on an attribute: `ReflectionTestUtils.setField` as well.

## 2. The dependencies' responses are axes

Every call to a dependency whose result affects what follows is an axis: nominal response, empty (`Optional.empty()`, an empty list), `null` if the contract allows it, exception.

```java
enum RepoResponse { FOUND, ABSENT, ERROR }

static void stub(ProductRepository repository, RepoResponse response) {
    switch (response) {
        case FOUND -> when(repository.findById("P1")).thenReturn(Optional.of(product()));
        case ABSENT -> when(repository.findById("P1")).thenReturn(Optional.empty());
        case ERROR -> when(repository.findById("P1")).thenThrow(new DataAccessResourceFailureException("db down"));
    }
}
```

Prefer broad matchers (`any()`) when the exact argument is not what the axis is about: the argument actually passed is printed with the interactions anyway.

## 3. Fresh mocks for every combination

Create the mocks **inside the lambda** given to `CombinationApprovals`, never as class fields: otherwise the interactions pile up from one combination to the next.

```java
@Test
void process() {
    CombinationApprovals.verifyAllCombinations(
            (repoResponse, pricingResponse, quantity) -> {
                Deps d = new Deps();                       // fresh mocks
                stub(d.repository, repoResponse);
                stub(d.pricing, pricingResponse);
                String result;
                try {
                    result = String.valueOf(d.service().process("P1", quantity));
                } catch (Exception e) {
                    result = e.getClass().getName() + ": " + e.getMessage();
                }
                return result + "\n    " + interactions(d.repository, d.pricing);
            },
            RepoResponse.values(), PricingResponse.values(), new Integer[]{null, 0, 1, 100},
            OPTIONS);
}
```

Here the exception is caught explicitly so that the interactions made **before** the error are printed too.

## 4. Recording the interactions

Mockito keeps every invocation of every mock, with a global sequence number: the exact order of the calls, across all dependencies, can be rebuilt.

```java
import org.mockito.invocation.Invocation;

static String interactions(Object... mocks) {
    return Arrays.stream(mocks)
            .flatMap(m -> Mockito.mockingDetails(m).getInvocations().stream())
            .sorted(Comparator.comparingInt(Invocation::getSequenceNumber))
            .map(i -> Mockito.mockingDetails(i.getMock()).getMockCreationSettings().getTypeToMock().getSimpleName()
                    + "." + i.getMethod().getName()
                    + Arrays.stream(i.getArguments()).map(GoldenMasterTest::print).collect(Collectors.joining(", ", "(", ")")))
            .collect(Collectors.joining("\n    "));
}
```

- `print` is the deterministic printing of `axes-and-printing.md` (sorted JSON when the argument has no useful `toString`).
- Read calls (`findById`) show up too, on purpose: a refactoring that doubles a query must be visible.

### An argument modified after the call

Mockito keeps a **reference** to the arguments. If the target modifies the entity after `repository.save(entity)`, the printout shows the final state, not the saved one. In that case, take a snapshot of the argument at the time of the call:

```java
List<String> saved = new ArrayList<>();
when(repository.save(any())).thenAnswer(inv -> {
    saved.add(print(inv.getArgument(0)));   // immediate text copy
    return inv.getArgument(0);
});
```

## 5. Clock, randomness, static calls

In order of preference:

1. **The target already receives a `Clock`, a `Supplier<UUID>`, a `Random`**: inject a fixed value. If the date is compared with data (a version's validity, a due date), the fixed date becomes an axis: before, during, after, and exactly on each bound.
2. **A direct static call** (`LocalDate.now()`, `UUID.randomUUID()`): mock it for the duration of the test with `mockStatic` (Mockito 5 enables it by default; Mockito 4 needs `mockito-inline`).

   ```java
   try (MockedStatic<LocalDate> now = mockStatic(LocalDate.class, CALLS_REAL_METHODS)) {
       now.when(LocalDate::now).thenReturn(LocalDate.of(2026, 1, 15));
       return callTarget(...);
   }
   ```

   Open the `MockedStatic` **inside** the lambda (it is bound to the thread and must be closed).
3. **A minimal seam** (replacing `LocalDate.now()` with `LocalDate.now(clock)` and an injected `Clock`): this changes the production code, so **only with the user's agreement**, through an automated IDE refactoring, in a commit of its own, before the golden master.
4. **A scrubber**: only if the value appears in the output without driving any branch.

## 6. What stays out of reach

- Real network or database calls, threads, `@Async`, transactions: the golden master stops at the mocks. Say so in the report if part of the behavior depends on them (e.g. a transactional rollback).
- Code in `@Query` / SQL queries: not covered by this test; characterize it separately against a test database if needed.
