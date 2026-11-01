---
name: clean-code
description: "Rules for writing, refactoring and reviewing code, production and test code alike, whatever the stack: the four rules of Simple Design in their order (and when to extract a constant or a method), naming (intent, one word per concept, business vocabulary, a name read at the call site), functions (small, do one thing, no boolean argument, command-query separation), comments (the why), errors (domain exceptions, no null), design (SOLID, tell don't ask, explicit dependencies, value objects, an external system's model kept at the boundary, an adapter limited to the documented contract), a catalog of code smells with the refactoring that fixes each, and code review (blocking, important, suggestion). Load at the start of any task that writes, modifies, cleans up or reviews code: its rules apply from the first test of the TDD cycle, at every refactor and at every review."
---

# Clean Code

Code that works, reveals its intent, and that the next developer can change without fear. These rules hold for every stack, and for test code as much as production code.

## When to use it

| Moment | What applies |
|---|---|
| At red in the TDD cycle: the test invents the interface of code that does not exist yet | "Naming" for the classes and methods it calls, "Design" for their dependencies and types |
| At green: the least code that makes the test pass, even if imperfect (*fake it*) | Nothing more: the duplication or clumsiness it leaves is dealt with at refactor, right after |
| At refactor, tests green | "Simple Design" in its order; to get there, all the other sections, and the "Code smells" with the refactoring that fixes each, in small steps, tests rerun after every step |
| To clean up or restructure code outside a TDD cycle | The same, only under green tests; code without tests is secured first (skill `legacy-code`, if installed) |
| To review code | "Code review" |

## Simple Design, in priority order

1. Passes all the tests.
2. Reveals the intent.
3. Contains no duplication (of knowledge, not just of lines).
4. Contains as few elements as possible.

Rule 4 comes last: no interface for every class, no "just in case" abstraction.

### Extracting a constant or a private method

Extracting has a cost: the reader must jump elsewhere to learn what the code says. For something used **once**, there is no duplication to remove, so the extraction must pay for itself with information the call site lacks. The test: **does the name say something the call site does not already say?**

- **The name only repeats the content: keep it inline.** `private static final String EUR = "EUR"` then `formatPrice(total, EUR)` adds an indirection and nothing else; write `formatPrice(total, "EUR")`. Likewise a private `getTotal()` that only returns `total`.
- **The name carries a meaning or a business rule: extract.** `MAX_LOGIN_ATTEMPTS = 3` explains *why* `3`; `isEligibleForFreeShipping(order)` names a rule that `order.total() > 50 && !order.isExpress()` leaves implicit.
- **A short expression that needs a name only here: a well-named local variable**, not a field or a method: `var priceAfterDiscount = total.minus(discount);`. It stays next to its use and does not widen the scope.

The rule is about single use. As soon as the same value or the same piece of logic appears in several places, that is duplication of knowledge (rule 3) and the extraction is justified, even if the name adds little.

## Naming

- A name reveals intent: why the thing exists, what it does, how to use it. If a name needs a comment, it is a bad name.
- Pronounceable and searchable names, no obscure abbreviations, no noise (`Data`, `Info`, `Manager`, `Impl`).
- One word per concept across the code (not `fetch`, `get` and `retrieve` for the same idea).
- The business domain's vocabulary in the code (ubiquitous language). A technical term (`id`, `status`, `flag`) does not enter the domain because an external API uses it: look for the business word (e.g. the *step* of a delivery, not its `statusId`). When in doubt, ask the user.
- Classes: nouns. Booleans: `is…`, `has…`, `can…`. Methods: verbs by default, but **a name is read at the call site**: it completes the sentence started by the class or field name, without repeating what they already say (`getDeliveryStepService.forParcel(reference)`, `deliveryStepProvider.provideFor(reference)` rather than `getDeliveryStepService.getDeliveryStep(reference)`). Beware of reserved words in the language (`for`, `new`, `default`…).

## Functions

- Small. Do one thing.
- One level of abstraction per function: all the statements of a function are steps at the same level, and the level is relative to that function. A high-level function is a sequence of named steps; a low-level one is made of elementary operations. Never both in the same body. Test: the function reads as "to do X, we do A, then B, then C", where A, B and C are of the same kind.
  - Mixed: `computePrice` calls `computeSellingPriceWithoutTaxes(order)` then computes the taxes inline with `base * rate` and a loop over the tax brackets. Fix: extract `computeTaxes(base)`, so `computePrice` is `withoutTaxes + computeTaxes(withoutTaxes)`.
  - Consistent: `computeTaxes` itself may contain the loop and the multiplications, since they are its level.
  - The same goes for orchestration: `processOrder` is `validate(order)`, `applyDiscount(order)`, `save(order)`, not two calls and a raw SQL query.
- One or two levels of indentation at most; the body of an `if` or a loop is ideally a call to a well-named function.
- Few arguments; no boolean argument that changes the behavior (two functions instead).
- Command / query separation: a function changes state **or** returns a value, not both.
- No hidden side effects: a function does what its name says and nothing else. It does not modify the objects passed to it, the fields of its class, or any global state, unless its name says so (`removeExpired()`, `initializeSession()`).
- Return a new instance instead of changing the one you were given. A computation on a value (amount, period, address…) builds and returns a new object (`price.withDiscount(rate)`, `name.withMiddleInitial("L")`) and leaves the original untouched; the caller sees the change in the return value, not by surprise in an object it shared. An entity keeps its identity and changes through simple commands that return nothing; the complex calculation goes in a value object.

## Comments

- Explain yourself in the code first: extract a method with an explicit name rather than commenting a block.
- Accepted comments: the *why* of a non-obvious decision, a warning, an external constraint, the Javadoc / TSDoc of a public API.
- No commented-out code, no comment that repeats the code, no change log.

## Errors

- Exceptions rather than return codes; domain exceptions named after the problem.
- Do not return `null` or pass `null`: `Optional` in Java for an expected absence, an empty object or an exception otherwise; `strictNullChecks` in TypeScript.
- Error handling is a responsibility: a `try` is the first statement of its function.
- No catch-all: catch only the error you can recover from, and let the rest propagate. A handler never turns a failure into `null`, an empty value or "success" unless the contract documents it.
- When most callers want the same default for "nothing there", return a special case (null object) rather than `null` (see `references/design-principles.md`).

## Design

- **SOLID.** In particular SRP in the sense "one reason to change, one actor", and DIP: business code does not depend on technical details (database, HTTP, framework); the details depend on the business.
- **Tell, don't ask.** Give orders to objects rather than pulling their data to decide in their place. Law of Demeter: no `a.getB().getC().doIt()` on objects (plain data structures may be navigated). No hybrids, half object and half data structure.
- **An abstraction needs a second user.** No interface, factory, base class, option or flag without a caller today; one implementation is inlined. A wrong abstraction costs more than duplication: re-inline it, then re-abstract. The interface lives with the code that consumes it (DIP). Prefer composition over inheritance; a subtype never refuses its parent's contract (LSP).
- **Explicit dependencies**, injected through the constructor. No singleton or hidden global state. Time (`Clock`) and randomness are dependencies.
- **Fight primitive obsession with immutable value objects.** A domain concept (amount, email, identifier, quantity, period) is a type of its own, not a `String`, `int` or `double` passed around: the type validates the value once at construction, carries its behavior (`amount.plus(other)`, `email.domain()`), and stops two different concepts of the same primitive type from being swapped by mistake (`transfer(accountId, orderId)` compiles with two `String`s, not with two distinct types).
- **An external system's model stays at the boundary**, in the adapter, with its own type and an explicit translation to the domain type; **the adapter handles only the documented contract** (details and examples: `references/external-systems.md`).
- **Third-party code is wrapped at the boundary**, and learning tests pin down its behavior when unclear.

## Code smells

Long method, large class, long parameter list, duplication, feature envy, data clumps, primitive obsession, repeated `switch`, divergent change, shotgun surgery, dead code, speculative generality, comments that mask obscure code.

For each smell found: name it, name the refactoring that treats it, apply it in small steps, tests green at every step (table in `references/code-smells.md`).

## Before delivering your own code

Run `references/delivery-checklist.md` over your diff: no catch-all, no hard-coded success or fixture, every import and external call verified, style matched to the neighbors (read the file, one neighbor and `CLAUDE.md` first), no unjustified abstraction or dependency, no dead code. For a refactor, observable behavior stays identical; a bug spotted on the way is flagged and fixed separately. Stay in scope: clean what you touch, not the whole repository (Boy Scout Rule). Validate at trust boundaries; never strip validation, security or data-loss handling in the name of simplicity.

## References

- `references/design-principles.md`: Demeter, special case, abstraction, LSP/OCP, layout.
- `references/delivery-checklist.md`: checklist for code you wrote yourself.
- `references/external-systems.md`: anticorruption layer, documented contract, third-party wrappers.
- `references/code-smells.md`: smell → refactoring table.

## Code review

When asked for a review, rank the remarks by importance:

1. **Blocking**: bug, behavior not covered by a test, a test that cannot fail, security flaw.
2. **Important**: design (mixed responsibilities, dependency in the wrong direction, coupling), fragile or unreadable test.
3. **Suggestion**: naming, minor duplication, style.

For each remark: the location (`file:line`), the problem, the principle or smell concerned, and a concrete proposal (code excerpt if useful). Also point out what is done well.

Reviewed tests are also judged with the `unit-tests` skill (what makes a good test, anti-patterns to refuse), if installed.
