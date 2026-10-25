# Backlog de {projet}

Ce dossier est le **backlog local** de {projet} : la source de vérité des tickets (epics, stories, tâches, spikes, bugs), de leur ordre, de leur statut et de leurs notes de cadrage. Il est versionné avec le code. Jira, s'il est branché, n'en est qu'une copie : on modifie les tickets ici, jamais là-bas.

## Voir le tableau

```sh
alias kanban='python3 -I <dossier de la skill kanban>/scripts/kanban.py'   # à mettre dans ~/.zshrc
# <dossier de la skill kanban> : par exemple ~/.claude/skills/kanban, ~/.copilot/skills/kanban ou ~/.config/opencode/skills/kanban
kanban          # le tableau dans le terminal
kanban serve    # dans le navigateur, sur 127.0.0.1:8765, rechargé à chaque changement
```

## Lire la documentation

`kanban serve` sert aussi, en lecture seule, la documentation du projet sur `http://127.0.0.1:8765/doc/` (lien « Documentation » en tête du tableau) : les fiches de spécification et leurs scénarios Gherkin, et la documentation écrite pour les humains. Les pages se rechargent quand leurs fichiers changent ; le champ `fiche` d'un ticket mène à la page de sa fiche.

Les dossiers servis se règlent dans `config.yml`, depuis la racine du dépôt :

```yaml
documentation: [docs/specs, docs/documentation]   # la valeur par défaut, sans la clé
```

Seuls les fichiers `.md` de ces dossiers sont servis. Un dossier absent n'est pas une erreur. `INDEX.md` ou `README.md` est le point d'entrée de son dossier, et un lien relatif entre deux fichiers (`[Glossaire](glossaire.md)`) mène d'une page à l'autre.

## Colonnes

| Statut | Colonne | Le ticket… |
|---|---|---|
| `a-cadrer` | À cadrer | a un titre, un résumé et des notes de cadrage brouillonnes |
| `en-cadrage` | En cadrage | a une fiche en cours d'écriture |
| `pret` | Prêt | a une fiche validée |
| `en-cours` | En cours | est en développement |
| `en-revue` | En revue | est livré, en revue d'acceptation et d'architecture |
| `termine` | Terminé | est accepté |
| `abandonne` | masquée | est retiré ; la raison est dans son suivi. Un ticket ne se supprime pas. |

## Un ticket

Un fichier par ticket : `tickets/{prefixe}-<n>-<titre>.md`. Une clé n'est jamais réutilisée.

```markdown
---
cle: {prefixe}-4
titre: Zone et vacances
type: story              # epic | story | tache | spike | bug
statut: a-cadrer
epic: {prefixe}-1        # facultatif : l'epic qui le contient
rang: 4                  # facultatif : son ordre dans l'epic (la fonctionnalité 4)
fiche: docs/specs/x.md   # dès qu'il est cadré
bloque_par: [{prefixe}-2, {prefixe}-3]   # facultatif
jira: ABC-12             # posé par la synchro Jira, comme synchro_jira et empreinte_jira
cree: 2026-10-22
---

# {prefixe}-4 · Zone et vacances

## Résumé
Le besoin en une ou deux phrases.

## Notes de cadrage
Les questions et les réponses qui le concernent, au fil de l'eau (ci-dessous).

## Suivi
- 2026-10-22 · créé
```

## Notes de cadrage

La matière brute du cadrage, en attendant qu'on arrive sur le ticket. Une note par échange, la plus récente à la fin :

```markdown
### 2026-10-22 · pendant {prefixe}-2, lot 3, Q4 · posée par le product-owner
**Question**
> La question telle qu'elle a été posée, avec ses options et la recommandation si la réponse y renvoie.

**Réponse**
> La réponse, mot pour mot.

Mémoire : R-024
```

- Mot pour mot : on ne reformule ni la question ni la réponse. Une précision donnée sans question s'écrit `**Précision**`.
- On ajoute, on ne réécrit pas : une note se corrige par une note suivante.
- On ne cadre pas : pas de règle, de scénario ni de question de plus. On cadrera en arrivant sur le ticket.

## Commandes

```sh
kanban nouveau "Titre" --type story --epic {prefixe}-1 --rang 5 --resume "Le besoin en une phrase."
kanban deplacer {prefixe}-4 en-cours --motif "fiche validée"
kanban verifier                       # après toute modification à la main
kanban a-pousser                      # ce qui reste à créer ou à mettre à jour dans Jira
kanban synchro {prefixe}-4 --jira ABC-12   # après avoir poussé le ticket dans Jira
```
