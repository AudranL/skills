"""The documentation served read-only by "serve": the .md files of the configured directories."""
import collections
import hashlib
from pathlib import Path

from kanban_lib.files import read_text
from kanban_lib.markdown_html import level_1_headings


def stays_under_root(relative):
    """True for a relative path that does not go up (..): it designates something under the root."""
    return not Path(relative).is_absolute() and ".." not in Path(relative).parts


def is_under(path, directory):
    try:
        path.relative_to(directory)
        return True
    except ValueError:
        return False


class Documentation:
    """The Markdown pages served read-only by "serve": the .md files of the configured directories."""

    def __init__(self, root, directories):
        self.root = root.resolve()
        self.directories = directories

    def document(self, relative):
        """The file of a path relative to the root, or None if it is not to be served.

        The real file, symbolic links followed, must be a .md under the root and under a documentation
        directory: a link does not lead out of the root. The path does not go up (..) and is not
        absolute: a page has only one address.
        """
        if not stays_under_root(relative):
            return None
        file = self.root / relative
        real = file.resolve()
        servable = (file.suffix == real.suffix == ".md" and real.is_file() and is_under(real, self.root)
                    and any(is_under(real, (self.root / d).resolve()) for d in self.directories))
        return file if servable else None

    def index(self):
        """One folder section per documentation directory, in the order of config.yml."""
        return [FolderSection(directory, (self.root / directory).is_dir(), self.pages(directory))
                for directory in self.directories]

    def pages(self, directory):
        """The pages of a directory and of its subdirectories, ordered like a file tree: those of a
        directory, its entry page first, before those of its subdirectories. Only those that
        document() agrees to serve."""
        pages = [Page(path, page_title(read_text(f), f.name)) for path, f in self.files(directory)]
        return sorted(pages, key=lambda p: (Path(p.path).parent.parts, not p.is_entry_page,
                                            p.path.lower()))

    def files(self, directory):
        """(path from the root, file) of the .md files of a directory and its subdirectories that document() serves."""
        if not stays_under_root(directory):
            return []
        paths = sorted(f.relative_to(self.root).as_posix() for f in (self.root / directory).rglob("*.md"))
        served = ((path, self.document(path)) for path in paths)
        return [(path, file) for path, file in served if file]

    def fingerprint(self):
        """Fingerprint of the served pages, for the live reload: it changes when one of them changes."""
        digest = hashlib.sha256()
        for directory in self.directories:
            for path, file in self.files(directory):
                stats = file.stat()
                digest.update(f"{path}:{stats.st_mtime_ns}:{stats.st_size};".encode())
        return digest.hexdigest()[:16]


FolderSection = collections.namedtuple("FolderSection", "directory exists pages")


class Page(collections.namedtuple("Page", "path title")):
    @property
    def is_entry_page(self):
        """INDEX.md or README.md: the page through which one enters a directory."""
        return Path(self.path).name.lower() in ("index.md", "readme.md")


def page_title(text, file_name):
    """The first level 1 heading of a Markdown text, or failing that the name of its file."""
    return next(level_1_headings(text), file_name)
