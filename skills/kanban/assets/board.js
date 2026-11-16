const data = JSON.parse(document.getElementById("data").textContent);
const $ = (s) => document.querySelector(s);
const byKey = Object.fromEntries(data.tickets.map((t) => [t.key, t]));
const filters = { epic: "", text: "", abandoned: false };
try { Object.assign(filters, JSON.parse(sessionStorage.getItem("kanban-filters") || "{}")); } catch (e) {}
const saveFilters = () => { try { sessionStorage.setItem("kanban-filters", JSON.stringify(filters)); } catch (e) {} };

function esc(s) {
  return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
function boardOrder(a, b) {
  const group = (t) => t.epicNumber ?? (t.type === "epic" ? t.number : 1e9);
  const rank = (t) => (t.type === "epic" ? -1 : t.rank ?? 1e6);
  return group(a) - group(b) || rank(a) - rank(b) || a.number - b.number;
}
function visible(t) {
  if (filters.epic === "-" && (t.epic || t.type === "epic")) return false;
  if (filters.epic && filters.epic !== "-" && t.epic !== filters.epic && t.key !== filters.epic) return false;
  if (filters.text) {
    const q = filters.text.toLowerCase();
    if (!(t.key + " " + t.title + " " + t.body).toLowerCase().includes(q)) return false;
  }
  return true;
}
function card(ticket) {
  const top = ['<span class="key">' + esc(ticket.key) + "</span>"];
  if (ticket.slice !== null) top.push('<span class="badge">' + esc(t("board.card.slice", { number: ticket.slice })) + "</span>");
  else if (ticket.type !== "story") top.push('<span class="badge">' + esc(valueLabel("type", ticket.type)) + "</span>");
  const bottom = [];
  if (ticket.epicTitle) bottom.push(esc(ticket.epicTitle));
  if (ticket.type === "epic") {
    const children = data.tickets.filter((e) => e.epic === ticket.key && e.status !== "abandoned");
    const done = children.filter((e) => e.status === "done").length;
    bottom.push(esc(t("board.epic.done", { done, total: children.length })));
  }
  if (ticket.notes) bottom.push(esc(t("board.card.notes", { count: ticket.notes })));
  if (ticket.spec) bottom.push(esc(t("board.card.spec")));
  if (ticket.blockedBy.length) bottom.push(esc(t("board.card.blockedBy", { keys: ticket.blockedBy.join(", ") })));
  if (ticket.jira) bottom.push(esc(t("board.jira", { key: ticket.jira })));
  return '<button class="card t-' + esc(ticket.type) + '" data-key="' + esc(ticket.key) + '">'
    + '<div class="top">' + top.join("") + "</div>"
    + '<div class="title">' + esc(ticket.title) + "</div>"
    + (bottom.length ? '<div class="bottom">' + bottom.join(" · ") + "</div>" : "") + "</button>";
}
function render() {
  const statuses = data.statuses.filter((s) => s !== "abandoned" || filters.abandoned);
  $("#board").innerHTML = statuses.map((s) => {
    const ts = data.tickets.filter((t) => t.status === s && visible(t)).sort(boardOrder);
    return '<section class="column"><h2><span>' + esc(valueLabel("status", s)) + "</span><span>" + ts.length + "</span></h2>"
      + (ts.map(card).join("") || '<p class="empty">—</p>') + "</section>";
  }).join("");
}
function renderHeader() {
  $("#title").textContent = t("board.title", { project: data.project });
  $("#subtitle").innerHTML = esc(data.directory) + " · " + esc(t("board.ticketCount", { count: data.tickets.length }))
    + " · " + esc(t("board.generated", { date: formatDateTime(data.generated) }))
    + (data.live ? ' · <span class="live">' + esc(t("board.live")) + "</span>" : "")
    + (data.documentation ? ' · <a href="' + esc(data.documentation) + '">' + esc(t("board.documentation")) + "</a>" : "");
  const epics = data.tickets.filter((t) => t.type === "epic").sort(boardOrder);
  $("#epic-filter").innerHTML = '<option value="">' + esc(t("board.filter.allEpics")) + "</option>"
    + epics.map((e) => '<option value="' + esc(e.key) + '">' + esc(e.key + " · " + e.title) + "</option>").join("")
    + '<option value="-">' + esc(t("board.filter.noEpic")) + "</option>";
  $("#epic-filter").value = filters.epic;
  $("#text-filter").value = filters.text;
  $("#abandoned-filter").checked = filters.abandoned;
  $("#epics").innerHTML = epics.map((e) => {
    const children = data.tickets.filter((t) => t.epic === e.key && t.status !== "abandoned");
    const done = children.filter((t) => t.status === "done").length;
    const percent = children.length ? Math.round((100 * done) / children.length) : 0;
    return '<div class="epic-progress" data-epic="' + esc(e.key) + '"><b>' + esc(e.title) + "</b> · "
      + esc(t("board.epic.done", { done, total: children.length })) + '<div class="bar"><span style="width:' + percent + '%"></span></div></div>';
  }).join("");
  $("#alerts").innerHTML = data.errors.length
    ? '<div class="alert">' + esc(t("board.unreadableTickets", { errors: data.errors.join(" · ") })) + "</div>" : "";
}
function openTicket(key, tab) {
  const ticket = byKey[key];
  if (!ticket) return;
  const meta = [esc(valueLabel("type", ticket.type)), esc(valueLabel("status", ticket.status))];
  if (ticket.epic) {
    meta.push(esc(t("board.panel.epic")) + ' <a data-open="' + esc(ticket.epic) + '">' + esc(ticket.epic + " · " + (ticket.epicTitle || "")) + "</a>");
  }
  if (ticket.slice !== null) meta.push(esc(t("board.panel.slice", { number: ticket.slice })));
  if (ticket.blockedBy.length) {
    meta.push(esc(t("board.panel.blockedBy")) + " "
      + ticket.blockedBy.map((c) => '<a data-open="' + esc(c) + '">' + esc(c) + "</a>").join(", "));
  }
  if (ticket.specUrl) meta.push('<a href="' + esc(ticket.specUrl) + '">' + esc(t("board.panel.specPage")) + "</a>");
  meta.push(esc(ticket.jira ? t("board.jira", { key: ticket.jira }) : t("board.panel.notInJira")));
  meta.push(esc(t("board.panel.created", { date: ticket.created })));
  meta.push('<span class="path">' + esc(ticket.file) + "</span>");
  const hasSpec = !!ticket.specHtml;
  const view = tab === "spec" && hasSpec ? "spec" : "ticket";
  const p = $("#panel");
  p.innerHTML = '<div class="panel-top"><div><span class="key">' + esc(ticket.key) + "</span><h1 style=\"margin:4px 0 0;font-size:18px\">"
    + esc(ticket.title) + '</h1></div><button class="close" aria-label="' + esc(t("board.panel.close")) + '">×</button></div>'
    + '<div class="meta">' + meta.join("<span>·</span>") + "</div>"
    + '<div class="tabs"><button data-tab="ticket" class="' + (view === "ticket" ? "active" : "") + '">'
    + esc(t("board.panel.ticketTab")) + "</button>"
    + (hasSpec ? '<button data-tab="spec" class="' + (view === "spec" ? "active" : "") + '">'
        + esc(t("board.panel.specTab", { spec: ticket.spec })) + "</button>"
      : (ticket.spec ? '<button disabled title="' + esc(t("board.panel.specNotFoundTitle")) + '">'
        + esc(t("board.panel.specNotFound")) + "</button>" : ""))
    + "</div>"
    + '<div class="md">' + (view === "spec" ? ticket.specHtml : ticket.bodyHtml) + "</div>";
  p.classList.add("open");
  p.setAttribute("aria-hidden", "false");
  p.scrollTop = 0;
  history.replaceState(null, "", "#" + key + (view === "spec" ? "/spec" : ""));
}
function closePanel() {
  $("#panel").classList.remove("open");
  $("#panel").setAttribute("aria-hidden", "true");
  history.replaceState(null, "", location.pathname + location.search);
}

document.addEventListener("click", (ev) => {
  const c = ev.target.closest(".card");
  if (c) return openTicket(c.dataset.key);
  const link = ev.target.closest("[data-open]");
  if (link) return openTicket(link.dataset.open);
  const tab = ev.target.closest("[data-tab]");
  if (tab) return openTicket(location.hash.slice(1).split("/")[0], tab.dataset.tab);
  if (ev.target.closest(".close")) return closePanel();
  const epic = ev.target.closest("[data-epic]");
  if (epic) { filters.epic = filters.epic === epic.dataset.epic ? "" : epic.dataset.epic; saveFilters(); renderHeader(); render(); }
});
document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") closePanel(); });
$("#epic-filter").addEventListener("change", (ev) => { filters.epic = ev.target.value; saveFilters(); render(); });
$("#text-filter").addEventListener("input", (ev) => { filters.text = ev.target.value; saveFilters(); render(); });
$("#abandoned-filter").addEventListener("change", (ev) => { filters.abandoned = ev.target.checked; saveFilters(); render(); });

renderHeader();
render();
if (location.hash.length > 1) {
  const [key, tab] = decodeURIComponent(location.hash.slice(1)).split("/");
  openTicket(key, tab);
}
if (data.live) {
  setInterval(async () => {
    try {
      const r = await fetch("/state", { cache: "no-store" });
      if (r.ok && (await r.text()) !== data.fingerprint) location.reload();
    } catch (e) { /* server stopped: keep the last view */ }
  }, 2000);
}
