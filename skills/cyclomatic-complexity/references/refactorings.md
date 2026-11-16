# Reducing complexity: one refactoring per kind of decision point

Examples in Java; the same idea holds in TypeScript. At each step: tests green, then `mccabe.py` on the file.

## Guard clauses (nested `if`s)

Before (complexity 4, three levels of indentation):

```java
double discount(Customer customer, Order order) {
    double rate = 0;
    if (customer != null) {
        if (customer.isActive()) {
            if (order.total() > 100) {
                rate = 0.1;
            }
        }
    }
    return rate;
}
```

After (still complexity 4, but it reads straight down):

```java
double discount(Customer customer, Order order) {
    if (customer == null || !customer.isActive()) return 0;
    if (order.total() <= 100) return 0;
    return 0.1;
}
```

A guard clause mostly reduces **nesting**; the number drops when guards merge or disappear (here, a `null` customer can be ruled out upstream).

## Extract the loop body

When the loop holds an `if`, a `catch` or another loop, its body becomes a method whose name says what is done **for one element**:

```java
for (Line line : lines) {
    total += discountedPrice(line, customer);
}
```

## Name a compound condition

Each `&&` / `||` counts. If the condition states a business rule, it deserves a business name:

```java
// before
if (customer.isActive() && order.total() > 100 || customer.isVip()) { ... }

// after
if (qualifiesForDiscount(customer, order)) { ... }
```

The two operators still count, now in `qualifiesForDiscount` (complexity 3): the rule is isolated and testable on its own, and the caller reads well. Stop there if the rule is already clear.

## A `switch` or `if / else if` on a type: polymorphism or a table

A `switch` on a type or a code that comes back in several places is a business rule scattered across the code.

```java
// before: every new mode touches this method
switch (order.mode()) {
    case STANDARD -> fee = 5;
    case EXPRESS  -> fee = 12;
    case PICKUP   -> fee = 0;
}

// after: one strategy per mode (or a method on the enum)
double fee = order.mode().fee();
```

If the `switch` is a plain value-to-value mapping, a `Map` or an enum method is enough. A **flat** `switch` of 12 cases, with no logic in its branches, can stay as it is: the number is high, the reading is easy.

## Exceptions and validations

Several `catch` blocks, or a run of `if (x is invalid) return error`: extract the validation into a method that throws a domain exception, and leave the caller on the main path.

## Cascading defaults

`a != null ? a : (b != null ? b : c)`, or a chain of `??`: carry the defaults in a value object or an `Optional`, built once at the boundary.

## After the refactoring

1. Rerun `mccabe.py` on the same file; note the before and after.
2. Reread the **class**: if it gained many private methods, ask whether it has two responsibilities.
3. Commit the refactoring on its own, with no change in behavior.
