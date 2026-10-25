#!/usr/bin/env bash
# Installe les agents et les skills de ce dépôt pour Claude Code, GitHub Copilot et opencode. Un dépôt peut ne
# contenir que des agents, ou que des skills (agents et skills publiés dans deux dépôts).
#
#   ./install.sh [--langue CODE] [--outils claude,copilot,opencode] [--projet DOSSIER] [--copie] [--check]
#
#   --langue   la langue à installer quand le dépôt en a plusieurs (fr/, en/…). Une seule à la fois :
#              les agents portent le même nom dans chaque langue, et les outils les confondraient.
#   --outils   les outils visés, séparés par des virgules (par défaut les trois)
#   --projet   installe dans un projet (.claude/agents, .github/agents, .opencode/agents) plutôt que
#              pour l'utilisateur (~/.claude/agents, ~/.copilot/agents, ~/.config/opencode/agents)
#   --copie    copie les fichiers au lieu de créer des liens symboliques : conseillé pour un projet,
#              qui versionne ses agents, et quand ce dépôt risque d'être déplacé
#   --check    vérifie l'installation sans rien modifier ; code de sortie 1 s'il y a un écart
#
# Relancer le script est sans risque. Un fichier qu'il remplacerait et qui ne vient pas de ce dépôt part
# d'abord dans une sauvegarde (~/.agents-sauvegarde/<date>/), dont le chemin est affiché. Changer de langue
# remplace les liens posés depuis ce dépôt et retire ceux que la nouvelle langue n'a pas ; avec --copie, le
# script ne sait pas reconnaître ses anciennes copies : un agent absent de la nouvelle langue reste à retirer
# à la main.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LANGUE=""
OUTILS="claude,copilot,opencode"
PROJET=""
COPIE=0
CHECK=0
ECARTS=0

usage() { awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --langue) LANGUE="${2:?--langue attend un code, par exemple fr}"; shift 2 ;;
    --outils) OUTILS="${2:?--outils attend une liste}"; shift 2 ;;
    --projet) PROJET="${2:?--projet attend un dossier}"; shift 2 ;;
    --copie) COPIE=1; shift ;;
    --check) CHECK=1; shift ;;
    -h|--help) usage 0 ;;
    *) echo "option inconnue : $1" >&2; usage 1 ;;
  esac
done

# --- La langue : agents/ à la racine, ou un dossier par langue ; skills/ seul pour un dépôt de skills --
LANGUES="$(cd "$REPO" && for d in */agents; do if [ -d "$d" ]; then dirname "$d"; fi; done | tr '\n' ' ')"
if [ -d "$REPO/agents" ] || { [ -z "$LANGUES" ] && [ -d "$REPO/skills" ]; }; then
  BASE="$REPO"
else
  if [ -z "$LANGUES" ]; then echo "✗ ni agents/ ni skills/ dans $REPO" >&2; exit 1; fi
  if [ -z "$LANGUE" ]; then
    set -- $LANGUES
    if [ $# -gt 1 ]; then echo "✗ plusieurs langues ($LANGUES) : choisir avec --langue" >&2; exit 1; fi
    LANGUE="$1"
  fi
  BASE="$REPO/$LANGUE"
  if [ ! -d "$BASE/agents" ]; then echo "✗ pas de langue « $LANGUE » (disponibles : $LANGUES)" >&2; exit 1; fi
fi

# Les skills d'une langue, sinon celles de la racine (gardées dans leur langue d'origine).
SKILLS="$BASE/skills"
[ -d "$SKILLS" ] || SKILLS="$REPO/skills"

[ -n "$PROJET" ] && PROJET="$(cd "$PROJET" && pwd)"
# Hors du projet : une sauvegarde rangée dans le projet finirait dans un commit.
SAUVEGARDE="${SAUVEGARDE:-$HOME/.agents-sauvegarde/$(date +%Y%m%d-%H%M%S)}"

# --- Où chaque outil lit ses agents et ses skills -----------------------------------------------
dossier_agents() {
  case "$1:${PROJET:+projet}" in
    claude:) echo "$HOME/.claude/agents" ;;
    copilot:) echo "$HOME/.copilot/agents" ;;
    opencode:) echo "$HOME/.config/opencode/agents" ;;
    claude:projet) echo "$PROJET/.claude/agents" ;;
    copilot:projet) echo "$PROJET/.github/agents" ;;
    opencode:projet) echo "$PROJET/.opencode/agents" ;;
  esac
}

dossier_skills() {
  case "$1:${PROJET:+projet}" in
    claude:) echo "$HOME/.claude/skills" ;;
    copilot:) echo "$HOME/.copilot/skills" ;;
    opencode:) echo "$HOME/.config/opencode/skills" ;;
    claude:projet) echo "$PROJET/.claude/skills" ;;
    copilot:projet) echo "$PROJET/.github/skills" ;;
    opencode:projet) echo "$PROJET/.opencode/skills" ;;
  esac
}

# Copilot ne lit que les fichiers *.agent.md ; Claude Code et opencode, les *.md (opencode tire le nom du fichier).
fichier_agent() {
  if [ "$1" = copilot ]; then echo "$2.agent.md"; else echo "$2.md"; fi
}

vient_d_ici() {  # un lien vers ce dépôt (une autre langue, une installation précédente)
  [ -L "$1" ] && case "$(readlink "$1")" in "$REPO"/*) return 0 ;; esac
  return 1
}

identique() {
  if [ "$COPIE" = 1 ]; then
    [ -e "$2" ] && [ ! -L "$2" ] && diff -rq "$1" "$2" > /dev/null 2>&1
  else
    [ -L "$2" ] && [ "$(readlink "$2")" = "$1" ]
  fi
}

poser() {
  local src="$1" dst="$2"
  if identique "$src" "$dst"; then return; fi
  if [ "$CHECK" = 1 ]; then
    echo "✗ $dst n'est pas $( [ "$COPIE" = 1 ] && echo "une copie à jour de" || echo "un lien vers" ) $src"
    ECARTS=$((ECARTS + 1))
    return
  fi
  if vient_d_ici "$dst"; then
    rm "$dst"
  elif [ -e "$dst" ] || [ -L "$dst" ]; then
    local garde="$SAUVEGARDE/${dst#/}"
    mkdir -p "$(dirname "$garde")"
    mv "$dst" "$garde"
    echo "  sauvegardé : $garde"
  fi
  mkdir -p "$(dirname "$dst")"
  if [ "$COPIE" = 1 ]; then cp -R "$src" "$dst"; else ln -s "$src" "$dst"; fi
  echo "✓ $dst"
}

# Les liens vers ce dépôt que la langue choisie n'a plus (installés depuis une autre langue).
retirer_restes() {
  local dossier="$1" attendus="$2" entree
  [ -d "$dossier" ] || return 0
  for entree in "$dossier"/*; do
    vient_d_ici "$entree" || continue
    case " $attendus " in *" $(basename "$entree") "*) continue ;; esac
    if [ "$CHECK" = 1 ]; then
      echo "✗ $entree vient de ce dépôt mais n'est pas dans la langue installée"
      ECARTS=$((ECARTS + 1))
    else
      rm "$entree"
      echo "  retiré : $entree"
    fi
  done
}

for outil in ${OUTILS//,/ }; do
  case "$outil" in claude|copilot|opencode) ;; *) echo "✗ outil inconnu : $outil" >&2; exit 1 ;; esac
  echo "== $outil${LANGUE:+ ($LANGUE)}"
  attendus=""
  for fichier in "$BASE"/agents/*.md; do
    [ -e "$fichier" ] || continue   # un dépôt de skills n'a pas d'agents
    nom="$(basename "$fichier" .md)"
    cible="$(fichier_agent "$outil" "$nom")"
    poser "$fichier" "$(dossier_agents "$outil")/$cible"
    attendus="$attendus $cible"
  done
  retirer_restes "$(dossier_agents "$outil")" "$attendus"
  attendus=""
  for dossier in "$SKILLS"/*/; do
    [ -d "$dossier" ] || continue
    dossier="${dossier%/}"
    poser "$dossier" "$(dossier_skills "$outil")/$(basename "$dossier")"
    attendus="$attendus $(basename "$dossier")"
  done
  # Même sans skills dans cette langue : celles d'une autre langue, installées avant, partent.
  retirer_restes "$(dossier_skills "$outil")" "$attendus"
done

if [ "$ECARTS" -gt 0 ]; then
  echo "$ECARTS écart(s)."
  exit 1
fi
[ "$CHECK" = 1 ] && echo "Tout est en place." || echo "Installé."
