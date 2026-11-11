# Angular (TestBed, HttpTestingController, Jasmine)

- **Runner**: the project's: Jasmine with Karma in older projects, Jest, or Vitest, which recent versions of the Angular CLI generate. Jasmine's API: below.
- **Logic outside the components**, in services or pure functions, tested without `TestBed`. A class without Angular dependencies is instantiated directly; a service that uses `inject()` is obtained with `TestBed.inject(…)`, its dependencies replaced in `providers`.
- **Components**: `TestBed.configureTestingModule({ imports: [OrderSummaryComponent], providers: […] })` for a standalone component; `fixture.componentRef.setInput('order', anOrder())` for an input, then `fixture.detectChanges()` or `await fixture.whenStable()`.
- **HTTP**: `provideHttpClient()` then `provideHttpClientTesting()`, and `HttpTestingController` (`expectOne(url)`, `flush(body)`, `verify()` in `afterEach`) to test the service that speaks HTTP; the other tests receive a fake of that service. Never a real network call.
- **Asynchrony**: `async` / `await` with `fixture.whenStable()`, and the runner's fake timers for time (`vi.useFakeTimers()`, `jasmine.clock()`). `fakeAsync` / `tick` / `flush` need zone.js (under Vitest, the `zone.js/plugins/vitest-patch` polyfill too), and the Angular documentation recommends moving away from them: keep them only where the project already uses them. No `setTimeout` in tests.
- **Names**: nested `describe` blocks by situation, an `it` that reads as a sentence (`it('should disable the submit button when the form is invalid')`).
- **Jasmine**: a stub or a spy through `jasmine.createSpyObj<OrderService>('OrderService', ['load', 'save'])`, `orderService.load.and.returnValue(of(anOrder()))`, `expect(orderService.save).toHaveBeenCalledWith(order)`; `spyOn(object, 'method')` only on a boundary that cannot be injected (a browser global, `console`). Exact text (`toBe`), complete list (`toEqual([…])`), queries stubbed and commands checked.

```ts
describe('OrderApi', () => {
  let api: OrderApi;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    api = TestBed.inject(OrderApi);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should load the order by its reference', async () => {
    const order = firstValueFrom(api.byReference('A-42'));

    http.expectOne('/api/orders/A-42').flush({ reference: 'A-42', total: 90 });

    expect(await order).toEqual(anOrder({ reference: 'A-42', total: 90 }));
  });
});
```
