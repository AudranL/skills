# ArchUnit (Java, Kotlin)

User guide: https://www.archunit.org/userguide/html/000_Index.html

## Setup

- Dependency `com.tngtech.archunit:archunit-junit5`, scope `test`. It is a new build dependency: the user's agreement.
- Location: the project's convention; otherwise, propose an `architecture` package under the test root.
- Reference models, to adapt and not to copy: `HexagonalArchTest` from jhipster-lite (https://github.com/jhipster/jhipster-lite/blob/main/src/test/java/tech/jhipster/lite/HexagonalArchTest.java), and `AnnotationArchTest` for test conventions.

## Before ArchUnit: what the compiler holds

- **Package-private implementations**: an adapter, a repository implementation, a use case's internal classes are not `public`; only the port and what another package must call are. Spring instantiates package-private classes without trouble.
- **Build modules**: a Maven or Gradle module per layer or per context makes a forbidden dependency fail at compilation, with no test to write. ArchUnit then checks what modules cannot say (no framework in the domain, cycles inside a module).

## Marking the architecture in the code

Tests rely on **marker annotations** rather than on package or class names: a context, a port or an adapter is declared, not guessed. The annotation also documents the class's role for the reader. Two options, to settle in an ADR:

1. **The project's own annotations** (for instance in an `annotations` package at the root of the code): `@BoundedContext` and `@SharedKernel` on `package-info.java`, `@PrimaryPort`, `@SecondaryPort`, `@PrimaryAdapter`, `@SecondaryAdapter` on types, plus domain notions (`@DomainObject`, `@DomainService`, `@DomainEvent`, `@AntiCorruptionLayer`).
    - For: no external dependency, the team's vocabulary, a Javadoc that explains each notion. The annotations can also carry configuration (for instance, meta-annotating `@SecondaryAdapter` with `@ProductionScope` to choose the implementation per environment).
    - Against: the ArchUnit rules are yours to write and maintain.
2. **jMolecules** (https://github.com/xmolecules/jmolecules): standard annotations (`org.jmolecules.ddd.annotation.BoundedContext`, `org.jmolecules.architecture.hexagonal.PrimaryPort`, `SecondaryAdapter`…, and the equivalent for onion and layers), with ready-made ArchUnit rules in `org.jmolecules.integrations:jmolecules-archunit`: `JMoleculesArchitectureRules.ensureHexagonal()`, `ensureOnionSimple()`, `ensureOnionClassical()`, `ensureLayering()`, and `JMoleculesDddRules.all()`.
    - For: a vocabulary shared beyond the team, ready and maintained rules, recognized by other tools (Spring Modulith, generated documentation).
    - Against: an external dependency in the domain (annotations only, without transitive dependencies), no direct equivalent of the shared kernel, rules less precise than hand-written ones.

The two combine: jMolecules annotations for the standard roles, the project's rules for what they do not cover (shared kernel, communication between contexts).

Rules that follow: a marker annotation has `RUNTIME` retention if a test reads it by reflection (as on `package-info.java`); a rule checks that every class that looks like a port or an adapter (name, package) does carry the annotation, otherwise an unannotated class escapes the tests.

## Spring Modulith

In a Spring Boot application split into modules (one top-level package per module under the application's package), `ApplicationModules.of(Application.class).verify()` in a test checks that modules form no cycle and only use each other's public package, not their sub-packages. It is a ready-made rule for the boundaries between modules, which can stand in for part of the hand-written ones; it is a new build dependency (`spring-modulith-starter-test`), with its ADR.

## The usual rules in ArchUnit

- **Bounded contexts and shared kernels found by annotation** on `package-info.java` (`@BoundedContext`, `@SharedKernel`) rather than listed by hand: a new context is covered without touching the test.
- **Per context**, a `layeredArchitecture().consideringOnlyDependenciesInAnyPackage(context + "..").withOptionalLayers(true)`: domain, application, primary adapters, secondary adapters; the adapters are accessed by no layer (`mayNotBeAccessedByAnyLayer`).
- **The domain** depends only on itself, `java..`, the shared kernels and the short list of utilities decided in the ADR: `noClasses().that().resideInAPackage("..domain..").should().dependOnClassesThat().resideInAnyPackage("org.springframework..", "jakarta.persistence..", "com.fasterxml.jackson..")` gives a precise message for the most frequent leaks, alongside the positive rule.
- **No domain between contexts**: `slices().matching("<root>.(*).domain..").should().notDependOnEachOther()`.
- **Onion**: `Architectures.onionArchitecture()`.
- **No cycle**: `slices().matching("<root>.(*)..").should().beFreeOfCycles()`.
- **Visibility held**: `classes().that().areAnnotatedWith(SecondaryAdapter.class).should().notBePublic()`, when the project chose package-private adapters.

## Good practices

- **One mechanism per test class**: either `@Test` methods that call `.check(classes)`, or `@AnalyzeClasses` with `@ArchTest` fields or methods. An `@ArchTest` method in a class without `@AnalyzeClasses` never runs, and the test passes in silence.
- **Import the classes once**, in a static field or through `@AnalyzeClasses(packagesOf = Application.class, importOptions = ImportOption.DoNotIncludeTests.class)`, without the tests.
- **`because(…)`** in plain words, pointing to the rule (`A-002`) or the ADR.
- **No `allowEmptyShould(true)` by reflex**: by default, ArchUnit fails when a rule applies to no class, which reveals a misnamed package. Allow it only for a convention not used yet, and say so.

## Freezing existing violations

`FreezingArchRule.freeze(rule)`:

- On the first run, ArchUnit records the current violations in a store, configured in `src/test/resources/archunit.properties`: `freeze.store.default.path`, and `freeze.store.default.allowStoreCreation=true` to allow its creation.
- Then the test fails only on a **new** violation. A fixed violation leaves the store and cannot come back: the number of violations can only go down.
- The store is versioned. Regenerating it (`freeze.refreeze=true`) to make a test pass is weakening a test: never without the user's agreement.
