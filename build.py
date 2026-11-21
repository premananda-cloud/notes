#!/usr/bin/env python3
"""
Build the static site.

Run from the Notes/ project root:
    python3 build.py

Reads   notes/<subject>/...        (sources, never uploaded)
Writes  static/                    (the only folder you upload)
          index.html
          third_semester.html
          assets/style.css
          assets/app.js
          notes/3sem/<slug>/<Module N>.pdf

Only Module 1-5 PDFs are copied. Everything else (DOCX_Archive, collegesent,
assignments, answer sheets, LICENSE) stays in notes/ only.
"""
import html
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "notes"
OUT = ROOT / "static"
SEM_DIR = OUT / "notes" / "3sem"

# slug, display name, short code, source folder (relative to notes/), glob pattern
SUBJECTS = [
    ("ad",   "Algorithm Design",         "AD",   "AD/PDFs",                 "AD_Module*.pdf"),
    ("ca",   "Computer Architecture",    "CA",   "computer_architecture/PDFs", "CA_Module*.pdf"),
    ("java", "Object-Oriented Programming in Java", "JAVA", "java_oop/PDFs", "JAVA_Module*.pdf"),
    ("os",   "Operating Systems",        "OS",   "os/PDFs",                 "OS_Module*.pdf"),
    ("ps",   "Probability and Statistics", "PS", "PS",                      "module-*.pdf"),
]

MODULE_RE = re.compile(r"[Mm]odule[_-]?(\d)")


def pretty_title(stem: str) -> str:
    """AD_Module1_Introduction_Analysis -> Introduction Analysis
       module-3-descriptive-statistics  -> Descriptive Statistics"""
    m = MODULE_RE.search(stem)
    rest = stem[m.end():] if m else stem
    rest = rest.strip("_- ").replace("_", " ").replace("-", " ")
    return rest.title()


def collect():
    data = []
    problems = []
    for slug, name, code, folder, pattern in SUBJECTS:
        src_dir = SRC / folder
        mods = {}
        for f in sorted(src_dir.glob(pattern)) if src_dir.exists() else []:
            m = MODULE_RE.search(f.stem)
            if not m:
                continue
            n = int(m.group(1))
            if 1 <= n <= 5:
                mods[n] = f
        missing = [n for n in range(1, 6) if n not in mods]
        if missing:
            problems.append(f"{name}: missing module(s) {missing} in {src_dir}")
        data.append((slug, name, code, [(n, mods[n]) for n in sorted(mods)]))
    return data, problems


def copy_files(data):
    if SEM_DIR.exists():
        shutil.rmtree(SEM_DIR)
    entries = []
    for slug, name, code, mods in data:
        dest = SEM_DIR / slug
        dest.mkdir(parents=True, exist_ok=True)
        rows = []
        for n, f in mods:
            # simple, URL-safe name: <slug>-module<N>.pdf
            target = dest / f"{slug}-module{n}.pdf"
            shutil.copy2(f, target)
            size_kb = max(1, round(target.stat().st_size / 1024))
            rows.append({
                "n": n,
                "title": pretty_title(f.stem),
                "href": f"notes/3sem/{slug}/{quote(target.name)}",
                "size": size_kb,
            })
        entries.append({"slug": slug, "name": name, "code": code, "rows": rows})
    return entries


def fmt_size(kb):
    return f"{kb / 1024:.1f} MB" if kb >= 1024 else f"{kb} KB"


# --------------------------------------------------------------------------- HTML

def page(title, body, active=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="top">
  <div class="wrap top-in">
    <a class="brand" href="index.html">Notes</a>
    <nav aria-label="Main">
      <a href="index.html"{' class="on"' if active == 'home' else ''}>Home</a>
      <a href="third_semester.html"{' class="on"' if active == 'sem3' else ''}>Third Semester</a>
    </nav>
  </div>
</header>
{body}
<footer class="foot">
  <div class="wrap">Study notes by Premananda Singh</div>
</footer>
<script src="assets/app.js"></script>
</body>
</html>
"""


def build_index(entries):
    total = sum(len(e["rows"]) for e in entries)
    body = f"""
<main class="wrap page">
  <h1>Course Notes</h1>
  <p class="sub">Module-wise PDF notes, organised by semester.</p>
  <ul class="plain">
    <li class="line">
      <a href="third_semester.html">Third Semester</a>
      <span class="muted">{len(entries)} subjects &middot; {total} modules</span>
    </li>
  </ul>
</main>
"""
    return page("Notes", body, "home")


def build_sem(entries):
    total = sum(len(e["rows"]) for e in entries)

    side = []
    sections = []
    for e in entries:
        side.append(
            f'<li><a href="#{e["slug"]}">{html.escape(e["name"])}</a></li>'
        )
        rows = []
        for r in e["rows"]:
            text = f'{e["name"]} {e["code"]} module {r["n"]} {r["title"]}'.lower()
            rows.append(f"""
        <li class="line row" data-text="{html.escape(text)}">
          <span class="mod">Module {r["n"]}</span>
          <span class="rt">{html.escape(r["title"])}</span>
          <span class="muted">{fmt_size(r["size"])}</span>
          <span class="acts">
            <a href="{r["href"]}" target="_blank" rel="noopener">View</a>
            <a href="{r["href"]}" download>Download</a>
          </span>
        </li>""")
        sections.append(f"""
    <section class="subject" id="{e["slug"]}">
      <h2>{html.escape(e["name"])}</h2>
      <ol class="plain">{''.join(rows)}
      </ol>
    </section>""")

    body = f"""
<div class="wrap page layout">
  <aside class="side">
    <ul class="side-list">{''.join(side)}</ul>
  </aside>
  <main class="main">
    <h1>Third Semester</h1>
    <p class="sub">{len(entries)} subjects &middot; {total} modules</p>
    <div class="search">
      <input id="q" type="search" placeholder="Search modules or subjects" aria-label="Search">
      <span id="shown" class="muted">{total} results</span>
    </div>
    {''.join(sections)}
    <p id="none" class="muted" hidden>No modules match your search.</p>
  </main>
</div>
"""
    return page("Third Semester", body, "sem3")


CSS = """
:root{
  --bg:#fafaf9; --ink:#1a1a1a; --mute:#6b6b68; --line:#e4e4e1;
  --serif:Georgia,"Times New Roman",serif;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 var(--sans)}
a{color:var(--ink);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:960px;margin:0 auto;padding:0 24px}
.muted{color:var(--mute);font-size:14px}

.top{border-bottom:1px solid var(--line)}
.top-in{display:flex;align-items:center;justify-content:space-between;height:60px}
.brand{font:700 18px var(--serif)}
.brand:hover{text-decoration:none}
.top nav a{margin-left:24px;font-size:14px;color:var(--mute)}
.top nav a.on{color:var(--ink)}

.page{padding-top:48px;padding-bottom:72px}
h1{margin:0;font:700 32px/1.25 var(--serif)}
.sub{margin:6px 0 32px;color:var(--mute)}
.plain{list-style:none;margin:0;padding:0}
.line{padding:14px 0;border-top:1px solid var(--line)}
.plain>.line:last-child{border-bottom:1px solid var(--line)}
.plain>.line{display:flex;align-items:baseline;gap:16px}
.plain>.line>a:first-child{font:600 18px var(--serif)}

.layout{display:grid;grid-template-columns:200px 1fr;gap:56px}
.side{position:sticky;top:24px;align-self:start;padding-top:6px}
.side-list{list-style:none;margin:0;padding:0}
.side-list li{padding:5px 0}
.side-list a{font-size:14px;color:var(--mute)}
.side-list a:hover{color:var(--ink)}

.search{display:flex;align-items:center;gap:16px;margin-bottom:40px}
.search input{flex:1;padding:9px 0;border:0;border-bottom:1px solid var(--ink);background:transparent;color:var(--ink);font:inherit;border-radius:0}
.search input:focus{outline:none;border-bottom-width:2px}

.subject{margin-bottom:44px;scroll-margin-top:24px}
.subject h2{margin:0 0 10px;font:700 22px var(--serif)}
.row{display:grid!important;grid-template-columns:84px 1fr 70px auto;align-items:baseline;gap:16px}
.mod{font-size:13px;color:var(--mute)}
.rt{font:500 17px var(--serif)}
.acts{display:flex;gap:18px;font-size:14px}
.acts a{text-decoration:underline;text-decoration-color:var(--line);text-underline-offset:3px}
.acts a:hover{text-decoration-color:var(--ink)}

.foot{border-top:1px solid var(--line);color:var(--mute);font-size:13px;padding:20px 0}

@media (max-width:760px){
  .layout{grid-template-columns:1fr;gap:20px}
  .side{position:static}
  .side-list{display:flex;flex-wrap:wrap;gap:4px 18px}
  h1{font-size:26px}
  .row{grid-template-columns:1fr auto;gap:2px 12px}
  .mod{grid-column:1/-1}
  .row>.muted{display:none}
}
"""

JS = """
(function () {
  var q = document.getElementById('q');
  if (!q) return;
  var subjects = [].slice.call(document.querySelectorAll('.subject'));
  var shown = document.getElementById('shown');
  var none = document.getElementById('none');

  function apply() {
    var term = q.value.trim().toLowerCase();
    var total = 0;
    subjects.forEach(function (s) {
      var n = 0;
      [].forEach.call(s.querySelectorAll('.row'), function (r) {
        var ok = !term || r.dataset.text.indexOf(term) !== -1;
        r.hidden = !ok;
        if (ok) n++;
      });
      s.hidden = n === 0;
      total += n;
    });
    shown.textContent = total + (total === 1 ? ' result' : ' results');
    none.hidden = total !== 0;
  }

  q.addEventListener('input', apply);
})();
"""


def main():
    data, problems = collect()
    for p in problems:
        print("WARNING:", p, file=sys.stderr)

    entries = copy_files(data)

    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    (OUT / "assets" / "style.css").write_text(CSS.strip() + "\n", encoding="utf-8")
    (OUT / "assets" / "app.js").write_text(JS.strip() + "\n", encoding="utf-8")
    (OUT / "index.html").write_text(build_index(entries), encoding="utf-8")
    (OUT / "third_semester.html").write_text(build_sem(entries), encoding="utf-8")

    n = sum(len(e["rows"]) for e in entries)
    print(f"Built {n} module PDFs across {len(entries)} subjects into {OUT}")


if __name__ == "__main__":
    main()
