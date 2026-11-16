"""What is left to push to Jira: the fingerprint of what Jira received of a ticket, and the changed tickets."""
import hashlib
import json

from kanban_lib.ticket_file import HISTORY_SECTION, body_without


# Fields whose change must go back to Jira (along with the body outside History, and the spec).
PUSHED_FIELDS = ("title", "type", "status", "epic", "rank", "spec", "blocked_by")


def jira_fingerprint(backlog, ticket):
    """What Jira received of a ticket: its pushed fields, its body outside History, and its spec."""
    fields = {k: ticket.fields.get(k) for k in PUSHED_FIELDS}
    body = body_without(ticket.body, HISTORY_SECTION)
    body = "\n".join(line.rstrip() for line in body.strip().split("\n"))
    digest = hashlib.sha256()
    digest.update(json.dumps(fields, sort_keys=True, ensure_ascii=False).encode())
    digest.update(b"\0" + body.encode())
    spec = backlog.spec_path(ticket)
    if spec and spec.is_file():
        digest.update(b"\0" + spec.read_bytes())
    return digest.hexdigest()[:12]


def to_push(backlog):
    result = []
    for ticket in sorted(backlog.tickets, key=lambda ticket: (ticket.type != "epic", ticket.number)):
        if not ticket.get("jira"):
            if ticket.status != "abandoned":
                result.append(("create", ticket))
        elif jira_fingerprint(backlog, ticket) != ticket.get("jira_fingerprint"):
            result.append(("update", ticket))
    return result
