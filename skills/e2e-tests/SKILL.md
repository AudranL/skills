---
name: e2e-tests
description: "Write, run and maintain end-to-end tests (journeys played from the outside on the application as it will be delivered) that disturb nobody and do not lie: few journeys, one per main user goal, a defect they catch also tested lower down; each one readable as its scenario (scenario, user actions in business words, screen details kept in one place); target by role and accessible name; exact text when another text can extend it; wait for an effect, never for a duration; isolation (temporary data folder, fresh context, network blocked, shared resources reset at the start), independent of order, date and chance; no visible window, no focus taken; journey seen red; traces kept on failure; screenshots checked then looked at; a flaky journey understood rather than rerun. Details for Playwright (browser and Electron), and a line for Cypress and Selenium. Load before writing the first end-to-end journey of a repository, before adding or fixing one, or to take screenshots of an application."
---

# End-to-end tests

An end-to-end test plays a journey on the application as it will be delivered, from the outside: built, packaged and installed the way users get it, driven through the doors they use. It tells whether the product works for its users, not whether its code is well written. It is costly to write, slow and more fragile than the others: it checks the main journeys and the wiring, not the rules, which are checked lower down. Tests that call the internal code can all pass while the delivered application does nothing: only an end-to-end test sees that.

The details of a tool: `references/playwright.md` (browser and Electron); for the others, `references/other-tools.md`. The repository's convention comes first: start from the existing journeys, then from the tool's documentation.

## Few journeys, well chosen

- **One journey per main user goal**: the one that plays the signal of success of a spec (its "Why"), and the wiring that only the real application has (data kept after a restart, packaging, rendering, the real external system's configuration). A rule's variations are covered by the acceptance tests at the entry point and by unit tests (skill `acceptance-tests`): do not replay each scenario end to end.
- **A defect an end-to-end journey catches is also tested lower down**, where the rule lives and the test runs in milliseconds: the journey said that something is broken, the lower test says where, and keeps it from coming back.

## A journey reads like its scenario

- **Three layers**: the scenario (its title and steps, those of the spec); the user's actions in business words ("book a bike"); the screen details (roles, labels, selectors), kept in one place, one object per screen or per screen part reused across screens (a menu, a list). A label that changes is fixed in that place only. Screen objects act and read; the journey asserts.
- **The journey's title is the title of the scenario it plays**: searching for the title finds the journey.

## Targeting and checking

- **Target an element by its role and accessible name** (a "Save" button, an "Address" field), not by a CSS class, a position or a technical identifier. If a landmark is missing, ask the one who writes the production code for it rather than adding it yourself.
- **An expected text is matched exactly when another text can extend it**: "Gate 4" is also found in "Gate 42", and the journey can no longer fail. Use the tool's exact match or an anchored expression (`/Gate 4$/`).
- **Wait for an effect, never for a duration.** A journey waits for a visible change (a text, a state of the screen, a file written) with a maximum delay set in one place, never a fixed pause. When the expected state is the starting one (a list emptied, a counter back to zero), first wait for a sign that the action happened: otherwise the journey passes before the application has done anything, and would pass just as well if it never did.
- **A journey that fails now and then is to be understood, not rerun.** The cause can be in the test (waiting for a duration, state shared with another journey, an order between journeys) or in the application (a real race that users will also meet): an automatic retry hides both.

## Disturbing nobody

- **No visible window, no focus taken**: the application starts in the mode provided for tests (hidden window), never in a way that would receive the user's keystrokes. The journey fails if a window of the application is still visible at the end. If the application has no such mode, ask for it before the first journey: it is test configuration, chosen at launch.
- **Never the user's data**: a temporary data folder per test, created then deleted; a fresh context per test (no shared session or storage); the network blocked, except what the journey has to call.
- **A resource that cannot be made per test** (a shared test server, a database) is reset to a known state at the start of each test, not only at the end: an interrupted run never spoils the next one, and what it left helps understand its failure.
- **On the application as it will be delivered** (installer, package, image), not on the development server: the same build that goes through the other checks.

## Independent of order, date and chance

- **Each journey runs alone and in any order**: it creates what it needs through the application's own doors (its screens, its API, its import), never by writing into its storage behind its back, which ties the journey to a schema it does not test.
- **No date of the day, no random input**: a journey that depends on today's date or on a random value passes or fails depending on when it runs. Use dates relative to a fixed one, or the fixed clock the tool or the application's test configuration offers.

## No false green

- **See it red**: a journey written on behavior already delivered is seen failing, against the previous build or by a manual mutation made in a temporary copy of the repository (`git worktree add`, removed afterwards), and you say so. Not in the working copy: others write in it, and a `git checkout` to undo would erase their uncommitted changes there.
- **A screen size requirement is measured with scroll bars that take up width**, forced on the tested process only, never on the user's setting. It is also measured by checking that nothing is cut, not only that nothing scrolls: an `overflow: hidden` holds "no scrolling" by hiding the content.
- **A screenshot first checks what it shows** (an expected text), animations disabled, then it is looked at before being handed over: a screenshot nobody looked at can lie. Its name says the scenario it shows.

## When a journey fails

- **The failure says what to look at**: keep the trace, the screenshot at the moment of failure and the application's logs for a failed journey only, next to the report.
- **The journeys run on every change of the main branch**, after the faster tests, on the packaged build; a red journey stops the delivery like any other red test (skill `unit-tests`, "A red test").
