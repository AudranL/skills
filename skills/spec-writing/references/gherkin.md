# Writing the Gherkin

A scenario is an example of a business rule, written so that the user can read it and a test can follow it. It says what the product does, never how.

## A scenario

- **The intent, not the gestures.** Say what the user wants done and in what situation, not where they click or how the data is stored: `Given a loyal customer`, not `Given a customer in the database with loyalty_flag=1`; `When I place my order`, not three steps that fill in a form and press a button.
- **Given: the situation before the action, and all of it.** Every precondition the outcome depends on, and no other: a missing one is an assumption the developer will guess, an extra one makes the reader look for a role it does not play. A Given states a fact that is already true ("I have placed three orders in the last twelve months"), not an action in progress.
- **When: a single action**, by the actor, in business words. Two "When" mean two behaviors, so two scenarios.
- **Then: what the user or the caller receives**, or what is now true for the business, stated as a fact ("the order is recorded"). One fact per line: several outcomes are joined by "And", so that a failure points to one of them.
- **A title that says what sets this scenario apart** from the others in the same rule, by its situation and its action, without announcing the outcome: `A basket at exactly €50`, not `The customer gets free delivery`.
- **The values that carry the rule, and no others.** Real values the reader can check against the rule (`3 orders in the last 12 months` gives `10% off`), never `foo` or `123`. A value that does not change the outcome is left out: if the customer's name plays no part, the scenario does not give one, and the reader does not wonder what it is for.
- **Both sides of a threshold.** `€49.99` and `€50.00`, not `€30` and `€80`: the off-by-one mistake is where the rule changes.
- **Fixed dates.** When a rule depends on time, the scenario sets the day (`Given today is 15 March 2027`) and gives every other date in full or relative to it ("ordered on 1 March 2027"). A scenario that reads "today" or "next month" changes meaning as the calendar moves.
- **Each scenario stands alone.** None relies on another having run before it: each sets its own Givens.
- **One person, one name.** First or third person, the one the project's `.feature` files use, kept for the whole file; an actor who has a name keeps it, and the same role, from one scenario to the next.

## Rules, refusals, and what is not shown

- **Failure cases count.** For each rule, at least one nominal scenario and one that shows the boundary or the refusal.
- **A refusal is written by its effect, not by what the screen offers.** "Then no order is recorded, and I am told my account is blocked", rather than "Then the Order button is not offered to me". Written this way, the refusal holds for every path that leads to the action (the "Order" button, "Order again" from the history, the mobile application's call), and it is checked where the action is recorded. "Is not offered to me" describes an interface, and a single path is enough to satisfy it.
- **"Only" is also written in the negative.** When a "Then" says what is shown, add an "And" that names what is not: "Then the basket shows the pen and the notebook And the eraser, out of stock, is not shown". The test that follows the scenario then checks the absence, without anyone having to remind it.
- **No screen or technique in a scenario**: no button, database column, HTTP code or log line, unless it is a real constraint (an imposed contract). A distinction that matters to the business is expressed by what the user or the caller receives. An external system's answer is written by what it means ("the carrier refuses the address"), its code stays in its contract.

## The structure of a feature file

- **`Feature:`** and its narrative: `In order to` the business goal, `As a` the role, `I want` the capability. Free text may follow, to give the context a reader needs.
- **`Rule:`** groups the scenarios under the business rule they illustrate, in the rule's own words.
- **A description under a scenario's title** (free text before the first step) can state the calculation the example applies ("10% of the basket, rounded down to the cent").
- **`Background:`** holds the Givens shared by all the scenarios of the file, or of a `Rule:` when it is placed inside it. Two or three lines at most: beyond that, someone reading one scenario has to scroll back up to know what its outcome depends on. A Given that only some scenarios share stays in those scenarios.
- **`Scenario Outline:`** with **`Examples:`** when several cases are the same behavior with other values: the columns are named in business words, and a first column can name each row (`| case | basket | delivery |`) so that a failing row says which case it is. The rows show the boundaries, not every possible combination. Never group scenarios into an outline to save lines: one behavior and one title per scenario.
- **A data table in a step** gives a list that belongs to one Given or one Then (the items of a basket); it is not an outline.
- **Tags**: only those the project already uses (a ticket key, `@wip`); none invented.

## Language

The language of the project's `.feature` files. If there are none, ask the user (French with `# language: fr` on the first line, or English). The French keywords:

| English | French |
|---|---|
| `Feature:` | `Fonctionnalité:` |
| `Rule:` | `Règle:` |
| `Background:` | `Contexte:` |
| `Scenario:` | `Scénario:` |
| `Scenario Outline:` | `Plan du scénario:` |
| `Examples:` | `Exemples:` |
| `Given` | `Étant donné`, agreed with the noun that follows (`Étant donnée une commande`, `Étant donnés deux clients`), or `Soit` |
| `When` | `Quand` |
| `Then` | `Alors` |
| `And`, `But` | `Et`, `Mais` |
