---
name: init
description: Set up a repo's docs site - a mkdocs.yml with the site's own port, a docs home page and site/ and .cache/ in .gitignore, so `uvx zensical serve` shows the Markdown in docs/ as a site with a sidebar, sections and search. One script writes them and keeps any that exist, so a second run changes nothing. Use when the user asks to set up, start, scaffold or initialize docs, a docs site or Zensical for a repo, or a repo needs a docs site and has no mkdocs.yml.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py *), Bash(uvx zensical build *)
---

# Set up a docs site

Zensical turns a repo's Markdown docs into a site with a sidebar, a section per folder, search, and a list of each page's headings. `uvx zensical serve` shows it in the browser and rebuilds it when a page changes. It reads `mkdocs.yml`, the same file as Material for MkDocs.

`scaffold.py` writes what the site needs, at the repo root, and keeps any of these files that already exist:

- `mkdocs.yml`: the site's name (the repo's folder name), its URL from the `origin` remote, its port, and the theme. It has no `nav` list, so the sidebar shows every page in the docs folder, titled by its `#` heading, and a new page needs no change to the config.
- The port, as `dev_addr`: each repo's site gets its own, from 8100 up, so any number of sites can be served at once. The script records each repo's port in `~/.local/share/docs-site/ports.json` and never gives one to two repos. An existing config keeps its own `dev_addr` unless another repo has that port, and gets the line if it has none.
- `docs/index.md`: the home page, with the site's name as its heading and the description under it.
- `site/` and `.cache/` in `.gitignore`: Zensical builds the site into `site/` and keeps a cache in `.cache/`. A tool that doesn't read `.gitignore`, such as ESLint's flat config, needs both in its own ignores.

Values in `mkdocs.yml` have quotes only where YAML needs them, so a formatter that prefers either kind of quote leaves the file alone.

It makes no other folders or pages, and commits nothing.

## 1. Run the script

Look for a line that says what the project is: the first sentence of the README, or the line under PROJECT.md's heading. If there's one, pass it with `--description`. If the repo keeps its docs in a folder other than `docs/`, such as `.project/docs`, pass that folder with `--docs-dir`. Pass `--name` only if the user gave the site a name.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py --description "A line that says what the project is."
```

Its first line is the repo root, each line after it says whether a file or line was created, kept, added or changed, and its last line gives the site's address. If it exits with `scaffold.py: --docs-dir …`, the folder is outside the repo or is the repo root: ask the user for a folder inside it. Any other `scaffold.py:` message names the file or port at fault, such as a `dev_addr` with no port: show it to the user. On any error the script writes nothing.

## 2. Check that it builds

Build the site from the config the script created or kept, at the repo root it printed:

```
uvx zensical build -f ROOT/mkdocs.yml
```

It ends with `No issues found` and `Build finished`. If `uvx` isn't found, the site needs uv (https://docs.astral.sh/uv/): say so and stop. If the build reports a problem in a page, show it to the user.

## 3. Report

Say which files the script created and which it kept, and that `uvx zensical serve -o` in the repo opens the site at the address it printed.
