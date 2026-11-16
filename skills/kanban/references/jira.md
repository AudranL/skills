# Pushing the backlog to Jira (Atlassian MCP)

The local backlog stays the source of truth: Jira receives a copy, on request, **never without the user's explicit agreement on what is going to be written**. Nothing comes down from Jira into the backlog without their agreement either.

## Tools

Those of the official Atlassian MCP, prefixed according to the client (`mcp__atlassian__…`, `mcp__claude_ai_Atlassian__…`): `getAccessibleAtlassianResources`, `getVisibleJiraProjects`, `getJiraProjectIssueTypesMetadata`, `getJiraIssue`, `searchJiraIssuesUsingJql`, `createJiraIssue`, `editJiraIssue`, `getTransitionsForJiraIssue`, `transitionJiraIssue`, `addCommentToJiraIssue`, `getIssueLinkTypes`, `createIssueLink`. Another Jira MCP (`jira_*`) maps the same way. The exact names and parameters are those of the tool's schema: rely on it rather than on this page.

Without a Jira tool in the session: say so in one line and offer the content ready to copy.

## First sync: the mapping

Done once per repo, then kept in `docs/backlog/config.yml` (one `key: value` line each):

1. **Site**: `getAccessibleAtlassianResources` gives the `cloudId`. If there are several sites, ask which one. → `jira_site: my-team.atlassian.net`
2. **Project**: ask the user (if needed, list with `getVisibleJiraProjects`). → `jira_project: BOUTIQUE`
3. **Types**: `getJiraProjectIssueTypesMetadata`, then map each local type to a type of the project. Without a "Spike" type, propose "Task" (or its name in the site's language). → `jira_type_epic: Epic`, `jira_type_story: Story`, `jira_type_task: Task`, `jira_type_spike: Task`, `jira_type_bug: Bug`
4. **Statuses**: the workflow is only visible from a ticket. After the first creation, `getTransitionsForJiraIssue` gives the reachable statuses; propose a mapping, several local statuses being allowed to land on the same Jira status. → `jira_status_to-refine: Backlog`, `jira_status_refining: Backlog`, `jira_status_ready: Selected for Development`, `jira_status_in-progress: In Progress`, `jira_status_in-review: In Review`, `jira_status_done: Done`, `jira_status_abandoned: Done`

Have the user validate the mapping before writing it in `config.yml`.

## Pushing

1. `kanban.py to-push --json`: the tickets to create (without a Jira key) and to update (changed since the last sync: fields, text outside History, or spec). An abandoned ticket that was never pushed is not pushed.
2. **Prepare the content** of each one (template below): summary = `title`; type and status according to the mapping; parent = the Jira key of its epic (the epic is pushed first).
3. **Show it to the user and wait for their agreement**: the list (creation or update, key, title, status), then the full content of each created ticket and what changes for each updated ticket. For a first push of many tickets, show one full ticket as an example and the list, and ask for agreement on the batch.
4. **Before updating an existing ticket**, read it again (`getJiraIssue`). If it was changed in Jira after `jira_sync` (description, status, new comments), show the difference and ask: take it back into the backlog (a dated `**Clarification**` note, source "Jira, comment by …"), or overwrite. Never overwrite silently.
5. **Create** (`createJiraIssue`) the epics first, then the other tickets by increasing key. If the wanted status is not the initial status, `getTransitionsForJiraIssue` then `transitionJiraIssue`. An unknown required field (e.g. "Epic Name"): read the error message and ask for the value.
6. **Update** (`editJiraIssue`): summary and description; the transition if the status changed.
7. **Links**: for `blocked_by`, once both tickets are in Jira, `createIssueLink` of type "Blocks" (the blocking one "blocks" the blocked one). Do not recreate a link that exists.
8. **After each successful ticket**: `kanban.py sync <KEY> --jira <JIRA-KEY>`. A failure is not synced: say so, with Jira's message.
9. Finish with `kanban.py to-push`: the list must be empty, except for announced failures.

## Description template

In Markdown (the MCP converts it):

```markdown
<The ticket's Summary>

<If the ticket has a spec: its Why, For whom and Scope sections, then its Gherkin scenarios in a ```gherkin block.>

## Refinement notes (draft)
<The ticket's notes, as they are.>

---
Copy of the local backlog of <project>: ticket <KEY> (docs/backlog/tickets/<file>). Edit the local ticket, not this one: it is rewritten at every sync.
```

The History does not go: Jira has its own history. A description too long for Jira (more than about 30,000 characters) keeps the Summary, Why, For whom, Scope and the titles of the scenarios, with the path of the spec.

## Starting from a Jira ticket

A Jira key cited by the user: look for it first in the backlog (`grep -l "^jira: ABC-12" docs/backlog/tickets/*.md`). Missing: read the ticket (`getJiraIssue`, with its comments and links), propose to take it into the backlog (`kanban.py new`, type and status according to the mapping, its description in the Summary, its useful comments as notes with their source), then `kanban.py sync` to link the two. Its description in Jira will be rewritten in the template's format at the first push that follows a change of the local ticket: say so.
