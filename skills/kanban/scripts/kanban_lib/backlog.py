"""A repo's backlog: config.yml, the tickets read from tickets/, and their verification."""
import hashlib
import re
from pathlib import Path

from kanban_lib.files import read_text
from kanban_lib.ticket_file import (
    HISTORY_SECTION, REFINEMENT_NOTES_SECTION, SUMMARY_SECTION, BacklogError, front_matter_end, level_3_headings,
    parse_fields, section,
)


STATUSES = {
    "to-refine": "To refine",
    "refining": "Refining",
    "ready": "Ready",
    "in-progress": "In progress",
    "in-review": "In review",
    "done": "Done",
    "abandoned": "Abandoned",
}
COLUMNS = [s for s in STATUSES if s != "abandoned"]
# Statuses in which a story should have its spec.
STATUSES_WITH_SPEC = ("ready", "in-progress", "in-review", "done")
TYPES = {"epic": "Epic", "story": "Story", "task": "Task", "spike": "Spike", "bug": "Bug"}
REQUIRED_FIELDS = ("key", "title", "type", "status", "created")
# Directories served by "serve" when config.yml has no documentation key.
DEFAULT_DOCUMENTATION_DIRECTORIES = ("docs/specs", "docs/documentation")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


class Ticket:
    def __init__(self, path, fields, body):
        self.path = path
        self.fields = fields
        self.body = body

    def get(self, key, default=None):
        value = self.fields.get(key)
        return default if value is None else value

    @property
    def key(self):
        return str(self.get("key", ""))

    @property
    def title(self):
        return str(self.get("title", ""))

    @property
    def type(self):
        return str(self.get("type", ""))

    @property
    def status(self):
        return str(self.get("status", ""))

    @property
    def epic(self):
        return self.get("epic")

    @property
    def rank(self):
        rank = self.get("rank")
        return rank if isinstance(rank, int) else None

    @property
    def number(self):
        found = re.search(r"-(\d+)$", self.key)
        return int(found.group(1)) if found else 0

    @property
    def blocked_by(self):
        value = self.get("blocked_by", [])
        return value if isinstance(value, list) else [value]

    def refinement_notes(self):
        return level_3_headings(section(self.body, REFINEMENT_NOTES_SECTION))

    def latest_refinement_note(self):
        dates = [d.group(0) for d in (DATE.match(note) for note in self.refinement_notes()) if d]
        return max(dates) if dates else None


def repo_root(start):
    for directory in [start, *start.parents]:
        if (directory / ".git").exists():
            return directory
    return None


def default_directory():
    root = repo_root(Path.cwd().resolve())
    return (root or Path.cwd()) / "docs" / "backlog"


class Backlog:
    def __init__(self, directory):
        self.directory = directory.resolve()
        if not (self.directory / "config.yml").is_file():
            raise BacklogError(
                f"no backlog in {self.directory} (config.yml missing). "
                'Run "kanban.py init --project NAME --prefix PRE", or pass --dir.'
            )
        self.root = repo_root(self.directory) or self.directory.parent.parent
        self.config = parse_fields(read_text(self.directory / "config.yml").split("\n"), "config.yml")
        self.tickets, self.errors = [], []
        for path in sorted((self.directory / "tickets").glob("*.md")):
            try:
                lines = read_text(path).split("\n")
                end = front_matter_end(lines, path.name)
                fields = parse_fields(lines[1:end], path.name, 2)
                self.tickets.append(Ticket(path, fields, "\n".join(lines[end + 1:])))
            except BacklogError as exc:
                self.errors.append(str(exc))
        self.by_key = {ticket.key: ticket for ticket in self.tickets}

    @property
    def project(self):
        return str(self.config.get("project") or self.root.name)

    @property
    def prefix(self):
        return self.config.get("prefix")

    def find(self, key):
        ticket = self.by_key.get(key) or self.by_key.get(key.upper())
        if ticket is None:
            raise BacklogError(f"no ticket {key} in {self.relative(self.directory)}")
        return ticket

    def next_key(self):
        if not self.prefix:
            raise BacklogError("config.yml has no prefix")
        numbers = [ticket.number for ticket in self.tickets]
        # A key is never reused: unreadable files count too.
        for path in (self.directory / "tickets").glob(f"{self.prefix}-*.md"):
            found = re.match(rf"{re.escape(self.prefix)}-(\d+)", path.name)
            if found:
                numbers.append(int(found.group(1)))
        return f"{self.prefix}-{max(numbers, default=0) + 1}"

    def relative(self, path):
        try:
            return str(Path(path).resolve().relative_to(Path.cwd().resolve()))
        except ValueError:
            return str(path)

    def spec_path(self, ticket):
        spec = ticket.get("spec")
        return (self.root / str(spec)) if spec else None

    def sort_key(self, ticket):
        epic = self.by_key.get(ticket.epic) if ticket.epic else None
        group = epic.number if epic else (ticket.number if ticket.type == "epic" else 10 ** 9)
        rank = -1 if ticket.type == "epic" else (ticket.rank if ticket.rank is not None else 10 ** 6)
        return (group, rank, ticket.number)

    def children(self, epic):
        return [ticket for ticket in self.tickets if ticket.epic == epic.key and ticket.status != "abandoned"]

    def slice_number(self, ticket):
        """The slice number of a story placed in an epic: its rank. None for any other ticket."""
        if ticket.type == "story" and ticket.epic and ticket.rank is not None:
            return ticket.rank
        return None

    def slice_label(self, ticket):
        """The label of a story placed in an epic, S3 for slice 3; empty for any other ticket."""
        number = self.slice_number(ticket)
        return "" if number is None else f"S{number}"

    def fingerprint(self):
        """Fingerprint of the files the board reads, for the live reload."""
        digest = hashlib.sha256()
        files = [self.directory / "config.yml", *sorted((self.directory / "tickets").glob("*.md"))]
        files += [f for f in (self.spec_path(ticket) for ticket in self.tickets) if f and f.is_file()]
        for file in files:
            stats = file.stat()
            digest.update(f"{file}:{stats.st_mtime_ns}:{stats.st_size};".encode())
        return digest.hexdigest()[:16]


def documentation_directories(config):
    """The directories of the documentation key of config.yml, relative to the repo root."""
    directories = config.get("documentation")
    if directories is None:
        return list(DEFAULT_DOCUMENTATION_DIRECTORIES)
    return [str(d) for d in directories] if isinstance(directories, list) else [str(directories)]


# ---------------------------------------------------------------- verification

def check(backlog):
    """Returns (errors, warnings), each a list of lines."""
    errors = list(backlog.errors)
    warnings = []
    seen = {}
    prefix = backlog.prefix
    for ticket in backlog.tickets:
        name = ticket.path.name
        missing = [field for field in REQUIRED_FIELDS if ticket.fields.get(field) in (None, "")]
        if missing:
            errors.append(f"{name}: missing required field(s): {', '.join(missing)}")
            continue
        if ticket.key in seen:
            errors.append(f"{ticket.key}: duplicate key ({seen[ticket.key]} and {name})")
        seen[ticket.key] = name
        if prefix and not re.fullmatch(rf"{re.escape(prefix)}-\d+", ticket.key):
            errors.append(f"{ticket.key}: the key must be of the form {prefix}-<n>")
        if not (name == f"{ticket.key}.md" or name.startswith(f"{ticket.key}-")):
            errors.append(f'{ticket.key}: the file {name} must start with "{ticket.key}-"')
        if ticket.type not in TYPES:
            errors.append(f'{ticket.key}: unknown type "{ticket.type}" ({", ".join(TYPES)})')
        if ticket.status not in STATUSES:
            errors.append(f'{ticket.key}: unknown status "{ticket.status}" ({", ".join(STATUSES)})')
        if not DATE.fullmatch(str(ticket.get("created"))):
            errors.append(f"{ticket.key}: created must be a YYYY-MM-DD date")
        if ticket.fields.get("rank") is not None and ticket.rank is None:
            errors.append(f"{ticket.key}: rank must be an integer")
        if ticket.epic:
            epic = backlog.by_key.get(ticket.epic)
            if ticket.type == "epic":
                errors.append(f"{ticket.key}: an epic does not go inside another epic")
            elif epic is None:
                errors.append(f"{ticket.key}: epic {ticket.epic} not found")
            elif epic.type != "epic":
                errors.append(f"{ticket.key}: {ticket.epic} is not an epic")
        for other in ticket.blocked_by:
            if other not in backlog.by_key:
                errors.append(f"{ticket.key}: blocked_by cites {other}, not found")
        spec = backlog.spec_path(ticket)
        if spec and not spec.is_file():
            warnings.append(f"{ticket.key}: spec {ticket.get('spec')} not found")
        if ticket.type == "story" and ticket.status in STATUSES_WITH_SPEC and not spec:
            warnings.append(f'{ticket.key}: story "{STATUSES[ticket.status]}" without a spec')
        for section_name in (SUMMARY_SECTION, REFINEMENT_NOTES_SECTION, HISTORY_SECTION):
            if section(ticket.body, section_name) is None:
                warnings.append(f'{ticket.key}: section "## {section_name}" missing')
        for note in ticket.refinement_notes():
            if not DATE.match(note):
                warnings.append(f'{ticket.key}: note "{note[:40]}" without a date at the start (YYYY-MM-DD)')
        if ticket.get("jira") and not ticket.get("jira_sync"):
            warnings.append(f"{ticket.key}: Jira key without a sync date (kanban.py sync)")
    return errors, warnings
