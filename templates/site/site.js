// Reader controls, word popover, glossary search. No dependencies, no network.
const root = document.documentElement;
const FORMS = { full: 0, nocase: 1, partial: 2, none: 3, raw: 4 };
const sheet = window.matchMedia("(max-width: 719px)");

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined) n.textContent = text;
  return n;
}

// ---------- reading settings ----------
const bookletKey = root.dataset.booklet ? "anrs:" + root.dataset.booklet : null;
const defaults = { vowels: root.dataset.vowels, gloss: root.dataset.gloss, english: root.dataset.english };

function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem(bookletKey) || "{}");
    return { ...defaults, ...saved };
  } catch (e) {
    return { ...defaults };
  }
}

function saveState(state) {
  try { localStorage.setItem(bookletKey, JSON.stringify(state)); } catch (e) { /* private mode: keep going */ }
}

function swapVowels(mode) {
  const i = FORMS[mode];
  document.querySelectorAll(".w[data-v]").forEach((w) => {
    const t = w.querySelector(".t");
    const next = w.dataset.v.split("|")[i];
    if (t.textContent !== next) t.textContent = next;
  });
}

function applyState(state) {
  root.dataset.vowels = state.vowels;
  root.dataset.gloss = state.gloss;
  root.dataset.english = state.english;
  swapVowels(state.vowels);
  document.querySelectorAll("[data-ctl]").forEach((b) => {
    b.setAttribute("aria-pressed", String(state[b.dataset.ctl] === b.dataset.val));
  });
}

function initReader() {
  const state = loadState();
  applyState(state);
  document.querySelectorAll("[data-ctl]").forEach((b) => {
    b.addEventListener("click", () => {
      state[b.dataset.ctl] = b.dataset.val;
      applyState(state);
      saveState(state);
      if (b.closest(".more")) { bar.classList.remove("open"); toggle.textContent = "More options"; toggle.setAttribute("aria-expanded", "false"); }
      closePop();
    });
  });
  const bar = document.querySelector(".bar");
  const toggle = document.querySelector(".bar .toggle");
  if (toggle) {
    toggle.addEventListener("click", () => {
      const open = bar.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
      toggle.textContent = open ? "Fewer options" : "More options";
    });
  }
  document.querySelectorAll(".sent .num").forEach((n) => {
    n.addEventListener("click", () => {
      const sent = n.closest(".sent");
      n.setAttribute("aria-expanded", String(sent.classList.toggle("open")));
    });
  });
  const marks = document.getElementById("marks");
  if (marks) {
    marks.addEventListener("click", () => {
      const on = marks.getAttribute("aria-pressed") !== "true";
      marks.setAttribute("aria-pressed", String(on));
      marks.textContent = on ? "Hide marks" : "Show marks";
      document.querySelectorAll(".uw[data-m]").forEach((s) => {
        const [bare, marked] = s.dataset.m.split("|");
        s.textContent = on ? marked : bare;
      });
    });
  }
}

// ---------- word popover ----------
let cards = {};
let pop = null;
let current = null;

function row(dl, label, ...nodes) {
  dl.append(el("dt", "", label));
  const dd = el("dd");
  dd.append(...nodes);
  dl.append(dd);
}

function arabic(text, cls) {
  const s = el("span", cls || "", text);
  s.lang = "ar";
  s.dir = "rtl";
  return s;
}

function fill(btn) {
  pop.replaceChildren();
  const form = btn.dataset.v.split("|")[FORMS.raw];
  const head = el("div", "head");
  const left = el("div");
  left.append(arabic(form, "word"));
  if (btn.dataset.gl) left.append(el("div", "gloss", btn.dataset.gl));
  const close = el("button", "close", "×");
  close.type = "button";
  close.setAttribute("aria-label", "Close");
  close.addEventListener("click", () => closePop(true));
  head.append(left, close);
  pop.append(head);

  const c = cards[btn.dataset.d];
  if (!c) {
    pop.append(el("p", "none", "No dictionary entry for this word in this booklet."));
    return;
  }
  const dl = el("dl");
  row(dl, "Meaning", c.en);
  row(dl, "Type", arabic(c.pos[0]), " " + c.pos[1]);
  if (c.root) row(dl, "Root", arabic(c.root.split("").join(" "), "root"));
  if (c.pattern) row(dl, "Pattern", arabic(c.pattern));
  if (c.present) row(dl, "Present", arabic(c.present), c.bab ? " (" : "", c.bab ? arabic(c.bab) : "", c.bab ? ")" : "");
  if (c.plural) row(dl, "Plural", arabic(c.plural));
  if (c.headword) row(dl, "Entry", arabic(c.headword));
  pop.append(dl);
  if (c.ayah) {
    const hook = el("div", "hook");
    hook.append(arabic(c.ayah.text, "t"), el("span", "r", c.ayah.ref));
    if (c.ayah.en) hook.append(el("div", "", c.ayah.en));
    pop.append(hook);
  }
  const link = el("a", "more-link", "See it in the dictionary");
  link.href = c.href;
  link.addEventListener("click", () => closePop());
  pop.append(link);
}

function place(btn) {
  pop.style.left = pop.style.top = "";
  const r = btn.getBoundingClientRect();
  if (sheet.matches) {
    const top = pop.getBoundingClientRect().top;
    if (r.bottom > top - 16) window.scrollBy({ top: r.bottom - top + 16 });
    return;
  }
  const pw = pop.offsetWidth, ph = pop.offsetHeight, gap = 8;
  let left = r.left + window.scrollX + r.width / 2 - pw / 2;
  left = Math.max(gap, Math.min(left, window.scrollX + root.clientWidth - pw - gap));
  let top = r.bottom + window.scrollY + gap;
  if (r.bottom + ph + gap * 2 > window.innerHeight && r.top > ph + gap * 2) top = r.top + window.scrollY - ph - gap;
  pop.style.left = left + "px";
  pop.style.top = top + "px";
}

function openPop(btn) {
  if (current) current.setAttribute("aria-expanded", "false");
  current = btn;
  btn.setAttribute("aria-expanded", "true");
  fill(btn);
  pop.hidden = false;
  place(btn);
  pop.focus({ preventScroll: true });
}

function closePop(refocus) {
  if (!current) return;
  current.setAttribute("aria-expanded", "false");
  pop.hidden = true;
  if (refocus) current.focus();
  current = null;
}

function initPopover() {
  const data = document.getElementById("cards");
  cards = data ? JSON.parse(data.textContent) : {};
  pop = el("div", "pop");
  pop.id = "pop";
  pop.hidden = true;
  pop.tabIndex = -1;
  pop.setAttribute("role", "dialog");
  pop.setAttribute("aria-label", "Word details");
  document.body.append(pop);
  document.addEventListener("click", (e) => {
    const w = e.target.closest(".reader .w");
    if (w) {
      if (w === current) closePop(); else openPop(w);
    } else if (!pop.contains(e.target)) {
      closePop();
    }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closePop(true);
  });
  window.addEventListener("resize", () => closePop());
}

// ---------- glossary search ----------
const strip = (s) => s.replace(/[ؐ-ًؚ-ٰٟۖ-ۭـ]/g, "")
  .replace(/[أإآٱ]/g, "ا").replace(/ى/g, "ي").toLowerCase().trim();

function initSearch() {
  const input = document.getElementById("gl-q");
  if (!input) return;
  const items = [...document.querySelectorAll(".gl li")];
  const count = document.getElementById("gl-count");
  const run = () => {
    const q = strip(input.value);
    let n = 0;
    items.forEach((li) => {
      const hit = !q || li.dataset.q.includes(q);
      li.hidden = !hit;
      if (hit) n++;
    });
    count.textContent = q ? n + " of " + items.length + " words" : items.length + " words";
  };
  input.addEventListener("input", run);
  run();
}

if (root.dataset.booklet) {
  initReader();
  initPopover();
}
initSearch();
