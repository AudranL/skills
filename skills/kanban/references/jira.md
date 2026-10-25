# Pousser le backlog dans Jira (MCP Atlassian)

Le backlog local reste la source de vérité : Jira en reçoit une copie, à la demande, **jamais sans l'accord explicite de l'utilisateur sur ce qui va être écrit**. Rien ne descend de Jira vers le backlog sans son accord non plus.

## Outils

Ceux du MCP officiel Atlassian, préfixés selon le client (`mcp__atlassian__…`, `mcp__claude_ai_Atlassian__…`) : `getAccessibleAtlassianResources`, `getVisibleJiraProjects`, `getJiraProjectIssueTypesMetadata`, `getJiraIssue`, `searchJiraIssuesUsingJql`, `createJiraIssue`, `editJiraIssue`, `getTransitionsForJiraIssue`, `transitionJiraIssue`, `addCommentToJiraIssue`, `getIssueLinkTypes`, `createIssueLink`. Un autre MCP Jira (`jira_*`) se mappe de la même façon. Les noms et paramètres exacts sont ceux que donne le schéma de l'outil : s'y fier plutôt qu'à cette page.

Sans outil Jira dans la session : le dire en une ligne et proposer le contenu prêt à copier.

## Première synchronisation : la correspondance

À faire une fois par dépôt, puis gardé dans `docs/backlog/config.yml` (une ligne `clé: valeur` chacune) :

1. **Site** : `getAccessibleAtlassianResources` donne le `cloudId`. S'il y a plusieurs sites, demander lequel. → `jira_site: mon-equipe.atlassian.net`
2. **Projet** : demander à l'utilisateur (au besoin, lister avec `getVisibleJiraProjects`). → `jira_projet: BOUTIQUE`
3. **Types** : `getJiraProjectIssueTypesMetadata`, puis faire correspondre chaque type local à un type du projet. Sans type « Spike », proposer « Tâche » / « Task ». → `jira_type_epic: Epic`, `jira_type_story: Story`, `jira_type_tache: Task`, `jira_type_spike: Task`, `jira_type_bug: Bug`
4. **Statuts** : le workflow n'est visible qu'à partir d'un ticket. Après la première création, `getTransitionsForJiraIssue` donne les statuts atteignables ; proposer une correspondance, plusieurs statuts locaux pouvant tomber sur le même statut Jira. → `jira_statut_a-cadrer: Backlog`, `jira_statut_en-cadrage: Backlog`, `jira_statut_pret: Selected for Development`, `jira_statut_en-cours: In Progress`, `jira_statut_en-revue: In Review`, `jira_statut_termine: Done`, `jira_statut_abandonne: Done`

Faire valider la correspondance par l'utilisateur avant de l'écrire dans `config.yml`.

## Pousser

1. `kanban.py a-pousser --json` : les tickets à créer (sans clé Jira) et à mettre à jour (modifiés depuis la dernière synchro : champs, texte hors Suivi, ou fiche). Un ticket abandonné qui n'a jamais été poussé ne l'est pas.
2. **Préparer le contenu** de chacun (modèle ci-dessous) : résumé = `titre` ; type et statut selon la correspondance ; parent = la clé Jira de son epic (l'epic se pousse d'abord).
3. **Le montrer à l'utilisateur et attendre son accord** : la liste (création ou mise à jour, clé, titre, statut), puis le contenu complet de chaque ticket créé et ce qui change pour chaque ticket mis à jour. Pour un premier envoi de nombreux tickets, montrer un ticket complet en exemple et la liste, et demander l'accord sur le lot.
4. **Avant de mettre à jour un ticket existant**, le relire (`getJiraIssue`). S'il a été modifié dans Jira après `synchro_jira` (description, statut, nouveaux commentaires), montrer la différence et demander : reprendre dans le backlog (une note `**Précision**` datée, source « Jira, commentaire de … »), ou écraser. Ne jamais écraser en silence.
5. **Créer** (`createJiraIssue`) les epics d'abord, puis les autres tickets par clé croissante. Si le statut voulu n'est pas le statut initial, `getTransitionsForJiraIssue` puis `transitionJiraIssue`. Un champ obligatoire inconnu (ex. « Epic Name ») : lire le message d'erreur et demander la valeur.
6. **Mettre à jour** (`editJiraIssue`) : résumé et description ; la transition si le statut a changé.
7. **Liens** : pour `bloque_par`, une fois les deux tickets dans Jira, `createIssueLink` du type « Blocks » (le bloquant « blocks » le bloqué). Ne pas recréer un lien qui existe.
8. **Après chaque ticket réussi** : `kanban.py synchro <CLE> --jira <CLE-JIRA>`. Un échec n'est pas synchronisé : le dire, avec le message de Jira.
9. Terminer par `kanban.py a-pousser` : la liste doit être vide, sauf échecs annoncés.

## Modèle de description

En Markdown (le MCP le convertit) :

```markdown
<Résumé du ticket>

<Si le ticket a une fiche : ses sections Pourquoi, Pour qui et Périmètre, puis ses scénarios Gherkin dans un bloc ```gherkin.>

## Notes de cadrage (brouillon)
<Les notes du ticket, telles quelles.>

---
Copie du backlog local de <projet> : ticket <CLE> (docs/backlog/tickets/<fichier>). Modifier le ticket local, pas celui-ci : il est réécrit à chaque synchronisation.
```

Le Suivi ne part pas : Jira a son propre historique. Une description trop longue pour Jira (plus de 30 000 caractères environ) garde le Résumé, Pourquoi, Pour qui, Périmètre et les titres des scénarios, avec le chemin de la fiche.

## Partir d'un ticket Jira

Une clé Jira citée par l'utilisateur : la chercher d'abord dans le backlog (`grep -l "^jira: ABC-12" docs/backlog/tickets/*.md`). Absente : lire le ticket (`getJiraIssue`, avec ses commentaires et liens), proposer de le reprendre dans le backlog (`kanban.py nouveau`, type et statut d'après la correspondance, sa description dans le Résumé, ses commentaires utiles en notes avec leur source), puis `kanban.py synchro` pour lier les deux. Sa description dans Jira sera réécrite au format du modèle à la première poussée qui suivra une modification du ticket local : le dire.
