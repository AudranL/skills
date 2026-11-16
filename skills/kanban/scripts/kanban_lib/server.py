"""The HTTP server of "serve": what it answers to each request, the accepted hosts, the listening address."""
import http.server
import re
import urllib.parse

from kanban_lib.backlog import Backlog
from kanban_lib.html_pages import board_html, document_page, index_page, not_found_page, project_documentation
from kanban_lib.ticket_file import BacklogError


HTML = "text/html; charset=utf-8"
TEXT = "text/plain; charset=utf-8"


def response(directory, target):
    """(HTTP code, content type, body) of a GET to "serve". An error without a page has neither type nor body."""
    path = target.split("?")[0]
    try:
        backlog = Backlog(directory)
        if path == "/":
            return 200, HTML, board_html(backlog, live=True)
        if path == "/state":
            return 200, TEXT, backlog.fingerprint()
        if path == "/state/documentation":
            return 200, TEXT, project_documentation(backlog).fingerprint()
        if path in ("/doc", "/doc/"):
            return 200, HTML, index_page(backlog)
        if path.startswith("/doc/"):
            document = urllib.parse.unquote(path[len("/doc/"):])
            page = document_page(backlog, document)
            return (200, HTML, page) if page else (404, HTML, not_found_page(backlog, document))
        return 404, None, None
    except BacklogError as exc:
        return 200, TEXT, f"Error: {exc}"


ACCEPTED_HOST = re.compile(r"(127\.0\.0\.1|localhost)(:[0-9]+)?", re.ASCII | re.IGNORECASE)


def is_accepted_host(host):
    """True if the Host header of a request to "serve" is 127.0.0.1 or localhost, with or without a port.
    Against DNS rebinding: another site's page can point its name to 127.0.0.1 to read the backlog
    from the browser, but its requests then carry that name in Host."""
    return ACCEPTED_HOST.fullmatch(host or "") is not None


def create_server(directory, port):
    """The server of "serve" for this backlog, bound to 127.0.0.1: it refuses (403, without any data) a Host
    that is not accepted, then answers each GET with response(). The listening address and the Host check
    protect the same thing: they change together."""

    class RequestHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if not is_accepted_host(self.headers.get("Host")):
                self.send_error(403)
                return
            code, content_type, body = response(directory, self.path)
            if content_type is None:
                self.send_error(code)
                return
            data = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *_):
            pass

    return http.server.ThreadingHTTPServer(("127.0.0.1", port), RequestHandler)
