# Skills d'une équipe agile

> **Work in progress.** Ces skills sont encore en cours de développement : leurs règles, leurs références, leurs scripts et leurs noms peuvent changer d'une version à l'autre, sans compatibilité garantie.

Quinze skills pour Claude Code, GitHub Copilot et opencode : spécifier, concevoir, développer en TDD et tester. Ce sont les prérequis des agents du dépôt [agents](https://github.com/AudranL/agents), mais chacune sert aussi seule : un agent ou un assistant la charge quand sa description correspond à la tâche.

## Contenu

| Skill | Ce qu'elle fait | Agents qui s'en servent |
|---|---|---|
| `acceptance-tests` | Tests d'acceptation tirés des scénarios Gherkin d'une fiche (boucle externe de l'ATDD), et revue d'acceptation d'une fonctionnalité livrée | `product-owner`, `software-engineer` |
| `adr-writer` | Rédige, complète, remplace et déprécie les ADR, selon le modèle du projet | `software-architect` |
| `agent-memory` | Protocole de la mémoire qu'un agent tient dans un projet : index, statuts, validation des entrées déduites, entretien, cession | les cinq |
| `architecture-review` | Revue d'architecture d'un diff, d'une branche ou d'une fonctionnalité livrée | `software-architect` |
| `architecture-styles` | Catalogue des styles d'architecture et de leurs compromis, diagnostic d'une architecture existante | `software-architect` |
| `architecture-tests` | Tests d'architecture (fonctions de conformité) selon la pile : ArchUnit, compilateur TypeScript, dependency-cruiser… | `software-architect` |
| `clean-code` | Simple Design, nommage, fonctions, commentaires, erreurs, conception, code smells et relecture de code | `software-engineer` |
| `e2e-tests` | Tests de bout en bout qui ne dérangent personne et ne mentent pas (Playwright, navigateur et Electron) | `quality-analyst` |
| `golden-master` | Golden master sur du code Java / Spring Boot avant un refactoring (ApprovalTests, JaCoCo, PIT) | `software-engineer` (facultative) |
| `kanban` | Backlog local en Markdown, tableau dans le terminal ou le navigateur, poussée vers Jira | `product-owner`, `orchestrator` |
| `legacy-code` | Modifier du code sans tests selon Michael Feathers : seams, tests de caractérisation, Sprout et Wrap | `software-engineer` |
| `spec-review` | Relecture d'une fiche à trois (product owner, architecte, testeur) et besoins non fonctionnels | `product-owner`, `software-architect`, `quality-analyst` |
| `spec-writing` | Découpage en fonctionnalités et fiche de spécification, avec ses scénarios Gherkin | `product-owner` |
| `test-conventions` | Conventions de test propres à une pile : Java / Spring Boot, Angular, TypeScript | `software-engineer` |
| `unit-tests` | Ce qui fait un bon test, où tester une règle, anti-patterns, doubles de test | `software-engineer` |

## Prérequis

- **Python 3** (bibliothèque standard seulement) pour les scripts de `kanban` et de `golden-master`.
- **Java et Maven** pour `golden-master`, qui ajoute ApprovalTests, JaCoCo et PIT au projet.
- **Skills facultatives** de Matt Pocock ([mattpocock/skills](https://github.com/mattpocock/skills)), que certaines skills citent quand elles sont installées : `domain-modeling` (`adr-writer`), `codebase-design` (`architecture-styles`), `tdd` (`unit-tests`, `test-conventions`).
- **Serveur MCP** (facultatif) : un serveur MCP Jira (Atlassian), pour que `kanban` pousse les tickets dans Jira.

## Installation

```sh
./install.sh                              # pour toi, dans les trois outils
./install.sh --outils claude              # un seul outil
./install.sh --projet <dossier> --copie   # dans un projet, en copies versionnables
./install.sh --check                      # vérifie sans rien modifier
```

| Outil | Pour toi | Dans un projet |
|---|---|---|
| Claude Code | `~/.claude/skills/<nom>/` | `.claude/skills/<nom>/` |
| GitHub Copilot | `~/.copilot/skills/<nom>/` | `.github/skills/<nom>/` |
| opencode | `~/.config/opencode/skills/<nom>/` | `.opencode/skills/<nom>/` |

## Langue

Les skills sont écrites en français ; leurs exemples de code et de tests suivent les conventions de chaque pile.

## Licence

MIT, voir `LICENSE`.
