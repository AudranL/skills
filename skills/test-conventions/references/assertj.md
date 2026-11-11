# AssertJ

The AssertJ shape of "a precise assertion", "a clear failure message" and "a custom assertion" (skill `unit-tests`). Static import from `org.assertj.core.api.Assertions`; keep the version the project already has.

- **The most precise assertion available**: `isEqualTo(…)`, `isEmpty()`, `hasSize(2)`, `contains(…)` on an `Optional`, `isEqualByComparingTo(…)` for a `BigDecimal` (whose `equals` compares the scale). Not `isNotNull()` or `isTrue()` as the only check.
- **Collections**: `containsExactly(…)` (order included) or `containsExactlyInAnyOrder(…)`; plain `contains(…)` also passes with extra elements. `extracting(Order::reference)` compares a single property, with a readable diff.
- **The negative form of a scenario** ("… is not shown"): the complete list, `assertThat(shown).containsExactly(pen, notebook)`, never `doesNotContain(eraser)` nor a filtered list (skill `acceptance-tests`).
- **Exact text when another text can extend it** ("closes at 4" in "closes at 4:30"): `isEqualTo("closes at 4")` or an expression matched on the whole string (`matches(".* at 4")`), not `contains`. The same goes for an exception message: `hasMessage("…")` rather than `hasMessageContaining("…")` when the message matters.
- **Dates with an offset**: `isEqualTo(…)` on an `OffsetDateTime` compares instants, not offsets: `12:00+02:00` equals `10:00Z`, so a test of "shown in Paris time" still passes with a UTC date. When the offset is the behavior under test, check it too: `hasToString("2026-10-29T12:00+02:00")`, or `assertThat(date.getOffset()).isEqualTo(ZoneOffset.ofHours(2))`.
- **Exceptions**: `assertThatThrownBy(() -> …).isInstanceOf(OutOfStock.class).hasMessage("…")`, or `assertThatExceptionOfType(OutOfStock.class).isThrownBy(() -> …)`. Never `assertThatCode(…).doesNotThrowAnyException()` as the only check of a test.
- **Objects without `equals`** (DTO, entity): `usingRecursiveComparison()`, ignoring what the test does not vary (`ignoringFields("id")`); never on a value object, which has its own `equals`.
- **Several checks of one concept**: `SoftAssertions.assertSoftly(softly -> { … })` reports every gap at once.
- **Name the checked value** when the failure does not: `assertThat(customer.outstandingBalance()).as("outstanding balance").isEqualTo(euros(163))`. `as(…)` comes before the assertion.

## Custom assertions

- **A class per domain type**: `OrderAssert extends AbstractAssert<OrderAssert, Order>` (the first type is the class itself, for chaining), a constructor that calls `super(actual, OrderAssert.class)`, a static `assertThat(Order)` entry point, and one method per check in the domain's words (`isPaid()`, `hasTotal(…)`) that starts with `isNotNull()` and returns `this`.
- **The failure**: `failWithActualExpectedAndMessage(actual, expected, "…", …)` when there is an expected value: it fills in the expected and actual values, and the IDE shows the diff. `failWithMessage("…", …)` otherwise. Both keep the description given by `as(…)`.
- **One entry point for the project**: a `ShopAssertions` class with one static `assertThat` per custom assertion, imported statically next to `org.assertj.core.api.Assertions.assertThat`. Inheriting from `Assertions` only works with a single such class: with two, `assertThat(String)` becomes ambiguous.
- **Soft assertions**: a `ShopSoftAssertions extends SoftAssertions` class whose `assertThat(Order actual)` returns `proxy(OrderAssert.class, Order.class, actual)`.
- **A lighter form** for a check without a value to compare: a `Condition<Order>` (`new Condition<>(Order::isPaid, "paid")`), used with `is(paid)`, or `are(paid)` on a collection; its message only says the condition is not met.
- **The custom assertion is tested**: it passes on a paid order, and on an unpaid one `assertThatExceptionOfType(AssertionError.class).isThrownBy(() -> assertThat(unpaidOrder).isPaid()).withMessage("…")`.

```java
public class OrderAssert extends AbstractAssert<OrderAssert, Order> {

    public OrderAssert(Order actual) {
        super(actual, OrderAssert.class);
    }

    public static OrderAssert assertThat(Order actual) {
        return new OrderAssert(actual);
    }

    public OrderAssert isPaid() {
        isNotNull();
        if (!actual.isPaid()) {
            failWithMessage("Expected order %s to be paid but its status was %s", actual.reference(), actual.status());
        }
        return this;
    }

    public OrderAssert hasTotal(Money expected) {
        isNotNull();
        if (!actual.total().equals(expected)) {
            failWithActualExpectedAndMessage(actual.total(), expected,
                    "Expected the total of order %s to be %s but was %s", actual.reference(), expected, actual.total());
        }
        return this;
    }
}
```

In the test: `assertThat(order).isPaid().hasTotal(euros(90));`
