# Splitting

A slice is a story small enough to be delivered and shown on its own. Before proposing a split, put each slice through these questions:

- **Can it be shown once done?** Someone outside the team (a customer, a buyer, the people who run the product) sees something change. A slice that only prepares the ground is rewritten with the value it serves, or merged into the business slice that needs it.
- **Can it be delivered before or after its neighbors?** If a slice is useless without another one, merge them or cut along another line. An order the business imposes ("the address before the delivery method") is written in the split, so that nobody discovers it halfway through development.
- **Does it state a need rather than a solution?** How to build it is the team's call; what it must do comes out of the conversation, as scenarios.
- **Can the team size it?** When nobody dares a size, name what is missing: something about the business (a question for the user), something technical (a spike), or the slice is simply too big (cut it).
- **Is it small?** Four or five rules at most, a few days of work.
- **Can each rule be shown by an example?** A word nobody can check ("fast", "easy", "never") becomes a non-functional requirement with a threshold (skill `spec-review`).

## Frame the feature before splitting it

Before proposing the slices of a feature that will take several (an onboarding, a whole journey), map it with the user: the journey end to end, in the order the information is asked for, the actors and the goal each one pursues, the business notions and what depends on what ("the delivery address before the delivery method"). The split follows from this map; the first slice is the thinnest one that crosses it. The map only carries titles and arrows: only the next slice is specified.

## Slices that go through every layer and stop where the user is done

- **Through every layer**: from what the user does to what gets stored, each slice goes all the way and changes something one can see. Not a slice for the tables, then one for the API, then one for the screen: that is three deliveries before anyone can try anything, and the pieces only meet at the end, when making them fit costs the most. Cut the other way, the product is usable from its first slices, limited but real.
- **Stopping where the user is done**: a slice ends where the user would say "there, that's done" ("change the delivery address of an order not yet shipped"), not on an activity that has no end ("manage my orders").

## Ways to split

There is usually more than one; keep the one whose first slice is the thinnest that is still useful.

- **One operation at a time**: place an order, then cancel it, then change its address.
- **The data, from the simplest**: an order of a single item first, several items next.
- **One variation of a rule at a time**: card payment first, vouchers next. Whichever comes first pays for what all of them share (taking a payment at all), and the next ones are much smaller: the first one goes alone.
- **One role at a time**: the customer first, then the customer service agent who acts on their behalf.
- **The required part, then the optional one**: an account opened with an e-mail address alone, then the optional details (phone, preferences).
- **The behavior first, its target later**: when the first users will not reach the volume the product is meant for, one slice makes it work and a later one makes it hold that volume, stated as a non-functional requirement with its threshold. The user decides this, never the developer as a shortcut.

## Splits to refuse

- **One slice per layer or component**: nothing can be tried before the last one.
- **The developer's task list** (create the table, write the endpoint, add the screen): that is how a slice gets built, not how a feature gets cut.
- **The nominal path now, its refusals later**: the boundaries and refusals of a rule stay in the slice of that rule.
- **Crumbs**: the street of a delivery address in one slice, its postcode in the next; nobody wants one without the other. The other way round, several small unrelated changes (a wording, a small fix) can share one slice.

## Too uncertain to size: a spike first

When nobody can size a slice because nobody knows how to build it, the question goes into a spike (an investigation with a timebox, that answers one question), and the slice comes after it, as a separate slice. The user weighs what the answer is worth on its own, and nobody expects the feature at the end of the spike. Its spec: `spec-template.md`, "A spike".

## A new or restarted product: the first slice is a walking skeleton

The first slice goes from one end of the product to the other along a single path, as plain as it gets (one screen, one rule, one record), but for real: built by the pipeline, installed or deployed where the user will use it, and shown to them. Each later slice adds one thing to it. Its point is less the feature than everything around it: how the product is built, installed and configured, and how it talks to the systems around it, questions better met in the first week than in the last.

## Propose a numbered split

Number the slices, the first one at the top, and have the split validated before specifying. The further a slice is, the less it is worth detailing: **only the next one** is specified, the few after it are cut to the size of a delivery, and beyond that a title is enough (an epic holds the place of a part nobody has discussed yet); the answers to come would change them anyway. The validated split enters the backlog: one epic, and one ticket to frame per slice, with its rank and a summary of one or two sentences.

## Revise the split when the scope changes

When an answer adds a notion, reveals a dependency or makes the slice grow (beyond four or five rules), or when the user cares about part of the slice and finds the rest secondary (home delivery, yes; delivery to a pickup point, later), propose to revise the split before going on: push back into a later slice what can wait, cut the current slice in two, or reorder. The split is a plan, revised with every new piece of information. If every planning ends with cutting a slice again, the remaining slices were sized too big from the start: resize them all in one pass rather than one per planning.
