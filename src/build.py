#!/usr/bin/env python3
"""Build the static site.

Reads Markdown from src/content and writes plain HTML to the repository root,
which GitHub Pages serves as-is (see .nojekyll).

    python3 -m pip install -r src/requirements.txt
    python3 src/build.py

Only the paths listed in GENERATED are deleted and rewritten, so nothing else
in the repository root is ever touched.
"""

from __future__ import annotations

import datetime as dt
import html
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

import markdown
from markdown.extensions.toc import slugify_unicode
from pygments.formatters import HtmlFormatter

# ---------------------------------------------------------------- config

SITE = {
    "url": "https://huangruidtu.github.io",
    "title": "Rui Huang",
    "tagline": "Notes on platforms, data, and the things in between.",
    "subline": "From segmentation fault to service not found.",
    "description": "Rui Huang's notes on platforms, data, and the things in between.",
    "author": "Rui Huang",
    "motto": "Ctrl + Alt + Solve",
    "since": 2020,
    "links": [
        ("GitHub", "https://github.com/huangruidtu"),
        ("LinkedIn", "https://www.linkedin.com/in/rui-huang-314a50168/"),
        ("Email", "mailto:huangruitjut@gmail.com"),
    ],
}

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
CONTENT = SRC / "content"
STATIC = SRC / "static"

# Everything the build owns in the repository root. Nothing else is deleted.
GENERATED = ["index.html", "404.html", "atom.xml", "sitemap.xml", "robots.txt",
             "posts", "about", "assets"]

MD_EXTENSIONS = ["fenced_code", "tables", "sane_lists", "codehilite", "toc"]
MD_CONFIG = {
    "codehilite": {"css_class": "highlight", "guess_lang": False},
    # slugify_unicode keeps CJK characters, so Chinese headings get readable anchors
    "toc": {"permalink": "#", "permalink_title": "Link to this section", "slugify": slugify_unicode},
}

# ---------------------------------------------------------------- content


@dataclass
class Page:
    slug: str
    title: str
    body_html: str
    date: dt.date | None = None
    summary: str = ""
    series: str = ""
    series_part: int = 0
    meta: dict = field(default_factory=dict)

    @property
    def url(self) -> str:
        return f"/posts/{self.slug}/" if self.date else f"/{self.slug}/"


def parse_front_matter(text: str, path: Path) -> tuple[dict, str]:
    """Minimal `key: value` front matter between two `---` lines."""
    if not text.startswith("---\n"):
        sys.exit(f"{path}: missing front matter")
    try:
        head, body = text[4:].split("\n---\n", 1)
    except ValueError:
        sys.exit(f"{path}: unterminated front matter")
    meta = {}
    for n, line in enumerate(head.splitlines(), 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            sys.exit(f"{path}:{n}: expected `key: value`")
        meta[key.strip()] = value.strip()
    return meta, body


def render_markdown(body: str) -> str:
    return markdown.markdown(body, extensions=MD_EXTENSIONS,
                             extension_configs=MD_CONFIG, output_format="html")


def load_page(path: Path, is_post: bool) -> Page:
    meta, body = parse_front_matter(path.read_text(encoding="utf-8"), path)
    for required in ("title",) + (("date", "summary") if is_post else ()):
        if not meta.get(required):
            sys.exit(f"{path}: front matter needs `{required}`")
    return Page(
        slug=meta.get("slug") or path.stem,
        title=meta["title"],
        body_html=render_markdown(body),
        date=dt.date.fromisoformat(meta["date"]) if is_post else None,
        summary=meta.get("summary", ""),
        series=meta.get("series", ""),
        series_part=int(meta.get("series_part") or 0),
        meta=meta,
    )


def load_posts() -> list[Page]:
    posts = [load_page(p, True) for p in sorted((CONTENT / "posts").glob("*.md"))]
    posts = [p for p in posts if p.meta.get("draft", "").lower() != "true"]
    slugs = [p.slug for p in posts]
    dupes = {s for s in slugs if slugs.count(s) > 1}
    if dupes:
        sys.exit(f"duplicate post slugs: {', '.join(sorted(dupes))}")
    return sorted(posts, key=lambda p: (p.date, p.series_part), reverse=True)

# ---------------------------------------------------------------- templates

e = html.escape


def layout(*, title: str, description: str, path: str, body: str,
           lang: str = "en", og_type: str = "website") -> str:
    full_title = title if title == SITE["title"] else f"{title} · {SITE['title']}"
    canonical = SITE["url"] + path
    image = SITE["url"] + "/assets/psyduck-512.jpg"
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(description)}">
<meta name="author" content="{e(SITE['author'])}">
<meta name="color-scheme" content="light dark">
<link rel="canonical" href="{canonical}">
<link rel="alternate" type="application/atom+xml" title="{e(SITE['title'])}" href="/atom.xml">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/style.css">
<meta property="og:site_name" content="{e(SITE['title'])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{image}">
<meta name="twitter:card" content="summary">
</head>
<body>
<div class="wrap">
{body}
{footer()}
</div>
</body>
</html>
"""


def footer() -> str:
    # Derived from content (set in build()), not the clock, so rebuilding the
    # same content always produces identical output.
    year = SITE["year"]
    return f"""<footer class="site-footer">
<span>&copy; {SITE['since']}–{year} {e(SITE['author'])}</span>
<span class="motto">{e(SITE['motto'])}</span>
</footer>"""


def topbar(current: str = "") -> str:
    about_attr = ' aria-current="page"' if current == "about" else ""
    return f"""<header class="topbar">
<a class="home" href="/"><img src="/assets/psyduck-192.jpg" alt="" width="32" height="32">{e(SITE['title'])}</a>
<nav><a href="/">Writing</a><a href="/about/"{about_attr}>About</a></nav>
</header>"""


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fmt_date(d: dt.date) -> str:
    # Spelled out by hand so the output never depends on the build machine's locale.
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def render_home(posts: list[Page]) -> str:
    links = "".join(f'<a href="{e(url)}">{e(name)}</a>' for name, url in SITE["links"])
    items = []
    for p in posts:
        meta = fmt_date(p.date)
        items.append(f"""<li>
<div class="meta"><time datetime="{p.date.isoformat()}">{meta}</time></div>
<h2><a href="{p.url}">{e(p.title)}</a></h2>
<p>{e(p.summary)}</p>
</li>""")
    body = f"""<header class="intro">
<img class="avatar" src="/assets/psyduck-192.jpg" alt="Psyduck, my avatar" width="72" height="72">
<div>
<h1>{e(SITE['title'])}</h1>
<p>{e(SITE['tagline'])}<br>{e(SITE['subline'])}</p>
<div class="links">{links}</div>
</div>
</header>
<main>
<h2 class="section-title">Writing</h2>
<ul class="post-list">
{chr(10).join(items)}
</ul>
</main>"""
    return layout(title=SITE["title"], description=SITE["description"], path="/", body=body)


def render_series_box(post: Page, posts: list[Page]) -> str:
    if not post.series:
        return ""
    parts = sorted((p for p in posts if p.series == post.series), key=lambda p: p.series_part)
    rows = []
    for p in parts:
        if p is post:
            rows.append(f'<li class="current">{e(p.title)}</li>')
        else:
            rows.append(f'<li><a href="{p.url}">{e(p.title)}</a></li>')
    return f"""<aside class="series">
<div class="label">Series: {e(post.series)}</div>
<ol>{''.join(rows)}</ol>
</aside>"""


def render_post(post: Page, posts: list[Page]) -> str:
    meta = fmt_date(post.date)
    body = f"""{topbar()}
<main>
<article>
<header class="post-header">
<h1>{e(post.title)}</h1>
<div class="meta"><time datetime="{post.date.isoformat()}">{meta}</time></div>
</header>
<div class="prose">
{post.body_html}
</div>
</article>
{render_series_box(post, posts)}
<div class="post-footer"><a href="/">&larr; All posts</a></div>
</main>"""
    return layout(title=post.title, description=post.summary, path=post.url,
                  body=body, og_type="article")


def render_about(page: Page) -> str:
    body = f"""{topbar('about')}
<main>
<article>
<header class="post-header"><h1>{e(page.title)}</h1></header>
<div class="prose">
{page.body_html}
</div>
</article>
</main>"""
    return layout(title=page.title, description=page.meta.get("summary") or SITE["description"],
                  path=page.url, body=body)


def render_404() -> str:
    body = f"""<main class="notfound">
<img src="/assets/psyduck-512.jpg" alt="Psyduck, confused" width="160" height="160">
<h1>404</h1>
<p>Psyduck can't find this page either.</p>
<p><a href="/">&larr; Back to the homepage</a></p>
</main>"""
    return layout(title="Page not found", description=SITE["description"], path="/404.html",
                  body=body)


def render_atom(posts: list[Page]) -> str:
    def ts(d: dt.date) -> str:
        return f"{d.isoformat()}T00:00:00Z"
    updated = ts(max(p.date for p in posts)) if posts else f"{SITE['since']}-01-01T00:00:00Z"
    entries = "".join(f"""
  <entry>
    <title>{e(p.title)}</title>
    <link href="{SITE['url']}{p.url}"/>
    <id>{SITE['url']}{p.url}</id>
    <published>{ts(p.date)}</published>
    <updated>{ts(p.date)}</updated>
    <summary>{e(p.summary)}</summary>
    <content type="html">{e(p.body_html)}</content>
  </entry>""" for p in posts)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{e(SITE['title'])}</title>
  <subtitle>{e(SITE['description'])}</subtitle>
  <link href="{SITE['url']}/atom.xml" rel="self"/>
  <link href="{SITE['url']}/"/>
  <id>{SITE['url']}/</id>
  <updated>{updated}</updated>
  <author><name>{e(SITE['author'])}</name></author>{entries}
</feed>
"""


def render_sitemap(urls: list[str]) -> str:
    rows = "".join(f"\n  <url><loc>{SITE['url']}{u}</loc></url>" for u in urls)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{rows}
</urlset>
"""

# ---------------------------------------------------------------- build


def write(rel: str, text: str) -> None:
    out = ROOT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def pygments_css() -> str:
    light = HtmlFormatter(style="default").get_style_defs(".highlight")
    dark = HtmlFormatter(style="github-dark").get_style_defs(".highlight")
    # Code-block backgrounds come from style.css; drop the themes' own.
    strip_bg = re.compile(r"^\.highlight\s*\{\s*background:[^}]*\}\s*$", re.M)
    light, dark = strip_bg.sub("", light), strip_bg.sub("", dark)
    dark = "\n".join("  " + line for line in dark.splitlines())
    return f"\n/* ---------- syntax highlighting (generated by build.py) ---------- */\n{light}\n" \
           f"@media (prefers-color-scheme: dark) {{\n{dark}\n}}\n"


def clean() -> None:
    for name in GENERATED:
        target = ROOT / name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()


def build() -> None:
    posts = load_posts()
    about = load_page(CONTENT / "about.md", is_post=False)
    SITE["year"] = max([SITE["since"]] + [p.date.year for p in posts])

    clean()

    assets = ROOT / "assets"
    assets.mkdir()
    for f in STATIC.iterdir():
        if f.is_file():
            shutil.copy2(f, assets / f.name)
    (assets / "style.css").write_text(
        (STATIC / "style.css").read_text(encoding="utf-8") + pygments_css(), encoding="utf-8")

    write("index.html", render_home(posts))
    for p in posts:
        write(f"posts/{p.slug}/index.html", render_post(p, posts))
    write("about/index.html", render_about(about))
    write("404.html", render_404())
    write("atom.xml", render_atom(posts))
    write("sitemap.xml", render_sitemap(["/", "/about/"] + [p.url for p in posts]))
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE['url']}/sitemap.xml\n")

    print(f"built {len(posts)} post(s) -> {ROOT}")


if __name__ == "__main__":
    build()
