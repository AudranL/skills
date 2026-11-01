# Design principles: details

Detail for the "Design" and "Errors" sections (external systems: `external-systems.md`) of `SKILL.md`.

## Law of Demeter, train wrecks, hybrids

A method should talk to friends, not strangers: only to its own class, objects it creates, its arguments, and its fields. `ctxt.getOptions().getScratchDir().getAbsolutePath()` is a train wreck.

- It is a violation **only for objects** (behavior, hidden state). For plain data structures (DTOs, records) navigation is fine: they expose structure by nature.
- The fix is not a method per path (`getAbsolutePathOfScratchDirectoryOption()`): ask what the caller wants to do with the value, and tell the object to do it (tell, don't ask).
- **Hybrids** (half object, half data structure: real behavior plus public accessors on every field) are the worst of both worlds: hard to add functions, hard to add types. Choose one.
- **Objects and data structures are opposites.** An object hides its data and exposes behavior; a data structure exposes its data and has none. Procedural code (data structures + separate functions) makes it easy to add a function but hard to add a type; object-oriented code makes it easy to add a type but hard to add a function.
- **Choose according to what is likely to change:** new types → objects; new operations on stable types → data structures and functions. Never both in one class (the hybrid above).

## Special Case (Null Object)

Instead of returning `null`, return an object with the normal protocol and a sensible default behavior (`GuestUser`, `NoCustomer`, `NullEmployee.pay()` does nothing). Callers lose their `if (x == null)`.

- Worth it only when **most** clients want the same default response. Otherwise prefer `Optional` or an exception.
- Several "nulls" can differ (no customer vs. unknown customer): several special-case classes.
- Beware of hiding a real error behind a silent default.

## Abstraction needs a second user

- Interface, factory, strategy, base class or plugin hook: only when two implementations exist today, or the spec explicitly requires the extension. One implementation: inline it.
- Triangulation: abstract only from two or more examples.
- Speculative generality: a hook, parameter, option or abstract class added for a need that "might come someday" costs reading and maintenance today, and the future need rarely has the shape guessed. Delete it. A method or class used only by its own tests is a sign: delete both.
- A wrong abstraction costs more than duplication. If an abstraction has grown a branch per caller, re-inline it into the callers, then re-abstract what is really common.
- Duplicate **knowledge** is the target, not similar-looking text: two functions that encode different rules are not duplication.

## Where the interface lives (DIP)

An interface belongs to the package that **consumes** it, not next to its implementation. The domain declares the port it needs; the infrastructure implements it.

## Composition over inheritance, LSP

- Prefer composition and delegation; inherit only for a true "is-a" substitutable relationship.
- A subtype never refuses its parent's contract: no override that throws "not supported", no stronger preconditions, no weaker postconditions. If you need that, the hierarchy is wrong.
- Interface segregation: do not force a client to depend on methods it does not use.
- OCP: if a new variant forces another type-tag branch in an existing function, refactor to polymorphism or a strategy first.

## Ceilings (heuristics, not laws)

Arguments: three or more call for a justification, five or more call for a parameter object. Cyclomatic complexity about 10, nesting about 3. Treat as alarm bells to look at the design, never as the goal. The project's linter configuration wins.

## Layout

- Stepdown rule: each function is followed by those at the next level of abstraction, so the file reads top-down.
- Related concepts stay vertically close; variables are declared near their use.
- Formatting is decided once and automated (formatter); it is not debated in review.
