# huangruidtu.github.io

Source of [huangruidtu.github.io](https://huangruidtu.github.io).

No framework: `src/build.py` turns Markdown into plain HTML. GitHub Actions
runs it on every push to `main` and deploys the result to GitHub Pages.
Nothing generated is committed.

```text
src/
  build.py              the whole generator
  requirements.txt      markdown, pygments (pinned)
  content/about.md
  content/posts/*.md    one file per post
  static/               stylesheet, avatar, favicons
.github/workflows/build.yml   build on every push/PR, deploy from main
```

## Writing a post

Add `src/content/posts/<slug>.md`:

```markdown
---
title: Post title
date: 2026-11-16
summary: One or two sentences for the homepage, the feed and link previews.
series: Project retrospectives   # optional
series_part: 3                   # optional, orders posts within a series
draft: true                      # optional, skips the post
---

Body in Markdown.
```

Push to `main` and the site updates itself.

## Previewing locally

```bash
python3 -m venv .venv && .venv/bin/pip install -r src/requirements.txt
.venv/bin/python src/build.py        # writes _site/
python3 -m http.server -d _site 8000
```

## Contact email

The email address is not stored in this repository. The build reads it from
the `SITE_EMAIL` environment variable; in CI that is the repository variable
`SITE_EMAIL` (Settings → Secrets and variables → Actions → Variables). Without
it the site still builds, just without an email link. Anywhere in the content,
`{{contact}}` expands to the GitHub, LinkedIn and email links.

## One-time repository settings

- Settings → Pages → Build and deployment → Source: **GitHub Actions**
- Settings → Secrets and variables → Actions → Variables: `SITE_EMAIL`
