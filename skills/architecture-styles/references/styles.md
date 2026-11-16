# The styles

## N-tier (layers)

Presentation → business → data access. Simple and known to everyone. Fits an application that is mostly data entry and display, with few rules and few integrations.

- **Strict or relaxed**: in strict layers, each layer calls only the one right below; in relaxed layers, any layer below. Relaxed layers are the common case, and the usual drift: a controller that calls a repository directly, skipping the business layer, which then stops being the place where the rules live.
- **A lower layer never calls a higher one directly**: when it must notify it, it declares an interface (a listener, a callback) that the higher layer implements.
- **Risks**: the business depends on the database, the layers are bypassed, the logic leaks toward the interface.
- **Without a domain layer**: for a small application made of forms over tables, with few rules and a short life, putting the logic next to the screens is a legitimate choice, and cheaper. It is a fork in the road, not a first step: moving to a domain model later means rewriting that logic. Say so when recommending it.

## Hexagonal (ports and adapters)

The reference is the original article (link in `SKILL.md`). When in doubt about a point, reread it rather than relying on interpretations.

- **Intent**: the application can be driven as well by users as by programs, automated tests or scripts, and is developed and tested in isolation from its databases and devices. It works without any interface and without any database; both are plugged in.
- **The boundary that matters is inside / outside**, not left / right nor top / bottom.
- **Port**: a conversation with a purpose, defined by an API in the application's terms. **Adapter**: translates a technology (UI, HTTP, SQL, test, memory) to that port.
- **Primary side** (*driving*): the actors that drive the application (user, API, batch, test). **Secondary side** (*driven*): what the application drives (database, external service, messaging).
- **Number of ports**: a matter of judgment, often two to four. Not one port per class or per table; the hexagon's six sides mean nothing.
- **Tests**: a test stands in for a primary actor; an in-memory adapter stands in for a secondary actor. A natural progression: first tests with hard-coded values, then the interface, then an in-memory adapter, replaced later by the real database.
- **Use cases are written at the application's boundary**, with no technology detail.
- The other meaning of "port": see "Vocabularies that diverge" in `SKILL.md`.

## Onion

Concentric rings, with the domain model at the center, then the domain services, the application services, and outside the UI, the infrastructure and the tests. Every dependency points toward the center. More prescriptive than hexagonal about the inside.

## Clean architecture

Entities, use cases, interface adapters, frameworks and drivers. The dependency rule: no name from an outer circle appears in an inner circle.

- **Crossing a boundary against the flow of control**: dependency inversion. The use case calls an interface it owns (an output port), implemented outside.
- **What crosses a boundary is a simple data structure**, shaped for the convenience of the inner circle: plain values, a data transfer object, function arguments. Never an entity going outward, never a database row or a framework object going inward.
- **The structure tells the use cases**: the top-level folders say what the system does; the web, the database and the framework are details plugged in from outside.

## Bounded contexts

A **vertical** split by business model, independent of the style: each context has its own internal architecture (its hexagon).

- No dependency between the domains of two contexts.
- The shared kernel stays small and explicit; a `common` or `shared` package that keeps growing is a warning sign.
- Two contexts talk through their adapters, not through their domains (A's secondary adapter calls one of B's primary adapters), across a declared contract: a published language (types, schema, messages), stable and distinct from each side's internal model, which each side translates. The exchange format is never the model of the one who hosts it.
- **The relationship between two contexts depends on their teams**, and decides how much translation each side carries. Draw the map of the relationships that exist before the one you want:
  - **shared kernel**: a small part of the model owned together, changed only by agreement;
  - **customer and supplier**: the downstream side's needs are planned with the upstream side, which delivers them;
  - **conformist**: the upstream side has no reason to adapt, and the downstream side takes its model as it is;
  - **anticorruption layer**: the downstream side translates the upstream model into its own, at its boundary;
  - **open service**: the upstream side offers a documented protocol to all its consumers, often in a published language;
  - **separate ways**: integrating costs more than it brings; each context does without the other.
- **A tangled legacy system** is drawn as a single context, without trying to model inside it; the new contexts protect themselves from it with an anticorruption layer.
- **Reading an event timeline**: a context boundary is looked for at the pivotal events between two phases of the business, between parallel swimlanes, where a word changes meaning and where the experts change; an aggregate, around a rule that must be true at every instant. What you draw from it remains a hypothesis to have validated.
- **Aggregates**: small, built around a rule that must hold at once; one aggregate changed per transaction; another aggregate referenced by its identity, not by an object; what ties two aggregates together becomes true a little later (through an event), with a delay the business accepts. A use case that needs to change two aggregates at once questions the model: either a concept is missing, or the business accepts the delay; the rare justified exception, and how to carry it: `references/modules.md`.
- The model of an external system stops at the boundary: an anticorruption layer, with an explicit translation into the domain's model.

## Microservices

Not a code style but a decision about deployment and organization. Propose it only for a real need: independent deployment, different scaling, autonomous teams. The main risk is the distributed monolith: the complexity of distributed services without their independence.

- **On the way: the modular monolith.** One deployment, modules aligned with the bounded contexts, their boundaries held by the compiler and by architecture tests. It gives most of the design benefits without the network; the boundaries that prove right can become services later. When splitting an existing monolith, go through a few coarse services (one per business area, sharing the database at first) before fine-grained services.
- **Each service has its own database, which it alone reads and writes.** This holds between services deployed separately; sharing a database server remains possible if each service has its own schema. A data's owner is the service that writes it. To change it, another service asks the owner: a call to its API if it waits for an answer, a message otherwise. To read it: call the owner's API, or keep a local copy (replicated columns or cache) that the owner updates through events, kept for stable and small data. Two services writing the same table: one becomes its owner, the other delegates its writes to it. The only exception, recorded in an ADR: a schema shared by several services (a data domain), when consistency or volume demands it; the schema then becomes the contract, and every change touches all those services.
- **A transaction across services is no longer atomic**: what must be true at once stays inside one service; what spans several becomes true a little later, with compensation when a step fails. If the business cannot accept that delay, the two pieces of data belong to the same service.
