# JUnit 5 and 6 (Jupiter)

The JUnit shape of the `unit-tests` rules.

## Find

- **The version**: `junit-jupiter` or `junit-bom` in `pom.xml` / `build.gradle*`, or the one managed by the Spring Boot BOM. JUnit 6 keeps the `org.junit.jupiter.api` packages, so tests are written the same way, but it needs Java 17 (JUnit 6.0 release notes). A major upgrade is a change of its own, never a side effect of writing a test.
- **JUnit 4** tests (`org.junit.Test`) run on the Vintage engine; a class uses one of the two APIs, never both.
- **The project's JDK** (`pom.xml`, `.sdkmanrc`, `.java-version`), chosen explicitly (macOS: `JAVA_HOME=$(/usr/libexec/java_home -v 21)`); a JDK that is too recent can break Lombok or the compiler.

## Name and organize

- One test class per tested class or per concept (`OrderPricingTest`), in the same package under `src/test/java`.
- A descriptive test name in `snake_case` (`should_reject_order_when_stock_is_insufficient`) or a sentence in `@DisplayName`, following the project's convention.
- `@Nested` classes (with `@DisplayName`) group the cases by situation; they see the fields and the `@BeforeEach` of the enclosing class.
- To triangulate a rule: as many tests as cases, or a `@ParameterizedTest` whose name repeats the values (`@ParameterizedTest(name = "{0} orders give a total of {1} €")`), fed by `@CsvSource` or `@MethodSource`; `@NullAndEmptySource` for the empty cases.
- An acceptance test: the class or the `@Nested` class carries the scenario title in `@DisplayName`; a scenario outline becomes a `@ParameterizedTest` named after it, one set of arguments per example row.

## Assertions and exceptions

- `assertEquals(expected, actual)` (expected first), `assertAll` for several checks of one concept, a lazy message naming the value (`() -> "outstanding balance"`).
- An expected exception: `assertThrows(OutOfStock.class, () -> …)` returns the exception, whose message is checked when it matters; `assertThrowsExactly` when a subclass must not pass.
- A custom assertion: a static method in the domain's words (`assertPaid(order)`), in a test support class. It is built from JUnit's assertions (`assertEquals(expected, actual, message)`, `assertAll`). For a check JUnit has no assertion for, such as two amounts equal whatever their scale (`expected.compareTo(actual) != 0`), it fails through `AssertionFailureBuilder` (JUnit 5.9 and later) rather than a bare `fail(…)`: the failure takes JUnit's format and carries the expected and actual values the IDE compares (`assertionFailure().message("total of order A-42").expected(expected).actual(actual).buildAndThrow()`).

## State, time, files

- A fresh object under test for each test (`@BeforeEach` or an initialized field); no mutable `static` field, no `@BeforeAll` preparing shared state.
- **Time and randomness are preferably injected** (a `Clock`, a `Random` or `RandomGenerator`): the code becomes deterministic, and the test chooses the date or the draw. In the test, `Clock.fixed(Instant.parse("2026-11-02T10:00:00Z"), ZoneOffset.UTC)` and a `Random` with a seed. When changing the code to inject them costs too much, the static call is mocked rather than left untested (with Mockito, `mockStatic(LocalDate.class, CALLS_REAL_METHODS)` in a `try`-with-resources).
- Neither the machine's locale nor its time zone: pass them explicitly (`Locale.FRANCE`, `ZoneId.of("Europe/Paris")`).
- Files: `@TempDir Path folder` as a non-static field or a parameter gives a new folder per test, deleted by JUnit.

## Running the tests

- **A test that starts a framework or a container is kept apart from the others**, whatever its level in the pyramid, because it is slower. Maven: Surefire runs the `*Test` classes (`mvn test`), Failsafe the `*IT` classes (`mvn verify`), a suffix that comes from Failsafe, not from the level of the test. Gradle: the `test` task, and a separate suite wired into `check`. Otherwise, split with `@Tag("slow")`.
- The failing test alone, then its class, then the build: `./mvnw -q -Dtest='OrderPricingTest#should_reject_order_when_stock_is_insufficient' test`, `./mvnw -q -Dtest=OrderPricingTest test`, then `./mvnw verify`; with Gradle, `./gradlew test --tests 'shop.OrderPricingTest'`, then `./gradlew check`. Prefer `./mvnw` or `./gradlew` when the repository ships them: they pin the build tool's version.
- A green build never comes from skipping tests: neither `-DskipTests` nor `-Dmaven.test.skip=true` with Maven, nor `-x test` with Gradle, nor `@Disabled` (skill `unit-tests`, "A red test").

## Coverage and mutation

- JaCoCo and PIT when the project already has them, or on request. JaCoCo hands its agent to the test JVM through the `argLine` property: a Surefire or Failsafe `<argLine>` that does not begin with `@{argLine}` silently drops it, and the report comes out empty.
- PIT: `mvn test-compile org.pitest:pitest-maven:mutationCoverage` with the `pitest-junit5-plugin` dependency, limited to the changed classes (`-DtargetClasses=shop.pricing.*`); report in `target/pit-reports`.

## Example

```java
class OrderPricingTest {

    private final OrderPricing pricing = new OrderPricing();

    @Test
    void should_apply_loyalty_discount_when_customer_has_more_than_ten_orders() {
        // Given
        Customer loyalCustomer = aCustomer().withOrderCount(11).build();
        Cart cart = aCart().withTotal(euros(100)).build();

        // When
        Money total = pricing.totalFor(cart, loyalCustomer);

        // Then
        assertThat(total).isEqualTo(euros(90));
    }

    @ParameterizedTest(name = "{0} orders give a total of {1} €")
    @CsvSource({"10, 100", "11, 90"})
    void loyalty_discount_starts_after_ten_orders(int orders, int expectedTotal) {
        Customer customer = aCustomer().withOrderCount(orders).build();
        Cart cart = aCart().withTotal(euros(100)).build();

        assertThat(pricing.totalFor(cart, customer)).isEqualTo(euros(expectedTotal));
    }
}
```
