# Maven verification: JaCoCo and PIT

## Profile to add to the `pom.xml`

A profile disabled by default: it changes nothing in the normal build and comes out in one block at the end. If the project already configures JaCoCo or PIT, reuse that configuration instead of adding this one.

```xml
<profiles>
    <profile>
        <id>golden-master</id>
        <build>
            <plugins>
                <plugin>
                    <groupId>org.jacoco</groupId>
                    <artifactId>jacoco-maven-plugin</artifactId>
                    <version><!-- latest version on Maven Central --></version>
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
                    <version><!-- 1.19.4 or newer --></version>
                    <dependencies>
                        <dependency>
                            <groupId>org.pitest</groupId>
                            <artifactId>pitest-junit5-plugin</artifactId>
                            <version><!-- 1.2.3 or newer --></version>
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

Notes:

- `pitest-junit5-plugin` must be a dependency **of the PIT plugin**, not a test dependency of the project: otherwise PIT finds no JUnit 5 test.
- If a BOM or the Spring Boot parent already manages the JaCoCo version, do not repeat it.
- A JaCoCo version too old for the JDK fails with `Unsupported class file major version`: take the latest.
- The `STRONGER` group adds mutants on conditions and return values compared with `DEFAULTS`. For a very combinatorial and slow target, go back to `DEFAULTS`.

## Pitfall: Surefire's `argLine`

`prepare-agent` hands the JaCoCo agent to Surefire through the `argLine` property. If the project sets its own `<argLine>` in Surefire, the agent is overwritten and `jacoco.xml` is not generated (or is empty). Fix it with a prefix:

```xml
<argLine>@{argLine} -Xmx1g …existing options…</argLine>
```

and declare an empty `<argLine></argLine>` in `<properties>` so that the build without the profile still works.

## Commands

Coverage:

```bash
mvn -q -P golden-master test -Dtest='<Target>GoldenMasterTest' -Dsurefire.failIfNoSpecifiedTests=false
# report: target/site/jacoco/jacoco.xml (and index.html for the user)
python3 <this skill's folder>/scripts/coverage_report.py target/site/jacoco/jacoco.xml com.example.Target --src src/main/java
```

Mutation:

```bash
mvn -q -P golden-master -Djacoco.skip=true test-compile org.pitest:pitest-maven:mutationCoverage \
    -DtargetClasses='com.example.Target*' \
    -DtargetTests='com.example.TargetGoldenMasterTest'
# report: target/pit-reports/mutations.xml (and index.html for the user)
python3 <this skill's folder>/scripts/mutation_report.py target/pit-reports/mutations.xml com.example.Target --src src/main/java
```

- `targetClasses` with `*` includes nested classes and lambdas (`Target$1`, `Target$Builder`); the report script then keeps only the exact target and its inner classes.
- `-Djacoco.skip=true` keeps the JaCoCo agent out of PIT's processes, since PIT does its own instrumentation.
- The scripts exit with code 0 when the goal is met (100% of branches, no surviving mutant), 1 otherwise: handy for looping.

## Multi-module project

Run from the root, targeting the module:

```bash
mvn -q install -DskipTests                     # once, so that the modules it depends on are available
mvn -q -P golden-master -pl <module> test -Dtest=…
mvn -q -P golden-master -Djacoco.skip=true -pl <module> test-compile org.pitest:pitest-maven:mutationCoverage -DtargetClasses=… -DtargetTests=…
```

The reports are then in `<module>/target/…`, and `--src` points to `<module>/src/main/java`.

## Final cleanup (after the refactoring and the unit tests)

- Delete `<Target>GoldenMasterTest.java` and its `*.approved.txt` files.
- Remove the `golden-master` profile from the `pom.xml` (and the ApprovalTests dependency if no test uses it any more).
