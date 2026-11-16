"""Read and write kanban's text files (UTF-8, LF line endings), and where the skill's templates are."""
from pathlib import Path

# This file is in <skill>/scripts/kanban_lib/: the skill is three directories up.
SKILL_DIR = Path(__file__).resolve().parents[2]
ASSETS = SKILL_DIR / "assets"


def read_text(path):
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def write_text(path, text):
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
