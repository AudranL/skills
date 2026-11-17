---
name: architecture-styles
description: "Catalog of architecture styles and their trade-offs, and diagnosis of an existing architecture: n-tier (strict or relaxed layers, the data-entry application without a domain layer), hexagonal in its original definition (port, adapter, primary and secondary sides, the other meaning of port), onion, clean architecture (what crosses a boundary), bounded contexts (relationships between two contexts and their owners, published language, anticorruption layer, reading an event timeline, aggregates and what must be true at once), microservices, the modular monolith on the way, and data ownership; splitting into modules (cohesion, no cycle, stability, what the whole application shares, a transaction across modules, naming a message, metrics); questions to ask before choosing (core, supporting and generic parts of the business, the code's language), which boundaries to build fully, partially or not yet, how to organize the code (by layer, by feature, ports and adapters, by component) and let the compiler hold it; diagnosis of an existing system (observe, deduce and have it validated, record, rewrite or evolve piece by piece). Load before recommending, comparing or evolving a style, when in doubt about a term (port, adapter, shared kernel, bounded context), to split code into modules or judge a split, to propose bounded contexts and aggregates from an event timeline, or to diagnose an architecture in place or decide between rewriting it and evolving it."
metadata:
  internal: true
---

# Architecture styles

What they share: keep the business rules apart from the details (database, framework, interface, network), and make the dependencies point toward the business rules. The styles differ mostly in their vocabulary and in how many circles they draw. A project picks one, names it in an ADR, and does not mix the vocabularies.

- **The styles, one by one**: `references/styles.md` (n-tier, hexagonal, onion, clean architecture, bounded contexts, microservices).
- **Diagnosing an existing system**, and choosing between rewriting and evolving: `references/diagnosis.md`.
- **Modules**: splitting the code into modules and judging a split, what the whole application shares, data tied by an invariant, a transaction across modules and the events between them, naming a message, metrics: `references/modules.md`.

## Choosing

The questions to ask before recommending a style:

- How many business rules, and will they change often?
- Which part of the business sets the product apart from its competitors (the core), which part supports it, and which part is the same everywhere (generic)? The richest design (a domain model behind ports) is worth its cost in the core; a supporting part can stay simple (layers, mostly data entry); a generic part is bought or taken from a library, behind an adapter. One product's core can be another's generic part: ask, do not assume.
- How many external systems, and are they likely to be replaced?
- Who drives the application: interface, API, batch, messages, other applications?
- Which qualities come first (testability, performance, availability, security, time to deliver), with which threshold?
- What conventions already exist in the team or the company, and what does the team know?
- In which language is the code written (identifiers, files, tests, comments, commits, messages): who are the application's users, and who will maintain the code?

Every recommendation comes with at least two options (often including "change nothing"), the criteria, the trade-offs of each and the recommendation: there is no best practice, only the least bad combination of trade-offs for this context.

**The code's language.** Have it decided explicitly at the framing, or at the first slice of an inherited project, without deducing it from the existing code or assuming English. When the business and the team speak another language than English, recommend by default writing the code in the business's language: translating the business terms in the code creates a second vocabulary, and every translation between the people who speak the business and the code that implements it loses something. A technical concept keeps the name developers usually give it, and the terms imposed by the language and the libraries stay as they are. The decision and its conventions (scope, accents in identifiers and file names, imposed terms, coexistence with the existing code) are the subject of an ADR.

## How much boundary, and when

A full boundary costs: interfaces on both sides, data structures to cross it, separate build modules, and their upkeep. Not every boundary deserves it now:

- **Full**: separate modules, the compiler and the architecture tests hold it. For the boundaries that already carry weight (the domain against the infrastructure, two contexts owned by different teams).
- **Partial**: everything is ready but stays in one build module, or an interface on one side only (the caller depends on an interface, the implementation sits next to it), or a single entry class in front of a group of classes. Cheaper, and it keeps the place for a full boundary; but it erodes as soon as nothing holds it: give it an architecture test.
- **Not yet**: the boundary is only noted (in the ADR or the debt), and watched.

Decide boundary by boundary, and revisit the decision when friction appears (a change that touches both sides, a test that cannot be written): the right moment to build a boundary is when ignoring it starts to cost more than building it.

## Organizing the code

The top-level folders should tell what the application does (orders, billing, catalog), not which framework it uses (controllers, services, repositories). Four ways to group the code, which all respect the dependency rule on a diagram but not equally in the code:

| Grouped | Inside | Risk |
|---|---|---|
| By layer (`web`, `service`, `repository`) | Each layer's types public, so the next one can see them | A controller can call a repository directly; the business is scattered across the layers |
| By feature (`orders`, `billing`) | One package per business capability, everything but its entry point hidden | Another feature cannot reuse a piece without going through that entry point |
| Ports and adapters (`domain`, `application`, `adapters`, per context) | The domain and its ports inside, the adapters outside | The adapters' implementations stay public unless someone hides them |
| By component (`orders` with its logic and its persistence behind one interface; the interface layer outside) | Only the component's interface public | The separation inside the component is a matter of discipline |

Whichever is chosen, **let the compiler hold the boundary where it can**: an implementation that nobody outside its package should use is not public (package-private in Java, `internal` in Kotlin and C#, not exported from its TypeScript package). Fewer public types means fewer possible wrong dependencies. What the compiler cannot hold, an architecture test does (skill `architecture-tests`).

## Vocabularies that diverge

- **Port**: part of the DDD literature calls "port" the technical mechanism (HTTP, AMQP) and "adapter" what translates it. Here, a port keeps its original meaning: a conversation with a purpose, defined in the application's terms.
- **The `codebase-design` skill** (deep modules) uses "seam" in its legacy-code sense (the place where a module's interface lives), "adapter" for anything that fills an interface at a seam, and advises against "boundary". Here, "boundary" means the boundary of a bounded context or the inside / outside of the hexagon: say which meaning when the two vocabularies meet.

## Further reading

The original article on hexagonal architecture (https://alistair.cockburn.us/hexagonal-architecture): reread it when in doubt rather than relying on later interpretations.
