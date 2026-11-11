# Mockito

The Mockito shape of "Test doubles" (skill `unit-tests`). Mockito makes all its doubles with `mock()`: their use in the test is what makes them a stub or a spy.

## Which double, with Mockito

| Role (skill `unit-tests`) | With Mockito |
|---|---|
| Stub | `when(catalog.priceOf(PEN)).thenReturn(euros(2))`; a failure: `when(…).thenThrow(new PaymentRefused())`, or `doThrow(…).when(gateway).charge(…)` for a `void` method |
| Spy (checking a command) | `verify(notifier).orderConfirmed(ALICE, id)` after the action; an `ArgumentCaptor` when the argument is checked part by part |
| Mock (expectations before the action) | Not in Mockito: checks happen after the action |
| Fake | A hand-written class (`InMemoryOrders implements Orders`), without Mockito |
| Dummy | Not a Mockito mock, which answers `null` or does nothing without failing: a lambda or a class that throws an error naming its role if it is called (`AuditTrail unusedAuditTrail = event -> { throw new AssertionError("unusedAuditTrail: this test must not record anything"); };`) |

Mockito's `spy()` and `@Spy` are not a spy in this sense: they wrap a real object to replace some of its methods (a partial mock), which doubles its internals. Avoid them.

## Rules

- `@ExtendWith(MockitoExtension.class)` with `@Mock`, and `@InjectMocks` on the object under test when all its dependencies are Mockito doubles. It only injects `@Mock` and `@Spy` fields: as soon as a dependency is a real object (a `Clock.fixed(…)`, a `Random` with a seed, an in-memory fake), the object under test is built by calling its constructor (`new PlaceOrder(catalog, gateway, orders, notifier, clock)`), as in the example below. A constructor parameter without its `@Mock` receives `null`, and Mockito does not say so (its documentation): a new dependency gets its `@Mock` in the test.
- **Strict stubs** (the extension's default): Mockito reports a stub the test never used (`UnnecessaryStubbingException`). It is usually a leftover, or a sign the test does not go where it claims: delete the stub. `lenient()` is for the rare setup several tests share on purpose.
- **Queries are stubbed, never verified**: a `verify` on an already stubbed query repeats the stub and ties the test to the implementation.
- **Commands are verified**: `verify(x).m(…)`, and `verify(x, never()).m(…)` for a command that must not go out. No `verifyNoMoreInteractions` by default, no `InOrder` unless the order is part of the behavior.
- **Argument matchers**: all arguments or none (`eq(…)` next to an `any()`). Prefer the exact value to `any()` for what the test varies.
- **What stays real**: values, whether a value object, a `record`, a collection or a `String`; the time, since `Clock.fixed(…)` is a ready-made fake; and of course the class under test. A third-party type is not mocked either: it is wrapped behind an interface of your own, which is.
- **`mockStatic` and `mockConstruction` when the code cannot simply be changed**: the need signals a hidden dependency, and injecting it comes first (skill `unit-tests`, "No magic"); but when changing the code to inject it costs too much, a test that mocks the static call is worth more than no test. Always in a `try`-with-resources, which stops the mock at the end of the test: `try (var dates = mockStatic(LocalDate.class, CALLS_REAL_METHODS)) { dates.when(LocalDate::now).thenReturn(NOVEMBER_2ND); … }`. `CALLS_REAL_METHODS` keeps the class's other static methods real (`LocalDate.of(…)` would return `null` otherwise), and the mock only applies to the current thread: code run in another thread still sees the real method.
- **BDDMockito** is the same API, named after the test's sections: `given(catalog.priceOf(PEN)).willReturn(euros(2))` under `// Given`, where Mockito's `when(…)` reads as if it belonged to the When; `then(notifier).should().orderConfirmed(ALICE, id)` under `// Then`. Follow the repository's choice, and never mix the two in a test class.

## Example

```java
@ExtendWith(MockitoExtension.class)
class PlaceOrderTest {

    @Mock Catalog catalog;
    @Mock PaymentGateway gateway;
    @Mock CustomerNotifier notifier;
    private final InMemoryOrders orders = new InMemoryOrders();
    private final Clock clock = Clock.fixed(Instant.parse("2026-11-02T10:00:00Z"), ZoneOffset.UTC);

    @Test
    void should_confirm_the_order_to_the_customer() {
        // Given
        when(catalog.priceOf(PEN)).thenReturn(euros(2));
        PlaceOrder placeOrder = new PlaceOrder(catalog, gateway, orders, notifier, clock);

        // When
        OrderId id = placeOrder.forCustomer(ALICE, PEN);

        // Then
        verify(notifier).orderConfirmed(ALICE, id);
    }
}
```
