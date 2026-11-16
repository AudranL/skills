"""The HTML rendering of the Markdown of tickets, specs and documentation. All the text is escaped."""
import html
import re


def escape(text):
    return html.escape(text, quote=True)


def markdown_to_html(text):
    """The HTML of a Markdown text. All the text is escaped: no HTML from the file gets through."""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text.replace("\r\n", "\n"))
    return "\n".join(blocks(without_html_comments(text.split("\n"))))


MD_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def without_html_comments(lines):
    """The lines without their <!-- … --> comments, which can span several lines, except in code."""
    output, text, closing = [], [], None

    def flush_text():
        if text:
            output.extend(MD_COMMENT.sub("", "\n".join(text)).split("\n"))
            text.clear()

    for line in lines:
        if closing:
            output.append(line)
            closing = None if closing.match(line) else closing
        elif MD_FENCE.match(line):
            flush_text()
            output.append(line)
            closing = closing_fence(line)
        else:
            text.append(line)
    flush_text()
    return output


def closing_fence(opening):
    """The closing fence of a code block: the same sign, at least as many times."""
    fence = MD_FENCE.match(opening).group(2)
    return re.compile(rf" {{0,3}}{re.escape(fence[0])}{{{len(fence)},}}[ \t]*$")


MD_HEADING = re.compile(r" {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
MD_ITEM = re.compile(r"( {0,3})([-*+]|\d{1,9}[.)])(?:( +)(.*))?$")
MD_FENCE = re.compile(r"( {0,3})(`{3,}|~{3,})(.*)$")
MD_DELIMITER_ROW = re.compile(r" {0,3}\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")
MD_BLOCKQUOTE = re.compile(r" {0,3}> ?(.*)$")
MD_THEMATIC_BREAK = re.compile(r" {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")


def level_1_headings(text):
    """The text of each level 1 heading of a Markdown text, in order (None for an empty heading)."""
    for line in text.split("\n"):
        md_heading = MD_HEADING.match(line)
        if md_heading and len(md_heading.group(1)) == 1:
            yield md_heading.group(2)


def blocks(lines):
    """The HTML of each block of the lines. Each block reader returns (HTML, index of the next line)."""
    output, i = [], 0
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        block, i = block_reader(lines, i)(lines, i)
        output.append(block)
    return output


def block_reader(lines, i):
    line = lines[i]
    if MD_FENCE.match(line):
        return code
    if MD_HEADING.match(line):
        return heading
    if MD_THEMATIC_BREAK.match(line):  # before lists: "- - -" is not a list
        return thematic_break
    if MD_ITEM.match(line):
        return item_list
    if MD_BLOCKQUOTE.match(line):
        return blockquote
    if is_table_row(line) and i + 1 < len(lines) and MD_DELIMITER_ROW.match(lines[i + 1]):
        return table
    return paragraph


def thematic_break(lines, i):
    return "<hr>", i + 1


def blockquote(lines, i):
    """The lines that start with >. They keep their line breaks: a refinement note quotes an answer
    word for word in them."""
    inner = []
    while i < len(lines) and MD_BLOCKQUOTE.match(lines[i]):
        text = MD_BLOCKQUOTE.match(lines[i]).group(1)
        inner.append(text + "  " if text.strip() else text)
        i += 1
    return "<blockquote>\n" + "\n".join(blocks(inner)) + "\n</blockquote>", i


def is_table_row(line):
    return line.lstrip().startswith("|")


def table(lines, i):
    """A table: a header row, a |---| delimiter row, then the rows that start with |."""
    head = "".join(f"<th>{inline(cell)}</th>" for cell in cells(lines[i]))
    i += 2
    rows = []
    while i < len(lines) and is_table_row(lines[i]):
        rows.append("<tr>" + "".join(f"<td>{inline(cell)}</td>" for cell in cells(lines[i])) + "</tr>")
        i += 1
    body = "".join(f"{row}\n" for row in rows)
    return f"<table>\n<thead>\n<tr>{head}</tr>\n</thead>\n<tbody>\n{body}</tbody>\n</table>", i


def cells(line):
    """The cells of a table row. An escaped bar (\\|) stays in its cell, even in code."""
    inner = line.strip()
    inner = inner[1:] if inner.startswith("|") else inner
    inner = inner[:-1] if re.search(r"(?<!\\)\|$", inner) else inner
    return [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", inner)]


def code(lines, i):
    """A code block fenced by ``` or ~~~: its text as it is, escaped, up to the closing fence or the end."""
    info, closing = MD_FENCE.match(lines[i]).group(3), closing_fence(lines[i])
    start = i = i + 1
    while i < len(lines) and not closing.match(lines[i]):
        i += 1
    text = "\n".join(lines[start:i])
    language = info.split()[0].lower() if info.strip() else ""
    class_attribute = f' class="language-{escape(language)}"' if language else ""
    content = gherkin_to_html(text) if language in ("gherkin", "feature") else escape(text)
    return f"<pre><code{class_attribute}>{content}</code></pre>", i + 1


# Step keywords, with the space or apostrophe that follows them (Gherkin's i18n dictionary, fr and en).
GHERKIN_STEPS = [
    "Soit ", "Sachant que ", "Sachant qu'", "Sachant ",
    "Étant donné que ", "Étant donné qu'", "Étant donné ", "Étant donnée ", "Étant donnés ",
    "Étant données ", "Etant donné que ", "Etant donné qu'", "Etant donné ", "Etant donnée ",
    "Etant donnés ", "Etant données ",
    "Quand ", "Lorsque ", "Lorsqu'", "Alors ", "Donc ",
    "Et que ", "Et qu'", "Et ", "Mais que ", "Mais qu'", "Mais ",
    "Given ", "When ", "Then ", "And ", "But ", "* ",
]
GHERKIN_STEPS += [keyword[:-1] + "’" for keyword in GHERKIN_STEPS if keyword.endswith("'")]
GHERKIN_BLOCKS = [
    "Fonctionnalité", "Contexte", "Règle", "Scénario", "Plan du scénario", "Plan du Scénario",
    "Exemple", "Exemples",
    "Feature", "Background", "Rule", "Scenario", "Scenario Outline", "Scenario Template", "Example", "Examples",
    "Scenarios",
]


def alternation(keywords):
    """A regular expression alternation where the longest keyword wins (Et qu' before Et)."""
    return "|".join(re.escape(keyword) for keyword in sorted(keywords, key=len, reverse=True))


GHERKIN_STEP = re.compile(rf"(\s*)({alternation(GHERKIN_STEPS)})(.*)$")
GHERKIN_BLOCK = re.compile(rf"(\s*)((?:{alternation(GHERKIN_BLOCKS)}):)(.*)$")


def gherkin_to_html(text):
    """The text of a Gherkin block, escaped, with its keywords highlighted line by line."""
    return "\n".join(gherkin_line(line) for line in text.split("\n"))


def gherkin_line(line):
    comment = re.match(r"(\s*)(#.*)$", line)
    if comment:
        indent, text = comment.groups()
        return f'{indent}<span class="gk-comment">{escape(text)}</span>'
    block = GHERKIN_BLOCK.match(line)
    if block:
        indent, keyword, block_title = block.groups()
        return (f'{indent}<span class="gk-keyword">{escape(keyword)}</span>'
                f'<span class="gk-title">{with_variables(block_title)}</span>')
    step = GHERKIN_STEP.match(line)
    if step:
        indent, keyword, rest = step.groups()
        space = " " if keyword.endswith(" ") else ""
        return f'{indent}<span class="gk-keyword">{escape(keyword.rstrip())}</span>{space}{with_variables(rest)}'
    return with_variables(line)


def with_variables(text):
    """The escaped text, where the variables of a scenario outline (<chosen levels>) are highlighted."""
    return re.sub(r"&lt;([^&]+?)&gt;", r'<span class="gk-variable">&lt;\1&gt;</span>', escape(text))


def item_list(lines, i):
    """The items that follow each other with the same kind of bullet. A blank line between two items, or
    inside an item, loosens the list: its paragraphs keep their <p> tags."""
    tag, start_attribute = list_tag(MD_ITEM.match(lines[i]).group(2))
    kind, contents, loose = bullet_kind(lines[i]), [], False
    while i < len(lines) and bullet_kind(lines[i]) == kind:
        content, i = item_lines(lines, i)
        contents.append(content)
        loose = loose or "" in content[1:]
        following = next_non_blank(lines, i)
        if following < len(lines) and bullet_kind(lines[following]) == kind:
            loose, i = loose or following > i, following
    items = "\n".join(list_item(content, loose) for content in contents)
    return f"<{tag}{start_attribute}>\n{items}\n</{tag}>", i


def list_tag(bullet):
    """The tag of a list and, for a numbered list that does not start at 1, its start attribute."""
    if not bullet[0].isdigit():
        return "ul", ""
    number = int(bullet[:-1])
    return "ol", "" if number == 1 else f' start="{number}"'


def list_item(content, loose):
    parts = blocks(content)
    return "<li>" + "\n".join(parts if loose else map(without_paragraph, parts)) + "</li>"


def next_non_blank(lines, i):
    while i < len(lines) and not lines[i].strip():
        i += 1
    return i


def bullet_kind(line):
    """The kind of bullet, - * + . or ), None outside an item: another kind starts another list."""
    bullet = MD_ITEM.match(line)
    if not bullet:
        return None
    return bullet.group(2)[-1] if bullet.group(2)[0].isdigit() else bullet.group(2)


def item_lines(lines, i):
    """The lines of an item, without its bullet or the indent of its content: a nested list stays a list."""
    indent, bullet, spaces, text = MD_ITEM.match(lines[i]).groups()
    content_column = len(indent) + len(bullet) + len(spaces or " ")
    content = [text or ""]
    i += 1
    while i < len(lines):
        if not lines[i].strip():
            following = next_non_blank(lines, i)
            if following == len(lines) or indent_of(lines[following]) < content_column:
                break
            content += [""] * (following - i)
            i = following
        if indent_of(lines[i]) >= content_column:
            content.append(lines[i][content_column:])
        elif block_reader(lines, i) is paragraph:
            content.append(lines[i].strip())  # continuation of the item's paragraph, without indent
        else:
            break
        i += 1
    return content, i


def indent_of(line):
    return len(line) - len(line.lstrip(" "))


def without_paragraph(block):
    """The text of an item's paragraph, without its <p> tags: the list is tight."""
    return block[3:-4] if block.startswith("<p>") and block.endswith("</p>") else block


def heading(lines, i):
    hashes, text = MD_HEADING.match(lines[i]).groups()
    return f"<h{len(hashes)}>{inline(text or '')}</h{len(hashes)}>", i + 1


def paragraph(lines, i):
    start = i
    i += 1
    while i < len(lines) and lines[i].strip() and block_reader(lines, i) is paragraph:
        i += 1
    *first_lines, last_line = lines[start:i]
    rendered = [line_followed_by_another(line) for line in first_lines] + [inline(last_line.strip())]
    return "<p>" + "\n".join(rendered) + "</p>", i


MD_HARD_BREAK = re.compile(r"(?:  +|\\)$")


def line_followed_by_another(line):
    """Two spaces or a backslash at the end of a line force a line break."""
    text = line.lstrip()
    if MD_HARD_BREAK.search(text):
        return inline(MD_HARD_BREAK.sub("", text).rstrip()) + "<br>"
    return inline(text.rstrip())


MD_BOLD = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
# An underscore in the middle of a word (synchro_jira) neither opens nor closes italics.
MD_ITALIC = re.compile(r"(?<!\*)\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?!\*)|(?<!\w)_(?=[^\s_])(.+?)(?<=[^\s_])_(?!\w)")
MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
ASIDE_MARKER = re.compile("\x00(\\d+)\x00")
PUNCTUATION = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"


def inline(text):
    """The HTML of a line of text: inline code, links, bold and italics, the rest escaped.

    Code and characters escaped by a backslash are rendered first and set aside
    (marker \\x00n\\x00): the formatting does not reach them.
    """
    aside = []

    def set_aside(fragment):
        aside.append(fragment)
        return f"\x00{len(aside) - 1}\x00"

    text = code_and_escapes(text, set_aside)
    text = MD_LINK.sub(lambda m: link(m.group(1), m.group(2)), escape(text))
    text = MD_BOLD.sub(r"<strong>\1</strong>", text)
    text = MD_ITALIC.sub(lambda m: f"<em>{m.group(1) or m.group(2)}</em>", text)
    return ASIDE_MARKER.sub(lambda m: aside[int(m.group(1))], text)


def code_and_escapes(text, set_aside):
    """Read from left to right: a backslash escapes a backtick, but escapes nothing inside code."""
    pieces, i = [], 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text) and text[i + 1] in PUNCTUATION:
            pieces.append(set_aside(escape(text[i + 1])))
            i += 2
        elif text[i] == "`":
            opening = re.match(r"`+", text[i:]).group(0)
            closing = re.compile(rf"(?<!`){opening}(?!`)").search(text, i + len(opening))
            if closing:
                code = text[i + len(opening):closing.start()]
                pieces.append(set_aside(f"<code>{escape(code)}</code>"))
                i = closing.end()
            else:
                pieces.append(opening)
                i += len(opening)
        else:
            pieces.append(text[i])
            i += 1
    return "".join(pieces)


def link(text, url):
    """A link whose text and url are already escaped. Another site opens in another tab.

    Only relative, http, https and mailto links are links: the other schemes (javascript:, data:…)
    could run code, and a url that contains code set aside is not one.
    """
    scheme = re.match(r"([a-zA-Z][a-zA-Z0-9+.-]*):", url)
    if "\x00" in url or (scheme and scheme.group(1).lower() not in ("http", "https", "mailto")):
        return text
    if re.match(r"https?://", url, re.IGNORECASE):
        return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{text}</a>'
    return f'<a href="{url}">{text}</a>'
