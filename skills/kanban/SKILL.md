---
name: kanban
description: "Backlog local en Markdown, façon Jira, versionné avec le dépôt : un ticket par fichier dans docs/backlog/ (epic, story, tâche, spike, bug), un tableau kanban dans le terminal ou dans le navigateur (rechargé en direct, avec la documentation du projet en lecture seule : fiches et leurs scénarios Gherkin, documentation écrite pour les humains), des notes de cadrage où l'on range mot pour mot, au fil de l'eau, les questions posées et les réponses de l'utilisateur, et la poussée vers Jira via le MCP Atlassian. À utiliser pour afficher le tableau, créer, lire, déplacer ou vérifier un ticket, ajouter une note de cadrage, amorcer un backlog dans un dépôt, ou pousser des tickets dans Jira. C'est l'outil du product-owner pour tenir le backlog."
---

# Kanban : le backlog local

Le backlog d'un dépôt vit dans `docs/backlog/`. C'est la **source de vérité** des tickets : leur découpage en epics, leur ordre, leur statut, leurs notes de cadrage et le lien vers leur fiche de spécification. Il est versionné avec le code, donc relu dans les diffs. Jira, s'il est branché, n'en reçoit qu'une copie, sur demande.

Le `README.md` du dossier décrit le format pour un humain ou un agent qui n'a pas cette skill : le garder à jour si le format change.

## Commandes

Le script n'a besoin que de Python 3 (bibliothèque standard) et se lance depuis n'importe où dans le dépôt :

```sh
python3 -I <dossier de cette skill>/scripts/kanban.py <commande>
```

`<dossier de cette skill>` est le dossier de ce fichier : par exemple `~/.claude/skills/kanban` dans Claude Code, `~/.copilot/skills/kanban` dans Copilot, `~/.config/opencode/skills/kanban` dans opencode. Ci-dessous, `kanban.py` désigne cette commande entière. Un agent l'écrit en entier à chaque appel : un alias ou une variable ne passe pas d'un appel de shell à l'autre, et zsh ne découpe pas une variable `$K` en mots. Pour l'utilisateur, proposer l'alias `alias kanban='python3 -I <dossier de cette skill>/scripts/kanban.py'` dans son `~/.zshrc`, avec le vrai chemin.

```sh
kanban.py                    # le tableau dans le terminal (= tableau ; --epic CLE, --tout)
kanban.py serve              # le tableau et la documentation (/doc/) dans le navigateur, sur 127.0.0.1:8765, rechargés en direct
kanban.py html               # le même tableau dans un fichier HTML autonome, ouvert dans le navigateur
kanban.py verifier           # contrôle tous les tickets ; code de sortie 1 en cas d'erreur
kanban.py nouveau "Titre" --type story --epic BOU-1 --rang 5 --resume "Le besoin en une phrase."
kanban.py deplacer BOU-4 en-cours --motif "fiche validée"
kanban.py a-pousser [--json] # ce qui reste à créer ou à mettre à jour dans Jira
kanban.py synchro BOU-4 --jira ABC-12
kanban.py init --projet Boutique --prefixe BOU
```

`--dossier DIR` (avant la commande) pointe un autre backlog.

Le tableau du navigateur est en lecture seule : on modifie les fichiers (à la main, par un agent ou par `deplacer`), le tableau suit.

## Amorcer un backlog

Dans un dépôt sans `docs/backlog/`, demander d'abord si le projet en veut un (un agent lancé par un autre le propose dans sa réponse plutôt que de le faire). Avec son accord :

1. `kanban.py init --projet <Nom> --prefixe <PRE>` ;
2. reporter le découpage connu : une epic, et un ticket à cadrer par fonctionnalité, avec son rang et un résumé d'une ou deux phrases ;
3. mettre dans chaque ticket une note « Reprise de <source> » qui cite ce que l'on savait déjà de lui (questions ouvertes, règles annoncées pour une fonctionnalité à venir), avec sa source ;
4. là où le découpage était tenu jusque-là (une mémoire, un document), ne garder qu'un renvoi vers le backlog.

Après toute modification de `scripts/kanban.py`, lancer `python3 -I -B scripts/selftest.py` (bibliothèque standard, moins d'une seconde).

## Documentation

`kanban.py serve` sert aussi la documentation du projet, en lecture seule, sur `http://127.0.0.1:8765/doc/` (lien « Documentation » en tête du tableau). Chaque page est rendue à la demande depuis son fichier Markdown et se recharge quand un fichier change : on écrit dans les fichiers, comme pour les tickets.

- **Les dossiers servis** : la clé `documentation` de `config.yml`, une liste de dossiers depuis la racine du dépôt. Sans la clé : `[docs/specs, docs/documentation]`, soit les fiches de spécification et la documentation du projet écrite pour les humains. Un dossier absent n'est pas une erreur : l'index dit qu'il n'a aucune page pour l'instant. `documentation: []` ne sert rien.
- **L'index** (`/doc/`) : une rubrique par dossier, sous-dossiers compris, chaque page sous son premier titre `#`. `INDEX.md` ou `README.md` passe en tête de son dossier : c'est son point d'entrée.
- **Une page** a pour adresse son chemin depuis la racine du dépôt (`/doc/docs/specs/onboarding.md`) : un lien relatif entre deux pages (`[Glossaire](glossaire.md)`, `../specs/onboarding.md`) y mène tel quel. La page d'une fiche cite les tickets dont le champ `fiche` la désigne, et le panneau d'un ticket a un lien « Page de la fiche ».
- **Le rendu**, celui du panneau du tableau aussi : titres, paragraphes, listes (imbriquées, numérotées), tableaux, blocs de code (dans un bloc ```` ```gherkin ````, mots-clés, titres de scénario, variables `<…>` et commentaires sont mis en valeur), citations, gras, italique, code en ligne, liens. Tout le texte est échappé : du HTML écrit dans un fichier s'affiche tel quel, sauf les commentaires `<!-- … -->`, qui ne s'affichent pas. Pas rendus : les images (un lien vers le fichier, qui n'est pas servi), l'alignement des colonnes, les tableaux sans `|` en début de ligne, le code en retrait de quatre espaces, les titres soulignés (`===`).
- **Ce qui est servi** : seulement les fichiers `.md` des dossiers configurés, et seulement sur `127.0.0.1`. Un chemin qui remonte (`..`) ou absolu, un lien symbolique qui sort de la racine du dépôt ou des dossiers, un autre type de fichier : la page est « introuvable ».

## Fichiers

```
docs/backlog/
  config.yml        projet, préfixe des clés, correspondance Jira, dossiers de documentation (une ligne « clé: valeur » chacune)
  README.md         le format, pour qui n'a pas cette skill
  tickets/
    BOU-1-premiere-ouverture.md
    BOU-13-onboarding.md
```

## Un ticket

En-tête YAML simple (une ligne `clé: valeur` par champ, listes en `[a, b]`), puis trois sections :

| Champ | Obligatoire | Sens                                                                           |
|---|---|--------------------------------------------------------------------------------|
| `cle` | oui | `<PRÉFIXE>-<n>`, jamais réutilisée ; le fichier s'appelle `<cle>-<titre>.md`   |
| `titre` | oui | le titre du ticket                                                             |
| `type` | oui | `epic`, `story`, `tache`, `spike` ou `bug`                                     |
| `statut` | oui | une colonne, ci-dessous                                                        |
| `cree` | oui | date de création, `AAAA-MM-JJ`                                                 |
| `epic` | | la clé de l'epic qui le contient (une epic n'est dans aucune epic)             |
| `rang` | | son ordre dans l'epic : pour une story, son numéro de fonctionnalité (affiché « F4 ») |
| `fiche` | | le chemin de sa fiche de spécification, depuis la racine du dépôt              |
| `bloque_par` | | les clés des tickets qui doivent passer avant                                  |
| `jira`, `synchro_jira`, `empreinte_jira` | | posés par `synchro`, à ne pas écrire à la main                                 |

- `## Résumé` : le besoin en une ou deux phrases, tel que le découpage le dit. Pas de cadrage.
- `## Notes de cadrage` : la matière brute, ci-dessous.
- `## Suivi` : une ligne datée par événement (créé, déplacé, poussé dans Jira, fiche écrite à partir des notes jusqu'au …). `deplacer` et `synchro` l'écrivent eux-mêmes.

## Colonnes

| Statut | Colonne | Le ticket… | Le déplace |
|---|---|---|---|
| `a-cadrer` | À cadrer | a un titre, un résumé et des notes | (création) |
| `en-cadrage` | En cadrage | a une fiche en cours d'écriture | le product-owner |
| `pret` | Prêt | a une fiche validée par l'utilisateur | le product-owner, ou l'orchestrator à l'étape de validation 1 |
| `en-cours` | En cours | est en développement | l'orchestrator, ou l'utilisateur |
| `en-revue` | En revue | est livré, en revue | l'orchestrator, ou l'utilisateur |
| `termine` | Terminé | est accepté | l'orchestrator à l'étape de validation 3, ou l'utilisateur |
| `abandonne` | masquée | est retiré, avec la raison dans le Suivi | celui qui le retire, avec l'accord de l'utilisateur |

Toujours déplacer avec `deplacer` (il trace le changement dans le Suivi). Un ticket ne se supprime pas : il passe à `abandonne` avec un `--motif`.

## Notes de cadrage

Ce que l'utilisateur a dit d'un ticket avant qu'on le cadre : ses réponses, et les questions qui les ont fait naître. Elles coûtent cher à obtenir ; une synthèse en perd le sens. Une note par échange, la plus récente à la fin :

```markdown
### 2026-10-22 · pendant BOU-2, lot 3, Q4 · posée par le product-owner
**Question**
> La question telle qu'elle a été posée, avec ses options et la recommandation quand la réponse y renvoie (« reco », « B »).

**Réponse**
> La réponse de l'utilisateur, mot pour mot.

Mémoire : R-024
```

- **Le titre** commence par la date, puis d'où vient l'échange (ticket en cours, lot, numéro de la question) et qui a posé la question (product-owner, software-architect, software-engineer, quality-analyst, orchestrator). Une précision que l'utilisateur donne sans question s'écrit `**Précision**` à la place du couple question-réponse.
- **Mot pour mot.** Ne reformuler ni la question ni la réponse, ne pas corriger les fautes. Couper seulement ce qui ne concerne pas le ticket, en le marquant `[…]`.
- **On ajoute, on ne réécrit pas.** Une note se complète ou se corrige par une note suivante. Une réponse qui concerne plusieurs tickets est notée dans chacun.
- **On ne cadre pas.** Pas de règle, de scénario, ni de question de plus : on cadrera en arrivant sur le ticket.
- **La dernière ligne** (facultative) cite ce que l'échange a changé ailleurs : une entrée de mémoire, une fiche.

## Règles

- **Lire avant d'écrire** : le tableau (`kanban.py`), puis le ticket entier. Pour retrouver un ticket par sa clé Jira : `grep -l "^jira: ABC-12" docs/backlog/tickets/*.md`.
- **Écrire** : créer avec `nouveau` (il donne la clé suivante), déplacer avec `deplacer`, ajouter les notes et le résumé en éditant le fichier. Garder la date du jour (`date +%F`) en tête de note.
- **Vérifier** après chaque modification : `kanban.py verifier` doit passer sans erreur.
- **Rien n'est commité ni poussé dans Jira sans l'accord de l'utilisateur.**

## Jira

Pour pousser des tickets, partir d'un ticket Jira ou établir la correspondance des types et statuts : lire `references/jira.md` (procédure avec le MCP Atlassian).
