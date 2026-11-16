"""The HTML pages: the board (live or written to a standalone file) and the documentation pages."""
import datetime as dt
import html
import json
import re
import urllib.parse
from pathlib import Path

from kanban_lib.backlog import STATUSES, documentation_directories
from kanban_lib.documentation import Documentation, page_title
from kanban_lib.files import ASSETS, read_text
from kanban_lib.markdown_html import escape, markdown_to_html


# ---------------------------------------------------------------- HTML board

def board_data(backlog, live):
    documentation = project_documentation(backlog) if live else None
    tickets = []
    for ticket in backlog.tickets:
        spec = backlog.spec_path(ticket)
        epic = backlog.by_key.get(ticket.epic)
        tickets.append({
            "key": ticket.key, "title": ticket.title, "type": ticket.type, "status": ticket.status,
            "epic": ticket.epic, "epicTitle": epic.title if epic else None,
            "epicNumber": epic.number if epic else None,
            "rank": ticket.rank, "number": ticket.number, "slice": backlog.slice_number(ticket),
            "spec": ticket.get("spec"), "jira": ticket.get("jira"), "blockedBy": ticket.blocked_by,
            "notes": len(ticket.refinement_notes()), "lastNote": ticket.latest_refinement_note(),
            "created": ticket.get("created"),
            "file": backlog.relative(ticket.path), "body": ticket.body,
            # The ticket's title is already at the top of the panel.
            "bodyHtml": markdown_to_html(re.sub(r"^\s*# .*\n", "", ticket.body, count=1)),
            "specHtml": markdown_to_html(read_text(spec)) if spec and spec.is_file() else None,
            "specUrl": spec_url(documentation, ticket) if documentation else None,
        })
    return {
        "project": backlog.project, "directory": backlog.relative(backlog.directory),
        "generated": dt.datetime.now().strftime("%Y-%m-%dT%H:%M"), "live": live,
        "fingerprint": backlog.fingerprint() if live else None, "errors": backlog.errors,
        "documentation": "/doc/" if live else None,
        "statuses": list(STATUSES),
        "tickets": tickets,
    }


def spec_url(documentation, ticket):
    """The address of the page of a ticket's spec, if the documentation serves it."""
    spec = ticket.get("spec")
    if not spec or documentation.document(str(spec)) is None:
        return None
    return page_url(Path(str(spec)).as_posix())


def board_html(backlog, live=False):
    data = json.dumps(board_data(backlog, live), ensure_ascii=False).replace("<", "\\u003c")
    return (BOARD_TEMPLATE.replace("__TITLE_ARGS__", i18n_args(project=backlog.project))
            .replace("__DATA__", data))


def i18n_args(**params):
    """The parameters of a message, for a data-i18n-args='…' attribute: JSON, escaped for single quotes."""
    return html.escape(json.dumps(params, ensure_ascii=False), quote=False).replace("'", "&#x27;")


def i18n_attributes(key, **params):
    """The attributes of an element that i18n.js fills with the text of a message, in the browser's language."""
    return f' data-i18n="{key}"' + (f" data-i18n-args='{i18n_args(**params)}'" if params else "")


# ---------------------------------------------------------------- documentation pages

def project_documentation(backlog):
    """The served documentation of a backlog's repo: the directories of the documentation key of its config.yml."""
    return Documentation(backlog.root, documentation_directories(backlog.config))


def page_url(path):
    """The address of a documentation page: its path from the repo root, under /doc/. A relative link
    from one page to another (glossary.md, ../specs/x.md) therefore leads there without being rewritten."""
    return "/doc/" + urllib.parse.quote(path)


def index_page(backlog):
    documentation = project_documentation(backlog)
    folder_sections = "\n".join(folder_section_html(folder_section)
                                for folder_section in documentation.index())
    header = (f'<nav class="breadcrumb"{i18n_attributes("doc.breadcrumb.documentation")}>'
              f'<a href="/"{i18n_attributes("doc.breadcrumb.board")}></a> › </nav>\n'
              f'<h1{i18n_attributes("doc.index.heading", project=backlog.project)}></h1>')
    return documentation_page(f'<title{i18n_attributes("doc.index.title", project=backlog.project)}></title>',
                              f"{header}\n{folder_sections}", documentation.fingerprint())


def document_page(backlog, path):
    """The page of a document of the documentation, or None if it is not to be served."""
    documentation = project_documentation(backlog)
    file = documentation.document(path)
    if file is None:
        return None
    text = read_text(file)
    content = f'<article class="md">\n{markdown_to_html(text)}\n</article>'
    return documentation_page(f"<title>{escape(page_title(text, file.name))} · {escape(backlog.project)}</title>",
                              document_breadcrumb(path) + tickets_of_spec(backlog, file) + f"\n{content}",
                              documentation.fingerprint())


def not_found_page(backlog, path):
    """The page of a documentation address that serves no document, with the trail back to the board."""
    title = f'<title{i18n_attributes("doc.notFound.title", project=backlog.project)}></title>'
    body = (f'{document_breadcrumb(path)}\n<h1{i18n_attributes("doc.notFound.heading")}></h1>\n'
            f'<p class="empty"{i18n_attributes("doc.notFound.text")}></p>')
    return documentation_page(title, body, project_documentation(backlog).fingerprint())


def document_breadcrumb(path):
    """The trail from the board and the documentation index down to the page of a document."""
    return (f'<nav class="breadcrumb"><a href="/"{i18n_attributes("doc.breadcrumb.board")}></a> › '
            f'<a href="/doc/"{i18n_attributes("doc.breadcrumb.documentation")}></a> › '
            f'<span class="path">{escape(path)}</span></nav>')


def tickets_of_spec(backlog, file):
    """The tickets whose spec field designates this file, with a link to each one on the board."""
    tickets = [ticket for ticket in backlog.tickets
               if backlog.spec_path(ticket) and backlog.spec_path(ticket).resolve() == file.resolve()]
    if not tickets:
        return ""
    links = ", ".join(f'<a href="/#{escape(ticket.key)}">{escape(ticket.key)} · {escape(ticket.title)}</a>'
                      for ticket in tickets)
    return f'\n<p class="subtitle"{i18n_attributes("doc.spec.tickets")} data-i18n-at="start"> {links}</p>'


def folder_section_html(folder_section):
    header = f'<section class="folder-section"><h2>{escape(folder_section.directory)}</h2>'
    if not folder_section.exists:
        missing = i18n_attributes("doc.folder.missing", directory=folder_section.directory)
        return f'{header}<p class="empty"{missing}></p></section>'
    if not folder_section.pages:
        return f'{header}<p class="empty"{i18n_attributes("doc.folder.empty")}></p></section>'
    return f'{header}<ul>{"".join(map(page_link, folder_section.pages))}</ul></section>'


def page_link(page):
    entry_badge = f' <span class="badge"{i18n_attributes("doc.entryPage")}></span>' if page.is_entry_page else ""
    return f'<li><a href="{escape(page_url(page.path))}">{escape(page.title)}</a>{entry_badge}</li>'


def documentation_page(title_element, body, fingerprint):
    """A documentation page, which reloads when the fingerprint of the documentation is no longer fingerprint.
    The template markers are replaced in a single pass: a text that contains one stays as it is."""
    values = {"TITLE": title_element, "FINGERPRINT": json.dumps(fingerprint), "BODY": body}
    return re.sub(r"__(TITLE|FINGERPRINT|BODY)__", lambda m: values[m.group(1)], PAGE_TEMPLATE)


# The templates of the board and of the documentation pages. The common style (colors, dark theme, rendering
# of the .md files) and the board script are copied into them: the page written by "html" stays standalone.
# Their marker stands alone on its line, hence the last line break removed.
COMMON_STYLE = read_text(ASSETS / "common.css").rstrip("\n")
# Both templates also carry the browser texts: the messages of every language and the script that picks one.
MESSAGES = read_text(ASSETS / "messages.json").rstrip("\n")
I18N_SCRIPT = read_text(ASSETS / "i18n.js").rstrip("\n")


def with_common_parts(template):
    return (template.replace("__COMMON_STYLE__", COMMON_STYLE).replace("__MESSAGES__", MESSAGES)
            .replace("__I18N_SCRIPT__", I18N_SCRIPT))


BOARD_TEMPLATE = with_common_parts(read_text(ASSETS / "board.html")
                                   .replace("__BOARD_SCRIPT__", read_text(ASSETS / "board.js").rstrip("\n")))
PAGE_TEMPLATE = with_common_parts(read_text(ASSETS / "page.html"))
