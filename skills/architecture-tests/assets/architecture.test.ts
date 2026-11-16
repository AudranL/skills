/**
 * Architecture tests: a model to adapt (skill architecture-tests, references/typescript.md).
 *
 * Reads the imports of every file under SRC with the TypeScript compiler, then checks rules
 * written as functions that return the list of violations. Each failure message cites the
 * rule's ADR and lists the files at fault.
 *
 * To adapt: the zones of the architecture, the files allowed outside a zone, the tsconfig
 * aliases, the rules and their ADRs, the language of the names (that of the project's code).
 * Vitest takes a message as the second argument of expect; Jest does not: put it in the title.
 */
import { readFileSync, readdirSync } from 'node:fs'
import { dirname, isAbsolute, join, relative, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import ts from 'typescript'
import { describe, expect, it } from 'vitest'

const SRC = dirname(fileURLToPath(import.meta.url))

/** The zones of the architecture, declared here and nowhere else. */
const DOMAIN = join(SRC, 'domain')
const APPLICATION = join(SRC, 'application')
const ADAPTERS = join(SRC, 'adapters')
/** The contract shared between modules or processes: types only. */
const CONTRACT = join(SRC, 'contract')
const ZONES = [DOMAIN, APPLICATION, ADAPTERS, CONTRACT]

/** The only files allowed outside a zone: the entry point that wires the zones, and this test. */
const OUTSIDE_ZONES = [join(SRC, 'main.ts'), fileURLToPath(import.meta.url)]

/** The aliases of compilerOptions.paths (tsconfig.json), to keep in sync. */
const ALIASES: [string, string][] = [
  ['@domain/', DOMAIN],
  ['@application/', APPLICATION],
  ['@contract/', CONTRACT]
]

/** The only external module the domain's tests may import. */
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
  if (!clause) return false // import 'module': loaded for its side effects
  // TypeScript 5.9 and later. Before: clause.isTypeOnly.
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

/** Every import: static, re-exports, dynamic import(), require, import('…').Type. */
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

/** The file an internal import targets, or null for an external module (npm or Node). */
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

/** The files of a zone. An empty zone fails the rule: it would no longer check anything. */
function sourcesOf(folder: string): SourceFile[] {
  const files = SOURCES.filter((file) => isInside(file.path, folder))
  expect(files.length, `Rule with nothing to check: ${readable(folder)}/ is empty or was renamed.`).toBeGreaterThan(0)
  return files
}

function violations(
  files: SourceFile[],
  isForbidden: (imported: Import, file: SourceFile) => boolean
): string[] {
  return files.flatMap((file) =>
    file.imports
      .filter((imported) => isForbidden(imported, file))
      .map((imported) => `${readable(file.path)} imports "${imported.specifier}"`)
  )
}

/** The module of a domain file: its top-level folder under DOMAIN. */
function domainModuleOf(path: string): string {
  return relative(DOMAIN, path).split(sep)[0]
}

/** The cycles between modules, written "a → b → a". The walk finds at least one if there is any. */
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

describe('Architecture rules', () => {
  it('every source file belongs to a declared zone (ADR 001)', () => {
    const unchecked = SOURCES.map((file) => file.path)
      .filter((path) => !OUTSIDE_ZONES.includes(path) && !ZONES.some((zone) => isInside(path, zone)))
      .map(readable)

    expect(
      unchecked,
      'ADR 001: a file outside the declared zones escapes every rule; move it into a zone, or declare a new zone.'
    ).toEqual([])
  })

  it('the domain imports only the domain, and its tests the test framework too (ADR 001)', () => {
    const forbidden = violations(sourcesOf(DOMAIN), (imported, file) => {
      const target = targetOf(imported.specifier, file.path)
      if (target !== null) return !isInside(target, DOMAIN)
      return !(isTest(file.path) && imported.specifier === TEST_FRAMEWORK)
    })

    expect(
      forbidden,
      'ADR 001: the domain depends on no framework, no library and no file outside the domain.'
    ).toEqual([])
  })

  it('the domain and the application import no adapter (ADR 001)', () => {
    const forbidden = violations(
      [...sourcesOf(DOMAIN), ...sourcesOf(APPLICATION)],
      (imported, file) => {
        const target = targetOf(imported.specifier, file.path)
        return target !== null && isInside(target, ADAPTERS)
      }
    )

    expect(
      forbidden,
      'ADR 001: dependencies go from the adapters to the application and the domain, never the other way round.'
    ).toEqual([])
  })

  it('the contract holds type declarations only (ADR 002)', () => {
    const code = sourcesOf(CONTRACT).flatMap((file) =>
      file.tree.statements
        .filter(
          (statement) =>
            !ts.isInterfaceDeclaration(statement) &&
            !ts.isTypeAliasDeclaration(statement) &&
            !ts.isImportDeclaration(statement) &&
            !ts.isExportDeclaration(statement)
        )
        .map((statement) => `${readable(file.path)}: "${statement.getText().split('\n')[0]}"`)
    )

    expect(
      code,
      'ADR 002: the contract holds types only, erased at compilation; the code goes in the module that runs it.'
    ).toEqual([])
  })

  it('the modules of the domain form no cycle (ADR 003)', () => {
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
      'ADR 003: a module may import another in one direction only; two modules in a cycle can no longer change or be tested one without the other.'
    ).toEqual([])
  })
})
