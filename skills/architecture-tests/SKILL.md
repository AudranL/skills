---
name: architecture-tests
description: "Write, review and maintain architecture tests (fitness functions) that check a project's structural rules: direction of dependencies between layers, boundaries between modules or bounded contexts, no cycles, every source file in a declared zone, folders reserved for types, forbidden imports, naming conventions, metrics with a threshold. First lets the compiler hold what it can (visibility, build modules, package exports), then picks the tool for the stack: ArchUnit (with jMolecules or Spring Modulith) in Java or Kotlin; a hand-written test with the TypeScript compiler, dependency-cruiser, eslint-plugin-boundaries or Nx module boundaries in TypeScript or JavaScript. Use to set up an architecture test, turn an ADR's rule into a test, freeze existing violations, or review an architecture test that passes too easily."
---

# Architecture tests

An architecture test is a fitness function: any automated check of a characteristic of the architecture, either one characteristic on its own (the direction of a dependency, no cycle between modules) or several that pull against each other and are checked together (security and response time). It makes a written rule (an ADR) verifiable at every build: an untested rule erodes, and a code review finds the violation days after it spread, when it is already copied elsewhere.

## Let the compiler hold what it can

A rule the compiler holds cannot be bypassed, and the developer sees it in the editor before any test runs. Before writing a test, see whether the structure can carry the rule:

- **Visibility**: only what another module must use is public; the implementations (an adapter, a repository, a use case's internals) are package-private in Java, `internal` in Kotlin or C#. Grouping a feature's classes in one package lets most of them be hidden.
- **Build modules**: one Maven or Gradle module per layer or per context, whose declared dependencies are the allowed ones (Java modules with `module-info.java` go further: only exported packages are visible).
- **In TypeScript**: a workspace package exposes only what its `exports` field lists; a project with `composite: true` cannot import a file outside its `include` without referencing the other project.

An architecture test then covers what visibility cannot express (no framework in the domain, no cycle, a folder reserved for types), and checks that the visibility itself is not loosened.

## Choosing the tool

Find the stack (build files, `package.json`, `tsconfig.json`) and the architecture tests already in place: if there are some, follow their tool and their shape.

| Stack | Tool | Reference |
|---|---|---|
| Java, Kotlin (JVM) | ArchUnit, with or without the jMolecules annotations; Spring Modulith for the modules of a Spring Boot application | `references/archunit.md` |
| TypeScript, JavaScript | A hand-written test with the TypeScript compiler, or dependency-cruiser, or eslint-plugin-boundaries; in an Nx monorepo, its module boundaries rule | `references/typescript.md` |
| Another language | A test that reads the imports with the language's parser, in the project's test framework | The principles below |

One more tool is a new build dependency: it needs the user's agreement and an ADR. A hand-written test adds nothing to the build, but it is code to maintain.

## Principles, whatever the tool

- **One rule, one test, one ADR.** The test's name or its failure message cites the rule (`A-002`, `ADR 003`) and states it in plain words: that is what the developer who breaks it will read.
- **The failure message lists the culprits**: the file and the offending import ("`domain/order.ts` imports \"express\""). Compare the list of violations with an empty list rather than a boolean.
- **Find the architecture through a declaration**, not by guessing from names: an annotation on the module, a declaration file, or the list of folders at the top of the test, in one place. A new module is then covered without touching the rules. The way of marking is an architecture decision (ADR).
- **Every source file belongs to a declared zone**: a test fails on a file outside any zone, so that a new folder is never left unchecked.
- **Read every import**: static, dynamic (`import()`, `require`), re-exports, type-only imports, path aliases. Depending on the rule, a type import may be allowed where a code import is not.
- **See each rule fail once.** Introduce a violation (a forbidden import), run the test, see it red for the right reason, then undo. A rule that has never been red proves nothing.
- **A rule with nothing to check fails.** If the folder or the marker it targets no longer designates any file (renamed, emptied), the test fails instead of passing in silence.
- **An exception is declared, never slipped in.** A known exception sits next to the rule, with its ADR and its reason; widening the rule's pattern until the offender no longer matches weakens the rule for everyone.
- **Freeze rather than fix everything first.** In code that already breaks a rule, record the current violations in a versioned file: the test fails only on a new violation, and a fixed violation leaves the file and cannot come back. Regenerating that file to make a test pass is weakening a test: never without the user's agreement. Each frozen rule has its debt entry, with the number of violations at the start.
- **Architecture tests run with the others**, at every build, fast enough to sit with the unit tests, not in a separate command someone forgets.
- **A recurring review remark becomes a test**: the second time a review points out the same kind of dependency, write the rule rather than repeat the remark.
- **What an architecture test does not check**: the business meaning of names, whether a model is right, the right number of ports. That belongs to the review (skill `architecture-review`).

## Usual rules

To adapt to the style the project chose (hexagonal, onion, clean architecture, layers, bounded contexts; skill `architecture-styles`):

- **The domain** depends only on itself, the language's standard library, the shared kernels and a short list of utilities. That list is an architecture decision: each addition is discussed and traced.
- **Layers**: per context or per module, domain, application (use cases), primary adapters, secondary adapters; no layer calls an adapter; the primary side does not depend on the secondary side; the secondary side does not depend on the application.
- **Ports and adapters**: ports are interfaces of the domain or the application; a secondary adapter implements a port.
- **Bounded contexts**: no dependency between the domains of two contexts; they talk through their adapters or through a declared contract.
- **No cycle** between modules.
- **A contract folder** (types shared between processes or modules) holds type declarations only, no executed code.
- **Forbidden imports** that carry a quality: no network module in an application that promises to send nothing, no direct database access outside the adapters.
- **File naming conventions** decided in an ADR (case, allowed characters).

## Metrics with a threshold

Some rules are not a yes or a no but a trend to watch: the number of dependencies of a module (incoming, outgoing or both), a module's share of the code base, dependencies that point toward the more volatile modules rather than toward the stable ones. Such a check computes the metric for each module, compares it with a threshold decided with the user, and lists the modules beyond it. It starts a discussion rather than blocking a delivery: run it with the build and report it, and make it fail only when the user decides the threshold is a rule.
