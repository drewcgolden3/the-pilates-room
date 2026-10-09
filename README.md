# The Pilates Room — Portsmouth, NH

Static site for The Pilates Room, 410 High Street, Portsmouth NH.
Built by The Switchboard Company.

## Build

```sh
python3 tools/build.py                              # production (domain root)
BASE=/the-pilates-room PREVIEW=1 python3 tools/build.py   # staging on GitHub Pages
```

`PREVIEW=1` adds `noindex` and a disallow-all `robots.txt`, so the staging copy
can never compete with the live site for the same content. `BASE` prefixes
every root-absolute path so the site works from a project-pages subpath.

## Where the content lives

- `content/site.json` — every fact on the site: address, hours, rates,
  credentials, FAQs, the What-is-Pilates copy. This is rendered into both the
  visible page **and** the schema.org markup, so the two cannot drift apart.
- `content/recipes-raw.json` — recipes exported from the old WordPress site.
- `content/source-posts/` — plain text of the old Pilates posts, kept for
  reference. Not published.
- `assets/img/` — her photography, re-encoded to two web sizes each.
- `raw/` — untouched originals (gitignored).

## Migration notes

URLs match the old WordPress paths, so nothing that currently ranks moves.
The 60 retired blog posts are generated as meta-refresh stubs pointing at
whatever replaced them (recipes index, What is Pilates, Rates, or home).

## Still to do before launch

- Decap CMS + DecapBridge so Michele can post recipes herself
- Confirm who controls the Namecheap, Cloudflare and Google Business Profile logins
- Find out where the Gravity Forms newsletter signups currently go
- Point DNS at GitHub Pages and rebuild without `PREVIEW`/`BASE`
