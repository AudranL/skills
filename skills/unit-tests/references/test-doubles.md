# Test doubles: examples and vocabulary

The rules are in the skill ("Test doubles"); here, one example of each double on the same use case, the contract test that keeps a fake honest, and what each book calls a fake or a mock. The examples are hand-written, without any tool, to show the role of each double; the same with Mockito, Jest, Vitest or Jasmine is in the `test-conventions` skill.

## One use case, five doubles

`PlaceOrder` places a customer's order: it asks the catalog for the price (a query), charges the customer (a command), stores the order (state), confirms it to the customer (a command), and dates it with today's date.

```ts
// Stub: answers a query.
const catalogWithPen: Catalog = { priceOf: () => euros(2) }

// A stub that accepts, and a stub that throws (Crash Test Dummy): the failure, without a real provider.
const acceptingPaymentGateway: PaymentGateway = { charge: () => {} }
const refusingPaymentGateway: PaymentGateway = {
  charge: () => { throw new PaymentRefused() },
}

// Fake: an implementation that really works, in memory.
// It has two sides: save and byId implement the Orders port,
// the only methods the code under test sees; all() is for the test alone,
// which holds the fake by its own type to read the state after the action.
class InMemoryOrders implements Orders {
  private readonly orders = new Map<OrderId, Order>()
  save(order: Order) { this.orders.set(order.id, order) }
  byId(id: OrderId) { return this.orders.get(id) }
  all() { return [...this.orders.values()] }
}

// Fake: a clock set to a known date.
const clockOnNovember2nd: Clock = { now: () => new Date('2026-11-02T10:00:00Z') }

// Spy: records the command it receives; the test checks it after the action.
class NotifierSpy implements CustomerNotifier {
  readonly confirmations: Array<{ customer: CustomerId; order: OrderId }> = []
  orderConfirmed(customer: CustomerId, order: OrderId) {
    this.confirmations.push({ customer, order })
  }
}

// Dummy: must not be used; if it is, the failure states its role (tracer object).
const unusedNotifier: CustomerNotifier = {
  orderConfirmed: () => { throw new Error('unusedNotifier: this test must not confirm any order') },
}
```

```ts
describe('Placing an order', () => {
  it('confirms the order to the customer', () => {
    const notifier = new NotifierSpy()
    const placeOrder = new PlaceOrder(catalogWithPen, acceptingPaymentGateway, new InMemoryOrders(), notifier, clockOnNovember2nd)

    const id = placeOrder.forCustomer(ALICE, PEN)

    expect(notifier.confirmations).toEqual([{ customer: ALICE, order: id }])
  })

  it('stores the order at the catalog price, dated today', () => {
    const orders = new InMemoryOrders()
    const placeOrder = new PlaceOrder(catalogWithPen, acceptingPaymentGateway, orders, new NotifierSpy(), clockOnNovember2nd)

    const id = placeOrder.forCustomer(ALICE, PEN)

    expect(orders.byId(id)).toEqual(anOrder({ id, customer: ALICE, total: euros(2), placedOn: '2026-11-02' }))
  })

  it('does not store the order when the payment is refused', () => {
    const orders = new InMemoryOrders()
    const placeOrder = new PlaceOrder(catalogWithPen, refusingPaymentGateway, orders, unusedNotifier, clockOnNovember2nd)

    expect(() => placeOrder.forCustomer(ALICE, PEN)).toThrow(PaymentRefused)
    expect(orders.all()).toEqual([])
  })
})
```

What to notice:

- **The price is a query**: the stub provides it, and no test checks that the catalog was called.
- **The confirmation is a command**: it alone is checked on the spy, on the complete list (one confirmation too many would fail the test).
- **Storage is checked through the fake's state**, not through "`save` was called": the test does not break if the code stores the order another way.
- **The accepted charge is not checked here**: it has its own test, with a spy of the `PaymentGateway`.
- **The dummy of the third test** fails the test, with a message saying why, if the code confirmed a refused order.

The same test with a **mock** in the strict sense: the expectation is set before the action, and the mock checks itself.

```ts
const notifier = new NotifierMock().expectsOrderConfirmedTo(ALICE)
new PlaceOrder(catalogWithPen, acceptingPaymentGateway, new InMemoryOrders(), notifier, clockOnNovember2nd).forCustomer(ALICE, PEN)
notifier.verify()
```

The spy keeps the Given / When / Then order and reads better; the mock is mostly useful outside-in, to write down the protocol of a neighbor that does not exist yet.

## The contract test of a fake

A fake is only worth something if it behaves like the real adapter. A single test suite describes the port's contract; it runs against the fake (unit test) and against the real adapter (integration test), only the setup changes.

```ts
function ordersContract(name: string, createOrders: () => Orders) {
  describe(`${name} honors the Orders contract`, () => {
    it('finds a stored order', () => {
      const orders = createOrders()
      orders.save(anOrder({ id: ORDER_1 }))

      expect(orders.byId(ORDER_1)).toEqual(anOrder({ id: ORDER_1 }))
    })

    it('does not find an unknown order', () => {
      const orders = createOrders()

      expect(orders.byId(UNKNOWN_ORDER)).toBeUndefined()
    })
  })
}

ordersContract('InMemoryOrders', () => new InMemoryOrders())             // in-memory-orders.test.ts
ordersContract('SqliteOrders', () => SqliteOrders.open(aTempDatabase())) // sqlite-orders.integration.test.ts
```

In Java, an abstract class `OrdersContract` holds the tests and an `abstract Orders createOrders()` method; `InMemoryOrdersTest` and `JdbcOrdersIT` extend it.