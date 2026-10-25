---
name: legacy-code
description: "Modifier du code sans tests selon Michael Feathers (Working Effectively with Legacy Code) : points de changement, points de test, dépendances cassées par une seam (de préférence une seam objet, avec les refactorings automatiques de l'IDE et le diff montré), modifications sans filet à petits risques (signatures préservées, compilateur comme guide, une intention par modification), tests de caractérisation qui figent le comportement actuel bugs compris, puis changement en TDD ; Sprout et Wrap quand le temps manque, et comment choisir entre les deux. À charger avant de modifier, de corriger ou d'étendre du code qui n'a pas de tests, ou quand un test est impossible à écrire sans casser une dépendance."
---

# Code legacy

Le code legacy est du code sans tests. Pour le modifier, suivre l'algorithme de Michael Feathers (*Working Effectively with Legacy Code*) :

1. **Identifier les points de changement.**
2. **Trouver les points de test** : l'endroit le plus haut et le plus rapide d'où l'on peut observer l'effet du changement.
3. **Casser les dépendances** qui empêchent d'instancier la classe ou d'appeler la méthode dans un test : trouver ou créer une **seam** (préférer les seams objet : paramètre, constructeur, méthode surchargeable, extraction d'interface). Ces premières incisions se font sans filet : les faire avec les refactorings automatiques de l'IDE, et montrer le diff à l'utilisateur. À la main, réduire le risque : préserver les signatures (recopier la liste des paramètres telle quelle), laisser le compilateur trouver les usages, une seule intention par modification (Feathers, ch. 23 « Preserve Signatures », « Lean on the Compiler », « Single-Goal Editing »).
4. **Écrire des tests de caractérisation** : ils figent ce que le code fait aujourd'hui, bugs compris. Écrire une assertion qu'on sait fausse, laisser l'échec dire ce que fait le code, puis attendre cette valeur : c'est la seule fois où une valeur attendue se recopie depuis la sortie. S'arrêter quand ces tests détecteraient une erreur dans le changement prévu. Un comportement suspect reste figé, marqué et signalé à l'utilisateur, pas corrigé en douce (Feathers, ch. 13 « Characterization Tests »). Pour une classe Java très combinatoire, proposer la skill `golden-master` si elle est installée.
5. **Faire le changement et refactorer**, en TDD.

## Quand le temps manque

Pour ajouter une fonctionnalité dans une méthode intestable sans la mettre d'abord sous tests :

- **Sprout Method / Sprout Class** (écrire le nouveau code à part, en TDD, et l'appeler depuis l'ancien) quand la méthode existante se lit bien comme un algorithme ;
- **Wrap Method / Wrap Class** (renommer l'ancienne méthode, l'envelopper dans une nouvelle qui fait le nouveau travail puis l'appelle) quand le nouveau comportement doit seulement se produire en même temps que l'ancien (journaliser chaque paiement) et compte autant que lui (Feathers, ch. 6).

Le code nouveau est sous tests ; l'ancien ne l'est toujours pas, et se dit tel quel dans le compte rendu.
