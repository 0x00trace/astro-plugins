# docs-site

Sets up a repo's docs site, so the Markdown in its `docs/` folder reads as a site with a sidebar, a section per folder, search, and a list of each page's headings. `/docs-site:init` sets up one repo, and `/docs-site:hub` serves every repo's site at once, each at its own `NAME.localhost` address, with a dashboard that lists them. [Zensical](https://zensical.org) builds and serves the site, from the same `mkdocs.yml` as Material for MkDocs.

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
| `.gitignore` | `site/` and `.cache/` lines, for the built site and Zensical's cache. A tool that doesn't read `.gitignore`, such as ESLint's flat config, needs both in its own ignores. |

Then Claude builds the site once with `uvx zensical build` to check it, and tells you what it created. It makes no other folders or pages, adds no GitHub Pages workflow, and commits nothing.

A repo that keeps its docs somewhere else, such as `.project/docs`, keeps them there: Claude passes the folder to the script, which writes it into `mkdocs.yml` as `docs_dir`.

`zensical new` isn't used because it writes a fixed `nav` list that every new page has to be added to, a demo page, a GitHub Pages workflow, and a placeholder name and URL.

## Read the docs

```
uvx zensical serve -o
```

It builds the site, opens it at its own port, such as http://127.0.0.1:8100, and rebuilds when a page changes. It needs [uv](https://docs.astral.sh/uv/). When the hub is running, the site is already served at `http://NAME.localhost:8099`, so you don't need to start it.

## The hub

```
/docs-site:hub
```

The hub serves every project's docs at once, and lists them on a dashboard:

- `http://localhost:8099` is the dashboard: each project's address, a line about it and a link to its repository.
- `http://NAME.localhost:8099` is a project's site, where NAME is its repo's folder name. `.localhost` names need no setup: browsers send them to your own machine.

It needs Docker with its compose plugin. `/docs-site:hub` installs it, and from then on `/docs-site:init` adds each new repo to it.

### Use the hub

`hub.py` installs the hub and checks it, and Docker Compose stops and starts it. `hub.py` is in the plugin's `scripts/` folder: `~/.claude/plugins/cache/astro-plugins/docs-site/VERSION/scripts/hub.py` in an install, where VERSION is the plugin's version, or `plugins/docs-site/scripts/hub.py` in a clone of this repo. Run it with `python3`. The `docker compose -p docs-site` commands work from any folder.

```
hub.py install                                # write the hub's files and start every site; safe to run again
hub.py install --port 80                      # another port; later runs keep it
hub.py status                                 # whether the dashboard and each site answer; exits 1 if one doesn't
docker compose -p docs-site ps                # each container and how long it has been up
docker compose -p docs-site stop              # stop the dashboard and every site
docker compose -p docs-site start             # start them again
docker compose -p docs-site stop site-NAME    # stop one site; start it the same way
docker compose -p docs-site logs site-NAME    # a site's log, when it isn't answering
hub.py remove                                 # stop the hub, and remove its containers and folder
```

- `start` and `install` both start every site. Use `start` after a `stop`. Use `install` after anything removes the containers, such as `docker compose -p docs-site down`, and after you delete a repo's folder: it writes the hub's files from the repos on record, then starts what isn't running.
- The containers start with Docker, so the hub comes back after a reboot when Docker's service is enabled (`sudo systemctl enable docker`). A site you stopped stays stopped through a reboot until you `start` it.
- `status` reports a site you stopped as `container exited, not answering (502)`, and exits 1.

### How it works

It's a Docker Compose project, `docs-site`, that `hub.py` writes to `~/.local/share/docs-site/hub/` from the repos `/docs-site:init` has set up:

- Each project gets a container running `zensical serve` from Zensical's own image, `zensical/zensical`, in the repo. A page you change is rebuilt and reloads in the browser.
- One Caddy container routes the names to them. Only it has a host port, so `uvx zensical serve` in a repo still works while the hub runs.
- Containers restart if they exit, unless you stopped them. A site whose repo is on a branch with no `mkdocs.yml` comes back by itself within about a minute of the file returning, and until then its address says the site isn't running and how to read its log.

A repo whose folder you delete stops being served, and the next `hub.py install` drops it. The hub's mounts never create a missing folder, which Docker would otherwise make as root where the repo was.

The sites run the Zensical in the image, which changes only when you download it again: `docker compose -f ~/.local/share/docs-site/hub/compose.yml pull`, then `hub.py install`. The proxy sends `Host` and `Origin` as `localhost` to Zensical's server, which answers 400 otherwise, so a Zensical update that changes that check could stop pages reloading on a change.

## Ports

Each repo's site gets its own port for `uvx zensical serve`, so any number of sites can be served at once without the hub. Zensical's default, 8000, would let only one run. The script hands out ports from 8100 up and records each in `~/.local/share/docs-site/ports.json` (or under `$XDG_DATA_HOME`), by repo path:

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
