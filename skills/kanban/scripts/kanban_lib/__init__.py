"""The code of kanban.py, one module per responsibility. See kanban.py for the usage.

The modules, from the leaves to the root:
  files           read and write kanban's text files (UTF-8), and where the templates are (assets/)
  markdown_html   Markdown to HTML: tickets, specs and documentation, all the text escaped
  ticket_file     a ticket's file: its name, its minimal YAML front matter, its sections, what is written in it
  documentation   the documentation served read-only: the .md files of the configured directories
  backlog         a repo's backlog: config.yml, the tickets read from tickets/, their verification
  jira            what is left to push to Jira: the fingerprint of what Jira received, the changed tickets
  html_pages      the HTML pages: the board, live or in a standalone file, and the documentation
  server          the HTTP server of "serve": its responses, the accepted hosts, listening on 127.0.0.1
  commands        the command line, and what each command reads, writes and prints

A module imports only modules placed before it in this list, never kanban; no module touches
sys.path.
"""
