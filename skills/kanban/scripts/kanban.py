#!/usr/bin/env python3
"""Local Markdown backlog, Jira style: one ticket per file, a kanban board, the Jira sync.

A repo's backlog lives in docs/backlog/: config.yml, README.md and tickets/<KEY>-<title>.md.
Each ticket starts with a simple YAML front matter (one "key: value" line per field), then its
text in Markdown: Summary, Refinement notes, History. The files are the source of truth; this
script only reads them, checks them and changes a few of their fields.

Usage:
  kanban.py [--dir DIR] init --project NAME --prefix PRE
  kanban.py [--dir DIR] board [--epic KEY] [--all]
  kanban.py [--dir DIR] html [--output FILE] [--no-open]
  kanban.py [--dir DIR] serve [--port 8765] [--no-open]
  kanban.py [--dir DIR] check
  kanban.py [--dir DIR] new "Title" --type story [--epic KEY] [--rank N] [--status S] [--summary TEXT]
  kanban.py [--dir DIR] move KEY STATUS [--reason TEXT]
  kanban.py [--dir DIR] to-push [--json]
  kanban.py [--dir DIR] sync KEY --jira JIRA-KEY

Without --dir: docs/backlog at the root of the git repo that contains the current directory.
Without a command: board.

"serve" also serves, read-only under /doc/, the project documentation: the .md files of the
directories of the documentation key of config.yml, from the repo root (default: docs/specs, the specs,
and docs/documentation). The spec field of a ticket leads to the page of its spec.
Code: kanban_lib/ (map in kanban_lib/__init__.py). Tests: python3 -I -B -W error scripts/selftest.py,
after any change to scripts/ or assets/.
"""
import sys
from pathlib import Path

# "python3 -I" does not put the script's directory in sys.path: without it, kanban_lib would not import.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from kanban_lib import commands


if __name__ == "__main__":
    sys.exit(commands.main())
