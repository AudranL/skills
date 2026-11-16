"""A ticket's file: its minimal YAML front matter, its Markdown sections, and what is written in it."""
import json
import re
import unicodedata

from kanban_lib.files import read_text, write_text


FIELD_ORDER = ("key", "title", "type", "status", "epic", "rank", "spec", "blocked_by",
               "jira", "jira_sync", "jira_fingerprint", "created")
SUMMARY_SECTION = "Summary"
REFINEMENT_NOTES_SECTION = "Refinement notes"
HISTORY_SECTION = "History"
REFINEMENT_NOTES_COMMENT = (
    "<!-- Draft. One note per exchange, the most recent last: the question as it was asked, "
    "the answer as it was given. Add, do not rewrite. The ticket gets refined when its turn comes. -->"
)


class BacklogError(Exception):
    pass


# ---------------------------------------------------------------- minimal YAML front matter

def without_comment(value):
    """Removes an end-of-line comment (# …), like YAML, outside quotes."""
    if value[:1] in ('"', "'"):
        quote, i = value[0], 1
        while i < len(value):
            if quote == '"' and value[i] == "\\":
                i += 2
                continue
            if value[i] == quote:
                if quote == "'" and value[i + 1:i + 2] == "'":
                    i += 2
                    continue
                return value[:i + 1]
            i += 1
        return value
    return re.split(r"\s+#", value, maxsplit=1)[0].rstrip()


def parse_value(value, source=""):
    """A simple YAML value: empty, string (bare or quoted), integer, list [a, b]."""
    value = without_comment(value)
    if value in ("", "~", "null"):
        return None
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise BacklogError(f"{source}: malformed string {value} ({exc.msg})") from exc
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    if value.startswith("[") and value.endswith("]"):
        inside = value[1:-1].strip()
        return [parse_value(v.strip(), source) for v in inside.split(",")] if inside else []
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def format_value(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(format_value(v) for v in value) + "]"
    text = str(value)
    if (text == "" or text != text.strip() or ": " in text or " #" in text
            or text.endswith(":") or text[0] in "[]{}\"'#&*!|>%@`,-?:"
            or re.fullmatch(r"-?\d+", text)
            or text.lower() in ("true", "false", "null", "yes", "no", "~")):
        return json.dumps(text, ensure_ascii=False)
    return text


def parse_fields(lines, source, first_line_number=1):
    fields = {}
    for line_number, line in enumerate(lines, first_line_number):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep or not re.fullmatch(r"[a-z_][a-z0-9_-]*", key.strip()):
            raise BacklogError(f'{source}, line {line_number}: "{line}" is not of the form key: value')
        fields[key.strip()] = parse_value(value.strip(), f"{source}, line {line_number}")
    return fields


def front_matter_end(lines, source):
    """Index of the --- line that closes the front matter (the first line is ---)."""
    if not lines or lines[0].strip() != "---":
        raise BacklogError(f"{source}: no YAML front matter (the file must start with ---)")
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return i
    raise BacklogError(f"{source}: YAML front matter not closed (--- missing)")


# ---------------------------------------------------------------- Markdown sections

def is_fence(line):
    return line.lstrip().startswith(("```", "~~~"))


def is_level_2_heading(line):
    return re.match(r"##\s+\S", line) is not None and not line.startswith("###")


def split_sections(body):
    """[(level 2 heading or None, [lines])], ignoring the headings inside code blocks."""
    parts = [[None, []]]
    in_code = False
    for line in body.split("\n"):
        if is_fence(line):
            in_code = not in_code
        if not in_code and is_level_2_heading(line):
            parts.append([line.lstrip("#").strip(), []])
        else:
            parts[-1][1].append(line)
    return parts


def section(body, heading):
    for name, lines in split_sections(body):
        if name == heading:
            return "\n".join(lines)
    return None


def body_without(body, heading):
    pieces = []
    for name, lines in split_sections(body):
        if name == heading:
            continue
        if name is not None:
            pieces.append(f"## {name}")
        pieces.extend(lines)
    return "\n".join(pieces)


def level_3_headings(text):
    headings, in_code = [], False
    for line in (text or "").split("\n"):
        if is_fence(line):
            in_code = not in_code
        elif not in_code and line.startswith("### "):
            headings.append(line[4:].strip())
    return headings


# ---------------------------------------------------------------- writing to a ticket

def set_fields(path, fields):
    """Changes or adds front matter fields without touching the rest of the file."""
    lines = read_text(path).split("\n")
    end = front_matter_end(lines, path.name)
    for key, value in fields.items():
        line = f"{key}: {format_value(value)}".rstrip()
        for i in range(1, end):
            if re.match(rf"{re.escape(key)}\s*:", lines[i]):
                lines[i] = line
                break
        else:
            position = 1
            order_index = FIELD_ORDER.index(key) if key in FIELD_ORDER else len(FIELD_ORDER)
            for i in range(1, end):
                name = lines[i].partition(":")[0].strip()
                if name in FIELD_ORDER and FIELD_ORDER.index(name) < order_index:
                    position = i + 1
            if key not in FIELD_ORDER:
                position = end
            lines.insert(position, line)
            end += 1
    write_text(path, "\n".join(lines))


def add_history_entry(path, text):
    lines = read_text(path).rstrip("\n").split("\n")
    start, in_code = None, False
    for i, line in enumerate(lines):
        if is_fence(line):
            in_code = not in_code
        elif not in_code and is_level_2_heading(line) and line.lstrip("#").strip() == HISTORY_SECTION:
            start = i
    if start is None:
        lines += ["", f"## {HISTORY_SECTION}", f"- {text}"]
    else:
        end, in_code = len(lines), False
        for i in range(start + 1, len(lines)):
            if is_fence(lines[i]):
                in_code = not in_code
            elif not in_code and is_level_2_heading(lines[i]):
                end = i
                break
        while end > start + 1 and not lines[end - 1].strip():
            end -= 1
        lines.insert(end, f"- {text}")
    write_text(path, "\n".join(lines))


def ticket_content(fields, summary):
    front_matter = "\n".join(
        f"{k}: {format_value(fields[k])}" for k in FIELD_ORDER if fields.get(k) not in (None, "", [])
    )
    return (
        f"---\n{front_matter}\n---\n\n# {fields['key']} · {fields['title']}\n\n"
        f"## {SUMMARY_SECTION}\n{summary or ''}\n\n"
        f"## {REFINEMENT_NOTES_SECTION}\n{REFINEMENT_NOTES_COMMENT}\n\n"
        f"## {HISTORY_SECTION}\n- {fields['created']} · created\n"
    )


def slug(text, length=50):
    ascii_ = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    ascii_ = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_).strip("-").lower()
    return ascii_[:length].rstrip("-") or "ticket"
