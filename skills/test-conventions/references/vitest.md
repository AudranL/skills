# Vitest

## Find

- `vitest` in `package.json`, and the configuration (`vitest.config.ts`, or a `test` block in `vite.config.ts`). Follow the project for explicit imports (`import { describe, expect, it, vi } from 'vitest'`) or globals (`globals: true`).

## Name and organize

- **Location**: the project's; by default, the test next to the tested file (`order.ts`, `order.test.ts`).
- **Names**: `describe` names the concept or the business rule ("Loyalty discount"), `it` is a sentence describing the behavior, in the language of the project's code; nested `describe` blocks by situation.
- **Examples of a rule**: as many `it` as cases, or `it.each` with objects whose fields are named rather than arrays of anonymous values; the title repeats the values (`'$orders orders give a total of $expectedTotal €'`).
- **Acceptance tests**: the scenario title appears in the `describe` or the `it`, so that searching for the title finds its test; a scenario outline becomes a `describe` named after it and one `it` per example row (`it.each`).

## Assertions

- **The most precise matcher**: `toBe` for a simple value, `toEqual` for a structure (`toStrictEqual` when an `undefined` property or the class matters), `toHaveLength`, `toBeNull`. Not `toBeTruthy` or `toBeDefined` as the only check.
- **Exact text when another text can extend it**: `toBe('closes at 4')` or an anchored expression (`toMatch(/ at 4$/)`), not `toContain`, nor `toMatch('…')` with a string, which also looks for a substring.
- **The negative form** ("… is not shown"): the complete list, `expect(shown).toEqual([…])`, not a `not.toContain` nor a filtered list (skill `acceptance-tests`).
- **An expected error**: `expect(() => placeOrder(…)).toThrow(OutOfStock)`; asynchronous: `await expect(promise).rejects.toThrow(OutOfStock)`. `toThrow('…')` with a string looks for a substring of the message: anchor it (`toThrow(/^Out of stock: pen$/)`) when the message matters.
- **Snapshots** (`toMatchSnapshot`, `toMatchInlineSnapshot`) are approval tests: they record today's output, and say nothing about whether it is right until someone has read it. Keep them for a large output that rarely changes, never to check a rule; read each diff before accepting it, since `-u` rewrites every failing snapshot at once.

## Doubles

| Role (skill `unit-tests`) | With Vitest |
|---|---|
| Stub | An object literal (`{ priceOf: () => euros(2) }`), or `vi.fn().mockReturnValue(…)`, `mockResolvedValue(…)`; a failure: `mockRejectedValue(new PaymentRefused())` |
| Spy (checking a command) | A `vi.fn()` handed to the code, checked after the action: `expect(notifier.orderConfirmed).toHaveBeenCalledWith(ALICE, id)` |
| Fake | A hand-written class (`InMemoryOrders`), written once and reused by the tests that need it |
| Dummy | An object that throws an error naming its role if it is called |

- **A stateful collaborator used by several tests gets an in-memory adapter**, a fake written once (`InMemoryOrders`), rather than a `vi.fn()` reprogrammed in each test: the test checks the state the fake keeps, not the calls it received.
- **A double is typed as what it replaces** (`const notifier: CustomerNotifier = { orderConfirmed: vi.fn() }`): the compiler checks that it matches, and `as any` takes that check away.
- **`vi.spyOn`** only on a boundary that cannot be injected (a browser global, `console`), restored after the test; never on a method of the object under test or of an object of your own.
- **`vi.mock('…')`** (a whole module swapped out, the call moved above the imports): a last resort, for legacy code while it is being secured; the need signals a dependency to inject (skill `unit-tests`, "No magic").
- **No double leaks from one test to the next**: create each double in its test. `restoreMocks: true` (or `vi.restoreAllMocks()` in `afterEach`) only puts back what `vi.spyOn` replaced; it does not empty the calls recorded by a `vi.fn()` shared between tests, which `clearMocks: true` does (the default since Vitest 5). A global or an environment variable replaced with `vi.stubGlobal` or `vi.stubEnv` is put back by `unstubGlobals: true` and `unstubEnvs: true` (or `vi.unstubAllGlobals()` and `vi.unstubAllEnvs()` in `afterEach`), not by `restoreMocks`.

## Time and asynchrony

- **Time and randomness are preferably injected** (a clock, a random source): the code becomes deterministic, and the test chooses the date or the draw. When injecting them is not simple, fake timers (`vi.useFakeTimers()` and `vi.setSystemTime(…)`, restored in `afterEach` with `vi.useRealTimers()`) and `vi.spyOn(Math, 'random').mockReturnValue(…)`.
- **`async` / `await`**; no `done` callback, no `setTimeout` in a test: advance the fake timers (`vi.advanceTimersByTime(…)`, `await vi.runAllTimersAsync()`) or await the effect.

## Data and persistence

- **A Test Data Builder** that returns a valid object, to be adjusted (`anOrder({ total: 100 })`), rather than `as any` or `!` to make a test compile.
- **The persistence layer is tested against the real storage**: the real database engine and the real schema, rather than an in-memory database of another engine. What lives on disk (an SQLite file, plain files) gets a temporary folder per test (`mkdtempSync(join(tmpdir(), 'app-'))`), removed in `afterEach` (`rmSync(folder, { recursive: true, force: true })`).

## Run

- **Narrowest first**: `npx vitest run src/order.test.ts -t "Loyalty discount"`, then the whole suite through the project's script (`npm test`). Without `run`, `vitest` stays in watch mode and never returns: always `vitest run` outside an interactive terminal.
- **Coverage**: `--coverage`, with the provider the project has installed (`@vitest/coverage-v8` or `@vitest/coverage-istanbul`). **Mutation**: Stryker (`@stryker-mutator/core` and `@stryker-mutator/vitest-runner`), if the project uses it.

## Example

```ts
import { describe, expect, it } from 'vitest'

describe('Loyalty discount', () => {
  it.each([
    { orders: 10, expectedTotal: 100 },
    { orders: 11, expectedTotal: 90 },
  ])('$orders orders give a total of $expectedTotal €', ({ orders, expectedTotal }) => {
    const customer = aCustomer({ orders })

    expect(totalFor(aCart({ total: 100 }), customer)).toBe(expectedTotal)
  })
})
```
