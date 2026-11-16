# Testing angle

The product owner and the analyst describe the path where everything goes well; the tester brings the paths that fail, far more numerous, and thinks of them before development, when they still shape the spec, rather than finding them afterwards as defects. The tester stops being the one who measures what is missing at the end, and becomes one who prevents it at the start.

For each rule of the spec:

- **The paths that fail**: refusals; boundary values (empty, zero, maximum, duplicate) and both sides of each threshold; an unexpected order of actions; going back, cancelling, starting over; an interruption halfway (network lost, application closed); two people acting on the same item; a role that should not see or do it; data already there in an older form.
- **Every path that leads to a refused action**: button, double click, keyboard shortcut, editing an existing item, import, restore, a direct call to the API. A refusal written as "it is not offered to me" is held by one path only; written by its effect ("no order is recorded"), it covers them all.
- **One proposal per real risk**: the tester brings the edge cases the others have not seen, the product owner judges their value; when the proposals become obvious, move to the next rule rather than lengthening the list.

For the slice:

- **The non-functional requirements it touches** (the response time of a new screen, more data in the backup, the platforms), read in their file, and what the acceptance check will verify. Validate or challenge each one (see `non-functional-requirements.md`, "Challenging and validating"); propose the one that is missing.
- **The main journey** that will be played end to end: the one that plays the spec's signal of success (its "Why"). A rule's scenario has no end-to-end journey of its own when the acceptance tests already cover it at the application's entry point: say so, rather than adding one.
- **What exploration will look for** once the slice is delivered (a combination of rules, a long session, unusual data): note it for yourself, not in the spec. What exploration finds becomes a test at the right level, or a new item for the product owner.

The proposed scenarios go to the product owner, in the section addressed to them, each with a concrete example.
