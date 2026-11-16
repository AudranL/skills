#!/usr/bin/env python3
"""Tests of kanban: scripts/kanban.py, scripts/kanban_lib/ and the templates of assets/
(unittest, standard library).

Usage, from the skill directory, after any change to scripts/ or assets/:
  python3 -I -B -W error scripts/selftest.py   (also with /usr/bin/python3, 3.9)
"""
import contextlib
import http.client
import io
import re
import socket
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("kanban.py")
# Like kanban.py, run with "python3 -I": its directory is not in sys.path.
sys.path.insert(0, str(SCRIPT.parent))

from kanban_lib.backlog import Backlog, documentation_directories
from kanban_lib.commands import main
from kanban_lib.documentation import Documentation, Page
from kanban_lib.html_pages import board_data, document_page, index_page, project_documentation
from kanban_lib.markdown_html import markdown_to_html
from kanban_lib.server import HTML, TEXT, is_accepted_host, response
from kanban_lib.ticket_file import slug, ticket_content


class ThrowawayRepo:
    """A throwaway git repo with a backlog: config.yml, tickets and documents."""

    def __init__(self, config="project: Boutique\nprefix: BOU\n"):
        self._directory = tempfile.TemporaryDirectory()
        self.root = Path(self._directory.name).resolve()
        (self.root / ".git").mkdir()
        self.backlog = self.root / "docs" / "backlog"
        (self.backlog / "tickets").mkdir(parents=True)
        self.write("docs/backlog/config.yml", config)

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def with_ticket(self, key, title, **fields):
        all_fields = {"key": key, "title": title, "type": "story", "status": "to-refine", "created": "2026-10-22",
                      **fields}
        self.write(f"docs/backlog/tickets/{key}-{slug(title)}.md",
                   ticket_content(all_fields, "The need."))
        return self

    def with_document(self, relative, text):
        self.write(relative, text)
        return self

    def close(self):
        self._directory.cleanup()


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class LiveServer(unittest.TestCase):
    """kanban.py serve, launched for real and queried on 127.0.0.1."""

    def setUp(self):
        self.repo = (ThrowawayRepo()
                     .with_ticket("BOU-1", "First launch", spec="docs/specs/onboarding.md")
                     .with_document("docs/specs/onboarding.md", ONBOARDING_SPEC)
                     .with_document("docs/documentation/INDEX.md", "# Boutique\n\n[Glossary](glossary.md)\n")
                     .with_document("docs/documentation/glossary.md", "# Glossary\n\n### Level\n- Grade 1 to grade 5\n"))
        self.addCleanup(self.repo.close)
        self.port = free_port()
        self.server = subprocess.Popen(
            [sys.executable, "-I", "-B", str(SCRIPT), "--dir", str(self.repo.backlog),
             "serve", "--no-open", "--port", str(self.port)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(self.stop)
        self.announcement = self.server.stdout.readline()  # "Live board at …": the server is listening

    def stop(self):
        self.server.terminate()
        self.server.wait(timeout=5)
        self.server.stdout.close()
        self.server.stderr.close()

    def fetch(self, path):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=5) as reply:
                return reply.status, reply.headers.get("Content-Type"), reply.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            exc.close()
            return exc.code, None, None

    def fetch_with_host(self, path, host):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("GET", path, headers={"Host": host})
            reply = connection.getresponse()
            return reply.status, reply.read().decode("utf-8")
        finally:
            connection.close()

    def test_refuses_without_any_data_a_request_addressed_to_another_name(self):
        code, body = self.fetch_with_host("/", f"evil.example:{self.port}")

        self.assertEqual(code, 403)
        self.assertNotIn("Boutique", body)

    def test_serves_the_board_at_the_root(self):
        code, content_type, body = self.fetch("/")

        self.assertEqual((code, content_type), (200, "text/html; charset=utf-8"))
        self.assertIn("""<title data-i18n="board.title" data-i18n-args='{"project": "Boutique"}'></title>""", body)

    def test_serves_the_fingerprint_of_the_backlog_for_the_live_reload(self):
        code, content_type, body = self.fetch("/state")

        self.assertEqual((code, content_type), (200, "text/plain; charset=utf-8"))
        self.assertRegex(body, r"^[0-9a-f]{16}$")

    def test_serves_nothing_else(self):
        code, _, _ = self.fetch("/config.yml")

        self.assertEqual(code, 404)

    def test_announces_the_address_of_the_board_and_that_of_the_documentation(self):
        self.assertIn(f"http://127.0.0.1:{self.port}/ ", self.announcement)
        self.assertIn(f"http://127.0.0.1:{self.port}/doc/ ", self.announcement)

    def test_serves_the_index_page_of_the_documentation(self):
        code, content_type, body = self.fetch("/doc/")

        self.assertEqual((code, content_type), (200, "text/html; charset=utf-8"))
        self.assertIn('<a href="/doc/docs/specs/onboarding.md">Onboarding</a>', body)
        self.assertIn('<a href="/doc/docs/documentation/INDEX.md">Boutique</a>', body)

    def test_serves_a_spec_with_its_scenarios(self):
        code, content_type, body = self.fetch("/doc/docs/specs/onboarding.md")

        self.assertEqual((code, content_type), (200, "text/html; charset=utf-8"))
        self.assertIn("<h1>Onboarding</h1>", body)
        self.assertIn('<span class="gk-keyword">Scenario:</span>', body)

    def test_does_not_serve_a_file_outside_the_documentation_directories(self):
        code, _, _ = self.fetch("/doc/docs/backlog/config.yml")

        self.assertEqual(code, 404)


class RequestHost(unittest.TestCase):
    """serve only answers the requests addressed to the local machine by its address or by its name."""

    def test_accepts_the_announced_address_with_or_without_a_port(self):
        for host in ("127.0.0.1", "127.0.0.1:8765"):
            self.assertTrue(is_accepted_host(host), host)

    def test_accepts_the_name_localhost_with_or_without_a_port_whatever_its_case(self):
        for host in ("localhost", "localhost:8765", "LocalHost:8765"):
            self.assertTrue(is_accepted_host(host), host)

    def test_refuses_any_other_host_even_with_the_port(self):
        for host in ("evil.example:8765", "evil.example", "localhost.evil.example", "127.0.0.1.nip.io",
                     "[::1]", "[::1]:8765"):
            self.assertFalse(is_accepted_host(host), host)

    def test_refuses_a_port_that_is_not_a_number(self):
        for host in ("localhost:evil.example", "127.0.0.1:http"):
            self.assertFalse(is_accepted_host(host), host)

    def test_refuses_a_request_without_a_host(self):
        for host in ("", None):
            self.assertFalse(is_accepted_host(host), host)


class BacklogInit(unittest.TestCase):

    def test_config_yml_points_out_the_default_documentation_directories(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            main(["--dir", directory, "init", "--project", "Boutique", "--prefix", "BOU"])
            config = (Path(directory) / "config.yml").read_text(encoding="utf-8")

        self.assertIn("\n# documentation: [docs/specs, docs/documentation]", config)


class BoardPanel(unittest.TestCase):
    """The panel of a ticket shows the ticket and its spec, rendered like the documentation."""

    def test_receives_the_ticket_without_its_title_and_its_spec_already_rendered(self):
        repo = (ThrowawayRepo()
                .with_ticket("BOU-1", "First launch", spec="docs/specs/onboarding.md")
                .with_document("docs/specs/onboarding.md", "# Onboarding\n"))
        self.addCleanup(repo.close)

        ticket, = board_data(Backlog(repo.backlog), live=False)["tickets"]

        self.assertEqual(ticket["bodyHtml"], "<h2>Summary</h2>\n<p>The need.</p>\n<h2>Refinement notes</h2>\n"
                                              "<h2>History</h2>\n<ul>\n<li>2026-10-22 · created</li>\n</ul>")
        self.assertEqual(ticket["specHtml"], "<h1>Onboarding</h1>")


class BoardToDocumentation(unittest.TestCase):
    """The data of the live board lead to the documentation; the standalone HTML file, without a server, does not."""

    def setUp(self):
        self.repo = (ThrowawayRepo()
                     .with_ticket("BOU-1", "First launch", spec="docs/specs/onboarding.md")
                     .with_document("docs/specs/onboarding.md", "# Onboarding\n"))
        self.addCleanup(self.repo.close)

    def data(self, live):
        return board_data(Backlog(self.repo.backlog), live)

    def test_the_live_board_leads_to_the_documentation(self):
        self.assertEqual(self.data(live=True)["documentation"], "/doc/")
        self.assertIsNone(self.data(live=False)["documentation"])

    def test_the_spec_field_of_a_ticket_leads_to_the_page_of_its_spec(self):
        ticket, = self.data(live=True)["tickets"]

        self.assertEqual(ticket["specUrl"], "/doc/docs/specs/onboarding.md")

    def test_no_page_for_a_spec_outside_the_documentation_or_without_a_server(self):
        self.repo.with_ticket("BOU-2", "Part time", spec="notes/part-time.md")
        self.repo.with_document("notes/part-time.md", "# Part time\n")

        live_urls = {ticket["key"]: ticket["specUrl"] for ticket in self.data(live=True)["tickets"]}
        standalone_urls = {ticket["key"]: ticket["specUrl"] for ticket in self.data(live=False)["tickets"]}

        self.assertIsNone(live_urls["BOU-2"])
        self.assertEqual(standalone_urls, {"BOU-1": None, "BOU-2": None})


class DocumentationRoutes(unittest.TestCase):
    """What serve answers to each address, without going through the network."""

    def setUp(self):
        self.repo = (ThrowawayRepo()
                     .with_document("docs/specs/onboarding.md", "# Onboarding\n")
                     .with_document("docs/backlog/README.md", "# Backlog\n"))
        self.addCleanup(self.repo.close)

    def response(self, target):
        return response(self.repo.backlog, target)

    def test_the_documentation_index_with_or_without_a_trailing_slash(self):
        for target in ("/doc", "/doc/?view=1"):
            code, content_type, body = self.response(target)
            self.assertEqual((code, content_type), (200, HTML), target)
            self.assertIn("""<h1 data-i18n="doc.index.heading" data-i18n-args='{"project": "Boutique"}'></h1>""",
                          body, target)

    def test_a_page_at_the_address_of_its_path_from_the_repo_root(self):
        self.repo.with_document("docs/specs/jalapeño menu.md", "# Jalapeño menu\n")

        code, content_type, body = self.response("/doc/docs/specs/jalape%C3%B1o%20menu.md")

        self.assertEqual((code, content_type), (200, HTML))
        self.assertIn("<h1>Jalapeño menu</h1>", body)

    def test_the_fingerprint_of_the_documentation_for_the_live_reload(self):
        code, content_type, body = self.response("/state/documentation")

        self.assertEqual((code, content_type), (200, TEXT))
        self.assertEqual(body, project_documentation(Backlog(self.repo.backlog)).fingerprint())

    def test_each_page_watches_the_fingerprint_of_the_documentation(self):
        fingerprint = project_documentation(Backlog(self.repo.backlog)).fingerprint()
        for target in ("/doc/", "/doc/docs/specs/onboarding.md"):
            body = self.response(target)[2]
            self.assertIn(f'const fingerprint = "{fingerprint}";', body, target)
            self.assertIn('fetch("/state/documentation"', body, target)

    def test_not_found_outside_the_documentation_directories(self):
        for target in ("/doc/docs/backlog/README.md", "/doc/docs/specs/%2E%2E/backlog/README.md",
                       f"/doc/{self.repo.root}/docs/specs/onboarding.md", "/doc/docs/specs/missing.md"):
            self.assertEqual(self.response(target)[0], 404, target)


class DocumentationDirectories(unittest.TestCase):
    """The documentation key of config.yml: the served directories, relative to the repo root."""

    def test_without_the_key_the_specs_and_the_project_documentation(self):
        self.assertEqual(documentation_directories({"project": "Boutique"}),
                         ["docs/specs", "docs/documentation"])

    def test_a_list_of_directories(self):
        self.assertEqual(documentation_directories({"documentation": ["docs/specs", "docs/adr"]}),
                         ["docs/specs", "docs/adr"])

    def test_a_single_directory_written_without_brackets(self):
        self.assertEqual(documentation_directories({"documentation": "docs/specs"}), ["docs/specs"])


class DocumentResolution(unittest.TestCase):
    """Only the .md files of the documentation directories, under the repo root, are served."""

    def setUp(self):
        self.repo = ThrowawayRepo().with_document("docs/specs/onboarding.md", "# Onboarding\n")
        self.addCleanup(self.repo.close)
        self.documentation = Documentation(self.repo.root, ["docs/specs"])

    def test_a_markdown_file_of_a_documentation_directory(self):
        self.assertEqual(self.documentation.document("docs/specs/onboarding.md"),
                         self.repo.root / "docs/specs/onboarding.md")

    def test_refuses_a_file_that_is_not_markdown(self):
        self.repo.write("docs/specs/mockup.html", "<p>mockup</p>")

        self.assertIsNone(self.documentation.document("docs/specs/mockup.html"))

    def test_refuses_a_markdown_file_outside_the_documentation_directories(self):
        self.repo.write("docs/backlog/README.md", "# Backlog\n")

        self.assertIsNone(self.documentation.document("docs/backlog/README.md"))

    def test_refuses_to_go_up_out_of_a_documentation_directory(self):
        self.repo.write("docs/backlog/README.md", "# Backlog\n")

        self.assertIsNone(self.documentation.document("docs/specs/../backlog/README.md"))

    def test_refuses_a_symbolic_link_that_leads_out_of_the_repo(self):
        elsewhere = tempfile.TemporaryDirectory()
        self.addCleanup(elsewhere.cleanup)
        secret = Path(elsewhere.name) / "secret.md"
        secret.write_text("# Secret\n", encoding="utf-8")
        (self.repo.root / "docs/specs/secret.md").symlink_to(secret)

        self.assertIsNone(self.documentation.document("docs/specs/secret.md"))

    def test_refuses_a_documentation_directory_that_is_a_link_outside_the_repo(self):
        elsewhere = tempfile.TemporaryDirectory()
        self.addCleanup(elsewhere.cleanup)
        (Path(elsewhere.name) / "secret.md").write_text("# Secret\n", encoding="utf-8")
        (self.repo.root / "docs/adr").symlink_to(elsewhere.name, target_is_directory=True)
        documentation = Documentation(self.repo.root, ["docs/adr"])

        self.assertIsNone(documentation.document("docs/adr/secret.md"))

    def test_refuses_a_markdown_link_to_a_file_that_is_not_markdown(self):
        self.repo.write("docs/specs/notes.txt", "notes")
        (self.repo.root / "docs/specs/notes.md").symlink_to("notes.txt")

        self.assertIsNone(self.documentation.document("docs/specs/notes.md"))

    def test_nothing_for_a_missing_document(self):
        self.assertIsNone(self.documentation.document("docs/specs/missing.md"))


class DocumentationIndex(unittest.TestCase):
    """The folder sections of the index page: one documentation directory each, with its pages."""

    def setUp(self):
        self.repo = ThrowawayRepo()
        self.addCleanup(self.repo.close)

    def folder_sections(self, *directories):
        return Documentation(self.repo.root, list(directories)).index()

    def test_the_pages_of_a_directory_with_their_title_in_the_order_of_the_paths(self):
        self.repo.with_document("docs/specs/part-time.md", "# Part time\n")
        self.repo.with_document("docs/specs/onboarding.md", "Status: ready\n\n# Onboarding\n")

        folder_section, = self.folder_sections("docs/specs")

        self.assertEqual(folder_section.directory, "docs/specs")
        self.assertEqual(folder_section.pages, [Page("docs/specs/onboarding.md", "Onboarding"),
                                                Page("docs/specs/part-time.md", "Part time")])

    def test_a_page_without_a_title_takes_the_name_of_its_file(self):
        self.repo.with_document("docs/specs/draft.md", "## Why\n")

        folder_section, = self.folder_sections("docs/specs")

        self.assertEqual(folder_section.pages, [Page("docs/specs/draft.md", "draft.md")])

    def test_the_entry_page_of_a_directory_comes_first(self):
        self.repo.with_document("docs/documentation/Appendix.md", "# Appendix\n")
        self.repo.with_document("docs/documentation/index.md", "# Boutique\n")

        folder_section, = self.folder_sections("docs/documentation")

        self.assertEqual([p.path for p in folder_section.pages],
                         ["docs/documentation/index.md", "docs/documentation/Appendix.md"])
        self.assertTrue(folder_section.pages[0].is_entry_page)
        self.assertFalse(folder_section.pages[1].is_entry_page)

    def test_a_missing_directory_gives_an_empty_folder_section_that_says_so(self):
        self.repo.with_document("docs/specs/onboarding.md", "# Onboarding\n")

        specs, documentation = self.folder_sections("docs/specs", "docs/documentation")

        self.assertTrue(specs.exists)
        self.assertEqual((documentation.exists, documentation.pages), (False, []))

    def test_does_not_list_what_would_not_be_served(self):
        elsewhere = tempfile.TemporaryDirectory()
        self.addCleanup(elsewhere.cleanup)
        secret = Path(elsewhere.name) / "secret.md"
        secret.write_text("# Secret title\n", encoding="utf-8")
        self.repo.with_document("docs/specs/onboarding.md", "# Onboarding\n")
        (self.repo.root / "docs/specs/secret.md").symlink_to(secret)

        folder_section, = self.folder_sections("docs/specs")

        self.assertEqual(folder_section.pages, [Page("docs/specs/onboarding.md", "Onboarding")])

    def test_the_pages_of_the_subdirectories_follow_those_of_the_directory(self):
        for path in ("rules/calendar.md", "rules/INDEX.md", "glossary.md", "INDEX.md"):
            self.repo.with_document(f"docs/documentation/{path}", "# Page\n")

        folder_section, = self.folder_sections("docs/documentation")

        self.assertEqual([p.path for p in folder_section.pages],
                         ["docs/documentation/INDEX.md", "docs/documentation/glossary.md",
                          "docs/documentation/rules/INDEX.md", "docs/documentation/rules/calendar.md"])

    def test_a_directory_configured_outside_the_repo_gives_no_page(self):
        elsewhere = tempfile.TemporaryDirectory()
        self.addCleanup(elsewhere.cleanup)
        (Path(elsewhere.name) / "secret.md").write_text("# Secret\n", encoding="utf-8")

        absolute, upward = self.folder_sections(elsewhere.name, f"../{Path(elsewhere.name).name}")

        self.assertEqual((absolute.pages, upward.pages), ([], []))


class DocumentationFingerprint(unittest.TestCase):
    """The fingerprint that the documentation pages watch to reload live."""

    def setUp(self):
        self.repo = ThrowawayRepo().with_document("docs/specs/onboarding.md", "# Onboarding\n")
        self.addCleanup(self.repo.close)
        self.documentation = Documentation(self.repo.root, ["docs/specs"])

    def test_changes_when_a_page_changes(self):
        before = self.documentation.fingerprint()

        self.repo.with_document("docs/specs/onboarding.md", "# Onboarding\n\nOne more rule.\n")

        self.assertNotEqual(self.documentation.fingerprint(), before)

    def test_changes_when_a_page_appears(self):
        before = self.documentation.fingerprint()

        self.repo.with_document("docs/specs/part-time.md", "# Part time\n")

        self.assertNotEqual(self.documentation.fingerprint(), before)

    def test_does_not_change_as_long_as_nothing_changes(self):
        self.assertEqual(self.documentation.fingerprint(), self.documentation.fingerprint())


def page_body(page):
    """The content of a documentation page, without its head or its style: readable failures."""
    return page.split('<div class="page">', 1)[1].split("</div>\n<script>", 1)[0]


class IndexPage(unittest.TestCase):
    """The index page of the documentation, served on /doc/."""

    def setUp(self):
        self.repo = ThrowawayRepo()
        self.addCleanup(self.repo.close)

    def page(self):
        return page_body(index_page(Backlog(self.repo.backlog)))

    def test_leads_back_to_the_board(self):
        self.assertIn('<nav class="breadcrumb" data-i18n="doc.breadcrumb.documentation">'
                      '<a href="/" data-i18n="doc.breadcrumb.board"></a> › </nav>\n'
                      """<h1 data-i18n="doc.index.heading" data-i18n-args='{"project": "Boutique"}'></h1>""",
                      self.page())

    def test_a_link_to_each_page_with_its_title(self):
        self.repo.with_document("docs/specs/onboarding.md", "# Onboarding\n")

        self.assertIn('<a href="/doc/docs/specs/onboarding.md">Onboarding</a>', self.page())

    def test_says_that_a_documentation_directory_does_not_exist_yet(self):
        self.assertIn("""<p class="empty" data-i18n="doc.folder.missing" """
                      """data-i18n-args='{"directory": "docs/documentation"}'></p>""", self.page())

    def test_says_that_a_documentation_directory_has_no_page_yet(self):
        (self.repo.root / "docs/specs").mkdir()

        self.assertIn('<h2>docs/specs</h2><p class="empty" data-i18n="doc.folder.empty"></p>', self.page())

    def test_points_out_the_entry_page_of_a_directory(self):
        self.repo.with_document("docs/documentation/INDEX.md", "# Boutique\n")

        self.assertIn('<a href="/doc/docs/documentation/INDEX.md">Boutique</a>'
                      ' <span class="badge" data-i18n="doc.entryPage"></span>',
                      self.page())


class DocumentPage(unittest.TestCase):
    """The page of a document, served on /doc/<path from the repo root>."""

    def setUp(self):
        self.repo = ThrowawayRepo().with_document("docs/specs/onboarding.md", "# Onboarding\n\nThe **need**.\n")
        self.addCleanup(self.repo.close)

    def page(self, path="docs/specs/onboarding.md"):
        return document_page(Backlog(self.repo.backlog), path)

    def test_the_document_rendered_under_a_trail_that_leads_back_to_the_documentation_and_the_board(self):
        self.assertEqual(page_body(self.page()),
                         '\n<nav class="breadcrumb"><a href="/" data-i18n="doc.breadcrumb.board"></a> › '
                         '<a href="/doc/" data-i18n="doc.breadcrumb.documentation"></a> › '
                         '<span class="path">docs/specs/onboarding.md</span></nav>\n'
                         '<article class="md">\n<h1>Onboarding</h1>\n'
                         '<p>The <strong>need</strong>.</p>\n</article>\n')

    def test_the_tab_bears_the_title_of_the_document(self):
        self.assertEqual(re.search(r"<title>(.*)</title>", self.page()).group(1), "Onboarding · Boutique")

    def test_nothing_for_a_document_that_is_not_to_be_served(self):
        self.assertIsNone(self.page("docs/backlog/config.yml"))

    def test_the_spec_leads_to_the_tickets_that_designate_it(self):
        self.repo.with_ticket("BOU-1", "First launch", spec="docs/specs/onboarding.md")
        self.repo.with_ticket("BOU-2", "Part time", spec="docs/specs/part-time.md")

        self.assertIn('<p class="subtitle" data-i18n="doc.spec.tickets" data-i18n-at="start">'
                      ' <a href="/#BOU-1">BOU-1 · First launch</a></p>',
                      page_body(self.page()))


def html(markdown):
    return markdown_to_html(markdown)


class ParagraphRendering(unittest.TestCase):

    def test_a_paragraph_with_its_text_escaped(self):
        self.assertEqual(html('A <script> & some "quotes"'),
                         "<p>A &lt;script&gt; &amp; some &quot;quotes&quot;</p>")

    def test_a_blank_line_separates_two_paragraphs(self):
        self.assertEqual(html("First line\nrest of the paragraph\n\nSecond paragraph\n"),
                         "<p>First line\nrest of the paragraph</p>\n<p>Second paragraph</p>")

    def test_two_spaces_or_a_backslash_at_the_end_of_a_line_force_a_line_break(self):
        self.assertEqual(html("Question  \nAnswer\\\nMemory: R-024  "),
                         "<p>Question<br>\nAnswer<br>\nMemory: R-024</p>")


class HeadingRendering(unittest.TestCase):

    def test_one_heading_per_level_of_hashes(self):
        self.assertEqual(html("# Glossary\n## Level\n###### Detail"),
                         "<h1>Glossary</h1>\n<h2>Level</h2>\n<h6>Detail</h6>")

    def test_a_heading_ends_the_paragraph_that_precedes_it(self):
        self.assertEqual(html("The need.\n## History"), "<p>The need.</p>\n<h2>History</h2>")

    def test_a_heading_keeps_its_formatting(self):
        self.assertEqual(html("## The `kanban serve` command"), "<h2>The <code>kanban serve</code> command</h2>")

    def test_the_closing_hashes_are_not_part_of_the_heading(self):
        self.assertEqual(html("## History ##"), "<h2>History</h2>")


class InlineRendering(unittest.TestCase):

    def test_bold(self):
        self.assertEqual(html("**Question** asked"), "<p><strong>Question</strong> asked</p>")

    def test_italics_with_an_asterisk_or_an_underscore(self):
        self.assertEqual(html("a *rhythm* and a _share_"), "<p>a <em>rhythm</em> and a <em>share</em></p>")

    def test_no_italics_between_the_underscores_of_a_word(self):
        self.assertEqual(html("the fields jira_sync and jira_fingerprint"),
                         "<p>the fields jira_sync and jira_fingerprint</p>")

    def test_inline_code_keeps_its_text_as_it_is(self):
        self.assertEqual(html("run `kanban **serve** <port>` then"),
                         "<p>run <code>kanban **serve** &lt;port&gt;</code> then</p>")

    def test_the_control_characters_of_the_file_are_removed(self):
        self.assertEqual(html("a\x000\x00b\x1b"), "<p>a0b</p>")

    def test_a_backslash_keeps_the_character_that_follows_it_as_it_is(self):
        self.assertEqual(html(r"\*not in italics\* nor \`in code\`"), "<p>*not in italics* nor `in code`</p>")


class ListRendering(unittest.TestCase):

    def test_a_bulleted_list(self):
        self.assertEqual(html("- Grade 1\n- **Grade 2**\n- Grade 3"),
                         "<ul>\n<li>Grade 1</li>\n<li><strong>Grade 2</strong></li>\n<li>Grade 3</li>\n</ul>")

    def test_a_list_ends_the_paragraph_that_precedes_it(self):
        self.assertEqual(html("In this slice:\n- the rhythm"),
                         "<p>In this slice:</p>\n<ul>\n<li>the rhythm</li>\n</ul>")

    def test_a_list_inside_a_list(self):
        self.assertEqual(html("- In this slice:\n  - the rhythm\n  - the share\n- Later: the zone"),
                         "<ul>\n<li>In this slice:\n"
                         "<ul>\n<li>the rhythm</li>\n<li>the share</li>\n</ul></li>\n"
                         "<li>Later: the zone</li>\n</ul>")

    def test_a_line_that_continues_the_item_without_indent(self):
        self.assertEqual(html("- Status: confirmed\nrest of the source\n- Second"),
                         "<ul>\n<li>Status: confirmed\nrest of the source</li>\n<li>Second</li>\n</ul>")

    def test_a_numbered_list(self):
        self.assertEqual(html("1. The rhythm\n2. The share"),
                         "<ol>\n<li>The rhythm</li>\n<li>The share</li>\n</ol>")

    def test_a_numbered_list_keeps_its_first_number(self):
        self.assertEqual(html("3. The working days"), '<ol start="3">\n<li>The working days</li>\n</ol>')

    def test_another_kind_of_bullet_starts_another_list(self):
        self.assertEqual(html("1. One\n- bullet"), "<ol>\n<li>One</li>\n</ol>\n<ul>\n<li>bullet</li>\n</ul>")

    def test_a_blank_line_between_two_items_loosens_the_list_without_splitting_it(self):
        self.assertEqual(html("1. One\n\n2. Two"), "<ol>\n<li><p>One</p></li>\n<li><p>Two</p></li>\n</ol>")

    def test_an_item_keeps_what_is_indented_after_a_blank_line(self):
        self.assertEqual(html("- One\n\n  the item's rest\n- Two"),
                         "<ul>\n<li><p>One</p>\n<p>the item&#x27;s rest</p></li>\n<li><p>Two</p></li>\n</ul>")


class CodeBlockRendering(unittest.TestCase):

    def test_a_code_block_keeps_its_text_escaped(self):
        self.assertEqual(html("```\nif a < b && c\n  # not a heading\n```"),
                         "<pre><code>if a &lt; b &amp;&amp; c\n  # not a heading</code></pre>")

    def test_the_language_of_the_block_becomes_its_class(self):
        self.assertEqual(html("~~~sh\nkanban serve\n~~~"),
                         '<pre><code class="language-sh">kanban serve</code></pre>')

    def test_only_a_closing_fence_as_long_and_of_the_same_sign_closes_the_block(self):
        self.assertEqual(html("````md\n```\n~~~~\n````"), '<pre><code class="language-md">```\n~~~~</code></pre>')


class CommentRendering(unittest.TestCase):

    def test_an_html_comment_does_not_appear_except_in_a_code_block(self):
        self.assertEqual(html("Before<!-- note\non two lines --> after\n\n"
                              "<!-- Draft -->\n```\n<!-- kept -->\n```"),
                         "<p>Before after</p>\n<pre><code>&lt;!-- kept --&gt;</code></pre>")


class ThematicBreakRendering(unittest.TestCase):

    def test_a_line_of_dashes_asterisks_or_underscores_separates_two_parts(self):
        self.assertEqual(html("Before\n\n---\n***\n- - -\n___\n\nAfter"),
                         "<p>Before</p>\n<hr>\n<hr>\n<hr>\n<hr>\n<p>After</p>")


class BlockquoteRendering(unittest.TestCase):

    def test_a_blockquote_keeps_its_line_breaks_like_a_word_for_word_answer(self):
        self.assertEqual(html("**Answer**\n> Yes, reco.\n> And **Wednesday** too.\n\nMemory: R-024"),
                         "<p><strong>Answer</strong></p>\n<blockquote>\n"
                         "<p>Yes, reco.<br>\nAnd <strong>Wednesday</strong> too.</p>\n"
                         "</blockquote>\n<p>Memory: R-024</p>")


class TableRendering(unittest.TestCase):

    def test_a_table_has_a_header_row_and_data_rows(self):
        self.assertEqual(html("| File | Read when… |\n|---|---|\n"
                              "| [context.md](context.md) | **always** |"),
                         "<table>\n<thead>\n<tr><th>File</th><th>Read when…</th></tr>\n</thead>\n<tbody>\n"
                         '<tr><td><a href="context.md">context.md</a></td>'
                         '<td><strong>always</strong></td></tr>\n'
                         "</tbody>\n</table>")

    def test_an_escaped_bar_stays_in_its_cell(self):
        self.assertIn("<tr><td>morning <code>|</code> afternoon</td><td>2</td></tr>",
                      html("| Half days | Count |\n|---|---|\n| morning `\\|` afternoon | 2 |"))


def gherkin(*lines):
    return html("```gherkin\n" + "\n".join(lines) + "\n```")


def gherkin_block(content):
    return f'<pre><code class="language-gherkin">{content}</code></pre>'


class GherkinRendering(unittest.TestCase):
    """The ```gherkin blocks of the specs: keywords, titles, comments and variables highlighted."""

    def test_the_keyword_of_a_step(self):
        self.assertEqual(gherkin("    When I open Boutique's home page"),
                         gherkin_block('    <span class="gk-keyword">When</span> I open Boutique&#x27;s home page'))

    def test_the_keyword_and_the_title_of_a_scenario(self):
        self.assertEqual(gherkin("  Scenario Outline: A class with one or several levels"),
                         gherkin_block('  <span class="gk-keyword">Scenario Outline:</span>'
                                       '<span class="gk-title"> A class with one or several levels</span>'))

    def test_the_variables_of_a_scenario_outline(self):
        self.assertEqual(gherkin("    Then Boutique shows my class as <levels shown>"),
                         gherkin_block('    <span class="gk-keyword">Then</span> Boutique shows my class as '
                                       '<span class="gk-variable">&lt;levels shown&gt;</span>'))

    def test_a_comment_stays_a_comment(self):
        self.assertEqual(gherkin("# language: en", "  # When <nothing> isn't said"),
                         gherkin_block('<span class="gk-comment"># language: en</span>\n'
                                       '  <span class="gk-comment">'
                                       '# When &lt;nothing&gt; isn&#x27;t said</span>'))

    def test_the_keywords_of_a_feature_file_written_in_french(self):
        self.assertEqual(gherkin("  Plan du scénario: Une classe", "    Quand j'ouvre Boutique"),
                         gherkin_block('  <span class="gk-keyword">Plan du scénario:</span>'
                                       '<span class="gk-title"> Une classe</span>\n'
                                       '    <span class="gk-keyword">Quand</span> j&#x27;ouvre Boutique'))


class LinkRendering(unittest.TestCase):

    def test_a_relative_link_leads_to_the_other_page_in_the_same_tab(self):
        self.assertEqual(html("see the [glossary](glossary.md)"),
                         '<p>see the <a href="glossary.md">glossary</a></p>')

    def test_a_link_to_another_site_opens_in_another_tab(self):
        self.assertEqual(html("[Jira](https://example.atlassian.net/browse/BOU-1?a=1&b=2)"),
                         '<p><a href="https://example.atlassian.net/browse/BOU-1?a=1&amp;b=2" target="_blank"'
                         ' rel="noopener noreferrer">Jira</a></p>')

    def test_a_link_that_would_run_code_keeps_only_its_text(self):
        self.assertEqual(html("[click](JavaScript:alert`1`) [image](data:text/html;base64,PHNjcmlwdD4)"),
                         "<p>click image</p>")

    def test_a_link_to_an_email_address(self):
        self.assertEqual(html("[write](mailto:po@example.com)"),
                         '<p><a href="mailto:po@example.com">write</a></p>')


ONBOARDING_SPEC = """# Onboarding

## Scenarios
```gherkin
Feature: First launch of Boutique

  Scenario: Very first launch
    Given Boutique has never been opened
    When I open Boutique
    Then Boutique shows me the onboarding
```
"""


if __name__ == "__main__":
    unittest.main()
