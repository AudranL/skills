/**
 * Tests d'architecture : modèle à adapter (skill architecture-tests, references/typescript.md).
 *
 * Lit les imports de chaque fichier de SRC avec le compilateur TypeScript, puis vérifie des règles
 * écrites comme des fonctions qui rendent la liste des violations. Chaque message d'échec cite
 * l'ADR de la règle et liste les fichiers en cause.
 *
 * À adapter : les zones de l'architecture, les alias de tsconfig, les règles et leurs ADR, la
 * langue des noms (celle du code du projet).
 * Vitest accepte un message en second argument de expect ; Jest non : le mettre dans le titre.
 */
import { readFileSync, readdirSync } from 'node:fs'
import { dirname, isAbsolute, join, relative, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import ts from 'typescript'
import { describe, expect, it } from 'vitest'

const SRC = dirname(fileURLToPath(import.meta.url))

/** Les zones de l'architecture, déclarées ici et nulle part ailleurs. */
const DOMAIN = join(SRC, 'domain')
const APPLICATION = join(SRC, 'application')
const ADAPTERS = join(SRC, 'adapters')
/** Le contrat partagé entre modules ou processus : des types seulement. */
const CONTRACT = join(SRC, 'contract')

/** Les alias de compilerOptions.paths (tsconfig.json), à garder synchronisés. */
const ALIASES: [string, string][] = [
  ['@domain/', DOMAIN],
  ['@application/', APPLICATION],
  ['@contract/', CONTRACT]
]

/** Le seul module externe que les tests du domaine peuvent importer. */
const TEST_FRAMEWORK = 'vitest'

interface Import {
  specifier: string
  typesOnly: boolean
}

interface SourceFile {
  path: string
  tree: ts.SourceFile
  imports: Import[]
}

function pathsUnder(folder: string): string[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry) => {
    const path = join(folder, entry.name)
    return entry.isDirectory() ? [path, ...pathsUnder(path)] : [path]
  })
}

function isInside(path: string, folder: string): boolean {
  const rel = relative(folder, path)
  return rel === '' || (!rel.startsWith('..') && !isAbsolute(rel))
}

function isTest(path: string): boolean {
  return /\.(test|spec)\.tsx?$/.test(path)
}

function readable(path: string): string {
  return relative(SRC, path)
}

function isTypesOnlyImport(declaration: ts.ImportDeclaration): boolean {
  const clause = declaration.importClause
  if (!clause) return false // import 'module' : chargé pour ses effets
  // TypeScript 5.9 et plus. Avant : clause.isTypeOnly.
  if (clause.phaseModifier === ts.SyntaxKind.TypeKeyword) return true
  if (clause.name) return false
  const bindings = clause.namedBindings
  return (
    bindings !== undefined &&
    ts.isNamedImports(bindings) &&
    bindings.elements.length > 0 &&
    bindings.elements.every((element) => element.isTypeOnly)
  )
}

/** Tous les imports : statiques, réexportations, import() dynamiques, require, import('…').Type. */
function importsOf(tree: ts.SourceFile): Import[] {
  const imports: Import[] = []
  const visit = (node: ts.Node): void => {
    if (ts.isImportDeclaration(node) && ts.isStringLiteral(node.moduleSpecifier)) {
      imports.push({ specifier: node.moduleSpecifier.text, typesOnly: isTypesOnlyImport(node) })
    } else if (
      ts.isExportDeclaration(node) &&
      node.moduleSpecifier &&
      ts.isStringLiteral(node.moduleSpecifier)
    ) {
      imports.push({ specifier: node.moduleSpecifier.text, typesOnly: node.isTypeOnly })
    } else if (
      ts.isCallExpression(node) &&
      node.arguments.length === 1 &&
      ts.isStringLiteral(node.arguments[0]) &&
      (node.expression.kind === ts.SyntaxKind.ImportKeyword ||
        (ts.isIdentifier(node.expression) && node.expression.text === 'require'))
    ) {
      imports.push({ specifier: node.arguments[0].text, typesOnly: false })
    } else if (
      ts.isImportTypeNode(node) &&
      ts.isLiteralTypeNode(node.argument) &&
      ts.isStringLiteral(node.argument.literal)
    ) {
      imports.push({ specifier: node.argument.literal.text, typesOnly: true })
    }
    ts.forEachChild(node, visit)
  }
  visit(tree)
  return imports
}

/** Le fichier visé par un import interne, ou null pour un module externe (npm ou Node). */
function targetOf(specifier: string, from: string): string | null {
  if (specifier.startsWith('.')) return resolve(dirname(from), specifier)
  for (const [alias, folder] of ALIASES) {
    if (specifier.startsWith(alias)) return join(folder, specifier.slice(alias.length))
  }
  return null
}

const SOURCES: SourceFile[] = pathsUnder(SRC)
  .filter((path) => /\.tsx?$/.test(path) && !path.endsWith('.d.ts'))
  .map((path) => {
    const tree = ts.createSourceFile(path, readFileSync(path, 'utf-8'), ts.ScriptTarget.Latest, true)
    return { path, tree, imports: importsOf(tree) }
  })

/** Les fichiers d'une zone. Une zone vide fait échouer la règle : elle ne vérifierait plus rien. */
function sourcesOf(folder: string): SourceFile[] {
  const files = SOURCES.filter((file) => isInside(file.path, folder))
  expect(files.length, `Règle sans objet : ${readable(folder)}/ est vide ou a changé de nom.`).toBeGreaterThan(0)
  return files
}

function violations(
  files: SourceFile[],
  isForbidden: (imported: Import, file: SourceFile) => boolean
): string[] {
  return files.flatMap((file) =>
    file.imports
      .filter((imported) => isForbidden(imported, file))
      .map((imported) => `${readable(file.path)} importe « ${imported.specifier} »`)
  )
}

/** Le module d'un fichier du domaine : son dossier de premier niveau sous DOMAIN. */
function domainModuleOf(path: string): string {
  return relative(DOMAIN, path).split(sep)[0]
}

/** Les cycles entre modules, écrits « a → b → a ». Le parcours en trouve au moins un s'il y en a. */
function cyclesOf(dependencies: Map<string, Set<string>>): string[] {
  const cycles: string[] = []
  const explored = new Set<string>()
  const walk = (module: string, path: string[]): void => {
    const start = path.indexOf(module)
    if (start >= 0) {
      cycles.push([...path.slice(start), module].join(' → '))
      return
    }
    if (explored.has(module)) return
    for (const next of dependencies.get(module) ?? []) walk(next, [...path, module])
    explored.add(module)
  }
  for (const module of dependencies.keys()) walk(module, [])
  return cycles
}

describe("Règles d'architecture", () => {
  it("le domaine n'importe que le domaine, et ses tests le framework de test en plus (ADR 001)", () => {
    const forbidden = violations(sourcesOf(DOMAIN), (imported, file) => {
      const target = targetOf(imported.specifier, file.path)
      if (target !== null) return !isInside(target, DOMAIN)
      return !(isTest(file.path) && imported.specifier === TEST_FRAMEWORK)
    })

    expect(
      forbidden,
      "ADR 001 : le domaine ne dépend d'aucun framework, d'aucune bibliothèque ni d'aucun fichier hors du domaine."
    ).toEqual([])
  })

  it("le domaine et l'application n'importent aucun adapter (ADR 001)", () => {
    const forbidden = violations(
      [...sourcesOf(DOMAIN), ...sourcesOf(APPLICATION)],
      (imported, file) => {
        const target = targetOf(imported.specifier, file.path)
        return target !== null && isInside(target, ADAPTERS)
      }
    )

    expect(
      forbidden,
      "ADR 001 : les dépendances vont des adapters vers l'application et le domaine, jamais l'inverse."
    ).toEqual([])
  })

  it('le contrat ne contient que des déclarations de types (ADR 002)', () => {
    const code = sourcesOf(CONTRACT).flatMap((file) =>
      file.tree.statements
        .filter(
          (statement) =>
            !ts.isInterfaceDeclaration(statement) &&
            !ts.isTypeAliasDeclaration(statement) &&
            !ts.isImportDeclaration(statement) &&
            !ts.isExportDeclaration(statement)
        )
        .map((statement) => `${readable(file.path)} : « ${statement.getText().split('\n')[0]} »`)
    )

    expect(
      code,
      "ADR 002 : le contrat ne contient que des types, effacés à la compilation ; le code va dans le module qui l'exécute."
    ).toEqual([])
  })

  it('les modules du domaine ne forment aucun cycle (ADR 003)', () => {
    const dependencies = new Map<string, Set<string>>()
    for (const file of sourcesOf(DOMAIN)) {
      const from = domainModuleOf(file.path)
      for (const imported of file.imports) {
        const target = targetOf(imported.specifier, file.path)
        if (target === null || !isInside(target, DOMAIN)) continue
        const to = domainModuleOf(target)
        if (to !== from) dependencies.set(from, (dependencies.get(from) ?? new Set()).add(to))
      }
    }

    expect(
      cyclesOf(dependencies),
      "ADR 003 : un module peut en importer un autre dans un seul sens ; deux modules en cycle ne peuvent plus changer ni se tester l'un sans l'autre."
    ).toEqual([])
  })
})
