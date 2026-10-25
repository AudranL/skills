---
name: agent-memory
description: "Protocole de la mémoire qu'un agent d'IA tient dans un projet (par exemple docs/ia/<agent>/) : un index « à lire quand… », une entrée par titre avec son statut et sa source, les statuts (confirmée, déduite, hypothèse, vérifiée) et ce que chacun tranche, la validation des entrées déduites, l'amorçage avec l'accord du projet, la reprise des entrées qu'un autre agent cède, le renvoi plutôt que la citation, l'entretien (état présent, découpage, questions résolues), le compte rendu des changements et le commit séparé. À charger avant d'amorcer une mémoire, d'y écrire ou d'y corriger une entrée, de la réorganiser, ou de céder des entrées à un autre agent."
---

# La mémoire d'un agent dans un projet

Une mémoire évite à l'agent de redécouvrir à chaque tâche ce qu'il a déjà appris dans ce projet, et de reposer les questions déjà tranchées. Elle doit coûter moins cher à lire que ce qu'elle remplace : elle dit l'état présent, en peu de mots, et renvoie au reste.

## Ce que l'agent fournit

L'agent qui renvoie à cette skill dit, dans sa section sur la mémoire :

- **son dossier** dans le projet (par exemple `docs/ia/<agent>/`) ;
- **la table de ses fichiers** : ce que chacun contient et le préfixe de ses identifiants ;
- **les statuts qu'il emploie**, parmi ceux de cette skill ;
- **ses sources d'amorçage** et ce qui, dans son rôle, va ou ne va pas dans sa mémoire.

**Chaque mémoire a un seul lecteur et un seul rédacteur : son agent.** Un agent ne lit ni ne modifie la mémoire d'un autre ; il lui pose ses questions, ou reçoit ce qu'il lui cède (voir « Céder une tâche »).

## Lire

- **Au démarrage**, lire `INDEX.md`, puis seulement les fichiers utiles à la tâche. Sans dossier, l'amorcer (voir « Amorcer »).
- **Une entrée `confirmée` ou `vérifiée` tranche** : ne pas reposer la question, ne pas redécouvrir ce qu'elle dit. Si elle s'avère fausse (une commande échoue), la corriger.
- **Une entrée `déduite` ou `hypothèse` se confirme en passant** : « Je pars de R-005 (déduite du code) : c'est toujours vrai ? »
- **Challenger avec la mémoire** : une demande qui contredit une entrée confirmée se signale en la citant (« R-003 dit le contraire : on change la règle ou la demande ? »).
- **Une entrée datée est un instantané** : avant de s'appuyer sur elle, regarder si ce qu'elle décrit a changé depuis sa date (`git log --since=<date> --oneline -- <chemin>`) ; si oui, revérifier puis la réécrire.

## Une entrée

`INDEX.md` est lu en premier : **une ligne courte par fichier, qui dit quand le lire** (« à lire avant d'écrire un test »), sans la liste de ses entrées ni historique.

Ailleurs, une entrée par titre `###`, lisible seule :

```markdown
### R-003 · Une panne du service de paiement n'est jamais présentée comme un paiement refusé
- Statut : confirmée · Source : notes de ABC-123 (AAAA-MM-JJ)
- Pourquoi : un « refusé » pousse le client à changer de carte, alors que la sienne est valide.
- <Ce qui sert à la prochaine tâche : exemples, conséquences, limites.>
- Voir aussi : D-002
```

Statuts (chaque agent dit lesquels il emploie) :

- `confirmée` : dite ou validée par l'utilisateur, ou écrite dans un document qu'il a validé ;
- `vérifiée` : constatée en l'exécutant (commande lancée, test observé), avec la date ; pas besoin de validation ;
- `déduite` : lue dans le code, la configuration, les tests ou la documentation, source citée, en attente de validation ; elle ne tranche jamais un point sans cette validation ;
- `hypothèse` : retenue faute de réponse, en attendant ; la question correspondante est ouverte.

Certains fichiers ont leur propre format, sans statut : une **décision** porte sa date et sa source ; une **question**, sa date d'ouverture, qui peut répondre, la tâche visée et l'hypothèse retenue en attendant ; une **dette**, sa date, son impact et le traitement proposé ; une **consigne de l'utilisateur**, son statut, sa date, sa source et ses mots quand ils comptent. L'agent le dit dans sa table de fichiers.

## Renvoyer plutôt que recopier

- **Une entrée qui s'appuie sur ce qu'un autre document tient déjà y renvoie par un lien** au lieu de le recopier : une note de ticket (ticket et date), une fiche, un ADR, une autre entrée (identifiant), un fichier (chemin). Si la règle change là-bas, le lien reste vrai ; une citation, elle, devient fausse sans que personne le voie.
- **Les mots de l'utilisateur se citent là où ils sont la source**, une fois : la note du ticket, la consigne. Ailleurs, on y renvoie. Seul un mot exact qui compte (un terme du métier, une valeur) se recopie.
- **Une règle se cite par son titre, pas par son numéro**, qui peut changer : « la règle « Demander avant d'écrire » », pas « la règle 11 ».
- **Pas d'identifiant d'une entrée de la mémoire d'un autre agent** : on ne peut pas la lire et elle peut changer. Écrire le fait et d'où il vient (« le software engineer a constaté le 2026-10-23 que… »).
- **Une copie du code ou de la configuration n'y va pas** : un chemin suffit.

## Amorcer

1. **Demander d'abord** si le projet veut cette mémoire, et où (en mode délégué, par l'agent qui t'a lancé). Un prompt qui invite à écrire ne vaut pas accord de l'utilisateur.
2. **Avec son accord, la créer** à partir des sources que dit l'agent, en `déduite` (sauf ce qu'un document validé dit déjà, en `confirmée`, et ce qu'une commande lancée vérifie, en `vérifiée`). Peu d'entrées : seulement ce qui sert au rôle.
3. **Soumettre les entrées déduites** à l'utilisateur, et ouvrir une vague de questions sur ce qui manque.
4. **Le signaler** dans le compte rendu.

## Écrire

- **Capitaliser** dès qu'un fait durable apparaît : une réponse de l'utilisateur qui tranche, une commande qui marche après un échec, ce qu'une tâche a appris. L'agent écrit sans demander : chaque entrée porte son statut et sa source, et le diff est relu. Seule une réponse explicite de l'utilisateur fait passer une entrée à `confirmée`.
- **Ce qui y va** : ce qui vaudra pour la prochaine tâche dans ce projet. **Ce qui n'y va pas** : le détail d'une tâche, ce qu'un autre document porte déjà (un lien suffit), les règles du rôle de l'agent (elles vont dans son fichier), ce qui appartient au rôle d'un autre agent.
- **Partageable** : la mémoire est versionnée avec le projet. Rien qui dépende d'une machine (chemin personnel, commande propre à un système sans la version à appliquer), chaque chemin écrit depuis la racine du dépôt, aucun secret.
- **Une entrée `déduite` se fait valider** dans la même réponse ou, au plus tard, en fin de tâche, groupée avec les autres. Validée, elle passe à `confirmée` ; corrigée, elle est réécrite puis confirmée ; refusée, elle est retirée ou devient une question.

## Entretenir

- **Une entrée dit l'état présent, pas son histoire.** Les tâches passées, les corrections successives et les longues citations vont au contrôle de version et aux documents sources ; l'entrée y renvoie.
- **Une règle contredite est remplacée, pas empilée.** Si l'agent tient un fichier de décisions, l'ancienne y passe avec le motif.
- **Une question résolue quitte le fichier des questions** : sa réponse rejoint l'entrée qu'elle tranche, qui cite l'ancien identifiant (« ex-Q-012 »). Pas de liste des questions résolues. De même, une dette soldée sort de son fichier, avec la date dans le commit.
- **Un fichier qui dépasse 150 lignes ou 12 000 caractères se découpe** par sujet (`regles-<sujet>.md`), sans renuméroter les entrées, et `INDEX.md` est mis à jour.

## Céder une tâche

Quand une tâche passe d'un agent à un autre, ses entrées partent avec elle :

- **Celui qui cède** rend les entrées qui la concernent dans une section « Pour le <agent> » de sa réponse, que l'agent qui les a lancés relaie telle quelle, puis les retire de sa mémoire et met son `INDEX.md` à jour.
- **Celui qui reçoit** les range dans sa mémoire, avec ses propres identifiants et son format. Ce qui se vérifie (une commande) se relance avant d'être marqué `vérifiée` ; le reste garde la source « cédée par <agent> le <date> », en `déduite` tant que l'utilisateur ne l'a pas confirmée.

## Dire ce qui a changé

- **En fin de réponse**, les entrées ajoutées, modifiées ou retirées, avec leur identifiant et une ligne.
- **En mode délégué**, dans une section de la réponse au nom de la mémoire (« Mémoire métier », « Mémoire QA »…), avant la ligne de statut ; les entrées `déduite` y sont regroupées sous « À valider », pour que l'agent qui t'a lancé les soumette à l'utilisateur.
- **Commit** : les changements de la mémoire vont dans un commit séparé (`docs(ia): …`), par l'agent qui commite dans ce projet et seulement quand c'est autorisé.
