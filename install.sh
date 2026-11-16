#!/usr/bin/env bash
# Installs this repository's agents and skills for Claude Code, GitHub Copilot and opencode. A repository may
# hold only agents, or only skills (agents and skills are published in two repositories).
#
#   ./install.sh [--lang CODE] [--tools claude,copilot,opencode] [--project DIR] [--copy] [--check]
#
#   --lang     the language to install when the repository has several (fr/, en/…). One at a time:
#              the agents have the same name in every language, and the tools would mix them up.
#   --tools    the target tools, comma-separated (all three by default)
#   --project  installs into a project (.claude/agents, .github/agents, .opencode/agents) rather than
#              for the user (~/.claude/agents, ~/.copilot/agents, ~/.config/opencode/agents)
#   --copy     copies the files instead of creating symbolic links: advised for a project, which
#              versions its agents, and when this repository may be moved
#   --check    checks the installation without changing anything; exit code 1 if anything differs
#
# Running the script again is safe. A file it would replace that does not come from this repository is
# first moved to a backup (~/.agents-backup/<date>/), whose path is printed. Switching language replaces
# the links made from this repository and removes those the new language does not have; with --copy, the
# script cannot recognize its earlier copies: an agent missing from the new language has to be removed
# by hand.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LANG_CODE=""
TOOLS="claude,copilot,opencode"
PROJECT=""
COPY=0
CHECK=0
ISSUES=0

usage() { awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --lang) LANG_CODE="${2:?--lang expects a code, for example en}"; shift 2 ;;
    --tools) TOOLS="${2:?--tools expects a list}"; shift 2 ;;
    --project) PROJECT="${2:?--project expects a directory}"; shift 2 ;;
    --copy) COPY=1; shift ;;
    --check) CHECK=1; shift ;;
    -h|--help) usage 0 ;;
    *) echo "unknown option: $1" >&2; usage 1 ;;
  esac
done

# --- The language: agents/ at the root, or one folder per language; skills/ alone for a skills repository --
LANGS="$(cd "$REPO" && for d in */agents; do if [ -d "$d" ]; then dirname "$d"; fi; done | tr '\n' ' ')"
if [ -d "$REPO/agents" ] || { [ -z "$LANGS" ] && [ -d "$REPO/skills" ]; }; then
  BASE="$REPO"
else
  if [ -z "$LANGS" ]; then echo "✗ neither agents/ nor skills/ in $REPO" >&2; exit 1; fi
  if [ -z "$LANG_CODE" ]; then
    set -- $LANGS
    if [ $# -gt 1 ]; then echo "✗ several languages ($LANGS): pick one with --lang" >&2; exit 1; fi
    LANG_CODE="$1"
  fi
  BASE="$REPO/$LANG_CODE"
  if [ ! -d "$BASE/agents" ]; then echo "✗ no language \"$LANG_CODE\" (available: $LANGS)" >&2; exit 1; fi
fi

# The skills of a language, otherwise those at the root (kept in their original language).
SKILLS="$BASE/skills"
[ -d "$SKILLS" ] || SKILLS="$REPO/skills"

[ -n "$PROJECT" ] && PROJECT="$(cd "$PROJECT" && pwd)"
# Outside the project: a backup kept in the project would end up in a commit.
BACKUP_DIR="${BACKUP_DIR:-$HOME/.agents-backup/$(date +%Y%m%d-%H%M%S)}"

# --- Where each tool reads its agents and its skills --------------------------------------------
agents_dir() {
  case "$1:${PROJECT:+project}" in
    claude:) echo "$HOME/.claude/agents" ;;
    copilot:) echo "$HOME/.copilot/agents" ;;
    opencode:) echo "$HOME/.config/opencode/agents" ;;
    claude:project) echo "$PROJECT/.claude/agents" ;;
    copilot:project) echo "$PROJECT/.github/agents" ;;
    opencode:project) echo "$PROJECT/.opencode/agents" ;;
  esac
}

skills_dir() {
  case "$1:${PROJECT:+project}" in
    claude:) echo "$HOME/.claude/skills" ;;
    copilot:) echo "$HOME/.copilot/skills" ;;
    opencode:) echo "$HOME/.config/opencode/skills" ;;
    claude:project) echo "$PROJECT/.claude/skills" ;;
    copilot:project) echo "$PROJECT/.github/skills" ;;
    opencode:project) echo "$PROJECT/.opencode/skills" ;;
  esac
}

# Copilot reads only *.agent.md files; Claude Code and opencode, *.md (opencode takes the name from the file).
agent_file() {
  if [ "$1" = copilot ]; then echo "$2.agent.md"; else echo "$2.md"; fi
}

comes_from_here() {  # a link into this repository (another language, an earlier installation)
  [ -L "$1" ] && case "$(readlink "$1")" in "$REPO"/*) return 0 ;; esac
  return 1
}

identical() {
  if [ "$COPY" = 1 ]; then
    [ -e "$2" ] && [ ! -L "$2" ] && diff -rq "$1" "$2" > /dev/null 2>&1
  else
    [ -L "$2" ] && [ "$(readlink "$2")" = "$1" ]
  fi
}

place() {
  local src="$1" dst="$2"
  if identical "$src" "$dst"; then return; fi
  if [ "$CHECK" = 1 ]; then
    echo "✗ $dst is not $( [ "$COPY" = 1 ] && echo "an up-to-date copy of" || echo "a link to" ) $src"
    ISSUES=$((ISSUES + 1))
    return
  fi
  if comes_from_here "$dst"; then
    rm "$dst"
  elif [ -e "$dst" ] || [ -L "$dst" ]; then
    local kept="$BACKUP_DIR/${dst#/}"
    mkdir -p "$(dirname "$kept")"
    mv "$dst" "$kept"
    echo "  backed up: $kept"
  fi
  mkdir -p "$(dirname "$dst")"
  if [ "$COPY" = 1 ]; then cp -R "$src" "$dst"; else ln -s "$src" "$dst"; fi
  echo "✓ $dst"
}

# The links into this repository that the chosen language no longer has (installed from another language).
remove_leftovers() {
  local dir="$1" expected="$2" entry
  [ -d "$dir" ] || return 0
  for entry in "$dir"/*; do
    comes_from_here "$entry" || continue
    case " $expected " in *" $(basename "$entry") "*) continue ;; esac
    if [ "$CHECK" = 1 ]; then
      echo "✗ $entry comes from this repository but is not in the installed language"
      ISSUES=$((ISSUES + 1))
    else
      rm "$entry"
      echo "  removed: $entry"
    fi
  done
}

for tool in ${TOOLS//,/ }; do
  case "$tool" in claude|copilot|opencode) ;; *) echo "✗ unknown tool: $tool" >&2; exit 1 ;; esac
  echo "== $tool${LANG_CODE:+ ($LANG_CODE)}"
  expected=""
  for file in "$BASE"/agents/*.md; do
    [ -e "$file" ] || continue   # a skills repository has no agents
    name="$(basename "$file" .md)"
    target="$(agent_file "$tool" "$name")"
    place "$file" "$(agents_dir "$tool")/$target"
    expected="$expected $target"
  done
  remove_leftovers "$(agents_dir "$tool")" "$expected"
  expected=""
  for dir in "$SKILLS"/*/; do
    [ -d "$dir" ] || continue
    dir="${dir%/}"
    place "$dir" "$(skills_dir "$tool")/$(basename "$dir")"
    expected="$expected $(basename "$dir")"
  done
  # Even without skills in this language: those of another language, installed earlier, go.
  remove_leftovers "$(skills_dir "$tool")" "$expected"
done

if [ "$ISSUES" -gt 0 ]; then
  echo "$ISSUES difference(s)."
  exit 1
fi
[ "$CHECK" = 1 ] && echo "Everything is in place." || echo "Installed."
