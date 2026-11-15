# Acceptance review

Reviewing a delivered slice, by the one who wrote the spec: compare the spec with the diff, the tests and the developer's report, without changing either the code or the tests. The criteria are the skill's: one test per scenario, at the level described in "Its level".

1. **For each scenario**, say whether it is covered and by which test. Start from the scenario-to-test table of the developer's report (skill, "The report") and check it rather than believe it: find each test by the scenario's title, read it, and run the tests. A scenario is delivered only when its test passes: a pending, skipped or disabled test, or an empty step, does not pass. For a test that was green as soon as it was written, the report says how it was seen red.
   - **Covered**: every part of its "Then" is checked, by its acceptance test at the application's entry point (skill, "Its level"), or by an end-to-end test for what only the real application shows (the journey, the way the rule appears to the user: message, presentation). A scenario does not have to be replayed end to end.
   - **Poorly covered**: tests exist, but
     - none exercises its "When" (the test checks the state before the action, not its effect);
     - a part of its "Then" is checked nowhere, or only loosely (an "is not shown" checked with a "does not contain" or on a filtered list);
     - the value that sets it apart from the others (a deadline, two equal amounts) is checked nowhere;
     - its only test goes through a real adapter (an HTTP controller, the database) or end to end, and its acceptance test at the entry point is missing;
     - or its test checks an earlier version of the scenario (a title, a step or a value that no longer matches the spec).
   - **Not covered**: no test matches it.
2. **The doubles the acceptance tests rely on**: each one has its contract test, run against the real implementation too. Without it, a scenario can be green on a double while the real adapter does something else: the scenarios that rely on that double are poorly covered.
3. **The spec's constraints**: platforms, no network request, non-functional requirements touched, with the result of their verification by the tester. A requirement not verified yet is reported as such: the slice is not accepted on it until it is.
4. **A refusal scenario**: look for every path by which the user can perform the refused action (button, shortcut, editing existing data, import), not only the one the test exercises.
5. **What was added out of scope**: a behavior that no scenario asks for. Either a scenario is missing, and the spec's author writes it with the user's agreement, or the behavior comes out.
6. **What the slice teaches** for what comes next: hypothesis confirmed or not, new questions, ideas for a next slice.

## Conclusion

The slice is accepted when every scenario is covered and its test passes, the constraints hold, and nothing was added out of scope without a scenario. Otherwise, the list of gaps goes back to the developer, each one attached to its scenario or its constraint, with what is expected.
