# Methods too long to test

Detail for `SKILL.md`: a method so long that no test reaches the part to change, or so nested that its cases cannot be listed. It usually mixes two shapes: stages that follow one another, and conditions and loops nested deep.

## With an automated extract method

The IDE's extract method is reliable even without tests: use it first. Pull out small pieces that can be named, and carry on. The extracted methods stay private and are tested through the public method; a piece that needs tests of its own moves into a class of its own (last item below), never gets its visibility widened. The guidance below still applies.

## Without it, or to reach a branch

- **The obvious pieces first**: a handful of lines whose name comes at once. Before extracting, count what would cross the new method's signature: each value it reads from the surrounding code, plus the one it hands back (fields do not count, they stay reachable). The fewer, the safer; a piece that needs nothing and returns nothing can hardly go wrong. Check the declared type of every value that crosses: a silent conversion (an `int` received as a `double`, another overload selected) is how an extraction most often changes behavior.
- **Coverage to see which branch a case reaches**: to know whether a given input goes through a buried branch, run the test with branch coverage, or stop it on a breakpoint in that branch: nothing is added to the code. For a test that must keep checking it, a log line in the branch, read through an in-memory appender (`SKILL.md`, step 3). It lets you characterize code far inside the method, then extract it with tests around it.
- **The rule that matters protected first**: when an important rule is tangled with secondary work (logging, display, statistics), put tests on the rule, then extract the rest around it with lighter testing.
- **The method moved into its own class**: a class whose constructor takes the method's parameters (copied as they are) and, if the method uses it, the original object, behind an interface if that object is hard to build; the body becomes its single method (`run`, `execute`), and the old method creates the object and calls it. The test builds that object directly, without what makes the original class hard to build, and goes through its single method; the pieces extracted from the body stay private to it, and those that form a responsibility of their own move on into classes of their own, which it calls.

## How to proceed

- **Keep the control flow, or name the steps.** Extracting a condition and its body separately leaves the method with nothing but its control flow and calls to named pieces: choose this when the flow itself must be reorganized (deep nesting). Extracting a condition together with its body turns the method into a list of named steps: choose this when the method is a series of stages. On the same method, the two often alternate.
- **Extract into the same class first.** Moving the pieces to other classes comes afterwards, once their names and the data they use show where they belong.
- **Small pieces, and no attachment.** Progress is slow at the start and speeds up as names appear. A badly cut extraction is inlined back and done again, rather than built upon.
