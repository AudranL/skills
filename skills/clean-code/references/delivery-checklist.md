# Delivery checklist for code you wrote yourself

Read this before handing over a diff you produced. An agent tends to repeat the same few mistakes; this list targets them.

## Errors

- A `catch` names an error that can be recovered from and does something about it. It never converts a failure into `null`, an empty value or a fake success, unless the function's contract says so. Otherwise a database outage reads as "no data".
- Inside a trust boundary, no check for a case the types or the caller's contract already rule out. At the boundary (external input, request payloads, deserialized data), always validate.
- Never remove, in the name of simplicity: validation at a boundary, error handling that prevents data loss, security measures (authorization, escaping, parameterized queries, secrets), anything the user explicitly asked for. Removing one is a behavior change: keep it or ask.

## Honesty

- No canned answer in code that is supposed to do real work. If you cannot implement it, fail explicitly and say so.
- Never skip, disable or weaken a test to get a green build.
- Every import and external call exists in the installed version: read the package or inspect it, do not write the API from memory.

## Fit with the codebase

- Before writing, read the file you edit, one neighbor, and the project instructions (`CLAUDE.md`, `AGENTS.md`). Search for an existing helper before writing a new one; reuse its error types and logging. One pattern per concern.
- A new dependency must own real complexity (cryptography, parsing, time zones). If a few local lines do the job, write them.
- No abstraction, option, flag or hook without a caller today (see `design-principles.md`).
- Remove what you leave unused: imports, symbols, unreachable branches. A method used only by its own test goes with its test.

## Scope and refactoring

- A refactor keeps observable behavior: same outputs, same exceptions, same side effects, same order. A bug noticed on the way is reported and fixed in a separate change after asking. Adding behavior and refactoring are two hats, never worn together.
- Clean what you touch or must understand, not the whole repository: "leave the campground cleaner", not "clean it until you could lick the floor".

## Edge cases

Before coding, write down the boundaries that concern the function: empty / one / many, first and last, off-by-one, null, even / odd, encoding (accents, case). Cover each one in the code and in a test.

Do not copy a similar function and tweak it: the copy keeps the boundaries of the original, which are not yours. Start from the spec (the rule, the scenario) and rebuild the boundaries from it.

## Last pass

1. Every catch recoverable and acting?
2. Any hard-coded success or fixture?
3. Imports and calls verified?
4. Style matched to the neighbors?
5. New abstraction or dependency unjustified?
6. Dead code left?
7. Refactor: behavior unchanged?
8. Diff within the agreed scope?
9. Boundaries listed, each one covered?

Report only what you actually changed (`file:line`, what). Do not invent a quality score.

## Knowingly breaking a rule

Leave a comment that names the principle set aside, the reason, and the condition under which to revisit it. An exception with no exit is deferred debt.
