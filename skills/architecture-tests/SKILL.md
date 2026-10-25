---
name: architecture-tests
description: "Écrit, relit et maintient les tests d'architecture (fonctions de conformité, fitness functions) qui vérifient les règles de structure d'un projet : sens des dépendances entre couches, frontières entre modules ou contextes bornés, absence de cycles, dossiers réservés aux types, imports interdits, conventions de nommage. Choisit l'outil selon la pile : ArchUnit (et jMolecules) en Java ou Kotlin ; un test écrit à la main avec le compilateur TypeScript, dependency-cruiser ou eslint-plugin-boundaries en TypeScript ou JavaScript. À utiliser pour mettre en place un test d'architecture, traduire la règle d'un ADR en test, geler les violations existantes, ou relire un test d'architecture qui passe trop facilement."
---

# Tests d'architecture

Un test d'architecture est une fonction de conformité (*fitness function*) : n'importe quel mécanisme automatique qui vérifie une caractéristique de l'architecture, une seule (le sens d'une dépendance) ou plusieurs à la fois (Ford, Richards, Sadalage, Dehghani, *Software Architecture: The Hard Parts*, ch. 1 « Using Fitness Functions »). Il rend une règle écrite (un ADR) vérifiable à chaque build : une règle non testée s'érode.

## Choisir l'outil

Repérer la pile (fichiers de build, `package.json`, `tsconfig.json`) et les tests d'architecture déjà en place : s'il y en a, suivre leur outil et leur forme.

| Pile | Outil | Référence |
|---|---|---|
| Java, Kotlin (JVM) | ArchUnit, avec ou sans les annotations jMolecules | `references/archunit.md` |
| TypeScript, JavaScript | Un test écrit à la main avec le compilateur TypeScript, ou dependency-cruiser, ou eslint-plugin-boundaries | `references/typescript.md` |
| Autre langage | Un test qui lit les imports avec l'analyseur du langage, dans le framework de test du projet | Les principes ci-dessous |

Un outil de plus est une nouvelle dépendance de build : il demande l'accord de l'utilisateur et un ADR. Un test écrit à la main n'ajoute rien au build, mais il est à maintenir.

## Principes, quel que soit l'outil

- **Une règle, un test, un ADR.** Le nom du test ou son message d'échec cite la règle (`A-002`, `ADR 003`) et la dit en langage clair : c'est ce que lira le développeur qui la casse.
- **Le message d'échec liste les coupables** : le fichier et l'import fautif (« `domain/order.ts` importe « express » »). Comparer la liste des violations à une liste vide plutôt qu'un booléen.
- **Repérer l'architecture par une déclaration**, pas en la devinant d'après les noms : annotation sur le module, fichier de déclaration, ou liste des dossiers en tête du test, à un seul endroit. Un nouveau module est alors couvert sans toucher aux règles. Le mode de marquage est une décision d'architecture (ADR).
- **Lire tous les imports** : statiques, dynamiques (`import()`, `require`), réexportations, imports de types seuls, alias de chemins. Selon la règle, un import de types peut être permis là où un import de code ne l'est pas.
- **Voir chaque règle échouer une fois.** Introduire une violation (un import interdit), lancer le test, le voir rouge pour la bonne raison, puis annuler. Une règle qui n'a jamais été rouge ne prouve rien.
- **Une règle sans objet échoue.** Si le dossier ou le marqueur visé ne désigne plus aucun fichier (renommé, vidé), le test échoue au lieu de passer en silence.
- **Geler plutôt que tout corriger d'abord.** Dans un code qui viole déjà une règle, enregistrer les violations actuelles dans un fichier versionné : le test n'échoue que sur une violation nouvelle, et une violation corrigée sort du fichier pour ne plus revenir. Régénérer ce fichier pour faire passer un test revient à affaiblir un test : jamais sans l'accord de l'utilisateur. Chaque règle gelée a son entrée de dette, avec le nombre de violations au départ.
- **Les tests d'architecture tournent avec les autres**, à chaque build, pas dans une commande à part qu'on oublie.
- **Ce qu'un test d'architecture ne vérifie pas** : le sens métier des noms, la justesse d'un modèle, le bon nombre de ports. Ça relève de la revue.

## Règles habituelles

À adapter au style retenu par le projet (hexagonale, onion, clean architecture, couches, contextes bornés) :

- **Le domaine** ne dépend que de lui-même, de la bibliothèque standard du langage, des noyaux partagés et d'une liste courte d'utilitaires. Cette liste est une décision d'architecture : chaque ajout se discute et se trace.
- **Couches** : par contexte ou par module, domaine, application (cas d'utilisation), adapters primaires, adapters secondaires ; aucune couche n'appelle un adapter ; le primaire ne dépend pas du secondaire ; le secondaire ne dépend pas de l'application.
- **Ports et adapters** : les ports sont des interfaces du domaine ou de l'application ; un adapter secondaire implémente un port.
- **Contextes bornés** : pas de dépendance entre les domaines de deux contextes ; ils se parlent par leurs adapters ou par un contrat déclaré.
- **Pas de cycle** entre modules.
- **Un dossier de contrat** (types partagés entre processus ou entre modules) ne contient que des déclarations de types, sans code exécuté.
- **Imports interdits** qui traduisent une qualité : aucun module réseau dans une application qui promet de ne rien envoyer, aucun accès direct à la base hors des adapters.
- **Conventions de noms de fichiers** décidées dans un ADR (casse, caractères permis).
