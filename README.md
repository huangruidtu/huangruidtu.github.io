# huangruidtu.github.io

Source and output of [huangruidtu.github.io](https://huangruidtu.github.io).

No framework: `src/build.py` turns Markdown into plain HTML, and GitHub Pages
serves the repository root as-is.

```text
src/
  build.py              the whole generator
  requirements.txt      markdown, pygments (pinned)
  content/about.md
  content/posts/*.md    one file per post
  static/               stylesheet, avatar, favicons
```

Everything else in the root (`index.html`, `posts/`, `about/`, `assets/`,
`atom.xml`, ...) is generated. Don't edit it by hand.

## Writing a post

Add `src/content/posts/<slug>.md`:

```markdown
---
title: Post title
date: 2026-11-16
summary: One or two sentences for the homepage, RSS and link previews.
series: 项目复盘        # optional
series_part: 2          # optional
draft: true             # optional, skips the post
---

Body in Markdown.
```

Then rebuild and commit both the source and the output:

```bash
python3 -m venv .venv && .venv/bin/pip install -r src/requirements.txt
.venv/bin/python src/build.py
```

CI rebuilds on every push and fails if the committed HTML is stale.
