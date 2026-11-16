# Modules

How to split the code into modules, and how to judge an existing split. The metrics at the end serve a diagnosis, never a goal.

## Cohesion and dependencies

- **What changes together for the same reason goes together.** A module groups what one kind of change touches; a change that touches several modules every time says the split is wrong.
- **No module forces its users to depend on what they do not use.** A module whose users each take a different part of it is a candidate for splitting in two.
- **The two pull against each other.** The first makes modules larger, the second smaller. Early in a project, favor the first: keeping a change inside one module matters more than reuse; split when other modules start to take only part of one. The split moves as the code grows: it is not drawn once, up front.
- **No cycle between modules**, held by an architecture test (skill `architecture-tests`). To break a cycle: invert one dependency (an interface in the module that uses it, implemented by the other), or move what both depend on into a new module.
- **Depend in the direction of stability.** A module that many others depend on must not depend on a module that changes often. Decide which modules are meant to change often (the screens, a rule revised at every release) and let nothing stable depend on them; when a stable module needs one, invert the dependency as for a cycle.
- **A stable module is abstract**, so that it can be extended without being modified. With the previous rule: dependencies point toward abstractions, which is dependency inversion at the scale of modules.

## What the whole application shares

It is created once, at the application's root. A clock, an ID generator, the configuration of a shared client are created at startup, where the application is assembled (its entry point, its configuration or its application state, depending on the stack), then handed to the modules by injection. Only what several modules use goes there: the root is not a common folder. The configuration of a single module (the database client of an adapter) stays in that module.

**Nothing depends on the root.** It is the only place that knows every concrete implementation, and no module imports it (an architecture test can forbid it, skill `architecture-tests`). The application can have one root per configuration (production, tests with in-memory adapters, a demo), each assembling its own adapters: a module never checks which environment it runs in.

## Data and transactions

- **Data tied by an invariant joins the aggregate of the data it ties.** When a rule must always hold between a new piece of data and existing data, checked in the same action, the new data joins their aggregate and their module: the rule is checked in one transaction, with no coordination. If the rule can wait (eventual consistency), the data can live elsewhere. Ask the product owner whether the rule must hold at once or after a delay, and which delay; when the answer hesitates, ask whose job it is to make the data consistent: the user performing the action (at once), or another user or the system (later). An aggregate grows only for a true invariant, not for reading convenience.
- **One transaction across several modules.** By default, a transaction changes one aggregate; the others follow by eventual consistency. The exception is justified when saving them together changes none of their invariants (several aggregates created at once, each keeping its rules), when a single user acts on that data, or when there is no asynchronous mechanism (messaging, background job). The use case that coordinates then lives in a module that depends on the modules it changes, never the reverse; it applies their rules without copying them, and a single save port carries the transaction. The decision is the subject of an ADR.
- **A listener inside the transaction is a transaction across modules.** A handler that runs during the save and changes another module's aggregate makes one transaction of two, without the previous rule's justification or its ADR. Under eventual consistency, the other module changes in its own transaction, after the first one commits.
- **The event is saved with the change.** The event that tells another module about a change is recorded in the same transaction as the change (a table of events to send, read by a forwarder), then delivered. Sent on its own, it is lost on a crash between the save and the send, or announces a change that was never saved. The receiver accepts the same event twice without harm.

## Naming a message

To name a channel, a route or a messaging topic, separate three questions and show them to the user:

- **Who handles it**: the module, the aggregate that guards the rule.
- **What it does**: a command that changes a state, a query or a computation without side effects, or an event that announces a fact.
- **Who owns the data**: the entity, in its aggregate.

By default, the prefix names the module that handles the message, like the file of its contract, and the name states the intent in the business's language; the owner reads in the name and in the types. A computation is named after what it computes, not after the argument it receives. A prefix per owner holds only if the owner is a module: otherwise the name states a split that the code does not have.

**An event is named by the module where it happened.** It states a fact in the past tense, in the business's words (an order placed, a payment refused), under the prefix of the module that emits it: it belongs to that module's contract, and its subscribers, however many, do not appear in its name. A command belongs to the module that carries it out; an event, to the module that announces it.

## Metrics, for a diagnosis

- **Instability** `I = Ce / (Ca + Ce)`: outgoing dependencies over all dependencies.
- **Abstraction** `A`: the share of abstract classes and interfaces in the module.
- **Distance from the main sequence** `D = |A + I − 1|`.

A stable and concrete module (I ≈ 0, A ≈ 0) is painful to change; an unstable and abstract module serves no one.

**Only what changes hurts.** A stable, concrete module that rarely changes (value types, a basic utility library) is harmless in that corner; the real problem is one that changes often, a database schema read by many modules being the usual case. The metrics do not show how often a module changes: the history does (`git log`). To watch a metric at every build, with a threshold: skill `architecture-tests`.
