# Non-functional requirements

A non-functional requirement says, in a measurable way, how the product must behave rather than what it does: "the `/order` route answers in under 100 ms, 95 times out of 100", rather than "the API is fast". It is a requirement like any other: the product owner sets it, the tester verifies it. Like any other, it is there for a business reason: a slow page loses customers, an unavailable service misses a deadline, a leak costs a fine. A requirement whose miss costs nothing is not a priority.

## Who does what

- **The product owner sets the non-functional requirements**, with the user, in the project's file. They are its sole author, as for the spec, and write only the requirements the user has accepted.
- **Anyone can propose one**: the user; the product owner when a need contains a vague word ("fast", "never"); the architect, for an implicit quality that drives the architecture; the tester, for a requirement that is missing or does not fit with the others. The proposal goes to the product owner, with the template below.
- **The tester verifies them**: they challenge and validate them when reviewing a spec (see "Challenging and validating"), then verify them at every acceptance check (see "Verifying"). How they verify them and what each verification gives stay in the tester's memory, not in the product owner's file.
- **The architect says how the architecture holds a requirement** (an ADR), and keeps the ranking of the qualities that drive their decisions; they do not copy the requirements.

## The file

Readable by the whole team, next to the specs: the project's convention, otherwise `docs/specs/non-functional-requirements.md`, its name, headings and identifier prefix in the language of the project's specs (`docs/specs/besoins-non-fonctionnels.md` and `ENF-04` in French). **It holds non-functional requirements only**: no business rule (it goes in the spec), no solution (it goes in an ADR), no way of verifying them (it goes in the tester's memory). A spec points to the requirements it touches by their identifier ("Known constraints: NFR-04, NFR-07") instead of copying them: if a requirement changes, the spec stays right.

```markdown
### NFR-04 · The `/order` route answers in under 100 ms
- Situation: 50 orders per second, a catalog of 10,000 items
- Threshold: under 100 ms 95 times out of 100, under 500 ms every time
- Why: beyond that, the checkout page times out on mobile
- Source: notes of ABC-12 (YYYY-MM-DD)
```

- **No status**, no more than a business rule has one in the spec: the file holds accepted requirements only. A proposed requirement, or a value the user has not given, stays a question for the user, with a default value they only have to confirm or correct; the question and its answer are filed like the others (in the ticket's notes, when there is a backlog). A rejected requirement is not kept.
- **What holds for every requirement** (the reference data set, the machines, the period over which the thresholds hold): once, at the top of the file.

## Making a requirement measurable

- **A vague word or a "never"** becomes a question for the user, with a threshold that makes sense to the business and what a miss costs: "in under 2 seconds in 95% of cases". A "never" cannot be demonstrated; a "rarely", given a number, can.
- **The typical case and the worst case**: a proportion alone ("95 times out of 100") says nothing about the remaining 5; when they matter, a second threshold bounds them ("and under 60 seconds every time").
- **The expected load comes from the business**: before any measurement, ask how many users, how much data, which peaks. A threshold measured on an empty database proves nothing about the one in service.
- **A composite quality** ("evolvable", "reliable") breaks down into measurable requirements.
- **A requirement says what to measure, not how to verify it**: the way of verifying it does not go into the file. The tester chooses it (a measurement at the acceptance check, an automated test); an architecture rule that serves the requirement is checked by a fitness function, which the architect writes.

## Where to look for the missing ones

Response time and throughput; volume and growth of the data; availability and what happens during an outage; security and personal data (who sees what, what is kept, for how long); accessibility; the platforms and versions to support; operability (logs, alerts, backups and restoring); installing and updating.

## Challenging and validating

When reviewing a spec, the tester rereads the non-functional requirements the slice touches, and the whole file when they discover it:

- **two requirements that contradict each other** (a response time impossible with the amount of data promised elsewhere);
- **a threshold nobody knows how to measure**, or set in a situation the project cannot reproduce;
- **a requirement that is missing** for what the slice adds (a new route without a response time, more data in a backup);
- **a "never" or a vague word** left in a requirement.

Each remark goes to the product owner, as a proposal with the template above. A requirement that is measurable as it stands, in the situation it sets, is **validated**: the tester says so in their answer and notes it in their memory.

## Verifying

At every acceptance check, the tester verifies every requirement of the file, on the built application and in the situation each one sets:

- **a time threshold is measured many times** and compared with its proportion ("95 times out of 100"): a single measurement proves nothing;
- **low-level measurements** (CPU, memory, average time) are recorded to explain a failure; they fail an acceptance check only if a requirement sets them;
- **every requirement has a result**: `held`, `missed` (with the measurement) or `not verified` (and why), in the tester's language.
