---
name: adr-writer
description: Rédige, complète, remplace et déprécie les ADR (Architecture Decision Records) dans tout projet, sans dépendre d'un agent spécialisé. Suit le template du projet s'il existe, sinon le modèle de la skill ; reprend le dossier et la langue des ADR existants, sinon les demande. À utiliser pour créer, écrire, mettre à jour, déprécier ou remplacer un ADR, ou quand l'utilisateur décrit une décision d'architecture à consigner.
---

# ADR Writer

Un ADR (Architecture Decision Record) explique **pourquoi** l'équipe a fait un choix de conception : le contexte, les exigences qui ont guidé la décision, les options étudiées, la décision et ses conséquences. C'est un court fichier Markdown (une à deux pages), rangé dans le dépôt près du code concerné, pour que son historique suive celui du code.

**Le problème qu'il résout** (Nygard) : quand la raison d'une décision est perdue, celui qui arrive n'a que deux mauvais choix, l'accepter aveuglément ou la défaire aveuglément. « It's better to avoid either blind acceptance or blind reversal. » Les gros documents ne sont ni lus ni tenus à jour ; de petits documents, un par décision, ont une chance de l'être.

**À quoi il sert** : intégrer un nouveau membre sans qu'il ait été là ; faire évoluer l'architecture sans rouvrir les mêmes débats, puisque les options écartées et leurs raisons sont écrites ; aligner les équipes voisines (architecture, sécurité) ; garder la trace des intentions à long terme (une refonte prévue, par exemple).

**Pour qui on écrit** : un lecteur qui n'était pas là, nouvel arrivant ou équipe qui reprendra l'application. Nygard : l'ADR se lit comme une conversation avec un futur développeur.

Sources : Michael Nygard, *Documenting Architecture Decisions* (2011, https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions) ; Google Cloud, *Présentation des enregistrements de décision d'architecture* (https://docs.cloud.google.com/architecture/architecture-decision-records?hl=fr) ; Ford, Richards et al., *Software Architecture: The Hard Parts*, ch. 1.

## Portabilité

Cette skill s'utilise directement, sans agent spécialisé, sous-agent, configuration locale ou structure de dépôt imposée. Dans le projet fourni, elle découvre les conventions existantes au lieu de supposer un chemin ou un template particulier ; si le projet ou les informations nécessaires ne sont pas accessibles, elle demande uniquement ce qui manque.

## Quand écrire un ADR

Pour une décision **architecturalement significative** : elle touche la structure, les qualités non fonctionnelles, les dépendances, les interfaces ou les techniques de construction (Nygard). En pratique :

- un problème technique sans base de décision existante (pas de solution recommandée, de procédure standard ni de précédent dans le code) ;
- une solution retenue qui n'est documentée nulle part d'accessible à l'équipe ;
- deux options ou plus, dont il faut garder le raisonnement.

Typiquement : choix ou changement de style d'architecture, découpage en contextes bornés, frontière avec un système externe, choix d'un produit ou de sa configuration (base, messagerie, haute disponibilité), dépendance de build structurante, exception assumée à une règle, convention d'architecture.

Pas pour un détail d'implémentation : le dire à l'utilisateur plutôt que d'écrire l'ADR.

## Conventions du projet

Avant d'écrire, repérer la racine du projet à partir du contexte fourni, puis chercher les ADR existants dans le dépôt (par exemple dans `docs/architecture_decisions/`, `docs/adr/`, `doc/adr/`, `docs/decisions/`). Ces chemins sont des exemples, pas des prérequis. Si l'un de ces chemins existe, chercher un template (`template.md` ou équivalent).

| Point | Des ADR existent | Aucun ADR |
|---|---|---|
| **Dossier** | Celui des ADR existants | **Demander le chemin** à l'utilisateur. Si un template existe, proposer son dossier. |
| **Modèle** | Le template du projet s'il existe, sinon le modèle ci-dessous | Idem |
| **Langue** | Celle des ADR existants | **Demander** à l'utilisateur, ne pas supposer |
| **Nom et numéro** | Le schéma des ADR existants, numéro suivant le plus haut | `NNN-<slug-kebab-case>.md`, à partir de `001` |

- Le template du projet fait foi : en respecter les sections, n'en ajouter aucune.
- Les ADR existants donnent le ton et le niveau de détail : rester cohérent avec eux.
- Un numéro n'est jamais réutilisé, même pour un ADR rejeté ou déprécié.
- Si une autre skill se déclenche avec son propre format ou ses propres critères d'ADR (par exemple `domain-modeling`), suivre celle-ci et les ADR existants du projet.

## Modèle

À utiliser quand le projet n'a pas de template. Les textes entre `<…>` indiquent ce qu'on attend : ils se remplacent par le contenu, rédigé dans la langue retenue.

````markdown
## JJ/MM/AAAA - <Titre de la décision>

### Status: Draft | Accepted | Rejected | Deprecated | Supersedes <NNN>

### Decision makers:

- **<Rôle>**: <Nom>

### Context

<En phrases : le problème à résoudre, les forces en jeu et leurs tensions, les contraintes, les parcours utilisateur critiques touchés. Ton neutre, des faits, pas la solution.>

### Decision factors

- <Exigence fonctionnelle ou non fonctionnelle, avec son seuil quand il existe (disponibilité, temps de réponse, testabilité…)>
- <Critère de projet : délai, coût, complexité, compétences de l'équipe>

### Solutions considered

1. **<Option>**
    - Pros: …
    - Cons: …
2. **<Option>** *(chosen)*
    - Pros: …
    - Cons: …

### Decision

<À la voix active, en phrases complètes : « Nous… ». L'option retenue, sa justification et les choix clés qui en découlent.>

### Consequences

<En phrases : ce qui devient plus facile, plus difficile ou ne change pas ; les compromis acceptés ; ce qu'il faut faire ensuite. Comment la décision est vérifiée : le test d'architecture, ou la vérification manuelle.>
````

## Règles de rédaction

### Forme

- **Une seule décision par ADR.** Une même force peut revenir dans plusieurs ADR ; c'est la décision qui fait l'unité.
- **Une à deux pages.** Au-delà, la décision est probablement double : proposer de la découper.
- **Concis.** Pas de sur-explication. Un concept technique (par exemple « monolithe distribué ») s'explique en une phrase dans le contexte, pas dans une sous-section.
- **Des phrases pour Context, Decision et Consequences** : une liste à puces perd le raisonnement. Les listes restent pour Decision factors et Solutions considered.

### Par section

- **Titre** : un groupe nominal court qui nomme la décision (« Annotations jMolecules pour marquer l'hexagone »), pas le problème.
- **Status** : voir « Cycle de vie ».
- **Decision makers** : les noms et rôles viennent de l'utilisateur. **Ne jamais les inventer** ; s'ils manquent, les demander.
- **Context** : les forces en présence (techniques, organisationnelles, propres au projet) et les **tensions** entre elles, dites explicitement ; les contraintes ; les parcours utilisateur critiques touchés. Ton neutre et factuel. Pas de solution dans cette section.
- **Decision factors** : les exigences fonctionnelles et non fonctionnelles qui pèsent sur le choix, **avec leur seuil** quand il existe, puis les critères de projet (délai, coût, complexité, compétences). Un mot vague (« scalable », « performant », « évolutif ») devient une question à l'utilisateur pour obtenir un seuil.
- **Solutions considered** : **au moins deux options**, souvent dont « ne rien changer ». Pour chacune, avantages et inconvénients en phrases courtes. L'option retenue porte *(chosen)*. Les options écartées et leur raison sont ce qui évite de rouvrir le débat plus tard.
- **Decision** : à la voix active, en phrases complètes (« Nous marquons les ports et les adapters avec… »). L'option retenue, **pourquoi** elle l'emporte au regard des critères, et les choix clés qui en découlent.
- **Consequences** : toutes, **positives, négatives et neutres**, avec les compromis acceptés (*Hard Parts*, ch. 1) : ce qui est supprimé, simplifié ou rendu possible, mais aussi ce qui devient plus difficile ou plus coûteux. Ce qu'il faut faire ensuite. Les conséquences d'un ADR deviennent souvent le contexte des suivants.

### Faire respecter la décision

Écrire une décision ne suffit pas (*Hard Parts*, ch. 1). Les Consequences disent **comment la décision est vérifiée** : de préférence un test d'architecture qui tourne en intégration continue (une *fitness function*, par exemple un test ArchUnit, nommé) ; sinon la vérification manuelle (revue, étape d'une checklist).

## Cycle de vie

| Statut | Sens | Ce qu'on peut modifier |
|---|---|---|
| `Draft` | Décision en discussion, pas encore acceptée (le *proposed* de Nygard) | Tout le contenu |
| `Accepted` | Accord explicite de l'utilisateur (ou des decision makers) | Seulement la ligne de statut |
| `Rejected` | Proposée puis refusée : le fichier reste, savoir qu'une option a été refusée est utile | Rien |
| `Deprecated` | Ne s'applique plus | Rien |
| `Supersedes <NNN>` | Porté par le nouvel ADR qui remplace l'ADR `NNN` | Comme un ADR `Accepted` |

- **`Draft` par défaut.** Passer à `Accepted` seulement après l'accord explicite de l'utilisateur, jamais par déduction.
- **Un ADR accepté ne se réécrit pas et ne se supprime pas.** Savoir qu'une décision a été prise puis abandonnée reste utile. Deux façons d'en sortir :
  - **Remplacer** : la décision change. Nouvel ADR avec le statut `Supersedes <NNN>`, dont le contexte dit ce qui a changé depuis l'ADR `NNN`. L'ancien passe à `Deprecated, superseded by <MMM>`.
  - **Déprécier sans remplacer** : la décision ne s'applique plus et rien ne la remplace (composant retiré, contrainte disparue). L'ADR passe à `Deprecated (JJ/MM/AAAA): <raison en une phrase>`. Pas de nouvel ADR.
- Dans les deux cas, seule la ligne de statut de l'ancien ADR change.
- **Correction sur place, seulement sur accord.** Quand la décision tient mais qu'un fait, une conséquence ou une vérification d'un ADR accepté s'avère faux, demander à l'utilisateur, à chaque fois, s'il préfère un nouvel ADR qui le remplace ou une correction sur place, avec une recommandation qui tient compte de ce que le texte faux a déjà fait décider (une version diffusée, un autre ADR qui s'appuie dessus). Un accord donné pour un ADR ne vaut pas pour un autre. Une correction ne se fait qu'avec son accord explicite pour cet ADR ; la ligne de statut la date et dit ce qui a changé : `Accepted (corrigé le JJ/MM/AAAA : <ce qui change>)`. Une décision qui change passe toujours par un nouvel ADR.
- **Décisions qui concernent d'autres équipes** : si l'équipe tient aussi un wiki ou un document partagé, proposer d'y reprendre la décision. L'ADR du dépôt reste la référence.

## Déroulé

1. **Conventions** : repérer les ADR existants, le template, la langue et le schéma de nommage (voir « Conventions du projet »).
2. **Cadrer** : la décision mérite-t-elle un ADR ? Est-elle unique, ou faut-il la découper ? Lire les ADR liés : celui qu'elle remplacerait ou contredirait, ceux dont elle découle.
3. **Rassembler l'information** :
   - ce qu'il faut : date, decision makers, contexte et forces, critères avec leurs seuils, au moins deux options, option retenue et justification, conséquences, mode de vérification ; et si besoin le dossier et la langue ;
   - ne pas demander ce que le code, la conversation ou les ADR existants disent déjà ;
   - **trois à cinq questions par vague**, les plus structurantes d'abord, **ouvertes et neutres** (« Qu'est-ce qui doit pouvoir changer sans toucher au reste ? » plutôt que « Veux-tu une architecture hexagonale ? ») ;
   - **proposer plutôt que demander** quand une hypothèse est raisonnable : « Je pars du principe que… Ça te va ? »
4. **Écrire** le fichier en `Draft`, sauf si l'utilisateur a déjà explicitement accepté la décision.
5. **Remplacement ou dépréciation** : mettre à jour la ligne de statut de l'ancien ADR.
6. **Montrer** le résultat et proposer des ajustements. Signaler les hypothèses restées sans réponse et les champs à compléter (decision makers, seuils). Demander l'accord explicite avant de passer à `Accepted`.

Si le mode d'exécution ne permet pas de poser des questions à l'utilisateur, présenter les questions et hypothèses non résolues dans la réponse et laisser l'ADR en `Draft`.
