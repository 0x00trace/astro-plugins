# docs-site

Sets up a repo's docs site, so the Markdown in its `docs/` folder reads as a site with a sidebar, a section per folder, search, and a list of each page's headings. [Zensical](https://zensical.org) builds and serves the site, from the same `mkdocs.yml` as Material for MkDocs.

```
/plugin install docs-site --marketplace astrosteveo/astro-plugins
```

## Set up a repo

```
/docs-site:init
```

Run it in any repo, or ask Claude to set up a docs site. A script writes three things at the repo root, and keeps any of them that already exist, so a second run changes nothing:

| File | What it holds |
| --- | --- |
| `mkdocs.yml` | The site's name (the repo's folder), its URL from the `origin` remote, its own port as `dev_addr`, and the theme. It has no `nav` list, so every page in the docs folder shows in the sidebar, titled by its `#` heading, with no change to the config. |
| `docs/index.md` | The home page: the site's name as its heading, and a line from the README or PROJECT.md that says what the project is. |
| `.gitignore` | A `site/` line, for the built site. |

Then Claude builds the site once with `uvx zensical build` to check it, and tells you what it created. It makes no other folders or pages, adds no GitHub Pages workflow, and commits nothing.

A repo that keeps its docs somewhere else, such as `.project/docs`, keeps them there: Claude passes the folder to the script, which writes it into `mkdocs.yml` as `docs_dir`.

`zensical new` isn't used because it writes a fixed `nav` list that every new page has to be added to, a demo page, a GitHub Pages workflow, and a placeholder name and URL.

## Read the docs

```
uvx zensical serve -o
```

It builds the site, opens it at its own port, such as http://127.0.0.1:8100, and rebuilds when a page changes. It needs [uv](https://docs.astral.sh/uv/).

## Ports

Each repo's site gets its own port, so any number of sites can be served at once. Zensical's default, 8000, would let only one run. The script hands out ports from 8100 up and records each in `~/.local/share/docs-site/ports.json` (or under `$XDG_DATA_HOME`), by repo path:

- A new repo gets the lowest port that no other repo has and nothing is using right now.
- A repo keeps its port on every later run, even while its own site is running.
- An existing config keeps its own `dev_addr` unless another repo has that port, and then gets a new one. A config without `dev_addr` gets the line.
- A repo whose folder is gone gives its port back.

## The script

```
scaffold.py                                   # in the repo, or any folder in it
scaffold.py --description "What the project is."
scaffold.py --docs-dir .project/docs          # docs kept in another folder
scaffold.py --name "My project"               # a site name other than the folder's
```

It prints the repo root, then a line per file saying whether it was created, kept, added or changed, then the site's address. SSH and HTTPS GitHub remotes become `https://github.com/OWNER/NAME`, and credentials in a remote's URL are left out. Python 3.11 or later, stdlib only.

## Tests

```
python3 -m unittest discover -s plugins/docs-site/tests
claude plugin validate plugins/docs-site
```
