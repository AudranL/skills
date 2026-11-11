# Cucumber (Cucumber-JVM, cucumber-js, jest-cucumber)

Runs the Gherkin text of a spec. What depends on no tool (one test per scenario, its level, the automation layer) is in the `acceptance-tests` skill.

- **A build dependency**: do not add it without asking (skill `acceptance-tests`). Without Cucumber, the scenario and its test are linked by the title.
- **The `.feature` files copy the spec word for word**: same title, same steps. A scenario that cannot be automated as written is reported, not rewritten.
- **Language**: a `.feature` file in a language other than English starts with `# language: <code>` (`# language: fr` gives `Fonctionnalité`, `Scénario`, `Plan du Scénario`, `Exemples`, `Contexte`, `Étant donné`, `Quand`, `Alors`, `Et`, `Mais`). Only the step text is matched: the English annotations (`@Given`, `@When`, `@Then`) also find the steps of a French feature.
- **Thin steps**: a step definition translates its sentence and calls the automation layer, in the domain vocabulary (`shop.placeOrder(…)`); no logic, no screen detail, no assertion other than its "Then".
- **Parameters**: Cucumber Expressions (`{int}`, `{string}`, and parameter types of your own for domain values: a `{money}` that returns a `Money`) rather than regular expressions.
- **The state of a scenario** is new for each scenario and shared between steps by injection (`cucumber-picocontainer` or `cucumber-spring` in Java, the `World` in JavaScript), never through a `static` field.
- **Step definitions are grouped by domain concept**, not by `.feature` file; a step never calls another step (go through the automation layer).
- **The business context is read in the "Given" steps**; hooks (`Before`, `After`) only do technical work (an emptied database, a temporary folder).
- **Tags** filter (`@slow`, `@wip`); they never hide a red scenario.
- **Run**: Cucumber-JVM on the JUnit Platform (`cucumber-junit-platform-engine`, a class annotated `@Suite @IncludeEngines("cucumber") @SelectClasspathResource("features")`); one scenario: `-Dcucumber.filter.name="…"`. cucumber-js: `npx cucumber-js --name "…"`.
- **jest-cucumber**: `defineFeature(loadFeature('features/loyalty-discount.feature'), (test) => { test('<scenario title>', ({ given, when, then }) => { … }) })`: the test carries the scenario title.

```gherkin
Feature: Loyalty discount

  Scenario: A customer with more than ten orders pays 10% less
    Given a customer who has placed 11 orders
    When they order for 100 €
    Then they pay 90 €
```

```java
public class LoyaltyDiscountSteps {

    private final Shop shop;   // automation layer, new for each scenario (PicoContainer)

    public LoyaltyDiscountSteps(Shop shop) { this.shop = shop; }

    @ParameterType("(\\d+) €")
    public Money money(String euros) { return euros(Integer.parseInt(euros)); }

    @Given("a customer who has placed {int} orders")
    public void aCustomerWhoHasPlacedOrders(int orders) { shop.aCustomerWithOrders(orders); }

    @When("they order for {money}")
    public void theyOrderFor(Money amount) { shop.order(amount); }

    @Then("they pay {money}")
    public void theyPay(Money amount) { assertThat(shop.amountPaid()).isEqualTo(amount); }
}
```
