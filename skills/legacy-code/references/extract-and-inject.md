# Extracting and injecting dependencies

Detail for step 3 of `SKILL.md`. Each technique is an edit made before any test exists: through the IDE's automated refactorings when it offers them, otherwise with parameter lists copied as they are and one intent per edit. Choose the edit you are surest of, not the one that gives the nicest design: the design improves later, under tests. None of them adds code that only the tests use: production goes through the same seam and passes the real collaborator.

## A parameter nobody can build

- **A dummy in its place.** When the tested path never touches the parameter, pass a dummy: an implementation that throws as soon as it is called, saying which role it stands for. `null` works too in languages that fail loudly when it is used (Java, C#), and never in production code. Start with the bare constructor call and add real parameters only as the tests require them. In strict TypeScript, a dummy typed as the parameter rather than `null as any`.
- **An interface with only what is used.** Extract an interface holding just the methods the code under test calls; the class implements it, the code depends on it, the test passes a fake. Most IDEs do it in one step. In TypeScript, structural typing often makes it free: type the parameter as `Pick<PaymentGateway, 'refund'>`, or as a small interface, and the real class fits without any change.
- **A narrow interface in front of a type you do not own.** When the parameter's type cannot take an interface of yours (a framework type with dozens of methods, a final class), declare an interface that says what the code needs, and an adapter that reads it from the real type: for a method that only reads the caller's language and customer id from the whole HTTP request, an interface `Caller` with `language()` and `customerId()`. Production passes the adapter, the test a fake. Unlike the other techniques, this one changes the type a method receives: take extra care, and keep the adapter to plain delegation.

## A collaborator created in the constructor

**The constructor receives it**, usually the first thing to try. With the IDE's introduce parameter on the expression that creates the collaborator, the parameter appears and every caller now creates the collaborator and passes it:

```java
// before
public LateFeeCalculator(int graceDays) {
    this.calendar = new HolidayCalendar();
    this.graceDays = graceDays;
}

// after
public LateFeeCalculator(HolidayCalendar calendar, int graceDays) {
    this.calendar = calendar;
    this.graceDays = graceDays;
}

// a production caller, updated by the IDE
new LateFeeCalculator(new HolidayCalendar(), 3)
```

By hand: add the parameter, assign it instead of creating the collaborator, and let the compiler list the callers; each one passes exactly what the constructor used to create. In a framework that injects dependencies (Spring, Angular), a `new` or a field injection in a managed class becomes a constructor parameter that the framework fills, and the callers do not change. No default value that only the tests replace (`clock: Clock = systemClock`): production passes its collaborator like any other argument.

What it costs: every caller now builds the collaborator, and comes to depend on its type. When the callers are many, give the creation one place: the code that already builds the objects of the application, a factory, or the injection framework. When the constructor builds a chain of objects from one another, receive the outermost one already built, or a factory that builds the chain.

## A collaborator created inside a method

- **Received by the constructor**, when the same collaborator can serve every call: it becomes a field, as above.
- **Received as a parameter of the method**, when it belongs to that call: `export()` becomes `export(uploader)`, and the callers pass the real `FtpUploader`.
- **A factory received by the constructor**, when each call needs a new one (a connection, a file writer): an interface with one method that creates it, implemented in production by the real creation, in the test by one that returns a double.

## A singleton, a global, a static call

- **An object of your own in its place, received by the constructor**: a `Clock` in place of `Instant.now()`, a random source in place of `Math.random`, a `Settings` interface in place of `Settings.getInstance().get(…)`. Production passes the real one (`Clock.systemUTC()`, the singleton's instance), the test a double. Time and randomness are almost always handled this way.
- **An interface in front of a static method**: an interface of your own with the operation the code needs, and an adapter that delegates to the static method, received by the code under test. Other callers keep calling the static method.
- **The globals gathered in an object**: when the code reads several globals, a class of your own exposes them through instance methods, and the code under test receives an instance.
- **The logic taken out of the object**: a method that uses no field of its object can become a function of its own (a static method in Java), which production calls in its place and the test calls without building the object. Useful when the class cannot be built but the logic to change does not need it.

No setter or reset method on the singleton: only the tests would call it. When the singleton is read in too many places to inject it now, test higher up, or substitute it behind the code's back (last section) until its users receive it.

## An effect the test cannot see

**What decides split from what acts.** Each piece that acts on the outside (displays, sends, writes) moves behind a collaborator received by the constructor, named after what it means for the class rather than after the technology (`warehouse.notify(order)`, not `queue.post(message)`); each computation becomes a query of the class. The query is tested directly; for the action, the test passes a spy, or a fake whose state it reads afterwards.

**A log line on the effect**, for a characterization test that is scaffolding: log the effect (what was sent, to whom) where it happens, and read it in the test through an appender that keeps log events in memory. Quicker than a collaborator when the effect is not yet worth one, and the log serves production too. The test depends on the log's wording and level: replace it with a spy on an injected collaborator once the code is refactored.

## A private method

Test it through the public method that calls it: the test then checks it as it is really used, and does not freeze an internal detail. When that is too hard, the method often belongs to another responsibility: move it into a class of its own (the IDE moves it with its fields), which the original class creates or receives and calls. The moved method is the new class's public interface, used by production, and the test reaches it directly. Never widen its visibility for the test.

## A third-party API called everywhere

- **Behind interfaces of your own**: interfaces that mirror the calls the code makes, a thin wrapper that only delegates to the library, a fake in the tests. The code under test stops depending on the library altogether. For a small API, or when getting free of the library is a goal in itself.
- **What the code does with it, extracted**: pull into methods, then into classes, each thing the code does with the API, named in your domain's terms (`InvoiceArchive.store(pdf)` rather than client, bucket, key and credentials). For a large API, with a reliable automated extract method. The extracted code may remain untested; the code that calls it no longer depends on the library.

Both can be combined: a thin wrapper that makes testing possible, and a higher-level interface for the rest of the application. The wrapper follows the rules for third-party code in the `clean-code` skill (its exceptions translated, only types you own are doubled).

## Substitution behind the code's back

Replacing an implementation without touching the code: a class with the same name earlier on the classpath, `jest.mock('./mailer')` or `vi.mock(…)` on a module, `mockStatic` or `mockConstruction` in Mockito. It adds nothing to production code, but nothing in the code under test reveals it, and the test depends on how modules are resolved. Only when the dependency is used so widely that no injection is within reach; mark it clearly in the test, and replace it with an injection once the code is covered.
