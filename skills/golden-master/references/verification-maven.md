# Vérification Maven : JaCoCo + PIT

## Profil à ajouter au `pom.xml`

Un profil désactivé par défaut : il ne change rien au build normal et se retire d'un bloc à la fin. Si le projet configure déjà JaCoCo ou PIT, réutiliser leur configuration au lieu d'ajouter celle-ci.

```xml
<profiles>
    <profile>
        <id>golden-master</id>
        <build>
            <plugins>
                <plugin>
                    <groupId>org.jacoco</groupId>
                    <artifactId>jacoco-maven-plugin</artifactId>
                    <version><!-- dernière version sur Maven Central --></version>
                    <executions>
                        <execution>
                            <id>gm-prepare-agent</id>
                            <goals><goal>prepare-agent</goal></goals>
                        </execution>
                        <execution>
                            <id>gm-report</id>
                            <phase>test</phase>
                            <goals><goal>report</goal></goals>
                        </execution>
                    </executions>
                </plugin>
                <plugin>
                    <groupId>org.pitest</groupId>
                    <artifactId>pitest-maven</artifactId>
                    <version><!-- 1.19.4 ou plus récent --></version>
                    <dependencies>
                        <dependency>
                            <groupId>org.pitest</groupId>
                            <artifactId>pitest-junit5-plugin</artifactId>
                            <version><!-- 1.2.3 ou plus récent --></version>
                        </dependency>
                    </dependencies>
                    <configuration>
                        <outputFormats>
                            <param>XML</param>
                            <param>HTML</param>
                        </outputFormats>
                        <timestampedReports>false</timestampedReports>
                        <mutators>
                            <mutator>STRONGER</mutator>
                        </mutators>
                    </configuration>
                </plugin>
            </plugins>
        </build>
    </profile>
</profiles>
```

Remarques :

- `pitest-junit5-plugin` doit être une dépendance **du plugin** PIT, pas une dépendance de test du projet : sinon PIT ne trouve aucun test JUnit 5.
- Si un BOM ou le parent Spring Boot gère déjà la version de JaCoCo, ne pas la répéter.
- Une version de JaCoCo trop ancienne pour le JDK échoue avec `Unsupported class file major version` : prendre la dernière.
- Le groupe `STRONGER` ajoute des mutants sur les conditions et les valeurs de retour par rapport à `DEFAULTS`. Pour une cible très combinatoire et lente, revenir à `DEFAULTS`.

## Piège : `argLine` de Surefire

`prepare-agent` passe l'agent JaCoCo à Surefire via la propriété `argLine`. Si le projet définit son propre `<argLine>` dans Surefire, l'agent est écrasé et `jacoco.xml` n'est pas généré (ou vide). Corriger en préfixant :

```xml
<argLine>@{argLine} -Xmx1g …options existantes…</argLine>
```

et déclarer `<argLine></argLine>` vide dans les `<properties>` pour que le build sans profil fonctionne toujours.

## Commandes

Couverture :

```bash
mvn -q -P golden-master test -Dtest='<Cible>GoldenMasterTest' -Dsurefire.failIfNoSpecifiedTests=false
# rapport : target/site/jacoco/jacoco.xml (et index.html pour l'utilisateur)
python3 <dossier de cette skill>/scripts/coverage_report.py target/site/jacoco/jacoco.xml com.exemple.Cible --src src/main/java
```

Mutation :

```bash
mvn -q -P golden-master -Djacoco.skip=true test-compile org.pitest:pitest-maven:mutationCoverage \
    -DtargetClasses='com.exemple.Cible*' \
    -DtargetTests='com.exemple.CibleGoldenMasterTest'
# rapport : target/pit-reports/mutations.xml (et index.html pour l'utilisateur)
python3 <dossier de cette skill>/scripts/mutation_report.py target/pit-reports/mutations.xml com.exemple.Cible --src src/main/java
```

- `targetClasses` avec `*` inclut les classes imbriquées et les lambdas (`Cible$1`, `Cible$Builder`) ; le script de rapport filtre ensuite sur la cible exacte et ses classes internes.
- `-Djacoco.skip=true` évite que l'agent JaCoCo soit chargé dans les processus de PIT, qui fait sa propre instrumentation.
- Les scripts sortent avec le code 0 si l'objectif est atteint (100 % des branches, aucun mutant survivant), 1 sinon : pratique pour boucler.

## Projet multi-module

Lancer depuis la racine en ciblant le module :

```bash
mvn -q install -DskipTests                     # une fois, pour que les modules dépendants soient disponibles
mvn -q -P golden-master -pl <module> test -Dtest=…
mvn -q -P golden-master -Djacoco.skip=true -pl <module> test-compile org.pitest:pitest-maven:mutationCoverage -DtargetClasses=… -DtargetTests=…
```

Les rapports sont alors dans `<module>/target/…`, et `--src` pointe vers `<module>/src/main/java`.

## Nettoyage final (après le refactoring et les tests unitaires)

- Supprimer `<Cible>GoldenMasterTest.java` et ses `*.approved.txt`.
- Retirer le profil `golden-master` du `pom.xml` (et la dépendance ApprovalTests si plus aucun test ne l'utilise).
