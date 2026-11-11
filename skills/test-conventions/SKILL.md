---
name: test-conventions
description: "Conventions of each test tool, one reference per tool: JUnit 5 and 6 (naming, @Nested, parameterized tests, Surefire and Failsafe), AssertJ (precise assertions, exact text, complete list, custom assertions), Mockito (stub or spy, what not to mock, strict stubs), Spring Boot Test (the pyramid level of each Spring test, slices, @MockitoBean), Jest and Vitest, one reference each (it.each, jest.fn or vi.fn, fake timers, in-memory adapters, snapshots), Testing Library for Angular and React (queries by role, userEvent), Angular (TestBed, HttpTestingController, Jasmine) and Cucumber (thin steps, Gherkin in another language, state per scenario). Use before writing the first test in a repository, or to name, organize, equip or run a test with a given tool. Does not override the conventions already in place in the repository; what depends on no tool is in the unit-tests skill."
---

# Test conventions per tool

What depends on no tool lives elsewhere: what makes a good test, where to test a rule, test doubles and red tests in the `unit-tests` skill; the TDD cycle in the agent that writes the code (or the `tdd` skill); acceptance and end-to-end tests in their own skills (`acceptance-tests`, `e2e-tests`). This skill only gives the shape those rules take with each tool.

A project combines several tools (a runner, an assertion library, a doubles library, sometimes a component testing library and a Gherkin runner), and the same tool serves several languages or frameworks (Testing Library with Angular and React, Cucumber in Java and TypeScript, Vitest with Angular or React): the references follow the tools, not the languages.

1. **Find the tools** in the build:

   | Clue in the repository | Tool | Reference |
   |---|---|---|
   | `junit-jupiter` or `junit-bom` in `pom.xml` / `build.gradle*` | JUnit 5 or 6 | `references/junit.md` |
   | `assertj-core` | AssertJ | `references/assertj.md` |
   | `mockito-core`, `mockito-junit-jupiter` | Mockito | `references/mockito.md` |
   | `spring-boot-starter-test` (brings JUnit, AssertJ and Mockito: read all four) | Spring Boot Test | `references/spring-boot-test.md` |
   | `jest` in `package.json` | Jest | `references/jest.md` |
   | `vitest` in `package.json` | Vitest | `references/vitest.md` |
   | `@testing-library/angular`, `@testing-library/react` | Testing Library (Angular Testing Library, React Testing Library) | `references/testing-library.md` |
   | `angular.json` | Angular (TestBed, HttpTestingController, Jasmine) | `references/angular.md` |
   | `io.cucumber`, `@cucumber/cucumber`, `jest-cucumber`, `.feature` files | Cucumber | `references/cucumber.md` |

2. **Read every reference that matches**: a Java / Spring Boot repository often reads four (JUnit, AssertJ, Mockito, Spring Boot Test), an Angular one `angular.md`, plus Jest or Vitest if it runs on one of them and Testing Library if it has it; a React one Jest or Vitest and Testing Library.

3. **The repository's convention wins.** Look at a few representative tests: when the repository does things differently from the reference (naming, location, library), follow the repository, and record what it does in the memory of the agent writing the test. A tool the repository does not have yet (AssertJ, Mockito, Testing Library, Cucumber, a coverage or mutation tool) is a new build dependency: ask before adding it, as `acceptance-tests` does for Cucumber. A tool missing from this list is handled the same way: the repository's conventions, then the tool's documentation.

**Elsewhere**: Playwright, Cypress, Selenium in the `e2e-tests` skill; ApprovalTests in `golden-master`; ArchUnit, dependency-cruiser in `architecture-tests`.

**Adding a tool**: one reference per tool, on the same outline (find, name and organize, assertions, doubles, time and asynchrony, run, example). It does not repeat the `unit-tests` skill; it says what shape its rules take with that tool. It stands on its own: the table above does the routing, so it links to another reference only when that is really useful.
