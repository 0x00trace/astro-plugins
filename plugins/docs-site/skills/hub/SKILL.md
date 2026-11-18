---
name: hub
description: Serve every project's docs at once behind one address, with a dashboard that lists them - each site at http://NAME.localhost:8099 and the dashboard at http://localhost:8099, in Docker containers that start at boot and reload a page when it changes. Use when the user asks for a docs hub or dashboard, to see every project's docs in one place, to keep docs sites running, to start or stop the hub, or why a docs site at a .localhost address isn't answering.
argument-hint: "[install | start | stop | status | remove]"
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hub.py status), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hub.py start), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hub.py stop)
---

# Serve every project's docs

The hub is a Docker Compose project, `docs-site`, that serves the docs of every repo `/docs-site:init` has set up:

- `http://localhost:8099` is the dashboard. It lists each project's address, a line about it and its repository.
- `http://NAME.localhost:8099` is a project's site. NAME is the repo's folder name in lowercase, with anything but letters and digits turned into hyphens. A second repo with the same folder name gets `NAME-2`. Browsers and this machine's resolver send every `.localhost` name to this machine, so the names need no setup.
- Each site is a container that runs `zensical serve` in its repo, so a changed page is rebuilt and reloads in the browser. One Caddy container routes the names to them. It's the only one with a host port, so `uvx zensical serve` in a repo still works while the hub runs.
- The containers restart if they exit, and start with Docker at boot, unless they were stopped.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hub.py install    # write the hub's files and start it
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hub.py start      # start the hub, and bring it up to date
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hub.py stop       # stop the dashboard and every site
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hub.py status     # whether the dashboard and each site answer
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hub.py remove     # stop the hub, and remove its containers and folder
```

The skill's argument, when it has one, is the command to run: `/docs-site:hub stop` runs `stop`. Run it and tell the user what it printed. With no argument, do what the user asked for, such as setting up the hub with `install` or checking it with `status`. Run `stop` and `remove` only when the user asks for them.

`status`, `start` and `stop` are pre-approved, since a `start` undoes a `stop` and the other way round. `install` downloads images on its first run and `remove` deletes the hub's folder, so the user approves each of those. The hub's files are in `~/.local/share/docs-site/hub/`: `compose.yml`, the proxy's `caddy/Caddyfile` and the dashboard, `www/index.html`. `install` and `start` write all three from the repos on record, so an edit to one is overwritten.

## Install it

Run `install`. It needs Docker with its compose plugin, and the first run downloads two images, `zensical/zensical` and `caddy:2-alpine`, about 360 MB together. Pass `--port N` for a port other than 8099; later runs keep it.

It prints which of its files it created, updated or kept, then the dashboard's address and each site's. Running it again is safe: it starts only what isn't running and changes only what's out of date. Once a hub is installed, `/docs-site:init` adds a new repo to it without this skill.

Tell the user the dashboard's address and each site's.

## Start and stop it

Only `install`, `start`, `stop` and `remove` change whether the hub runs.

- `stop` stops the dashboard and every site. Docker keeps them stopped, through a reboot too, until `start`.
- `start` does what `install` does on an installed hub: it writes the hub's files from the repos on record, starts every site and waits for each to answer. So it also brings back removed containers, adds repos set up since the last run and drops repos whose folder is gone. When no hub is installed, it says so and runs nothing: `install` sets one up.
- While the hub is stopped, `/docs-site:init` adds a new repo's container without starting anything, and says `the hub is stopped`.
- One site stops with `docker compose -p docs-site stop site-NAME` and starts with `start site-NAME`. It starts again at the next `install`, `start` or `/docs-site:init`.

## A site that isn't answering

`install` and `start` mark a site `not answering yet`. `status` gives each container's state, and exits 1 when anything isn't answering:

- `stopped`: the hub or the site was stopped. Tell the user, and run `start` if they want it running.
- `no container`: the container was removed, such as by `docker compose -p docs-site down`. `start` creates it.
- `container restarting`: `zensical serve` keeps exiting. The usual cause is that the branch checked out in that repo has no `mkdocs.yml`. The site comes back by itself, within about a minute, once the file does.
- `container running` but not answering: the first build is still running, or a page failed to build.

For the last two, read the site's log and show the user what it says:

```
docker compose -p docs-site logs site-NAME
```

The site's own address says the same when its container is down and the proxy runs: "The docs site for NAME is not running", with that command.

A repo whose folder is gone isn't listed, and `start` or `install` drops its container. The hub's mounts never create a missing folder: Docker would make it as root where the repo was.

## Update Zensical

The sites run the Zensical in the image, which changes only when the image is downloaded again:

```
docker compose -f ~/.local/share/docs-site/hub/compose.yml pull
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hub.py install
```

The proxy sends each request to Zensical's server with `Host` and `Origin` set to `localhost`, because that server answers 400 otherwise. If pages stop reloading on a change after an update, check that first: `status` still passes, since the pages themselves are served.
