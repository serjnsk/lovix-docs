#!/usr/bin/env python3
"""Build email-template.html from email-template.md.

Skeleton (styles, top nav, marked render, TOC) is taken from scenarios.html
so the page stays in sync with the site look. Page-specific JS (device toggle
for the email preview) is appended here.

Usage: python3 build_email_spec.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
TITLE = "Lovix — Шаблон email-рассылок"
CUR = "email-template.html"


PAGE_JS = """
function mailpvSet(btn, mob){
  const pv = document.getElementById('mailpv');
  pv.classList.toggle('mob', mob);
  pv.querySelectorAll('.dev').forEach(b => b.classList.toggle('on', b === btn));
}
"""


def retarget_nav(head):
    # Nav is inherited verbatim from the scenarios.html donor (it carries the
    # dropdown structure); we only move the `cur` marker to this page's link.
    m = re.search(r"<nav>.*?</nav>", head, re.S)
    if not m:
        return head
    nav = m.group(0).replace(' class="cur"', "").replace("dd-btn cur", "dd-btn")
    nav = nav.replace(f'<a href="{CUR}">', f'<a class="cur" href="{CUR}">')
    dd = re.search(r'<div class="dd">.*?</nav>', nav, re.S)
    if dd and f'href="{CUR}"' in dd.group(0):
        nav = nav.replace('class="dd-btn"', 'class="dd-btn cur"')
    return head[:m.start()] + nav + head[m.end():]


def main():
    donor = (ROOT / "scenarios.html").read_text(encoding="utf-8")

    head_end = donor.index('<script type="text/markdown" id="src">')
    head = donor[: head_end + len('<script type="text/markdown" id="src">')]
    head = re.sub(r"<title>.*?</title>", f"<title>{TITLE}</title>", head, count=1)
    head = retarget_nav(head)

    foot_start = donor.rindex("</script>\n<script>")
    foot = donor[foot_start:]
    # drop the chips post-processing (🔔/✉/💬 замены не нужны на этой странице):
    # keep marked render + TOC builder only
    foot = re.sub(
        r'document\.querySelectorAll\("#out table td.*?\n\n\n', "", foot,
        count=1, flags=re.S,
    )
    foot = re.sub(
        r'document\.querySelectorAll\("#out table"\).*?\n\n\n', "", foot,
        count=1, flags=re.S,
    )
    foot = foot.replace("</script>\n</body>", PAGE_JS + "</script>\n</body>")

    md = (ROOT / "email-template.md").read_text(encoding="utf-8")
    assert "</script>" not in md, "литеральный </script> в md сломает страницу"

    (ROOT / "email-template.html").write_text(head + "\n" + md + "\n" + foot, encoding="utf-8")
    print("built email-template.html")


if __name__ == "__main__":
    main()
