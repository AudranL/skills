"""The commands of kanban.py and their command line: what each one reads, writes and prints."""
import argparse
import datetime as dt
import json
import re
import sys
import tempfile
import webbrowser
from pathlib import Path

from kanban_lib.backlog import (
    COLUMNS, DEFAULT_DOCUMENTATION_DIRECTORIES, STATUSES, STATUSES_WITH_SPEC, TYPES, Backlog, check,
    default_directory,
)
from kanban_lib.files import ASSETS, read_text, write_text
from kanban_lib.html_pages import board_html
from kanban_lib.jira import jira_fingerprint, to_push
from kanban_lib.server import create_server
from kanban_lib.ticket_file import BacklogError, add_history_entry, format_value, set_fields, slug, ticket_content


README_TEMPLATE = ASSETS / "README.md"


def today():
    return dt.date.today().isoformat()


def truncate(text, width):
    return text if len(text) <= width else text[: width - 1] + "…"


def cmd_init(args):
    directory = args.resolved_directory
    if (directory / "config.yml").exists():
        raise BacklogError(f"{directory} already holds a backlog")
    prefix = args.prefix.upper()
    if not re.fullmatch(r"[A-Z][A-Z0-9]{1,9}", prefix):
        raise BacklogError("the prefix must be 2 to 10 letters or digits, starting with a letter")
    (directory / "tickets").mkdir(parents=True, exist_ok=True)
    write_text(directory / "config.yml", "\n".join([
        "# Local backlog: the source of truth for the tickets. See README.md.",
        f"project: {format_value(args.project)}",
        f"prefix: {prefix}",
        "# Jira (optional): filled in at the first sync (kanban skill, references/jira.md).",
        "jira_site:",
        "jira_project:",
        '# Read-only documentation of "kanban serve" (/doc/): directories from the repo root.',
        f"# documentation: {format_value(list(DEFAULT_DOCUMENTATION_DIRECTORIES))}   (default value)",
    ]))
    template = read_text(README_TEMPLATE)
    write_text(directory / "README.md",
               template.replace("{project}", args.project).replace("{prefix}", prefix))
    print(f"Backlog created in {directory}: config.yml, README.md, tickets/")


def cmd_board(args):
    backlog = Backlog(args.resolved_directory)
    tickets = backlog.tickets
    if args.epic:
        epic = backlog.find(args.epic)
        tickets = [ticket for ticket in tickets if ticket.epic == epic.key or ticket.key == epic.key]
    bold = (lambda text: f"\033[1m{text}\033[0m") if sys.stdout.isatty() else (lambda text: text)
    print(f"{backlog.project} · backlog ({backlog.relative(backlog.directory)}) · {len(tickets)} ticket(s)")
    for epic in sorted((ticket for ticket in backlog.tickets if ticket.type == "epic"), key=backlog.sort_key):
        if args.epic and epic.key != args.epic.upper():
            continue
        children = backlog.children(epic)
        done = sum(1 for ticket in children if ticket.status == "done")
        in_progress = [ticket.key for ticket in children
                       if ticket.status in ("refining", "ready", "in-progress", "in-review")]
        suffix = f" · in progress: {', '.join(in_progress)}" if in_progress else ""
        print(f'  Epic {epic.key} "{epic.title}": {done}/{len(children)} done{suffix}')
    key_width = max((len(ticket.key) for ticket in tickets), default=6)
    statuses = COLUMNS + (["abandoned"] if args.all else [])
    for status in statuses:
        column = sorted((ticket for ticket in tickets if ticket.status == status), key=backlog.sort_key)
        print()
        print(bold(f"{STATUSES[status].upper()} ({len(column)})"))
        for ticket in column:
            label = backlog.slice_label(ticket) or (
                TYPES.get(ticket.type, ticket.type).lower() if ticket.type != "story" else "")
            epic = backlog.by_key.get(ticket.epic)
            extras = []
            if epic:
                extras.append(truncate(epic.title, 18))
            if ticket.refinement_notes():
                extras.append(f"{len(ticket.refinement_notes())} note(s)")
            if ticket.get("spec"):
                extras.append("spec")
            if ticket.blocked_by:
                extras.append("blocked by " + ", ".join(ticket.blocked_by))
            if ticket.get("jira"):
                extras.append(f"Jira {ticket.get('jira')}")
            title = truncate(ticket.title, 52)
            print(f"  {ticket.key:<{key_width}}  {label:<6} {title:<52}  {' · '.join(extras)}")
    for error in backlog.errors:
        print(f"! {error}", file=sys.stderr)


def cmd_check(args):
    backlog = Backlog(args.resolved_directory)
    errors, warnings = check(backlog)
    for line in errors:
        print(f"✗ {line}")
    for line in warnings:
        print(f"! {line}")
    if errors:
        print(f"{len(errors)} error(s), {len(warnings)} warning(s).")
        return 1
    print(f"✓ {len(backlog.tickets)} ticket(s), no errors, {len(warnings)} warning(s).")
    return 0


def cmd_new(args):
    backlog = Backlog(args.resolved_directory)
    if args.type not in TYPES:
        raise BacklogError(f'unknown type "{args.type}" ({", ".join(TYPES)})')
    if args.status not in STATUSES:
        raise BacklogError(f'unknown status "{args.status}" ({", ".join(STATUSES)})')
    epic = None
    if args.epic:
        if args.type == "epic":
            raise BacklogError("an epic does not go inside another epic")
        epic = backlog.find(args.epic)
        if epic.type != "epic":
            raise BacklogError(f"{epic.key} is not an epic")
    key = backlog.next_key()
    fields = {
        "key": key, "title": args.title.strip(), "type": args.type, "status": args.status,
        "epic": epic.key if epic else None, "rank": args.rank, "created": today(),
    }
    path = backlog.directory / "tickets" / f"{key}-{slug(args.title)}.md"
    write_text(path, ticket_content(fields, args.summary))
    print(f"{key} created: {backlog.relative(path)}")


def cmd_move(args):
    backlog = Backlog(args.resolved_directory)
    if args.status not in STATUSES:
        raise BacklogError(f'unknown status "{args.status}" ({", ".join(STATUSES)})')
    ticket = backlog.find(args.key)
    if ticket.status == args.status:
        print(f'{ticket.key} is already "{STATUSES[args.status]}".')
        return 0
    previous = ticket.status
    set_fields(ticket.path, {"status": args.status})
    reason = f" · {args.reason}" if args.reason else ""
    add_history_entry(ticket.path, f"{today()} · {previous} → {args.status}{reason}")
    print(f"{ticket.key}: {STATUSES.get(previous, previous)} → {STATUSES[args.status]}")
    if ticket.type == "story" and args.status in STATUSES_WITH_SPEC and not ticket.get("spec"):
        print(f"! {ticket.key} has no spec (spec field).")
    return 0


def cmd_to_push(args):
    backlog = Backlog(args.resolved_directory)
    pending = to_push(backlog)
    if args.json:
        print(json.dumps([{
            "key": ticket.key, "action": action, "type": ticket.type, "status": ticket.status,
            "title": ticket.title,
            "jira": ticket.get("jira"), "epic": ticket.epic,
            "epic_jira": backlog.by_key[ticket.epic].get("jira") if ticket.epic in backlog.by_key else None,
            "blocked_by": ticket.blocked_by, "file": backlog.relative(ticket.path),
            "spec": ticket.get("spec"),
        } for action, ticket in pending], ensure_ascii=False, indent=2))
        return 0
    if not (backlog.config.get("jira_site") and backlog.config.get("jira_project")):
        print("Jira is not configured yet (config.yml: jira_site, jira_project).")
    if not pending:
        print("Nothing to push: Jira is up to date.")
        return 0
    action_labels = {"create": "to create", "update": "to update"}
    ticket_labels = [ticket.key + (f" ({ticket.get('jira')})" if ticket.get("jira") else "")
                     for _, ticket in pending]
    width = max(len(label) for label in ticket_labels)
    for (action, ticket), label in zip(pending, ticket_labels):
        status = STATUSES.get(ticket.status, ticket.status)
        print(f"  {action_labels[action]:<16} {label:<{width}}  {status:<11}  {ticket.title}")
    return 0


def cmd_sync(args):
    backlog = Backlog(args.resolved_directory)
    ticket = backlog.find(args.key)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    already_pushed = ticket.get("jira")
    set_fields(ticket.path, {
        "jira": args.jira, "jira_sync": now, "jira_fingerprint": jira_fingerprint(backlog, ticket),
    })
    add_history_entry(ticket.path,
                      f"{today()} · {'updated in' if already_pushed else 'pushed to'} Jira ({args.jira})")
    print(f"{ticket.key} ↔ {args.jira} synced ({now}).")
    return 0


def cmd_html(args):
    backlog = Backlog(args.resolved_directory)
    output = (Path(args.output) if args.output
              else Path(tempfile.gettempdir()) / f"kanban-{slug(backlog.project)}.html")
    output.write_text(board_html(backlog), encoding="utf-8")
    print(f"Board written to {output}")
    if not args.no_open:
        webbrowser.open(output.resolve().as_uri())
    return 0


def cmd_serve(args):
    directory = args.resolved_directory
    Backlog(directory)  # fails right away if there is no backlog

    server = create_server(directory, args.port)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Live board at {url} and documentation at {url}doc/ (Ctrl+C to stop). "
          "They reload when a file changes.", flush=True)
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    return 0


# ---------------------------------------------------------------- entry point

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="kanban.py", description="Local Markdown backlog, Jira style.")
    parser.add_argument("--dir", dest="directory", metavar="DIR",
                        help="backlog directory (default: docs/backlog of the git repo)")
    # dest stays "command": argparse cites it in its errors ("argument command: invalid choice").
    subparsers = parser.add_subparsers(dest="command")

    p = subparsers.add_parser("init", help="bootstrap a backlog in the repo")
    p.add_argument("--project", dest="project", metavar="PROJECT", required=True)
    p.add_argument("--prefix", dest="prefix", metavar="PREFIX", required=True, help="key prefix, e.g. BOU")
    p.set_defaults(run=cmd_init)

    p = subparsers.add_parser("board", help="show the board in the terminal")
    p.add_argument("--epic", help="only this epic and its tickets")
    p.add_argument("--all", dest="all", action="store_true", help="with the abandoned tickets")
    p.set_defaults(run=cmd_board)

    p = subparsers.add_parser("html", help="write the board to an HTML file and open it")
    p.add_argument("--output", dest="output", metavar="OUTPUT",
                   help="file to write (default: temporary directory)")
    p.add_argument("--no-open", dest="no_open", action="store_true")
    p.set_defaults(run=cmd_html)

    p = subparsers.add_parser("serve",
                              help="serve the board and the documentation (/doc/) live on 127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--no-open", dest="no_open", action="store_true")
    p.set_defaults(run=cmd_serve)

    p = subparsers.add_parser("check", help="check the tickets (exit code 1 on error)")
    p.set_defaults(run=cmd_check)

    p = subparsers.add_parser("new", help="create a ticket with the next key")
    p.add_argument("title", metavar="title")
    p.add_argument("--type", default="story", help=", ".join(TYPES))
    p.add_argument("--epic")
    p.add_argument("--rank", dest="rank", metavar="RANK", type=int)
    p.add_argument("--status", dest="status", metavar="STATUS", default="to-refine", help=", ".join(STATUSES))
    p.add_argument("--summary", dest="summary", metavar="SUMMARY", help="the need in one or two sentences")
    p.set_defaults(run=cmd_new)

    p = subparsers.add_parser("move", help="change a ticket's status and record it in its history")
    p.add_argument("key", metavar="key")
    p.add_argument("status", metavar="status", help=", ".join(STATUSES))
    p.add_argument("--reason", dest="reason", metavar="REASON")
    p.set_defaults(run=cmd_move)

    p = subparsers.add_parser("to-push", help="list the tickets to create or update in Jira")
    p.add_argument("--json", action="store_true")
    p.set_defaults(run=cmd_to_push)

    p = subparsers.add_parser("sync", help="record that a ticket has just been pushed to Jira")
    p.add_argument("key", metavar="key")
    p.add_argument("--jira", required=True, help="key of the ticket in Jira, e.g. BOUTIQUE-12")
    p.set_defaults(run=cmd_sync)

    args = parser.parse_args(argv)
    if not args.command:
        args = parser.parse_args([*(argv or sys.argv[1:]), "board"])
    args.resolved_directory = (Path(args.directory).expanduser().resolve() if args.directory
                               else default_directory())
    try:
        return args.run(args) or 0
    except BacklogError as exc:
        print(f"kanban: {exc}", file=sys.stderr)
        return 2
