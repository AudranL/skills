# Diagnosing an existing system

1. **Observe** without interpreting: how the packages are organized, the direction of the dependencies, cycles, frameworks present in the domain, external models crossing the domain, bypassed layers, where the business rules actually live (controllers, SQL queries, screens, stored procedures). Module metrics if they shed light (size of each module as a share of the code base, number of dependencies in and out; instability and abstraction: `references/modules.md`). The history too: the files that are often committed together reveal a coupling the imports do not show (`git log --name-only`). A Mermaid diagram of the contexts and their dependencies if useful.
2. **Deduce and have it validated**: each structuring observation becomes a `deduced` entry (style, dependency rule, bounded context), put to the user: "I deduce that…: is it intended?" Call nothing debt as long as the rule is not confirmed.
3. **Record**: the rules (deduced, then confirmed), the gaps from a confirmed rule as debt, the rest as open questions.
4. **Rewrite or evolve.** When the user considers starting from scratch, present at least two options: evolve module by module (each module is kept, refactored or rewritten the first time a slice touches it) and rewrite in one go. Criteria: does the existing system work (code that does not work is a clear sign for a rewrite); what the users lose as long as the port is not finished; the users and the data to migrate. By default, recommend evolving module by module: the decision to redo is taken component by component, and replacing a whole system on a single date almost never works: months without anything new for the users, and a cut-over that fails costs even more.

## Replacing piece by piece

When a part has to be replaced (rewritten, or swapped for a product):

- **Take over a small piece early**: a function, a category of data, a group of users. Put it in service, and run the old and the new side by side for the rest. The scaffolding that allows it (routing, synchronizing data, two tools for a while) is the price of the insurance.
- **A translation layer between the old and the new** keeps the old model out of the new code. It grows and shrinks as pieces move across; all else being equal, move first the pieces whose translation is the smallest.
- **Once a piece runs in the new system**, remove what the translation no longer needs, and the old code that nothing calls anymore, when it can be cut out; otherwise leave it until the whole old system is switched off.
- **Data that the old system got wrong** (rounding, incomplete records) is a decision for the user, taken early: reproduce the old behavior, or correct it and explain the differences.
