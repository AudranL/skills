// The browser texts, in the first language of navigator.languages that messages.json has, English otherwise.
// Neither remembered nor chosen: the page follows the browser. Copied before the page's own script.
const MESSAGES = JSON.parse(document.getElementById("messages").textContent);
const LOCALE = chooseLocale(navigator.languages || [navigator.language]);
const PLURALS = new Intl.PluralRules(LOCALE.language);

// The language of the messages, and the browser tag that chose it (fr-FR, en-GB…), which formats the dates.
function chooseLocale(tags) {
  for (const tag of tags) {
    const language = String(tag).split("-")[0].toLowerCase();
    if (Object.hasOwn(MESSAGES, language)) return { language, tag };
  }
  return { language: "en", tag: "en" };
}

// The text of a message, with its {parameters}: plain text, for textContent or for esc() in HTML. A message
// written {"one": …, "other": …} is chosen by the plural rules of the language, for the count parameter.
function t(key, params = {}) {
  const messages = MESSAGES[LOCALE.language];
  if (!Object.hasOwn(messages, key)) {
    console.error("i18n: no message " + key + " in " + LOCALE.language);
    return key;
  }
  const message = messages[key];
  const text = typeof message === "string" ? message : message[PLURALS.select(params.count)] ?? message.other;
  return text.replace(/\{(\w+)\}/g, (placeholder, name) => {
    if (Object.hasOwn(params, name)) return String(params[name]);
    console.error("i18n: no parameter " + name + " for " + key);
    return placeholder;
  });
}

// The label of a value of the data (a status, a type), or the value itself when it has none: an unknown value
// shows as it is written in the ticket.
function valueLabel(namespace, value) {
  const key = namespace + "." + value;
  return Object.hasOwn(MESSAGES[LOCALE.language], key) ? t(key) : value;
}

// A local date and time of the data (YYYY-MM-DDTHH:MM), in the short format of the browser's locale.
function formatDateTime(localDateTime) {
  return new Intl.DateTimeFormat(LOCALE.tag, { dateStyle: "short", timeStyle: "short" })
    .format(new Date(localDateTime));
}

// Sets lang, then fills the [data-i18n] elements: the text goes after their content (a label keeps its
// checkbox), or before it with data-i18n-at="start"; data-i18n-args holds the parameters, in JSON.
// data-i18n-aria-label and data-i18n-placeholder give the key of these attributes.
function translatePage() {
  document.documentElement.lang = LOCALE.language;
  for (const element of document.querySelectorAll("[data-i18n]")) {
    const text = t(element.dataset.i18n, JSON.parse(element.dataset.i18nArgs || "{}"));
    if (element.dataset.i18nAt === "start") element.prepend(text);
    else element.append(text);
  }
  for (const attribute of ["aria-label", "placeholder"]) {
    for (const element of document.querySelectorAll("[data-i18n-" + attribute + "]")) {
      element.setAttribute(attribute, t(element.getAttribute("data-i18n-" + attribute)));
    }
  }
}

translatePage();
