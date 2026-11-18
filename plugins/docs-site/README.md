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

It needs Docker with its compose plugin. `/docs-site:hub install` installs it, and from then on `/docs-site:init` adds each new repo to it.

### Use the hub

In Claude Code, give `/docs-site:hub` the command to run:

```
/docs-site:hub install    # create the hub, or bring it up to date, and start it
/docs-site:hub start      # start it; refuses when no hub is installed
/docs-site:hub stop       # stop the dashboard and every site
/docs-site:hub status     # whether the dashboard and each site answer
/docs-site:hub remove     # stop the hub, and remove its containers and folder
```

`status`, `start` and `stop` run without asking. `install` downloads about 360 MB of images on its first run, and `remove` deletes the hub's folder, so Claude asks before each.

From a shell, the same commands are `hub.py install`, `start`, `stop`, `status` and `remove`, and `hub.py install --port 80` picks another port, which later runs keep. `hub.py` is in the plugin's `scripts/` folder: `~/.claude/plugins/cache/astro-plugins/docs-site/VERSION/scripts/hub.py` in an install, where VERSION is the plugin's version, or `plugins/docs-site/scripts/hub.py` in a clone of this repo. Run it with `python3`.

- Only `install`, `start`, `stop` and `remove` change whether the hub runs. `/docs-site:init` adds a new repo's container to a stopped hub without starting anything.
- `stop` keeps the hub stopped, through a reboot too, until `start`. Otherwise the hub starts with Docker at boot, when Docker's service is enabled (`sudo systemctl enable docker`).
- `start` writes the hub's files from the repos on record before it starts the sites. So it also brings back containers that something removed, such as `docker compose -p docs-site down`, adds repos set up since the last run, and drops repos whose folder is gone.
- `status` names the command that fixes what it finds: `stopped: hub.py start starts it`, or `no container: hub.py start creates it`. It exits 1 when anything doesn't answer.

Docker Compose handles single sites and logs, from any folder:

```
docker compose -p docs-site ps                # each container and how long it has been up
docker compose -p docs-site stop site-NAME    # stop one site; start it with start site-NAME
docker compose -p docs-site logs site-NAME    # a site's log, when it isn't answering
```

A site stopped this way starts again at the next `install`, `start` or `/docs-site:init`.

### How it works

It's a Docker Compose project, `docs-site`, that `hub.py` writes to `~/.local/share/docs-site/hub/` from the repos `/docs-site:init` has set up:

- Each project gets a container running `zensical serve` from Zensical's own image, `zensical/zensical`, in the repo. A page you change is rebuilt and reloads in the browser.
- One Caddy container routes the names to them. Only it has a host port, so `uvx zensical serve` in a repo still works while the hub runs.
- Containers restart if they exit, unless you stopped them. A site whose repo is on a branch with no `mkdocs.yml` comes back by itself within about a minute of the file returning, and until then its address says the site isn't running and how to read its log.

A repo whose folder you delete stops being served, and the next `hub.py install` or `start` drops it. The hub's mounts never create a missing folder, which Docker would otherwise make as root where the repo was.

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
