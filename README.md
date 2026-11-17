# Skills for an agile team

> **Work in progress.** These skills are still being developed: their rules, their references, their scripts and their names may change from one version to the next, with no compatibility guaranteed.

Sixteen skills for Claude Code, GitHub Copilot and opencode: specify, design, develop in TDD and test. They are the prerequisites of the agents in the [agents](https://github.com/AudranL/agents) repository, but each one also works on its own: an agent or an assistant loads it when its description matches the task.

## Contents

| Skill | What it does | Agents that use it |
|---|---|---|
| `acceptance-tests` | Acceptance tests drawn from the Gherkin scenarios of a spec (the outer loop of ATDD), and the acceptance review of a delivered slice | `product-owner`, `software-engineer` |
| `adr-writer` | Writes, completes, supersedes and deprecates ADRs, following the project's template | `software-architect` |
| `agent-memory` | Protocol for the memory an agent keeps in a project: index, statuses, validation of deduced entries, upkeep, handing entries over to another agent | all five |
| `architecture-review` | Architecture review of a diff, a branch or a delivered slice, and architecture debt proposed as a slice | `software-architect` |
| `architecture-styles` | Catalog of architecture styles and their trade-offs, splitting into modules, diagnosis of an existing architecture | `software-architect` |
| `architecture-tests` | Architecture tests (fitness functions) for the stack: ArchUnit, TypeScript compiler, dependency-cruiser… | `software-architect` |
| `clean-code` | Simple Design, naming, functions, comments, errors, design, code smells and code review | `software-engineer` |
| `cyclomatic-complexity` | McCabe complexity of a method, a class or a set of Java / TypeScript / JavaScript files (script), thresholds, how to read the result, and the refactoring that reduces each kind of decision point; measures and recommends, does not refactor without tests | none (used on its own) |
| `e2e-tests` | End-to-end tests that disturb nobody and do not lie (Playwright, browser and Electron; a line for Cypress and Selenium) | `quality-analyst` |
| `golden-master` | Golden master on Java / Spring Boot code before a refactoring (ApprovalTests, JaCoCo, PIT) | `software-engineer` (optional) |
| `kanban` | Local Markdown backlog: a board in the terminal or in the browser (`kanban.py board`, `serve`), tickets created, moved and checked (`new`, `move`, `check`), refinement notes, push to Jira | `product-owner`, `orchestrator` |
| `legacy-code` | Changing code without tests: dependencies extracted and injected to make it deterministic, characterization tests, then the change in TDD; new code beside the old when time runs short | `software-engineer` |
| `spec-review` | Review of a spec by three (product owner, architect, tester), and non-functional requirements | `product-owner`, `software-architect`, `quality-analyst` |
| `spec-writing` | Splitting a feature into slices and writing the spec of one slice, with its Gherkin scenarios | `product-owner` |
| `test-conventions` | Conventions of each test tool: JUnit, AssertJ, Mockito, Spring Boot Test, Jest, Vitest, Testing Library, Angular, Cucumber | `software-engineer` |
| `unit-tests` | What makes a good test, where to test a rule, anti-patterns, test doubles, a red or flaky test | `software-engineer` |

## Prerequisites

- **Python 3** (standard library only) for the scripts of `kanban`, `golden-master` and `cyclomatic-complexity`.
- **Java and Maven** for `golden-master`, which adds ApprovalTests, JaCoCo and PIT to the project.
- **Optional skills** by Matt Pocock ([mattpocock/skills](https://github.com/mattpocock/skills)), which some skills mention when they are installed: `domain-modeling` (`adr-writer`), `codebase-design` (`architecture-styles`), `tdd` (`unit-tests`, `test-conventions`, `cyclomatic-complexity`).
- **MCP server** (optional): a Jira (Atlassian) MCP server, for `kanban` to push tickets to Jira.

## Installation

```sh
./install.sh                                # for yourself, in all three tools
./install.sh --tools claude                 # a single tool
./install.sh --project <dir> --copy         # in a project, as copies you can commit
./install.sh --check                        # checks without changing anything
```

| Tool | For yourself | In a project |
|---|---|---|
| Claude Code | `~/.claude/skills/<name>/` | `.claude/skills/<name>/` |
| GitHub Copilot | `~/.copilot/skills/<name>/` | `.github/skills/<name>/` |
| opencode | `~/.config/opencode/skills/<name>/` | `.opencode/skills/<name>/` |

### From skills.sh

Eleven skills are published on [skills.sh](https://skills.sh): `clean-code`, `legacy-code`, `unit-tests`, `test-conventions`, `acceptance-tests`, `e2e-tests`, `golden-master`, `architecture-tests`, `architecture-styles`, `architecture-review` and `adr-writer`.

```sh
npx skills add AudranL/skills                        # choose among the eleven
npx skills add AudranL/skills --skill clean-code     # a single one
```

The other five (`agent-memory`, `cyclomatic-complexity`, `kanban`, `spec-review`, `spec-writing`) carry `metadata.internal: true` in their frontmatter: the `skills` CLI hides them, and `install.sh` installs them as usual.

## Language

The skills are written in English; their code and test examples follow the conventions of each stack.

## License

MIT, see `LICENSE`.
