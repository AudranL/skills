# Java / Spring Boot

- JUnit 5 + AssertJ (assertions fluides) + Mockito pour les doubles.
- Nom de test descriptif en `snake_case` ou phrase via `@DisplayName`, selon la convention du projet. Exemple : `should_reject_order_when_stock_is_insufficient`.
- `@Nested` pour regrouper les cas par situation. Pour trianguler une règle : autant de tests que de cas, ou un `@ParameterizedTest`, selon ce qui se lit le mieux.
- Tests unitaires **sans contexte Spring** (instanciation directe, injection par constructeur). `@SpringBootTest`, `@WebMvcTest`, `@DataJpaTest` uniquement pour les tests d'intégration, explicitement séparés.
- `Clock` injectée pour le temps ; jamais `LocalDate.now()` en dur dans le code métier.
- `Optional` pour une absence attendue, jamais `null` renvoyé ni passé.
- Texte exact quand un autre peut le prolonger (« à 16h » dans « à 16h30 ») : `assertThat(texte).isEqualTo("à 16h")` ou une expression ancrée (`matches(".* à 16h")`), pas `contains`.
- Version du JDK : celle du projet (`pom.xml`, `.sdkmanrc`, `.java-version`), choisie explicitement (macOS : `JAVA_HOME=$(/usr/libexec/java_home -v 21)`) ; un JDK trop récent peut casser Lombok ou le compilateur.

```java
@Test
void should_apply_loyalty_discount_when_customer_has_more_than_ten_orders() {
    // Given
    Customer loyalCustomer = aCustomer().withOrderCount(11).build();
    Cart cart = aCart().withTotal(euros(100)).build();

    // When
    Money total = pricing.totalFor(cart, loyalCustomer);

    // Then
    assertThat(total).isEqualTo(euros(90));
}
```

Code legacy très combinatoire à sécuriser avant un refactoring : la skill `golden-master` (ApprovalTests, JaCoCo, PIT).
