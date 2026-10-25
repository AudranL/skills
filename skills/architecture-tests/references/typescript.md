# TypeScript, JavaScript

Trois façons de faire, à choisir avec l'utilisateur (l'outil choisi se consigne dans un ADR) :

| | Test écrit à la main | dependency-cruiser | eslint-plugin-boundaries |
|---|---|---|---|
| Dépendance de build | Aucune (le compilateur `typescript` est déjà là) | Une | Une, dans le linter |
| Où il tourne | Avec les autres tests | Une commande à brancher dans les tests ou la CI | Dans l'éditeur et au lint |
| Règles | Des fonctions, aussi fines qu'il faut (imports de types, contenu d'un dossier, noms de fichiers) | Des expressions régulières sur les chemins, cycles, modules orphelins | Des types d'éléments par dossier et qui peut importer qui |
| Gel des violations | À écrire (voir plus bas) | `depcruise-baseline`, puis `--ignore-known` | Non |
| À retenir quand | Peu de règles, ou des règles que les outils n'expriment pas | Les règles se multiplient, ou un graphe des dépendances est utile | L'équipe veut le retour dans l'éditeur, en plus d'un test |

Un lint se contourne plus facilement qu'un test (avertissement ignoré, règle désactivée sur une ligne) : s'il porte des règles d'architecture, le build doit échouer sur une erreur.

## Test écrit à la main

Modèle à adapter : `assets/architecture.test.ts` (Vitest). Il :

- parcourt les fichiers `.ts` et `.tsx` de la racine des sources et lit leurs imports avec `ts.createSourceFile`, sans compiler le projet : rapide, et indépendant de la configuration du build ;
- voit tous les imports : `import` (en distinguant `import type`), `export … from`, `import()` dynamique, `require`, `import('…').Type` ;
- résout les chemins relatifs et les alias de `tsconfig.json` (`compilerOptions.paths`), déclarés une fois en tête du fichier : un module externe (npm, Node) n'a pas de cible ;
- écrit chaque règle comme une fonction qui rend la liste des violations (« `domain/order.ts` importe « express » »), comparée à `[]` avec un message qui cite l'ADR ;
- fait échouer une règle dont la zone ne contient plus aucun fichier (« Règle sans objet ») ;
- détecte les cycles entre modules (dossiers de premier niveau d'une zone) par un parcours en profondeur.

À adapter : les zones, les alias, les règles et leurs ADR, la langue des noms. Avec Jest, `expect` n'accepte pas de message en second argument : le mettre dans le titre du test.

Autres règles qui s'écrivent de la même façon :

- **Imports permis seulement en types** : une zone (l'interface, un autre processus) peut importer les types du domaine, mais pas son code. La règle refuse les imports internes vers le domaine dont `typesOnly` est faux.
- **Personne n'importe une zone** (un point d'entrée, un fichier de préchargement) : la règle refuse tout import dont la cible est dans cette zone.
- **Modules interdits** qui traduisent une qualité, par exemple aucune requête réseau : refuser `http`, `https`, `http2`, `net`, `tls`, `dgram`, avec ou sans le préfixe `node:`.
- **Noms de fichiers** : parcourir les chemins et refuser ceux qui ne suivent pas la convention de l'ADR (par exemple, des caractères hors ASCII qui s'écrivent différemment selon le système).

Limites : les alias sont à garder synchronisés avec `tsconfig.json` ; une dépendance déclarée dans `package.json` sans être importée n'est pas vue ; un fichier qui réexporte tout un dossier (`index.ts`) se vérifie comme les autres, par le dossier qu'il vise.

**Geler les violations existantes** : enregistrer les violations actuelles dans un fichier versionné à côté du test (par exemple `architecture.known-violations.json` : pour chaque règle, la liste de ses messages de violation). Le test échoue sur une violation absente de la liste, et aussi sur une entrée de la liste qui ne se produit plus, pour qu'on l'en retire : le nombre de violations ne peut que baisser. Régénérer ce fichier pour faire passer le test, jamais sans l'accord de l'utilisateur.

## dependency-cruiser

- Configuration `.dependency-cruiser.cjs` (générée par `npx depcruise --init`) : des règles `forbidden` avec `from` et `to` (`path`, `pathNot`, `dependencyTypes`), `circular: true` pour les cycles. `options.tsConfig` pour lire les alias, `options.tsPreCompilationDeps: true` pour voir aussi les imports de types.
- Lancer `npx depcruise src --config .dependency-cruiser.cjs` dans un script du `package.json` appelé par la commande de test ou par la CI, pour que le build échoue sur une erreur.
- Chaque règle a un `name` et un `comment` qui cite l'ADR : c'est le message que lira le développeur.
- Gel : `npx depcruise-baseline src` écrit `.dependency-cruiser-known-violations.json` ; ensuite, `depcruise --ignore-known` n'échoue que sur une violation nouvelle.
- Le graphe des dépendances (`--output-type dot` ou `mermaid`) aide à un diagnostic ; il ne remplace pas les règles.

## eslint-plugin-boundaries

- Déclarer les éléments (`settings['boundaries/elements']` : un type par dossier, par exemple `domain`, `application`, `adapters`) et les dépendances permises (`boundaries/element-types` : `default: 'disallow'`, puis une liste de `from` / `allow`).
- Les cycles ne sont pas couverts : `import/no-cycle` (eslint-plugin-import) ou un autre outil.
- Mettre ces règles en `error`, et faire échouer le build sur une erreur de lint.
